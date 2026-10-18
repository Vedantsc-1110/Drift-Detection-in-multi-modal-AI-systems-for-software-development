"""Task 4.1 tests: drift fixtures (PART4_PLAN Task 4.1, §7.3 scenario inputs).

V(n) graph, agent snapshots A/B/C, and re-extraction output parse with
rdflib and contain the documented triples. The git repo fixture is created
at runtime in tmp_path (see test_drift_change_detector.py). No network.
"""

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

rdflib = pytest.importorskip("rdflib")

FIX = PROJECT_ROOT / "tests" / "fixtures" / "drift"
CTX = "http://context.example.org/"


def _load(name):
    graph = rdflib.Graph()
    graph.parse(str(FIX / name), format="turtle")
    return graph


def test_vn_contains_findorders_with_provenance():
    graph = _load("vn.ttl")
    assert len(graph) > 10
    service = rdflib.URIRef(CTX + "findOrders")
    assert (service, rdflib.RDF.type, rdflib.URIRef(CTX + "Service")) in graph
    conf = list(graph.objects(service, rdflib.URIRef(CTX + "confidence")))
    assert len(conf) == 1 and float(conf[0]) == 1.0
    assert (service, rdflib.URIRef(CTX + "factType"), rdflib.Literal("deterministic")) in graph
    assert next(graph.objects(service, rdflib.URIRef(CTX + "definedIn")), None) is not None


def test_snapshot_contents():
    snap_a = _load("snap_a.ttl")
    services = {s for s in snap_a.subjects(rdflib.RDF.type, rdflib.URIRef(CTX + "Service"))}
    assert {str(s) for s in services} == {CTX + "createOrder", CTX + "findOrders"}
    snap_b = _load("snap_b.ttl")
    assert (rdflib.URIRef(CTX + "createInvoice"), rdflib.RDF.type, rdflib.URIRef(CTX + "Service")) in snap_b
    assert (rdflib.URIRef(CTX + "Invoice"), rdflib.RDF.type, rdflib.URIRef(CTX + "Entity")) in snap_b
    snap_c = _load("snap_c.ttl")
    assert (rdflib.URIRef(CTX + "etl_task"), rdflib.URIRef(CTX + "invokesService"),
            rdflib.URIRef(CTX + "findOrders")) in snap_c


def test_reextraction_shows_rename_with_new_param():
    graph = _load("reextraction.ttl")
    service = rdflib.URIRef(CTX + "searchOrders")
    assert (service, rdflib.RDF.type, rdflib.URIRef(CTX + "Service")) in graph
    params = list(graph.objects(service, rdflib.URIRef(CTX + "hasInputParam")))
    assert len(params) == 1 and str(params[0]).endswith("partyId")
    assert (rdflib.URIRef(CTX + "findOrders"), rdflib.RDF.type, rdflib.URIRef(CTX + "Service")) not in graph
