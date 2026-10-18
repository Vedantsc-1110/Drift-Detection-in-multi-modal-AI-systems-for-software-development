"""Task 3.6 tests: SPARQL API (§4.1) via FastAPI TestClient.

All six predefined questions return fixture answers; raw SPARQL executes;
confidence filter works. No network (TestClient is in-process).
"""

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

pytest.importorskip("fastapi")
pytest.importorskip("httpx")
pytest.importorskip("pyoxigraph")
starlette_testclient = pytest.importorskip("starlette.testclient")

from contextgraph.contract_api import QUERIES, create_app  # noqa: E402
from contextgraph.contract_store import ContractStore  # noqa: E402

FIX = PROJECT_ROOT / "tests" / "fixtures" / "contract" / "api"
LOADS = (("structural.ttl", "urn:ofbiz_structural"), ("airflow.ttl", "urn:airflow"),
         ("semantic.ttl", "urn:ofbiz_semantic"), ("cuad.ttl", "urn:cuad"),
         ("bridges.ttl", "urn:bridges"))


@pytest.fixture(scope="module")
def client(tmp_path_factory):
    store = ContractStore(tmp_path_factory.mktemp("store"))
    for filename, graph in LOADS:
        store.load_file(FIX / filename, graph)
    test_client = starlette_testclient.TestClient(create_app(store))
    yield test_client
    store.close()


def test_order_services(client):
    rows = client.get("/services/order").json()["rows"]
    assert [r["service"] for r in rows] == ["findOrders"]


def test_invoice_io_params(client):
    rows = client.get("/services/createInvoice/io").json()["rows"]
    assert sorted(r["param"] for r in rows) == ["invoiceId", "invoiceTypeId"]


def test_dags_for_findorders(client):
    rows = client.get("/dags/for-service", params={"service": "findOrders"}).json()["rows"]
    assert [r["dag"] for r in rows] == ["orders_etl"]
    assert client.get("/dags/for-service", params={"service": "nope"}).json()["rows"] == []


def test_policies_for_invoice(client):
    rows = client.get("/policies/for-service", params={"service": "createInvoice"}).json()["rows"]
    assert [r["policy"] for r in rows] == ["createInvoice requires manager approval"]


def test_contracts_for_order_module(client):
    rows = client.get("/contracts/for-module").json()["rows"]
    assert [r["contract"] for r in rows] == ["Services Agreement"]


def test_low_confidence_filter(client):
    rows = client.get("/facts/low-confidence").json()["rows"]
    assert len(rows) == 1 and rows[0]["subject"].endswith("GuessModule")
    assert float(rows[0]["confidence"]) < 0.7
    strict = client.get("/facts/low-confidence", params={"threshold": 0.5}).json()["rows"]
    assert strict == []


def test_raw_sparql_executes_contract_example(client):
    query = ("PREFIX ctx: <http://context.example.org/> "
             "SELECT ?service WHERE { GRAPH <urn:ofbiz_structural> "
             "{ ?service a ctx:Service } } ORDER BY ?service")
    rows = client.post("/sparql", json={"query": query}).json()["rows"]
    assert len(rows) == 2
    assert set(QUERIES) == {"order_services", "invoice_io", "dags_for_findorders",
                            "policies_for_invoice", "contracts_for_order", "low_confidence"}
