"""Task 3.10 tests: Part 3 CONTRACT.md compliance handoff (PART3_PLAN Task 3.10).

Ontology declares exactly the §2 classes / §3 properties (no more, no
fewer — relatedTo stays out, flagged since 3.4); the store holds exactly
the seven §4 Named Graphs plus urn:bridges; SHACL messages match the
documented set. No network.
"""

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

rdflib = pytest.importorskip("rdflib")
pytest.importorskip("pyoxigraph")

from rdflib.namespace import OWL, RDF  # noqa: E402

from contextgraph.bridges import BRIDGES_GRAPH, discover_bridges, insert_bridges  # noqa: E402
from contextgraph.contract_store import GRAPH_FILES, ContractStore  # noqa: E402
from contextgraph.contract_validate import validate  # noqa: E402

ONTOLOGY = PROJECT_ROOT / "ontology" / "contract-ontology.ttl"
SHAPES = PROJECT_ROOT / "ontology" / "contract-shapes.ttl"
GRAPHS = PROJECT_ROOT / "tests" / "fixtures" / "contract" / "graphs"
BRIDGES_FIX = PROJECT_ROOT / "tests" / "fixtures" / "contract" / "bridges"
CTX = "http://context.example.org/"

SECTION_2 = {"Module", "Service", "Entity", "Field", "JavaClass", "JavaMethod",
             "ECA", "DAG", "Task", "Workflow", "Job", "Step", "Document",
             "BusinessConcept", "Policy", "BusinessRule", "Contract", "Clause",
             "Party", "Filing", "Section", "RiskFactor"}

SECTION_3 = {"calls", "implementedBy", "hasField", "relatesTo", "invokesService",
             "constrains", "mentionsEntity", "hasClause", "belongsToConcept",
             "referencesModule", "mentionsProcess", "engine", "hasInputParam",
             "hasOutputParam", "hasParameter", "hasTask", "dependsOn",
             "scheduledAt", "operatorType", "triggeredBy", "hasStep",
             "usesAction", "clauseType", "imports", "definedIn", "atLine",
             "sourceLocation", "sourceHash", "businessPurpose", "confidence",
             "factType", "extractedBy", "supportType"}

MESSAGES = {"Every Service must have ctx:definedIn.",
            "Every probabilistic fact must have ctx:confidence.",
            "Every probabilistic fact must have ctx:extractedBy.",
            "Every Contract must have at least one ctx:hasClause."}


def test_ontology_matches_sections_2_and_3_exactly():
    graph = rdflib.Graph()
    graph.parse(str(ONTOLOGY), format="turtle")
    classes = {str(s)[len(CTX):] for s in graph.subjects(RDF.type, OWL.Class)
               if str(s).startswith(CTX)}
    assert classes == SECTION_2, (classes - SECTION_2, SECTION_2 - classes)
    props = set()
    for kind in (OWL.ObjectProperty, OWL.DatatypeProperty):
        props.update(str(s)[len(CTX):] for s in graph.subjects(RDF.type, kind)
                     if str(s).startswith(CTX))
    assert props == SECTION_3, (props - SECTION_3, SECTION_3 - props)
    assert "relatedTo" not in props, "relatedTo is §3.4-only; stays flagged, not declared"


def test_store_uses_exactly_seven_graphs_plus_bridges(tmp_path):
    store = ContractStore(tmp_path / "store")
    try:
        counts = store.load_directory(GRAPHS)
        assert set(counts) == set(GRAPH_FILES)
        union = rdflib.Graph()
        for path in sorted(BRIDGES_FIX.glob("*.ttl")):
            union.parse(str(path), format="turtle")
        inserted = insert_bridges(store, discover_bridges(union))
        assert inserted > 0
        assert store.graphs() == sorted([*GRAPH_FILES, BRIDGES_GRAPH])
        for graph_uri in GRAPH_FILES:
            assert store.verify_metadata(graph_uri) == [], graph_uri
    finally:
        store.close()


def test_shacl_messages_match_documented_set():
    data = rdflib.Graph()
    data.parse(str(PROJECT_ROOT / "tests" / "fixtures" / "contract" / "shacl_invalid.ttl"))
    report = validate(data, SHAPES)
    assert not report["conforms"]
    assert {v["message"] for v in report["violations"]} == MESSAGES
