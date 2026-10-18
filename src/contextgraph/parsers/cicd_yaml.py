"""CI/CD GitHub Actions extractor (PART1_PLAN Task 1.6, proposal §7.2 1.3).

PyYAML only. Extracts workflow name, triggers, jobs, steps (uses/run/needs),
plus environment-variable references and secrets usage. Every fact carries
an internal ``graph`` field ``"urn:cicd"`` (serialized by Task 1.7).

Line numbers come from ``yaml.compose`` marks (safe_load alone drops them).
"""

from __future__ import annotations

import re

import yaml

from .. import EXTRACTOR_NAME, EXTRACTOR_VERSION
from ..facts import make_fact, uri

METHOD = "yaml-read"
GRAPH = "urn:cicd"

_SECRETS = re.compile(r"secrets\.([A-Za-z0-9_]+)")
_ENV_REF = re.compile(r"env\.([A-Za-z0-9_]+)")
_SHELL_VAR = re.compile(r"\$([A-Za-z_][A-Za-z0-9_]*)")


def _prov(ctx, line):
    return {
        "repository": ctx.repo_id,
        "file": ctx.artifact.relpath,
        "line": line,
        "xpath": None,
        "extractor": EXTRACTOR_NAME,
        "extractor_version": EXTRACTOR_VERSION,
        "method": METHOD,
        "extraction_type": "direct",
        "evidence": [],
    }


def _scalar(node):
    return node.value if isinstance(node, yaml.ScalarNode) else ""


def _mapping(node):
    """MappingNode -> {scalar_key: value_node} (document order)."""
    out = {}
    if isinstance(node, yaml.MappingNode):
        for k, v in node.value:
            out[_scalar(k)] = v
    return out


def _as_str(node):
    if isinstance(node, yaml.ScalarNode):
        return node.value
    return ""


def _as_list(node):
    if isinstance(node, yaml.SequenceNode):
        return [_scalar(i) for i in node.value]
    if isinstance(node, yaml.ScalarNode):
        return [node.value]
    return []


def _triggers(on):
    """Normalize the `on:` value to [{event, detail}]."""
    if on is None:
        return []
    if isinstance(on, str):
        return [{"event": on, "detail": ""}]
    if isinstance(on, list):
        return [{"event": str(e), "detail": ""} for e in on]
    if isinstance(on, dict):
        out = []
        for event, spec in on.items():
            if spec is None:
                out.append({"event": str(event), "detail": ""})
            elif isinstance(spec, dict):
                for key in sorted(spec):
                    out.append({"event": str(event), "detail": "%s=%s" % (key, spec[key])})
            elif isinstance(spec, list):
                for item in spec:
                    if isinstance(item, dict) and "cron" in item:
                        out.append({"event": str(event), "detail": "cron=%s" % item["cron"]})
                    else:
                        out.append({"event": str(event), "detail": str(item)})
            else:
                out.append({"event": str(event), "detail": str(spec)})
        return out
    return [{"event": str(on), "detail": ""}]


def _secrets_and_env(*texts):
    secrets: set[str] = set()
    env_refs: set[str] = set()
    for text in texts:
        if not isinstance(text, str):
            continue
        secrets.update(_SECRETS.findall(text))
        env_refs.update(_ENV_REF.findall(text))
        env_refs.update(v for v in _SHELL_VAR.findall(text) if v.isupper())
    return sorted(secrets), sorted(env_refs)


def _walk_strings(node):
    if isinstance(node, yaml.ScalarNode):
        yield node.value
    elif isinstance(node, yaml.SequenceNode):
        for item in node.value:
            yield from _walk_strings(item)
    elif isinstance(node, yaml.MappingNode):
        for k, v in node.value:
            yield from _walk_strings(k)
            yield from _walk_strings(v)


def parse(path, ctx):
    text = path.read_text(encoding="utf-8")
    data = yaml.safe_load(text) or {}
    doc = yaml.compose(text)
    root_marks = _mapping(doc) if doc is not None else {}

    name = data.get("name") or path.stem
    # YAML 1.1: unquoted `on:` parses as boolean True (PyYAML core schema).
    on_value = data.get("on", None)
    if on_value is None and True in data:
        on_value = data[True]
    triggers = _triggers(on_value)
    jobs = data.get("jobs") or {}

    jobs_node = _mapping(root_marks.get("jobs")) if root_marks.get("jobs") is not None else {}

    facts: list = []
    candidates: list = []

    facts.append(
        make_fact(
            "cicd_workflow",
            uri("workflow", name),
            {"name": name, "triggers": triggers, "graph": GRAPH},
            _prov(ctx, 1),
        )
    )
    for trig in triggers:
        facts.append(
            make_fact(
                "edge",
                uri("edge", "triggeredBy", name, trig["event"], trig["detail"] or "any"),
                {
                    "predicate": "triggeredBy",
                    "from": uri("workflow", name),
                    "to": uri("event", trig["event"]),
                    "via": "workflow-trigger",
                    "graph": GRAPH,
                },
                _prov(ctx, 1),
            )
        )

    for job_id in sorted(jobs):
        spec = jobs[job_id] or {}
        job_node = jobs_node.get(job_id)
        job_line = (job_node.start_mark.line + 1) if job_node is not None else 1
        needs = spec.get("needs")
        needs_list = needs if isinstance(needs, list) else ([needs] if isinstance(needs, str) else [])
        steps = spec.get("steps") or []
        facts.append(
            make_fact(
                "cicd_job",
                uri("job", name, job_id),
                {
                    "workflow": name,
                    "job_id": job_id,
                    "runs_on": str(spec.get("runs-on", "")),
                    "needs": [str(n) for n in needs_list],
                    "graph": GRAPH,
                },
                _prov(ctx, job_line),
            )
        )
        for need in needs_list:
            facts.append(
                make_fact(
                    "edge",
                    uri("edge", "dependsOn", name, job_id, str(need)),
                    {
                        "predicate": "dependsOn",
                        "from": uri("job", name, job_id),
                        "to": uri("job", name, str(need)),
                        "via": "job-needs",
                        "graph": GRAPH,
                    },
                    _prov(ctx, job_line),
                )
            )
        steps_seq = None
        if job_node is not None:
            for k, v in job_node.value:
                if _scalar(k) == "steps" and isinstance(v, yaml.SequenceNode):
                    steps_seq = v.value
                    break
        for i, step in enumerate(steps):
            step = step or {}
            step_name = str(step.get("name") or step.get("id") or "step-%d" % (i + 1))
            uses = str(step.get("uses") or "")
            run = str(step.get("run") or "")
            with_node_texts = list(_walk_strings(steps_seq[i])) if steps_seq is not None and i < len(steps_seq) else []
            secrets, env_refs = _secrets_and_env(run, *with_node_texts)
            step_line = (steps_seq[i].start_mark.line + 1) if steps_seq is not None and i < len(steps_seq) else job_line
            facts.append(
                make_fact(
                    "cicd_step",
                    uri("step", name, job_id, str(i)),
                    {
                        "workflow": name,
                        "job": job_id,
                        "name": step_name,
                        "uses": uses,
                        "run": run,
                        "secrets": secrets,
                        "env_refs": env_refs,
                        "graph": GRAPH,
                    },
                    _prov(ctx, step_line),
                )
            )
            facts.append(
                make_fact(
                    "edge",
                    uri("edge", "hasStep", name, job_id, str(i)),
                    {
                        "predicate": "hasStep",
                        "from": uri("job", name, job_id),
                        "to": uri("step", name, job_id, str(i)),
                        "via": "job-step",
                        "graph": GRAPH,
                    },
                    _prov(ctx, step_line),
                )
            )
            if uses:
                facts.append(
                    make_fact(
                        "edge",
                        uri("edge", "usesAction", name, job_id, str(i)),
                        {
                            "predicate": "usesAction",
                            "from": uri("step", name, job_id, str(i)),
                            "to": uri("action", uses),
                            "via": "step-uses",
                            "graph": GRAPH,
                        },
                        _prov(ctx, step_line),
                    )
                )
    return facts, candidates
