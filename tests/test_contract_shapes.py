"""Task 3.2 tests: contract SHACL shapes (PART3_PLAN Task 3.2, §7.2 3.5).

Shapes parse; PySHACL loads them; valid fixture conforms; invalid fixture
triggers each documented message. No network.
"""

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

rdflib = pytest.importorskip("rdflib")
pyshacl = pytest.importorskip("pyshacl")

ONTOLOGY = PROJECT_ROOT / "ontology" / "contract-shapes.ttl"
FIX = PROJECT_ROOT / "tests" / "fixtures" / "contract"

MESSAGES = [
    "Every Service must have ctx:definedIn.",
    "Every probabilistic fact must have ctx:confidence.",
    "Every probabilistic fact must have ctx:extractedBy.",
    "Every Contract must have at least one ctx:hasClause.",
]


def _validate(data_path):
    data = rdflib.Graph()
    data.parse(str(data_path), format="turtle")
    shapes = rdflib.Graph()
    shapes.parse(str(ONTOLOGY), format="turtle")
    conforms, results_graph, results_text = pyshacl.validate(
        data, shacl_graph=shapes, inference="none", abort_on_first=False)
    return conforms, results_graph, results_text


def test_shapes_parse():
    shapes = rdflib.Graph()
    shapes.parse(str(ONTOLOGY), format="turtle")
    assert len(shapes) > 10


def test_valid_fixture_conforms():
    conforms, _, text = _validate(FIX / "shacl_valid.ttl")
    assert conforms, text


def test_invalid_fixture_triggers_each_message():
    conforms, _, text = _validate(FIX / "shacl_invalid.ttl")
    assert not conforms
    for message in MESSAGES:
        assert message in text, message
