"""Pipeline: scan -> parse -> resolve -> emit facts + unresolved + manifest + report."""
from __future__ import annotations

import datetime
import json
from collections import Counter
from pathlib import Path

from . import EXTRACTOR_NAME, EXTRACTOR_VERSION, REPO_ID
from .facts import make_fact, snippet_of, uri
from .parsers import PARSERS
from .provenance import ParseContext, artifact_for, parse_xml
from .scanner import discover

ARTIFACT_TYPES = {
    "component": "component-descriptor",
    "service": "service-def",
    "entity": "entity-model",
    "eca": "eca-mixed",  # refined per file below
    "controller": "controller",
    "gradle": "build-gradle",
}

PIPELINE_ROLES = ("component", "service", "entity", "eca", "controller", "gradle")


def _eca_subtype(path: Path) -> str:
    name = path.name
    if name == "eecas.xml":
        return "entity-eca"
    return "service-eca"


def _sorted_key(fact):
    return (fact["kind"], fact["id"])


def run(repo_root, component_name, out_dir, include_dependencies=False):
    repo_root = Path(repo_root)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    comp_dir = repo_root / "applications" / component_name

    discovered = discover(comp_dir, repo_root, include_dependencies)
    files_meta = []
    all_facts = []
    candidates = []
    errors = []

    for role in PIPELINE_ROLES:
        for path, owner in discovered.get(role, []):
            atype = ARTIFACT_TYPES[role]
            if role == "eca":
                atype = _eca_subtype(path)
            try:
                artifact = artifact_for(repo_root, path, atype)
                tree = None if role == "gradle" else parse_xml(path)
            except Exception as exc:  # noqa: BLE001 - record and continue deterministically
                errors.append({"file": path.relative_to(repo_root).as_posix(), "error": str(exc)})
                continue
            files_meta.append(
                {"relpath": artifact.relpath, "sha256": artifact.sha256, "artifact_type": atype, "role": role, "owner": owner}
            )
            ctx = ParseContext(repo_root=repo_root, repo_id=REPO_ID, artifact=artifact, tree=tree)
            ctx.component_name = owner
            try:
                facts, cands = PARSERS[role](path, ctx)
            except Exception as exc:  # noqa: BLE001
                errors.append({"file": artifact.relpath, "error": "parser %s: %s" % (role, exc)})
                continue
            all_facts.extend(facts)
            candidates.extend(cands)

    service_index = {}  # name -> service fact id
    entity_index = {}  # name -> entity/view fact id
    entity_kind = {}  # name -> kind
    for fact in all_facts:
        if fact["kind"] == "service":
            service_index.setdefault(fact["props"]["name"], fact["id"])
        elif fact["kind"] in ("entity", "view_entity"):
            entity_index.setdefault(fact["props"]["name"], fact["id"])
            entity_kind.setdefault(fact["props"]["name"], fact["kind"])

    resolved_edges = []
    unresolved = []
    edge_counter = Counter()

    def edge_id(pred, from_id, to_id, via):
        fshort = short(from_id)
        tshort = short(to_id)
        key = (pred, fshort, tshort, via)
        edge_counter[key] += 1
        parts = ["edge", pred, fshort, tshort, via]
        if edge_counter[key] > 1:
            parts.append(str(edge_counter[key]))
        return uri(*parts)

    def short(from_id):
        return from_id.rsplit("/", 1)[-1]

    # Deterministic candidate order.
    candidates.sort(key=lambda c: (c["edge"], c["from"], c["to_name"], c["via"]))
    inherit_candidates = []
    for cand in candidates:
        edge = cand["edge"]
        if edge == "param_mode_absent":
            unresolved.append(
                {
                    "kind": "param_mode_absent",
                    "from": cand["from"],
                    "param": cand["to_name"],
                    "via": cand["via"],
                    "source": _src(cand["prov"]),
                }
            )
            continue
        to_kind = cand["to_kind"]
        target_id = None
        if to_kind == "service":
            target_id = service_index.get(cand["to_name"])
        elif to_kind == "entity":
            target_id = entity_index.get(cand["to_name"])
        if target_id is None:
            unresolved.append(
                {
                    "kind": "dangling_reference",
                    "edge": edge,
                    "from": cand["from"],
                    "to_name": cand["to_name"],
                    "to_kind": to_kind,
                    "via": cand["via"],
                    "source": _src(cand["prov"]),
                }
            )
            if cand.get("inherit"):
                inherit_candidates.append(None)  # placeholder to keep accounting simple
            continue
        eid = edge_id(edge, cand["from"], target_id, cand["via"])
        resolved_edges.append(
            make_fact(
                "edge",
                eid,
                {"predicate": edge, "from": cand["from"], "to": target_id, "via": cand["via"]},
                cand["prov"],
            )
        )
        if cand.get("inherit"):
            inherit_candidates.append((cand, target_id))

    # implements-chain param inheritance (fixpoint, sorted, cycle-safe).
    inferred = _inherit_params(all_facts, service_index, inherit_candidates)

    # auto-attributes expansion against in-scope base entities (deterministic join).
    auto_inferred, auto_unresolved = _expand_auto_attributes(all_facts, entity_index, entity_kind)
    inferred.extend(auto_inferred)

    all_facts.extend(resolved_edges)
    all_facts.extend(inferred)
    all_facts.sort(key=_sorted_key)
    unresolved.extend(auto_unresolved)
    unresolved.sort(key=lambda u: (u["kind"], u.get("edge", ""), u.get("from", ""), u.get("to_name", "")))

    extracted_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
    _write_jsonl(out_dir / ("%s-facts.jsonl" % component_name), all_facts)
    _write_json(out_dir / ("%s-unresolved.json" % component_name), unresolved)
    manifest = {
        "extractor": EXTRACTOR_NAME,
        "extractor_version": EXTRACTOR_VERSION,
        "repository": REPO_ID,
        "component": component_name,
        "scope": {
            "include_dependencies": include_dependencies,
            "dependency_files": sorted({f["relpath"] for f in files_meta if f.get("owner") != component_name}),
        },
        "extracted_at": extracted_at,
        "files": sorted(files_meta, key=lambda f: f["relpath"]),
        "counts": dict(Counter(f["kind"] for f in all_facts)),
        "unresolved_count": len(unresolved),
        "errors": errors,
    }
    _write_json(out_dir / ("%s-manifest.json" % component_name), manifest)
    (out_dir / ("%s-report.md" % component_name)).write_text(_report(manifest, all_facts, unresolved), encoding="utf-8")
    return manifest


def _src(prov):
    return {"file": prov.get("file"), "line": prov.get("line"), "xpath": prov.get("xpath")}


def _inherit_params(all_facts, service_index, inherit_candidates):
    """Copy explicit params across implements links (fixpoint). Inferred, evidenced."""
    inferred = []
    params_by_service = {}
    for fact in all_facts:
        if fact["kind"] == "service_param":
            svc_name = fact["props"].get("service") or _service_of_param(fact["id"])
            params_by_service.setdefault(svc_name, []).append(fact)
    # seed with explicit params only
    edges = {}  # (from_name, to_name) -> prov of implements element
    for item in inherit_candidates:
        if not item:
            continue
        cand, _target_id = item
        from_name = cand["from"].rsplit("/", 1)[-1]
        if (from_name, cand["to_name"]) not in edges:
            impl_prov = dict(cand["prov"])
            impl_prov["element"] = cand.get("inherit_el")  # transient, never serialized
            edges[(from_name, cand["to_name"])] = impl_prov
    changed = True
    seen = set()
    used_pids = set()
    while changed:
        changed = False
        for (from_name, to_name) in sorted(edges):
            for param in sorted(params_by_service.get(to_name, []), key=lambda f: f["id"]):
                key = (from_name, param["props"]["name"], param["id"])
                if key in seen:
                    continue
                seen.add(key)
                pname = param["props"]["name"]
                pid = uri("service", from_name, "param", pname, "via", to_name)
                if pid in used_pids:  # interface declared the name twice; keep IDs unique
                    suffix = 2
                    while "%s#%d" % (pid, suffix) in used_pids:
                        suffix += 1
                    pid = "%s#%d" % (pid, suffix)
                used_pids.add(pid)
                impl = edges[(from_name, to_name)]
                impl_el = impl.get("element")
                evidence = [
                    {
                        "file": impl["file"],
                        "line": impl["line"],
                        "xpath": impl["xpath"],
                        "snippet": snippet_of(impl_el) if impl_el is not None else "",
                    },
                    {
                        "file": param["prov"]["file"],
                        "line": param["prov"]["line"],
                        "xpath": param["prov"]["xpath"],
                        "snippet": param["props"].get("decl", ""),
                    },
                ]
                prov = {
                    "repository": param["prov"]["repository"],
                    "file": impl["file"],
                    "line": impl["line"],
                    "xpath": impl["xpath"],
                    "extractor": EXTRACTOR_NAME,
                    "extractor_version": EXTRACTOR_VERSION,
                    "method": "implements-chain-resolution",
                    "extraction_type": "inferred",
                    "evidence": evidence,
                }
                pprops = dict(param["props"])
                pprops["inherited_via"] = to_name
                inferred.append(make_fact("service_param", pid, pprops, prov))
                mode = (param["props"].get("mode") or "").upper()
                if mode in ("IN", "INOUT"):
                    inferred.append(
                        make_fact(
                            "edge",
                            uri("edge", "hasInput", from_name, pname, "via", to_name),
                            {
                                "predicate": "hasInput",
                                "from": uri("service", from_name),
                                "to": pid,
                                "via": "implements-inheritance",
                            },
                            dict(prov),
                        )
                    )
                if mode in ("OUT", "INOUT"):
                    inferred.append(
                        make_fact(
                            "edge",
                            uri("edge", "hasOutput", from_name, pname, "via", to_name),
                            {
                                "predicate": "hasOutput",
                                "from": uri("service", from_name),
                                "to": pid,
                                "via": "implements-inheritance",
                            },
                            dict(prov),
                        )
                    )
                params_by_service.setdefault(from_name, []).append(
                    {"id": pid, "kind": "service_param", "props": pprops, "prov": prov}
                )
                changed = True
    return inferred


def _service_of_param(pid):
    parts = pid.split("/param/")[0].split("/")
    return parts[-1]


def _expand_auto_attributes(all_facts, entity_index, entity_kind):
    """Expand <auto-attributes> against in-scope BASE entities (deterministic join).

    include=pk -> primary-key fields only; nonpk -> the rest; all -> every field.
    Each expanded param is inferred, evidenced by the directive element AND the
    consumed entity field. Directives whose entity is unknown (or a view, which
    has aliases rather than fields) stay unresolved with a reason.
    """
    fields_by_entity = {}
    for fact in all_facts:
        if fact["kind"] == "entity_field":
            fields_by_entity.setdefault(fact["props"]["entity"], []).append(fact)
    inferred = []
    unresolved = []
    used_pids = {f["id"] for f in all_facts if f["kind"] == "service_param"}
    for fact in sorted([f for f in all_facts if f["kind"] == "auto_attributes"], key=lambda f: f["id"]):
        props = fact["props"]
        ref = props.get("entity_ref", "")
        svc = props.get("service", "")
        via = "auto-attributes(include=%s,mode=%s)" % (props.get("include"), props.get("mode"))
        fields = fields_by_entity.get(ref) if entity_kind.get(ref) == "entity" else None
        if not fields:
            reason = "entity-out-of-scope" if ref not in entity_index else "view-aliases-not-fields"
            unresolved.append(
                {
                    "kind": "auto_attributes_unexpanded",
                    "from": svc,
                    "to_name": ref,
                    "via": via,
                    "reason": reason,
                    "source": _src(fact["prov"]),
                }
            )
            continue
        include = (props.get("include") or "").lower()
        if include == "pk":
            wanted = [f for f in fields if f["props"].get("is_primary_key")]
        elif include == "nonpk":
            wanted = [f for f in fields if not f["props"].get("is_primary_key")]
        else:
            wanted = list(fields)
        for field in sorted(wanted, key=lambda f: f["id"]):
            fname = field["props"]["name"]
            pid = uri("service", svc, "param", fname, "via", "auto")
            if pid in used_pids:
                suffix = 2
                while "%s#%d" % (pid, suffix) in used_pids:
                    suffix += 1
                pid = "%s#%d" % (pid, suffix)
            used_pids.add(pid)
            dprov = fact["prov"]
            prov = {
                "repository": dprov["repository"],
                "file": dprov["file"],
                "line": dprov["line"],
                "xpath": dprov["xpath"],
                "extractor": EXTRACTOR_NAME,
                "extractor_version": EXTRACTOR_VERSION,
                "method": "auto-attributes-expansion",
                "extraction_type": "inferred",
                "evidence": [
                    {
                        "file": dprov["file"],
                        "line": dprov["line"],
                        "xpath": dprov["xpath"],
                        "snippet": props.get("decl", ""),
                    },
                    {
                        "file": field["prov"]["file"],
                        "line": field["prov"]["line"],
                        "xpath": field["prov"]["xpath"],
                        "snippet": field["props"].get("decl", ""),
                    },
                ],
            }
            pprops = {
                "name": fname,
                "role": "service-parameter",
                "type": field["props"].get("type", ""),
                "mode": props.get("mode", ""),
                "optional": props.get("optional", ""),
                "expansion_source": ref,
            }
            inferred.append(make_fact("service_param", pid, pprops, prov))
            mode = (props.get("mode") or "").upper()
            if mode in ("IN", "INOUT"):
                inferred.append(
                    make_fact(
                        "edge",
                        pid + "/in",
                        {"predicate": "hasInput", "from": uri("service", svc), "to": pid, "via": "auto-attributes-expansion"},
                        dict(prov),
                    )
                )
            if mode in ("OUT", "INOUT"):
                inferred.append(
                    make_fact(
                        "edge",
                        pid + "/out",
                        {"predicate": "hasOutput", "from": uri("service", svc), "to": pid, "via": "auto-attributes-expansion"},
                        dict(prov),
                    )
                )
    return inferred, unresolved


def _write_jsonl(path, facts):
    with open(path, "w", encoding="utf-8") as fh:
        for fact in facts:
            fh.write(json.dumps(fact, sort_keys=True, ensure_ascii=False) + "\n")


def _write_json(path, obj):
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=2, sort_keys=True)
        fh.write("\n")


def _report(manifest, facts, unresolved):
    lines = []
    lines.append("# Extraction report: component `%s`" % manifest["component"])
    lines.append("")
    lines.append("- Extractor: %s %s" % (manifest["extractor"], manifest["extractor_version"]))
    lines.append("- Repository: %s" % manifest["repository"])
    lines.append("- Extracted at: %s" % manifest["extracted_at"])
    lines.append("- Files parsed: %d (errors: %d)" % (len(manifest["files"]), len(manifest["errors"])))
    lines.append("- Facts: %d; unresolved references: %d" % (len(facts), len(unresolved)))
    lines.append("")
    lines.append("## Files")
    for f in manifest["files"]:
        lines.append("- `%s` (%s)" % (f["relpath"], f["artifact_type"]))
    lines.append("")
    lines.append("## Fact counts by kind")
    for kind in sorted(manifest["counts"]):
        lines.append("- %s: %d" % (kind, manifest["counts"][kind]))
    lines.append("")
    lines.append("## Unresolved (reported, never minted as graph edges)")
    by_kind = Counter(u["kind"] for u in unresolved)
    for kind in sorted(by_kind):
        lines.append("- %s: %d" % (kind, by_kind[kind]))
    lines.append("")
    lines.append("### Examples (first 20)")
    for u in unresolved[:20]:
        lines.append(
            "- [%s] %s --%s--> %s (via %s, %s:%s)"
            % (
                u["kind"],
                u.get("from", "?"),
                u.get("edge", u.get("via", "?")),
                u.get("to_name", u.get("param", "?")),
                u.get("via", "?"),
                (u.get("source") or {}).get("file", "?"),
                (u.get("source") or {}).get("line", "?"),
            )
        )
    if manifest["errors"]:
        lines.append("")
        lines.append("## Errors")
        for e in manifest["errors"]:
            lines.append("- %s: %s" % (e["file"], e["error"]))
    lines.append("")
    lines.append("Note: base entities referenced here (e.g. OrderHeader) are defined in")
    lines.append("`applications/datamodel/entitydef/order-entitymodel.xml`, outside this")
    lines.append("prototype's scope; their references are reported above, not invented.")
    lines.append("")
    return "\n".join(lines)
