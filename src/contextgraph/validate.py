"""SHACL validation of the generated Context Graph (pyshacl).

Returns (conforms, violations, warnings, report_text, report_graph_ttl).
conforms is False only on sh:Violation results; sh:Warning results are
reported but do not fail the graph.
"""
from __future__ import annotations

from pyshacl import validate
from rdflib import Graph, Namespace

SH = Namespace("http://www.w3.org/ns/shacl#")


def validate_graph(graph_path, shapes_path):
    data = Graph()
    data.parse(str(graph_path), format="turtle")
    shapes = Graph()
    shapes.parse(str(shapes_path), format="turtle")
    _raw_conforms, report_graph, report_text = validate(
        data,
        shacl_graph=shapes,
        inference=None,
        abort_on_first=False,
        meta_shacl=False,
        debug=False,
    )
    violations, warnings = [], []
    for result in report_graph.query(
        "SELECT ?r ?sev ?path ?msg ?focus WHERE {"
        " ?r a sh:ValidationResult ; sh:resultSeverity ?sev ;"
        " sh:focusNode ?focus ; sh:sourceConstraintComponent ?c ."
        " OPTIONAL { ?r sh:resultPath ?path }"
        " OPTIONAL { ?r sh:resultMessage ?msg } }"
    ):
        _r, sev, path, msg, focus = result
        entry = {"focus": str(focus), "path": str(path) if path else "", "message": str(msg) if msg else ""}
        if sev == SH.Violation:
            violations.append(entry)
        else:
            warnings.append(entry)
    violations.sort(key=lambda e: (e["focus"], e["path"]))
    warnings.sort(key=lambda e: (e["focus"], e["path"]))
    # Spec-correct conformance: only sh:Violation fails the graph. (pyshacl's
    # raw boolean counts warnings too, so we derive it from severities.)
    return {
        "conforms": len(violations) == 0,
        "violations": violations,
        "warnings": warnings,
        "report_text": report_text,
        "report_graph_ttl": report_graph.serialize(format="turtle"),
    }
