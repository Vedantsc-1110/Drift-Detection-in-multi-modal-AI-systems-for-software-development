"""Oxigraph store tests on the real order graph: load/query/export/clear/rebuild."""
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent

pyoxigraph = pytest.importorskip("pyoxigraph")

from contextgraph import queries as Q  # noqa: E402
from contextgraph.store import ContextStore  # noqa: E402

NB = "http://example.org/ofbiz/0.1/"


@pytest.fixture(scope="module")
def store(tmp_path_factory):
    work = tmp_path_factory.mktemp("store")
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
            sys.executable, "build_graph.py", "--facts", str(fx / "order-facts.jsonl"),
            "--manifest", str(fx / "order-manifest.json"), "--out", str(ttl),
            "--as-of", "2026-01-01T00:00:00+00:00",
        ],
        cwd=PROJECT_ROOT,
        check=True,
    )
    st = ContextStore(work / "oxi")
    st.load_turtle(ttl)
    st.ttl = ttl
    return st


def test_load_count(store):
    assert store.count() > 30000


def test_services(store):
    rows = store.sparql(Q.q_services())
    assert len(rows) == 467
    assert any(r["name"] == "storeOrder" for r in rows)
    assert [r["name"] for r in rows] == sorted(r["name"] for r in rows)


def test_implementations(store):
    rows = store.sparql(Q.q_implementations())
    by_name = {r["service"].rsplit("/", 1)[-1]: r for r in rows}
    so = by_name["storeOrder"]
    assert so["invoke"] == "createOrder"
    assert so["class"] == "org.apache.ofbiz.order.order.OrderServices"
    auto = by_name["createOrderAdjustmentAttribute"]
    assert auto["method"] is None and auto["invoke"] is None


def test_inputs_outputs(store):
    inputs = store.sparql(Q.q_inputs("storeOrder"))
    by_param = {r["param"]: r for r in inputs}
    assert by_param["partyId"]["type"] == "String"
    assert by_param["orderItems"]["mode"] == "IN"
    assert by_param["grandTotal"]["optional"] == "true"
    assert [r["param"] for r in inputs] == sorted(by_param)
    outputs = store.sparql(Q.q_outputs("storeOrder"))
    assert any(r["param"] == "statusId" and r["mode"] == "OUT" for r in outputs)


def test_entities_referenced(store):
    rows = store.sparql(Q.q_entities_referenced())
    assert rows
    assert all(r["via"] in ("operatesOn", "defaultEntityName") for r in rows)
    assert any(r["entity"] == "OrderAdjustment" for r in rows)


def test_eca_rules(store):
    rows = store.sparql(Q.q_eca_rules())
    assert len(rows) == 111
    assert any(r.get("event") == "return" for r in rows)


def test_eca_triggered_services(store):
    rows = store.sparql(Q.q_eca_triggered_services())
    assert any(r["service"] == "resetGrandTotal" for r in rows)


def test_fact_provenance(store):
    rows = store.sparql(Q.q_fact_provenance(NB + "service/storeOrder"))
    assert len(rows) == 1
    (row,) = rows
    assert row["file"] == "applications/order/servicedef/services.xml"
    assert row["sha"] and row["artifactType"] == "service-def"
    assert row["extractionType"] == "direct" and row["line"] is not None


def test_service_files(store):
    rows = store.sparql(Q.q_service_files("storeOrder"))
    assert "applications/order/servicedef/services.xml" in [r["file"] for r in rows]


def test_component_services(store):
    rows = store.sparql(Q.q_component_services("order"))
    assert len(rows) == 467
    assert any(r["service"] == "storeOrder" for r in rows)


def test_queries_reproducible(store):
    assert store.sparql(Q.q_services()) == store.sparql(Q.q_services())


def test_export_roundtrip(store, tmp_path):
    out = tmp_path / "export.ttl"
    store.export_turtle(out)
    rdflib = pytest.importorskip("rdflib")
    g = rdflib.Graph()
    g.parse(str(out), format="turtle")
    assert len(g) == store.count()


def test_clear_and_rebuild(store):
    n = store.count()
    store.clear()
    assert store.count() == 0
    store.load_turtle(store.ttl)
    assert store.count() == n
