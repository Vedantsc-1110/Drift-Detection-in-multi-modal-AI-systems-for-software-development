"""Contract SHACL validation reports (PART3 Task 3.5, §7.2 3.5).

Runs PySHACL over an rdflib data graph and returns a report dict; violations
are REPORTED, never silently discarded, and this module never modifies the
data graph to "fix" them (read-only by construction: it only queries).
"""

from __future__ import annotations

from pathlib import Path

import rdflib
from rdflib.namespace import RDF

SH = "http://www.w3.org/ns/shacl#"


def validate(data: rdflib.Graph, shapes_path) -> dict:
    """Validate data against a shapes file. Returns a report dict."""
    import pyshacl

    shapes = rdflib.Graph()
    shapes.parse(str(shapes_path), format="turtle")
    before = set(data)
    conforms, results_graph, results_text = pyshacl.validate(
        data, shacl_graph=shapes, inference="none", abort_on_first=False)
    assert set(data) == before, "validation must not modify the data graph"
    violations = []
    for result in results_graph.subjects(RDF.type, rdflib.URIRef(SH + "ValidationResult")):
        violations.append({
            "focus": str(results_graph.value(result, rdflib.URIRef(SH + "focusNode"))),
            "path": str(results_graph.value(result, rdflib.URIRef(SH + "resultPath"))),
            "message": str(results_graph.value(result, rdflib.URIRef(SH + "resultMessage"))),
            "severity": str(results_graph.value(result, rdflib.URIRef(SH + "resultSeverity"))).rsplit("#", 1)[-1],
            "shape": str(results_graph.value(result, rdflib.URIRef(SH + "sourceShape"))),
        })
    violations.sort(key=lambda v: (v["message"], v["focus"]))
    return {"conforms": bool(conforms), "violations": violations, "text": results_text}


def format_console(report: dict) -> str:
    """Human-readable rendering of a validation report."""
    lines = ["SHACL validation: %s" % ("CONFORMS" if report["conforms"] else "VIOLATIONS: %d" % len(report["violations"]))]
    for violation in report["violations"]:
        lines.append("- [%s] %s (%s: %s)" % (violation["severity"], violation["message"], violation["focus"], violation["path"]))
    return "\n".join(lines) + "\n"


def validate_file(data_path, shapes_path, out_json=None) -> dict:
    """File-level entry: validate a .ttl file, optionally write JSON report."""
    import json

    data = rdflib.Graph()
    data.parse(str(data_path), format="turtle")
    report = validate(data, shapes_path)
    if out_json is not None:
        serializable = {"conforms": report["conforms"], "violations": report["violations"]}
        Path(out_json).write_text(json.dumps(serializable, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(format_console(report), end="")
    return report
