"""Developer inspection commands over the Oxigraph Context Graph.

Readable terminal output. Every value comes from SPARQL over the store or
from pipeline outputs; nothing is synthesized. Out-of-scope names resolve
to their unresolved-reference evidence instead of invented nodes.
"""
from __future__ import annotations

import json
from pathlib import Path

from . import queries as Q
from .store import ContextStore

NB = "http://example.org/ofbiz/0.1/"
P = "PREFIX ofbiz: <http://example.org/ofbiz/0.1/>\n"

METHOD_LABEL = {
    "xml-attribute-read": "deterministic XML extraction",
    "xml-literal-reference": "deterministic literal reference",
    "implements-chain-resolution": "deterministic implements-chain inference (evidenced)",
    "auto-attributes-expansion": "deterministic auto-attributes expansion (evidenced)",
    "code-literal-scan": "deterministic code literal scan",
    "join-validate": "deterministic join validation",
}


def _svc_uri(name):
    return NB + "service/" + name


def cmd_services(store: ContextStore) -> str:
    rows = store.sparql(Q.q_services())
    lines = ["Services (%d):" % len(rows)]
    engines = {}
    for row in store.sparql(
        P + "SELECT ?name ?engine WHERE { ?s a ofbiz:Service ; ofbiz:name ?name . OPTIONAL { ?s ofbiz:engine ?engine } } ORDER BY ?name"
    ):
        engines[row["name"]] = row.get("engine") or "?"
    for row in rows:
        lines.append("  %-40s [%s]" % (row["name"], engines.get(row["name"], "?")))
    return "\n".join(lines)


def cmd_entities(store: ContextStore) -> str:
    rows = store.sparql(
        P + "SELECT ?name WHERE { ?e a ofbiz:ViewEntity ; ofbiz:name ?name } ORDER BY ?name"
    )
    lines = ["View-entities in scope (%d):" % len(rows)]
    lines += ["  %s" % r["name"] for r in rows]
    lines.append("Note: base entities (e.g. OrderHeader) live outside this run's scope.")
    return "\n".join(lines)


def cmd_eca(store: ContextStore) -> str:
    rows = store.sparql(Q.q_eca_rules())
    lines = ["ECA rules (%d):" % len(rows)]
    for r in rows:
        short = r["eca"].rsplit("/", 1)[-1]
        lines.append(
            "  %s [%s] trigger=%s event=%s operation=%s"
            % (short, (r.get("class") or "").rsplit("/", 1)[-1], r.get("trigger") or "?", r.get("event") or "?", r.get("operation") or "-")
        )
    return "\n".join(lines)


def cmd_service(store: ContextStore, name: str) -> str:
    uri = _svc_uri(name)
    rows = store.sparql(Q.q_fact_provenance(uri))
    if not rows:
        return "Service not found in graph: %s" % name
    detail = store.sparql(
        P + "SELECT ?engine ?loc ?inv ?desc ?defent WHERE {"
        " <%s> a ofbiz:Service . OPTIONAL { <%s> ofbiz:engine ?engine }"
        " OPTIONAL { <%s> ofbiz:implLocation ?loc } OPTIONAL { <%s> ofbiz:implInvoke ?inv }"
        " OPTIONAL { <%s> ofbiz:description ?desc }"
        " OPTIONAL { <%s> ofbiz:defaultEntityName ?defent } }" % ((uri,) * 6)
    )
    d = detail[0] if detail else {}
    impls = store.sparql(
        P + "SELECT ?m WHERE { <%s> ofbiz:implementedBy ?m }" % uri
    )
    impl = impls[0]["m"].split("method/", 1)[-1] if impls else "(none in source)"
    inputs = store.sparql(Q.q_inputs(name))
    outputs = store.sparql(Q.q_outputs(name))
    files = store.sparql(Q.q_service_files(name))
    method_rows = store.sparql(P + "SELECT ?m WHERE { <%s> ofbiz:generatedBy ?ex . ?ex ofbiz:extractionMethod ?m }" % uri)
    method = METHOD_LABEL.get(method_rows[0]["m"] if method_rows else "", "deterministic extraction")
    lines = [
        "Service: %s" % name,
        "",
        "Description:",
        d.get("desc") or "(none)",
        "",
        "Engine:",
        d.get("engine") or "(absent)",
        "",
        "Implementation:",
        impl,
        "",
        "Default entity (stated):",
        d.get("defent") or "(none)",
        "",
        "Inputs (%d):" % len(inputs),
    ]
    lines += ["- %s" % r["param"] for r in inputs] or ["(none)"]
    lines += ["", "Outputs (%d):" % len(outputs)]
    lines += ["- %s" % r["param"] for r in outputs] or ["(none)"]
    lines += ["", "Source:"]
    lines += [f["file"] for f in files] or ["(unknown)"]
    lines += ["", "Provenance:", method]
    return "\n".join(lines)


def cmd_entity(store: ContextStore, name: str, unresolved_path=None) -> str:
    uri = NB + "entity/" + name
    kind = store.sparql(P + "SELECT ?c WHERE { <%s> a ?c }" % uri)
    if not kind:
        lines = ["Entity '%s' has no node in this graph (out of run scope)." % name]
        if unresolved_path and Path(unresolved_path).is_file():
            unresolved = json.loads(Path(unresolved_path).read_text(encoding="utf-8"))
            hits = [u for u in unresolved if u.get("to_name") == name][:15]
            if hits:
                lines.append("Stated references found in unresolved report (%d total):" % len([u for u in unresolved if u.get("to_name") == name]))
                for u in hits:
                    src = u.get("source", {})
                    lines.append("  - %s --%s--> %s  (%s:%s)" % (u.get("from", "?").rsplit("/", 1)[-1], u.get("edge", u.get("via", "?")), name, src.get("file"), src.get("line")))
            else:
                lines.append("No stated references to it either.")
        return "\n".join(lines)
    cls = kind[0]["c"].rsplit("/", 1)[-1]
    attrs = store.sparql(
        P + "SELECT ?a ?role WHERE { <%s> ofbiz:hasAttribute ?x . ?x ofbiz:name ?a . OPTIONAL { ?x ofbiz:role ?role } } ORDER BY ?a" % uri
    )
    lines = ["Entity: %s [%s]" % (name, cls), "", "Attributes (%d):" % len(attrs)]
    lines += ["- %s (%s)" % (a["a"], a.get("role") or "?") for a in attrs] or ["(none)"]
    return "\n".join(lines)


def cmd_source(store: ContextStore, pattern: str) -> str:
    files = store.sparql(
        P + "SELECT DISTINCT ?file ?type WHERE { ?a ofbiz:filePath ?file . OPTIONAL { ?a ofbiz:artifactType ?type } } ORDER BY ?file"
    )
    hits = [f for f in files if pattern in f["file"]]
    if not hits:
        return "No source files matching: %s" % pattern
    lines = ["Source files matching '%s':" % pattern]
    for h in hits:
        n = store.sparql(
            P + "SELECT (COUNT(*) AS ?n) WHERE { ?s ofbiz:definedIn ?a . ?a ofbiz:filePath \"%s\" }" % h["file"]
        )[0]["n"]
        lines.append("  %s [%s] — %s triples defined here" % (h["file"], h.get("type") or "?", n))
    return "\n".join(lines)


def cmd_stats(store: ContextStore) -> str:
    one = lambda q: int(store.sparql(q)[0]["n"])
    n_svc = one(P + "SELECT (COUNT(DISTINCT ?s) AS ?n) WHERE { ?s a ofbiz:Service }")
    n_ent = one(P + "SELECT (COUNT(DISTINCT ?s) AS ?n) WHERE { ?s a ofbiz:ViewEntity }")
    n_eca = one(P + "SELECT (COUNT(DISTINCT ?s) AS ?n) WHERE { ?s a ?c . FILTER(?c IN (ofbiz:EntityECA, ofbiz:ServiceECA)) }")
    n_files = one(P + "SELECT (COUNT(DISTINCT ?a) AS ?n) WHERE { ?a a ofbiz:SourceArtifact }")
    n_facts = one(P + "SELECT (COUNT(DISTINCT ?s) AS ?n) WHERE { ?s ofbiz:definedIn ?a }")
    n_direct = one(P + 'SELECT (COUNT(DISTINCT ?s) AS ?n) WHERE { ?s ofbiz:extractionType "direct" }')
    n_inf = one(P + 'SELECT (COUNT(DISTINCT ?s) AS ?n) WHERE { ?s ofbiz:extractionType "inferred" }')
    return "\n".join(
        [
            "Context Graph stats:",
            "  Services discovered: %d" % n_svc,
            "  Entities discovered (views): %d" % n_ent,
            "  ECA rules discovered: %d" % n_eca,
            "  Source files analyzed: %d" % n_files,
            "  Facts extracted (nodes): %d" % n_facts,
            "  Direct facts: %d" % n_direct,
            "  Inferred facts: %d" % n_inf,
            "  Triples in store: %d" % store.count(),
        ]
    )


def cmd_validate(graph_path, shapes_path) -> str:
    from .validate import validate_graph

    result = validate_graph(graph_path, shapes_path)
    lines = [
        "SHACL validation:",
        "  conforms: %s" % result["conforms"],
        "  violations: %d" % len(result["violations"]),
        "  warnings: %d" % len(result["warnings"]),
    ]
    for v in result["violations"][:10]:
        lines.append("  VIOLATION %s | %s" % (v["focus"], v["message"]))
    return "\n".join(lines)
