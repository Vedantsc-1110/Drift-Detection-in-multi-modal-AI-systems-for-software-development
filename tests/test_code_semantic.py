"""Task 2.4 tests: code semantic extractor (PART2_PLAN Task 2.4, §7.2 2.1).

Mocked LLM (fake router transport): OrderModule businessPurpose appears with
extractedBy llama-3.3-70b and in-band confidence; corroborated dependency
claim scores >= 0.95. No network.
"""

import json
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

rdflib = pytest.importorskip("rdflib")

from contextgraph.prob.code_semantic import (  # noqa: E402
    build_module_summary,
    extract_module_semantics,
)
from contextgraph.prob.router import Router  # noqa: E402
from contextgraph.triple_builder import CTX as PART1_CTX  # noqa: E402 (namespace check)

STAGE1 = PROJECT_ROOT / "tests" / "fixtures" / "llm" / "stage1_fixture.ttl"
CTX = PART1_CTX

RESPONSE = json.dumps([
    {"subject": "OrderModule", "predicate": "businessPurpose",
     "object": "Capture and fulfil customer orders", "confidence": 0.78,
     "evidence": ["createOrder"]},
    {"subject": "createOrder", "predicate": "belongsToConcept",
     "object": "OrderCapture", "confidence": 0.8, "evidence": ["createOrder"]},
    {"subject": "OrderServices_createOrder", "predicate": "calls",
     "object": "PartyServices_getParty", "confidence": 0.74,
     "evidence": ["PartyServices.getParty"]},
])


class _FakeClient:
    name = "groq:test"

    def __init__(self, text):
        self._text = text

    def complete_json(self, system, user):
        assert "ONLY reference entities" in system
        return self._text


@pytest.fixture(scope="module")
def stage1():
    graph = rdflib.Graph()
    graph.parse(str(STAGE1), format="turtle")
    return graph


@pytest.fixture(scope="module")
def result(stage1):
    router = Router(_FakeClient(RESPONSE), _FakeClient("[]"))
    return extract_module_semantics("OrderModule", stage1, router, generated_at="2026-01-01T00:00:00+00:00")


def test_summary_uses_stage1_names(stage1):
    summary = build_module_summary(stage1, "OrderModule")
    blob = "\n".join(summary)
    assert "findOrders" in blob and "createOrder" in blob and "OrderHeader" in blob


def test_business_purpose_with_extracted_by(result):
    graph = result["graph"]
    module = CTX["Module/OrderModule"]
    purposes = list(graph.objects(module, CTX.businessPurpose))
    assert len(purposes) == 1 and "fulfil customer orders" in str(purposes[0])
    assert (module, CTX.extractedBy, rdflib.Literal("llama-3.3-70b")) in graph
    assert (module, CTX.factType, rdflib.Literal("probabilistic")) in graph
    conf = list(graph.objects(module, CTX.confidence))
    assert len(conf) == 1 and 0.70 <= float(conf[0]) <= 0.85
    assert result["extracted_by"] == "llama-3.3-70b"
    assert result["errors"] == []


def test_corroborated_dependency_at_least_095(result):
    by_pred = {}
    for claim in result["scored"]:
        by_pred.setdefault(claim["predicate"], []).append(claim)
    calls = by_pred["calls"][0]
    assert calls["confidence"] >= 0.95 and calls["supportType"] == "DIRECT"
    graph = result["graph"]
    dep_edges = list(graph.objects(CTX["Module/OrderModule"], CTX.dependsOn))
    assert dep_edges, "expected inter-module dependency edge"


def test_concept_node_typed(result):
    graph = result["graph"]
    concept = CTX["BusinessConcept/OrderCapture"]
    assert (concept, rdflib.RDF.type, CTX.BusinessConcept) in graph
