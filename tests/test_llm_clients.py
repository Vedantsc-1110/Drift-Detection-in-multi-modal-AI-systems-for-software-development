"""Task 2.1 tests: LLM clients + JSON validation (PART2_PLAN Task 2.1).

Mocks/fakes only — no network, no keys. Covers router fallback, validator
accept/reject, and the recorded LLM fixture.
"""

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from contextgraph.prob.groq_client import GroqClient, GroqError  # noqa: E402
from contextgraph.prob.json_validator import validate_response  # noqa: E402
from contextgraph.prob.prompts import (  # noqa: E402
    EXTRACTION_SYSTEM,
    build_extraction_prompt,
)
from contextgraph.prob.router import Router  # noqa: E402

FIXTURE = PROJECT_ROOT / "tests" / "fixtures" / "llm" / "recorded_order_semantic.json"


class _Failing:
    name = "groq:test"

    def complete_json(self, system, user):
        raise GroqError("boom")


class _Canned:
    def __init__(self, text, name="canned"):
        self._text = text
        self.name = name

    def complete_json(self, system, user):
        return self._text


def test_router_falls_back_on_groq_failure():
    router = Router(_Failing(), _Canned("[]", "ollama:qwen3.5:4b"))
    text, model, errors = router.complete_json("sys", "user")
    assert text == "[]"
    assert model == "ollama:qwen3.5:4b"
    assert len(errors) == 1 and "groq:test" in errors[0]


def test_router_prefers_primary_when_healthy():
    router = Router(_Canned("[{}]", "groq:llama-3.3-70b-versatile"), _Canned("[]", "fallback"))
    text, model, errors = router.complete_json("sys", "user")
    assert (text, model, errors) == ("[{}]", "groq:llama-3.3-70b-versatile", [])


def test_router_raises_when_both_fail():
    import pytest

    router = Router(_Failing(), _Failing())
    with pytest.raises(RuntimeError):
        router.complete_json("sys", "user")


def test_groq_client_uses_injected_transport():
    seen = {}

    def fake_transport(payload):
        seen.update(payload)
        return {"choices": [{"message": {"content": "[{}]"}}]}

    client = GroqClient(transport=fake_transport)
    assert client.complete_json("sys", "user") == "[{}]"
    assert seen["model"] == "llama-3.3-70b-versatile"
    assert seen["messages"][0]["role"] == "system"


def test_groq_client_rejects_bad_shape():
    client = GroqClient(transport=lambda payload: {"nope": True})
    try:
        client.complete_json("sys", "user")
        raise AssertionError("expected GroqError")
    except GroqError:
        pass


def test_validator_accepts_recorded_fixture():
    response = validate_response(FIXTURE.read_text(encoding="utf-8"), "groq:llama-3.3-70b-versatile")
    assert response["errors"] == []
    assert len(response["claims"]) == 4
    first = response["claims"][0]
    assert first["subject"] == "OrderModule" and first["confidence"] == 0.78
    assert all(set(c) == {"subject", "predicate", "object", "confidence", "evidence"} for c in response["claims"])


def test_validator_rejects_malformed():
    response = validate_response("not json {", "m")
    assert response["claims"] == [] and len(response["errors"]) == 1
    response = validate_response(json.dumps({"claims": [{"subject": "a", "predicate": "", "object": "b", "confidence": 9.0}]}), "m")
    assert response["claims"] == []
    assert any("predicate" in e for e in response["errors"])
    assert any("confidence" in e for e in response["errors"])
    # One bad claim does not sink the good one; errors name the culprit.
    response = validate_response(json.dumps([{"subject": "a", "predicate": "p", "object": "o", "confidence": 0.7}, {"subject": "", "predicate": "p", "object": "o", "confidence": 0.5}]), "m")
    assert len(response["claims"]) == 1 and len(response["errors"]) == 1
    assert "claim #1" in response["errors"][0]


def test_extraction_prompt_grounds_on_context():
    prompt = build_extraction_prompt(
        [{"text": "OrderHeader", "label": "SYSTEM"}, {"text": "2026-01-01", "label": "DATE"}],
        ["service createOrder (java)", "entity OrderHeader"],
    )
    assert "OrderHeader" in prompt and "createOrder" in prompt
    assert "ONLY reference entities that appear in the provided context" in EXTRACTION_SYSTEM
    assert "JSON" in EXTRACTION_SYSTEM
