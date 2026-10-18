"""Task 3.4 tests: bridge edges (PART3_PLAN Task 3.4, §7.2 3.4).

All five §3.4 types emerge on fixtures; every bridge has a provenance
record; the constrains query returns the fixture policy. No network.
"""

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

rdflib = pytest.importorskip("rdflib")
pytest.importorskip("pyoxigraph")

from contextgraph.bridges import (  # noqa: E402
    BRIDGES_GRAPH,
    BRIDGE_PREDICATES,
    bridges_graph,
    discover_bridges,
    insert_bridges,
)
from contextgraph.contract_store import ContractStore  # noqa: E402
from contextgraph.triple_builder import CTX  # noqa: E402

FIX = PROJECT_ROOT / "tests" / "fixtures" / "contract" / "bridges"
FILES = ("structural.ttl", "tasks.ttl", "semantic.ttl", "contract.ttl", "filing.ttl", "docs.ttl")


@pytest.fixture(scope="module")
def union():
    graph = rdflib.Graph()
    for name in FILES:
        graph.parse(str(FIX / name), format="turtle")
    return graph


@pytest.fixture(scope="module")
def bridges(union):
    return discover_bridges(union)


def test_all_five_types_created(bridges):
    by_type = {}
    for bridge in bridges:
        by_type.setdefault(bridge["p"], []).append(bridge)
    assert set(by_type) == set(BRIDGE_PREDICATES), set(BRIDGE_PREDICATES) - set(by_type)
    assert len(bridges) == 5


def test_expected_endpoints(bridges):
    edges = {(b["p"], str(b["s"]).rsplit("/", 1)[-1], str(b["o"]).rsplit("/", 1)[-1]) for b in bridges}
    assert ("invokesService", "nightly_sync", "findOrders") in edges
    assert ("constrains", "invoiceApproval", "createInvoice") in edges
    assert ("mentionsEntity", "CUAD-1", "Invoice") in edges
    assert ("referencesModule", "F2025", "OrderModule") in edges
    assert ("relatedTo", "Doc2025", "Doc2026") in edges


def test_bridge_provenance_records(bridges):
    graph = bridges_graph(bridges)
    records = list(graph.subjects(rdflib.RDF.type, rdflib.URIRef("http://www.w3.org/ns/prov#Entity")))
    assert len(records) == 5
    for record in records:
        assert next(graph.objects(record, rdflib.URIRef("http://www.w3.org/ns/prov#wasGeneratedBy")), None) is not None
        assert next(graph.objects(record, CTX.confidence), None) is not None


def test_store_insertion_and_constrains_query(bridges, tmp_path):
    store = ContractStore(tmp_path / "store")
    count = insert_bridges(store, bridges)
    assert count > 5 and BRIDGES_GRAPH in store.graphs()
    rows = store.sparql(
        "PREFIX ctx: <http://context.example.org/> "
        "SELECT ?policy WHERE { GRAPH <urn:bridges> { ?policy ctx:constrains ?service } "
        'FILTER(STRENDS(STR(?service), "createInvoice")) }')
    assert len(rows) == 1 and rows[0]["policy"].endswith("invoiceApproval")
    store.close()
