"""Parser: controller.xml routes + build.gradle module deps (PART1_PLAN Task 1.3).

Direct facts only; cross-module/service name references are candidates
resolved by the pipeline (never minted as edges here).
"""

from __future__ import annotations

import re

from ..facts import base_prov, make_fact, uri
from ..provenance import localname

CTRL_METHOD = "xml-attribute-read"
GRADLE_METHOD = "gradle-dependency-read"
REF_METHOD = "xml-literal-reference"

# Matches: implementation project(':applications:party') / api project(":foo")
_PROJECT_DEP = re.compile(
    r"""(?P<config>\w+)\s+project\(\s*['"](?P<proj>[^'"]+)['"]\s*\)""",
)
# Matches: implementation 'org.foo:bar:1.2' / api("g:n:v")
_EXTERNAL_DEP = re.compile(
    r"""(?P<config>\w+)\s*[( ]\s*['"](?P<coord>[^'":\s]+:[^'":\s]+(?::[^'":\s]+)?)['"]\s*\)?""",
)


def parse_controller(path, ctx):
    """Parse controller.xml: <request-map uri> + <event> + <response>."""
    facts = []
    candidates = []
    root = ctx.tree.getroot()
    for req in root.iter():
        if localname(req) != "request-map":
            continue
        req_uri = req.get("uri", "")
        if not req_uri:
            continue
        rid = uri("route", ctx.component_name, req_uri)
        event_type, event_invoke = "", ""
        responses = []
        for child in req:
            tag = localname(child)
            if tag == "event":
                event_type = child.get("type", "")
                event_invoke = child.get("invoke", "")
            elif tag == "response":
                responses.append(
                    {
                        "name": child.get("name", ""),
                        "type": child.get("type", ""),
                        "value": child.get("value", ""),
                    }
                )
        facts.append(
            make_fact(
                "route",
                rid,
                {
                    "uri": req_uri,
                    "component": ctx.component_name,
                    "event_type": event_type,
                    "event_invoke": event_invoke,
                    "responses": responses,
                },
                base_prov(ctx, req, CTRL_METHOD),
            )
        )
        if event_type == "service" and event_invoke:
            candidates.append(
                {
                    "edge": "referencesService",
                    "from": rid,
                    "to_name": event_invoke,
                    "to_kind": "service",
                    "via": "controller-event",
                    "prov": base_prov(ctx, req, REF_METHOD),
                }
            )
    return facts, candidates


def parse_gradle(path, ctx):
    """Parse build.gradle dependencies block (regex, read-only, no eval)."""
    from .. import EXTRACTOR_NAME, EXTRACTOR_VERSION

    facts = []
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    in_deps = False
    depth = 0
    for lineno, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not in_deps:
            if re.search(r"\bdependencies\s*\{", stripped):
                in_deps = True
                depth = stripped.count("{") - stripped.count("}")
            continue
        depth += stripped.count("{") - stripped.count("}")
        if depth < 0:
            in_deps = False
            continue
        if not stripped or stripped.startswith("//"):
            continue
        match = _PROJECT_DEP.search(stripped) or _EXTERNAL_DEP.search(stripped)
        if not match:
            continue
        target = match.group("proj") if "proj" in match.groupdict() and match.group("proj") else match.group("coord")
        config = match.group("config")
        prov = {
            "repository": ctx.repo_id,
            "file": ctx.artifact.relpath,
            "line": lineno,
            "xpath": None,
            "extractor": EXTRACTOR_NAME,
            "extractor_version": EXTRACTOR_VERSION,
            "method": GRADLE_METHOD,
            "extraction_type": "direct",
            "evidence": [],
        }
        facts.append(
            make_fact(
                "module_dependency",
                uri("module", ctx.component_name, "depends", re.sub(r"[^A-Za-z0-9_.-]+", "_", target)),
                {"module": ctx.component_name, "configuration": config, "depends_on": target},
                prov,
            )
        )
        if depth <= 0 and stripped.endswith("}"):
            in_deps = False
    return facts, []


def parse(path, ctx):
    """Dispatcher for the legacy single-filename plan module (by suffix/name)."""
    name = path.name
    if name == "build.gradle":
        return parse_gradle(path, ctx)
    return parse_controller(path, ctx)
