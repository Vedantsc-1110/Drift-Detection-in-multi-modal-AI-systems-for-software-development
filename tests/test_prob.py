"""Probabilistic layer tests. Hermetic except the gated live-Ollama test."""
import json
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent

from contextgraph.prob.client import OllamaClient, StubClient  # noqa: E402
from contextgraph.prob.propose import collect_example_services, propose  # noqa: E402
from contextgraph.prob.review import (  # noqa: E402
    auto_reject_duplicates,
    load_proposals,
    review,
    save_proposals,
)
from contextgraph.prob.schema import is_valid, validate  # noqa: E402

RESERVATIONS = "applications/order/servicedef/services_reservations.xml"


def _good():
    return {
        "subject": "http://example.org/ofbiz/0.1/service/createAccommodationSpot",
        "predicate": "managesEntity",
        "object": "AccommodationSpot",
        "evidence": ["createAccommodationSpot"],
        "confidence": 0.7,
        "model": "ollama:x",
        "promptVersion": "prob-v1",
        "extractionType": "probabilistic",
        "status": "proposed",
    }


def test_schema_accepts_valid():
    assert is_valid(_good())


def test_schema_rejects():
    bad = _good()
    del bad["evidence"]
    assert not is_valid(bad)
    assert any("evidence" in e for e in validate(bad))
    for conf in (-0.1, 1.5, "high", True):
        b = _good()
        b["confidence"] = conf
        assert not is_valid(b), conf
    b = _good()
    b["extractionType"] = "direct"
    assert not is_valid(b)
    b = _good()
    b["status"] = "maybe"
    assert not is_valid(b)


def test_propose_stub_filters_and_labels():
    canned = json.dumps([
        {"subject": "Accommodation", "predicate": "suggestsDomain",
         "object": "Hospitality", "evidence": ["createAccommodationSpot"], "confidence": 0.6},
        {"subject": "x", "predicate": "inventedPredicate", "object": "y",
         "evidence": ["z"], "confidence": 0.5},
        {"subject": "x", "predicate": "suggestsDomain", "object": "y", "confidence": 0.5},
    ])
    facts, errors = propose(StubClient(canned), [], StubClient.name, now="2026-01-01T00:00:00+00:00")
    assert len(facts) == 1 and len(errors) == 2
    (fact,) = facts
    assert fact["model"] == "stub-test-client" and fact["promptVersion"] == "prob-v1"
    assert fact["extractionType"] == "probabilistic" and fact["status"] == "proposed"
    assert fact["extractedAt"] == "2026-01-01T00:00:00+00:00"
    assert is_valid(fact)


def test_propose_rejects_non_json():
    facts, errors = propose(StubClient("not json {"), [], StubClient.name)
    assert facts == [] and errors


def test_collect_example_services_real_facts():
    facts = [json.loads(x) for x in (PROJECT_ROOT / "outputs" / "order-facts.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
    services = collect_example_services(facts, RESERVATIONS)
    assert [s["name"] for s in services] == ["createAccommodationSpot", "deleteAccommodationSpot", "updateAccommodationSpot"]
    assert all(s["uri"].startswith("http://example.org/ofbiz/0.1/service/") for s in services)


def test_guard_rejects_deterministic_duplicates():
    det = {("s1", "referencesService", "s2")}
    proposals = [
        {"subject": "s1", "predicate": "referencesService", "object": "s2", "status": "proposed"},
        {"subject": "n1", "predicate": "suggestsDomain", "object": "n2", "status": "proposed"},
    ]
    assert auto_reject_duplicates(proposals, det) == 1
    assert proposals[0]["status"] == "rejected"
    assert proposals[0]["reviewReason"] == "duplicates-deterministic"
    assert proposals[1]["status"] == "proposed"


def test_accept_refuses_duplicates_and_lifecycle(tmp_path):
    path = tmp_path / "p.jsonl"
    proposals = [
        {"subject": "s1", "predicate": "referencesService", "object": "s2", "status": "proposed"},
        {"subject": "n1", "predicate": "suggestsDomain", "object": "n2", "status": "proposed"},
    ]
    save_proposals(path, proposals)
    loaded = load_proposals(path)
    ok, msg = review(loaded, 0, accept=True, deterministic={("s1", "referencesService", "s2")})
    assert not ok and loaded[0]["status"] == "rejected"
    ok, msg = review(loaded, 1, accept=True, deterministic=set(), reason="looks right")
    assert ok and loaded[1]["status"] == "accepted" and loaded[1]["reviewReason"] == "looks right"
    ok, _msg = review(loaded, 5, accept=True)
    assert not ok


def test_live_ollama_gated():
    client = OllamaClient("qwen2.5:1.5b", timeout=240)
    if not client.ping():
        pytest.skip("ollama not reachable; start `ollama serve` + pull a model for the live path")
    facts = [json.loads(x) for x in (PROJECT_ROOT / "outputs" / "order-facts.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
    services = collect_example_services(facts, RESERVATIONS)
    found, errors = propose(client, services, client.name)
    assert all(is_valid(f) for f in found)
    assert all(f["status"] == "proposed" and f["extractionType"] == "probabilistic" for f in found)
