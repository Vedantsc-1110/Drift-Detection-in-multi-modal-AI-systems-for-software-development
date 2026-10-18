"""Task 3.5 tests: SHACL validation reports (PART3_PLAN Task 3.5, §7.2 3.5).

Valid fixture → zero violations; invalid fixture → exactly the documented
messages; validation never modifies data. No network.
"""

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

rdflib = pytest.importorskip("rdflib")
pytest.importorskip("pyshacl")

from contextgraph.contract_validate import (  # noqa: E402
    format_console,
    validate,
    validate_file,
)

SHAPES = PROJECT_ROOT / "ontology" / "contract-shapes.ttl"
FIX = PROJECT_ROOT / "tests" / "fixtures" / "contract"

MESSAGES = [
    "Every Contract must have at least one ctx:hasClause.",
    "Every Service must have ctx:definedIn.",
    "Every probabilistic fact must have ctx:confidence.",
    "Every probabilistic fact must have ctx:extractedBy.",
]


def _graph(name):
    graph = rdflib.Graph()
    graph.parse(str(FIX / name), format="turtle")
    return graph


def test_valid_graph_zero_violations():
    report = validate(_graph("shacl_valid.ttl"), SHAPES)
    assert report["conforms"] is True
    assert report["violations"] == []


def test_violations_carry_documented_messages():
    report = validate(_graph("shacl_invalid.ttl"), SHAPES)
    assert report["conforms"] is False
    assert sorted(v["message"] for v in report["violations"]) == sorted(MESSAGES)
    assert all(v["severity"] == "Violation" for v in report["violations"])
    assert "CONFORMS" not in format_console(report)


def test_file_entry_writes_json_and_preserves_data(tmp_path):
    data_path = FIX / "shacl_invalid.ttl"
    before = set(_graph("shacl_invalid.ttl"))
    out = tmp_path / "report.json"
    report = validate_file(data_path, SHAPES, out_json=out)
    assert not report["conforms"] and out.is_file()
    assert set(_graph("shacl_invalid.ttl")) == before
