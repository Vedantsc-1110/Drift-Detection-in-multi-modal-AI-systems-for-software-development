"""Regression checks for graph rendering, isolation, and provenance."""

from html.parser import HTMLParser
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from contextgraph.contract_api import create_app
from contextgraph.contract_store import ContractStore


FIXTURES = Path(__file__).parent / "fixtures" / "contract" / "api"
CTX = "http://context.example.org/"


@pytest.fixture
def client(tmp_path):
    store = ContractStore(tmp_path / "store")
    for filename, graph in (
        ("structural.ttl", "urn:ofbiz_structural"),
        ("airflow.ttl", "urn:airflow"),
        ("semantic.ttl", "urn:ofbiz_semantic"),
        ("cuad.ttl", "urn:cuad"),
        ("bridges.ttl", "urn:bridges"),
    ):
        store.load_file(FIXTURES / filename, graph)
    extra = tmp_path / "extra.ttl"
    extra.write_text(
        '@prefix ctx: <http://context.example.org/> .\n'
        '@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .\n'
        'ctx:findOrders a ctx:Service, ctx:JavaMethod ; rdfs:label "findOrders" ; '
        'ctx:confidence 1.0 ; ctx:factType "deterministic" .\n'
        'ctx:findOrders ctx:calls ctx:createInvoice .\n',
        encoding="utf-8",
    )
    store.load_file(extra, "urn:ofbiz_semantic")
    with TestClient(create_app(store)) as test_client:
        yield test_client
    store.close()


class Elements(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
        self.tags = {}

    def handle_starttag(self, tag, attrs):
        identifier = dict(attrs).get("id")
        if identifier:
            self.ids.append(identifier)
            self.tags[identifier] = tag


def test_renderer_has_a_unique_non_form_container(client):
    elements = Elements()
    elements.feed(client.get("/dashboard").text)
    assert len(elements.ids) == len(set(elements.ids)), "Duplicate IDs target the wrong element"
    assert elements.tags["graph"] == "div"
    assert elements.tags["graphFilter"] == "select"


def test_dashboard_assets_and_root_entrypoint(client):
    assert client.get("/").url.path == "/dashboard"
    for asset, mime in (("dashboard.css", "text/css"), ("dashboard.js", "javascript")):
        response = client.get("/assets/" + asset)
        assert response.status_code == 200
        assert mime in response.headers["content-type"]
    assert client.get("/assets/contract_api.py").status_code == 404


def test_one_visual_node_per_uri_preserves_graph_membership(client):
    payload = client.get("/graph/nodes").json()
    identifiers = [node["id"] for node in payload["nodes"]]
    assert len(identifiers) == len(set(identifiers))
    service = next(node for node in payload["nodes"] if node["id"] == CTX + "findOrders")
    assert set(service["graphs"]) == {"urn:ofbiz_structural", "urn:ofbiz_semantic"}
    assert CTX + "JavaMethod" in service["classes"]
    assert any(edge["label"] == "calls" for edge in payload["edges"])


def test_selected_graph_cannot_leak_relationships_from_other_graphs(client):
    payload = client.get("/graph/nodes", params={"graph": "urn:ofbiz_structural"}).json()
    assert not any(edge["label"] == "calls" for edge in payload["edges"])
    assert all(edge["graph"] == "urn:ofbiz_structural" for edge in payload["edges"])


def test_natural_language_search_is_safely_quoted(client):
    response = client.get("/graph/nodes", params={"search": '"approval" \\ details'})
    assert response.status_code == 200
    assert response.json()["nodes"] == []


@pytest.mark.parametrize("endpoint,params", [
    ("/node", {"uri": CTX + "findOrders> } } #"}),
    ("/graph/nodes", {"graph": "urn:x> { ?s ?p ?o } #"}),
])
def test_sparql_iri_injection_returns_validation_error(client, endpoint, params):
    assert client.get(endpoint, params=params).status_code == 400


def test_summary_reports_loaded_graphs_without_inventing_live_state(client):
    response = client.get("/graph/summary")
    assert response.status_code == 200
    summary = response.json()
    assert summary["mode"] == "local"
    assert summary["liveMonitoring"] is False
    assert {item["id"] for item in summary["graphs"]} >= {"urn:cuad", "urn:airflow"}
    assert all(item["triples"] > 0 for item in summary["graphs"])


def test_provenance_can_be_scoped_to_selected_graph(client):
    payload = client.get("/node", params={"uri": CTX + "findOrders", "graph": "urn:ofbiz_structural"}).json()
    assert payload["graph"] == "urn:ofbiz_structural"
    assert payload["source"].endswith("services.xml")
    assert payload["line"] == "142"
    assert client.get("/node", params={"uri": CTX + "findOrders", "graph": "urn:cuad"}).status_code == 404


def test_absent_provenance_is_null_rather_than_fabricated_text(client):
    payload = client.get("/node", params={"uri": CTX + "findOrders", "graph": "urn:ofbiz_semantic"}).json()
    assert payload["source"] is None
    assert payload["line"] is None
