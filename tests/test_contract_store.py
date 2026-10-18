"""Task 3.3 tests: contract quad store (PART3_PLAN Task 3.3, §7.2 3.3).

Seven §4 Named Graphs load in isolation; export round-trips; §5 metadata
verification passes on fixtures and fails loudly on the bad fixture.
"""

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

rdflib = pytest.importorskip("rdflib")
pytest.importorskip("pyoxigraph")

from contextgraph.contract_store import GRAPH_FILES, ContractStore  # noqa: E402

GRAPHS = PROJECT_ROOT / "tests" / "fixtures" / "contract" / "graphs"


@pytest.fixture()
def store(tmp_path):
    marquee = ContractStore(tmp_path / "store")
    counts = marquee.load_directory(GRAPHS)
    assert set(counts) == set(GRAPH_FILES), "bad.ttl must not load via load_directory"
    yield marquee
    marquee.close()


def test_all_seven_graphs_present(store):
    assert store.graphs() == sorted(GRAPH_FILES)
    for graph_uri in GRAPH_FILES:
        assert store.count(graph_uri) > 0, graph_uri


def test_graphs_isolated(store):
    services_in_airflow = store.sparql(
        "PREFIX ctx: <http://context.example.org/> "
        "SELECT ?s WHERE { GRAPH <urn:airflow> { ?s a ctx:Service } }")
    assert services_in_airflow == []
    services_in_structural = store.sparql(
        "PREFIX ctx: <http://context.example.org/> "
        "SELECT ?s WHERE { GRAPH <urn:ofbiz_structural> { ?s a ctx:Service } }")
    assert len(services_in_structural) == 1


def test_export_round_trip(store, tmp_path):
    out = tmp_path / "structural.ttl"
    count = store.export_graph("urn:ofbiz_structural", out)
    assert count == store.count("urn:ofbiz_structural") > 0
    reparsed = rdflib.Graph()
    reparsed.parse(str(out), format="turtle")
    assert len(reparsed) == count


def test_verify_passes_on_fixtures(store):
    for graph_uri in GRAPH_FILES:
        assert store.verify_metadata(graph_uri) == [], graph_uri


def test_verify_fails_loudly_on_bad_fixture(tmp_path):
    marquee = ContractStore(tmp_path / "bad")
    marquee.load_file(GRAPHS / "bad.ttl", "urn:quarantine")
    errors = marquee.verify_metadata("urn:quarantine")
    assert errors, "expected loud failure for provenance-free subjects"
    assert any("orphanService" in e and "confidence" in e for e in errors)
    marquee.close()
