"""Inspection tool tests: readable output, real data, honesty on missing nodes."""
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent

pyoxigraph = pytest.importorskip("pyoxigraph")

from contextgraph import inspect as I  # noqa: E402
from contextgraph.graph import build as build_graph  # noqa: E402
from contextgraph.pipeline import run as run_extract  # noqa: E402
from contextgraph.store import ContextStore  # noqa: E402


@pytest.fixture(scope="module")
def env(tmp_path_factory):
    work = tmp_path_factory.mktemp("inspect")
    fx = work / "fx"
    repo = PROJECT_ROOT / "dataset" / "apache-ofbiz-24.09.07"
    assert repo.is_dir(), "OFBiz dataset missing"
    run_extract(repo, "order", fx)
    ttl = work / "g.ttl"
    build_graph(fx / "order-facts.jsonl", fx / "order-manifest.json", ttl, as_of="2026-01-01T00:00:00+00:00")
    store = ContextStore(work / "oxi")
    store.load_turtle(ttl)
    return store, fx, ttl


def test_services(env):
    out, _fx, _ttl = env
    text = I.cmd_services(out)
    assert "Services (467):" in text and "storeOrder" in text and "java" in text


def test_service_detail_matches_spec_example(env):
    store, _fx, _ttl = env
    text = I.cmd_service(store, "storeOrder")
    for expected in [
        "Service: storeOrder", "Creates order entities", "java",
        "org.apache.ofbiz.order.order.OrderServices#createOrder",
        "- partyId", "- orderItems", "- currencyUom", "- statusId",
        "applications/order/servicedef/services.xml", "Provenance:",
    ]:
        assert expected in text, expected
    assert "Outputs (" in text


def test_service_missing(env):
    store, _fx, _ttl = env
    assert "not found" in I.cmd_service(store, "noSuchService")


def test_entities(env):
    store, _fx, _ttl = env
    text = I.cmd_entities(store)
    assert "OrderHeaderAndItems" in text and "(53)" in text


def test_eca(env):
    store, _fx, _ttl = env
    text = I.cmd_eca(store)
    assert "(111)" in text and "OrderHeader" in text


def test_entity_out_of_scope_is_honest(env):
    store, fx, _ttl = env
    text = I.cmd_entity(store, "OrderHeader", fx / "order-unresolved.json")
    assert "no node" in text and "services.xml" in text


def test_source(env):
    store, _fx, _ttl = env
    text = I.cmd_source(store, "services.xml")
    assert "applications/order/servicedef/services.xml" in text
    assert "No source files" in I.cmd_source(store, "does-not-exist-zzz")


def test_stats(env):
    store, _fx, _ttl = env
    text = I.cmd_stats(store)
    for expected in ["Services discovered: 467", "ECA rules discovered: 111",
                     "Direct facts:", "Inferred facts:", "Triples in store:"]:
        assert expected in text, expected


def test_validate(env):
    _store, _fx, ttl = env
    text = I.cmd_validate(ttl, PROJECT_ROOT / "ontology" / "context-shapes.ttl")
    assert "conforms: True" in text and "violations: 0" in text
