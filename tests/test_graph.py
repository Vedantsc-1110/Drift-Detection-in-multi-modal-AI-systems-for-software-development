"""RDF graph tests: validity (rdflib), determinism, spot checks on real data."""
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent

rdflib = pytest.importorskip("rdflib")

NB = "http://example.org/ofbiz/0.1/"
OFBIZ = "http://example.org/ofbiz/0.1/"


@pytest.fixture(scope="module")
def graph_path(tmp_path_factory):
    out = tmp_path_factory.mktemp("graph") / "order-graph.ttl"
    repo = PROJECT_ROOT / "dataset" / "apache-ofbiz-24.09.07"
    assert repo.is_dir(), "OFBiz dataset missing"
    # Regenerate facts deterministically, then build with a fixed timestamp.
    subprocess.run(
        [sys.executable, "extract.py", "--root", str(repo), "--component", "order", "--out", str(out.parent / "fx")],
        cwd=PROJECT_ROOT,
        check=True,
    )
    subprocess.run(
        [
            sys.executable,
            "build_graph.py",
            "--facts",
            str(out.parent / "fx" / "order-facts.jsonl"),
            "--manifest",
            str(out.parent / "fx" / "order-manifest.json"),
            "--out",
            str(out),
            "--as-of",
            "2026-01-01T00:00:00+00:00",
        ],
        cwd=PROJECT_ROOT,
        check=True,
    )
    return out


@pytest.fixture(scope="module")
def graph(graph_path):
    g = rdflib.Graph()
    g.parse(str(graph_path), format="turtle")
    return g


def test_parses_and_has_scale(graph):
    assert len(graph) > 20000


def test_deterministic_bytes(graph_path):
    second = graph_path.parent / "order-graph-2.ttl"
    repo = PROJECT_ROOT / "dataset" / "apache-ofbiz-24.09.07"
    subprocess.run(
        [
            sys.executable,
            "build_graph.py",
            "--facts",
            str(graph_path.parent / "fx" / "order-facts.jsonl"),
            "--manifest",
            str(graph_path.parent / "fx" / "order-manifest.json"),
            "--out",
            str(second),
            "--as-of",
            "2026-01-01T00:00:00+00:00",
        ],
        cwd=PROJECT_ROOT,
        check=True,
    )
    assert graph_path.read_bytes() == second.read_bytes()


def _q(graph, sparql):
    return list(graph.query(sparql))


def test_service_node_and_method(graph):
    OFB = rdflib.Namespace(OFBIZ)
    svc = rdflib.URIRef(NB + "service/cancelOrderItemNoActions")
    assert (svc, rdflib.RDF.type, OFB.Service) in graph
    assert (svc, OFB.engine, rdflib.Literal("java")) in graph
    impls = list(graph.objects(svc, OFB.implementedBy))
    assert len(impls) == 1
    (method,) = impls
    assert (method, rdflib.RDF.type, OFB.Method) in graph
    assert "OrderServices" in str(method) and str(method).endswith("#cancelOrderItem")


def test_inputs_outputs_present(graph):
    OFB = rdflib.Namespace(OFBIZ)
    n_in = len(_q(graph, "SELECT ?s WHERE { ?s <%shasInput> ?o }" % OFBIZ))
    n_out = len(_q(graph, "SELECT ?s WHERE { ?s <%shasOutput> ?o }" % OFBIZ))
    assert n_in > 500 and n_out > 40


def test_eca_applies_to_and_conditions(graph):
    OFB = rdflib.Namespace(OFBIZ)
    n_app = len(_q(graph, "SELECT ?s WHERE { ?s <%sappliesTo> ?o }" % OFBIZ))
    assert n_app > 50
    n_cond = len(_q(graph, "SELECT ?s WHERE { ?s <%shasCondition> ?o }" % OFBIZ))
    assert n_cond >= 80
    n_trig = len(_q(graph, "SELECT ?s WHERE { ?s <%striggersService> ?o }" % OFBIZ))
    assert n_trig > 50


def test_every_service_has_provenance(graph):
    OFB = rdflib.Namespace(OFBIZ)
    services = _q(graph, "SELECT ?s WHERE { ?s a <%sService> }" % OFBIZ)
    # 468 <service> elements in source, but createQuoteWorkEffort is defined
    # twice in services_quote.xml -> one merged node.
    assert len(services) == 467
    for (svc,) in services:
        assert (svc, OFB.definedIn, None) in graph
        assert (svc, OFB.extractionType, None) in graph


def test_duplicate_source_definition_merges(graph):
    OFB = rdflib.Namespace(OFBIZ)
    dup = rdflib.URIRef(NB + "service/createQuoteWorkEffort")
    assert (dup, rdflib.RDF.type, OFB.Service) in graph


def test_no_invented_out_of_scope_entities(graph):
    OFB = rdflib.Namespace(OFBIZ)
    assert (rdflib.URIRef(NB + "entity/OrderHeader"), rdflib.RDF.type, OFB.Entity) not in graph
    assert (rdflib.URIRef(NB + "entity/OrderHeader"), rdflib.RDF.type, OFB.ViewEntity) not in graph


def test_no_confidence_anywhere(graph):
    OFB = rdflib.Namespace(OFBIZ)
    assert len(list(graph.subject_objects(OFB.confidence))) == 0
