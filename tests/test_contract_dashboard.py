"""Task 3.7 tests: dashboard (§4.2) via TestClient.

Page loads with filter hooks and provenance panel; filter parameters reach
the query layer; provenance payload present for a fixture node. No network.
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

from contextgraph.contract_api import create_app  # noqa: E402
from contextgraph.contract_store import ContractStore  # noqa: E402

FIX = PROJECT_ROOT / "tests" / "fixtures" / "contract" / "api"
LOADS = (("structural.ttl", "urn:ofbiz_structural"), ("airflow.ttl", "urn:airflow"),
         ("semantic.ttl", "urn:ofbiz_semantic"), ("cuad.ttl", "urn:cuad"),
         ("bridges.ttl", "urn:bridges"))
FIND_ORDERS = "http://context.example.org/findOrders"
GUESS = "http://context.example.org/GuessModule"


@pytest.fixture(scope="module")
def client(tmp_path_factory):
    store = ContractStore(tmp_path_factory.mktemp("store"))
    for filename, graph in LOADS:
        store.load_file(FIX / filename, graph)
    test_client = starlette_testclient.TestClient(create_app(store))
    yield test_client
    store.close()


def test_dashboard_page_loads(client):
    response = client.get("/dashboard")
    assert response.status_code == 200
    html = response.text
    assert "/vendor/vis-network.min.js" in html
    assert "What am I looking at" in html
    for hook in ('id="confidence"', 'id="factType"', 'id="graph"', 'id="search"', 'id="provenance"', 'id="status"', 'id="nodelist"'):
        assert hook in html, hook


def test_vendor_bundle_served_locally(client):
    response = client.get("/vendor/vis-network.min.js")
    assert response.status_code == 200
    assert "vis-network" in response.text
    assert client.get("/vendor/../contract_api.py").status_code in (400, 404)
    assert client.get("/vendor/missing.js").status_code == 404


def test_filters_reach_query_layer(client):
    all_nodes = client.get("/graph/nodes").json()
    assert len(all_nodes["nodes"]) > 5 and isinstance(all_nodes["edges"], list)
    prob_only = client.get("/graph/nodes", params={"factType": "probabilistic"}).json()
    assert prob_only["nodes"] and all(n["factType"] == "probabilistic" for n in prob_only["nodes"])
    high = client.get("/graph/nodes", params={"confidence": "high"}).json()
    assert high["nodes"] and all(float(n["confidence"]) >= 0.85 for n in high["nodes"])
    assert not [n for n in high["nodes"] if n["id"] == GUESS]
    scoped = client.get("/graph/nodes", params={"graph": "urn:cuad"}).json()
    assert scoped["nodes"] and all(n["graph"].endswith("cuad") or "cuad" in n["graph"] for n in scoped["nodes"])
    searched = client.get("/graph/nodes", params={"search": "findOrders"}).json()
    assert {n["id"] for n in searched["nodes"]} == {FIND_ORDERS, "http://context.example.org/orders_etl_sync"}
    assert client.get("/graph/nodes", params={"confidence": "bogus"}).status_code == 400


def test_provenance_payload_for_fixture_node(client):
    payload = client.get("/node", params={"uri": FIND_ORDERS}).json()
    assert payload["label"] == "findOrders"
    assert float(payload["confidence"]) == 1.0 and payload["ft"] == "deterministic"
    assert payload["source"].endswith("services.xml")
    assert str(payload["line"]) == "142"
    guess = client.get("/node", params={"uri": GUESS}).json()
    assert guess["extractedBy"] == "llama-3.3-70b"
    assert client.get("/node", params={"uri": "http://context.example.org/nope"}).status_code == 404
