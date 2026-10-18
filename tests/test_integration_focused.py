"""Focused integration test: eecas.xml + services.xml + services_order.xml -> graph.

Nothing is hardcoded into the extractor: these tests parse the ACTUAL XML
files through the real pipeline and assert the expected facts exist in the
generated RDF graph (plus the honesty guarantees for out-of-scope targets).
"""
import json
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent

rdflib = pytest.importorskip("rdflib")

NB = "http://example.org/ofbiz/0.1/"
OFBIZ = NB
SERVICES_XML = "applications/order/servicedef/services.xml"
SVC_ORDER_XML = "applications/order/servicedef/services_order.xml"
EECAS_XML = "applications/order/entitydef/eecas.xml"


@pytest.fixture(scope="module")
def bundle(tmp_path_factory):
    """Run the real extractor + RDF builder; return (graph, unresolved, facts_dir)."""
    work = tmp_path_factory.mktemp("focused")
    fx = work / "fx"
    repo = PROJECT_ROOT / "dataset" / "apache-ofbiz-24.09.07"
    assert repo.is_dir(), "OFBiz dataset missing"
    subprocess.run(
        [sys.executable, "extract.py", "--root", str(repo), "--component", "order", "--out", str(fx)],
        cwd=PROJECT_ROOT,
        check=True,
    )
    ttl = work / "order-graph.ttl"
    subprocess.run(
        [
            sys.executable,
            "build_graph.py",
            "--facts",
            str(fx / "order-facts.jsonl"),
            "--manifest",
            str(fx / "order-manifest.json"),
            "--out",
            str(ttl),
            "--as-of",
            "2026-01-01T00:00:00+00:00",
        ],
        cwd=PROJECT_ROOT,
        check=True,
    )
    graph = rdflib.Graph()
    graph.parse(str(ttl), format="turtle")
    unresolved = json.loads((fx / "order-unresolved.json").read_text(encoding="utf-8"))
    return graph, unresolved, fx


@pytest.fixture(scope="module")
def graph(bundle):
    return bundle[0]


@pytest.fixture(scope="module")
def unresolved(bundle):
    return bundle[1]


OFB = rdflib.Namespace(OFBIZ)
RDF = rdflib.RDF


def svc(name):
    return rdflib.URIRef(NB + "service/" + name)


# ---------------- storeOrder (services.xml) ----------------


def test_storeOrder_binding(graph):
    s = svc("storeOrder")
    assert (s, RDF.type, OFB.Service) in graph
    assert (s, OFB.engine, rdflib.Literal("java")) in graph
    assert (s, OFB.implLocation, rdflib.Literal("org.apache.ofbiz.order.order.OrderServices")) in graph
    assert (s, OFB.implInvoke, rdflib.Literal("createOrder")) in graph
    assert (s, OFB.description, rdflib.Literal("Creates order entities")) in graph
    assert (s, OFB.definedIn, rdflib.URIRef(NB + "source/" + SERVICES_XML)) in graph


def test_storeOrder_implementation(graph):
    (method,) = list(graph.objects(svc("storeOrder"), OFB.implementedBy))
    assert (method, RDF.type, OFB.Method) in graph
    assert str(method).endswith("#createOrder") and "OrderServices" in str(method)


EXPECTED_INPUTS = {
    "partyId": ("String", "false"),
    "orderItems": ("List", "false"),
    "currencyUom": ("String", "false"),
    "grandTotal": ("BigDecimal", "true"),
    "taxAmount": ("BigDecimal", "true"),
}


@pytest.mark.parametrize("pname,typ_opt", list(EXPECTED_INPUTS.items()))
def test_storeOrder_inputs(graph, pname, typ_opt):
    typ, opt = typ_opt
    p = rdflib.URIRef(NB + "service/storeOrder/param/" + pname)
    assert (p, RDF.type, OFB.Attribute) in graph
    assert (p, OFB.attrType, rdflib.Literal(typ)) in graph
    assert (p, OFB.paramMode, rdflib.Literal("IN")) in graph
    assert (p, OFB.optional, rdflib.Literal(opt)) in graph
    assert (svc("storeOrder"), OFB.hasInput, p) in graph
    assert (p, OFB.definedIn, rdflib.URIRef(NB + "source/" + SERVICES_XML)) in graph


def test_storeOrder_output_statusId(graph):
    p = rdflib.URIRef(NB + "service/storeOrder/param/statusId")
    assert (p, OFB.paramMode, rdflib.Literal("OUT")) in graph
    assert (p, OFB.optional, rdflib.Literal("false")) in graph
    assert (svc("storeOrder"), OFB.hasOutput, p) in graph


# ---------------- OrderHeader ECA (eecas.xml) ----------------


def _order_header_eca(graph):
    hits = [
        eca
        for eca in graph.subjects(OFB.triggerEntityName, rdflib.Literal("OrderHeader"))
        if (eca, RDF.type, OFB.EntityECA) in graph
    ]
    assert hits, "no EntityECA triggered on OrderHeader"
    return hits[0]


def test_eca_trigger_and_event(graph):
    eca = _order_header_eca(graph)
    assert (eca, OFB.ecaOperation, rdflib.Literal("create-store")) in graph
    assert (eca, OFB.ecaEvent, rdflib.Literal("return")) in graph
    assert (eca, OFB.definedIn, rdflib.URIRef(NB + "source/" + EECAS_XML)) in graph


def test_eca_conditions(graph):
    eca = _order_header_eca(graph)
    conds = set()
    for cond in graph.objects(eca, OFB.hasCondition):
        field = graph.value(cond, OFB.condField)
        op = graph.value(cond, OFB.condOperator)
        val = graph.value(cond, OFB.condValue)
        conds.add((str(field), str(op), str(val)))
        assert (cond, OFB.definedIn, rdflib.URIRef(NB + "source/" + EECAS_XML)) in graph
    assert ("statusId", "equals", "ORDER_COMPLETED") in conds
    assert ("needsInventoryIssuance", "equals", "Y") in conds


def test_eca_action_reported_not_invented(graph, unresolved):
    # issueImmediatelyFulfilledOrder is defined outside applications/order:
    # no Service node may be minted for it...
    assert (rdflib.URIRef(NB + "service/issueImmediatelyFulfilledOrder"), RDF.type, OFB.Service) not in graph
    # ...but the stated action must be reported with exact evidence.
    hits = [u for u in unresolved if u.get("to_name") == "issueImmediatelyFulfilledOrder"]
    assert hits and all(h["edge"] == "triggersService" and h["via"] == "eca-action" for h in hits)
    assert any(h["source"]["file"] == EECAS_XML and h["source"]["line"] == 27 for h in hits)


# ---------------- default entity names (services*.xml) ----------------


@pytest.mark.parametrize(
    "service,entity",
    [
        ("createOrderAdjustment", "OrderAdjustment"),
        ("createOrderItemAssoc", "OrderItemAssoc"),
        ("createOrderItemGroup", "OrderItemGroup"),
    ],
)
def test_default_entity_names(graph, unresolved, service, entity):
    s = svc(service)
    assert (s, RDF.type, OFB.Service) in graph
    # Stated name preserved as a literal (ontology: defaultEntityName)...
    assert (s, OFB.defaultEntityName, rdflib.Literal(entity)) in graph
    # ...but no Entity node invented for an out-of-scope target...
    assert (rdflib.URIRef(NB + "entity/" + entity), RDF.type, OFB.Entity) not in graph
    assert (rdflib.URIRef(NB + "entity/" + entity), RDF.type, OFB.ViewEntity) not in graph
    # ...and the reference is reported with evidence instead.
    hits = [
        u
        for u in unresolved
        if u.get("edge") == "operatesOn" and u.get("to_name") == entity and service in u.get("from", "")
    ]
    assert hits, "missing operatesOn report for %s -> %s" % (service, entity)
