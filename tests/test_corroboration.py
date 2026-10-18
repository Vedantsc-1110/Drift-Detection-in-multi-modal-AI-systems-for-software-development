"""Task 2.3 tests: corroboration + confidence (PART2_PLAN Task 2.3).

Corroborated claims floor at 0.95; uncorroborated stay in 0.70–0.85;
support types DIRECT/INDIRECT/SYNTHETIC/UNRESOLVED assigned per rule.
Runs on the hand-made Stage-1 fixture .ttl — no network, no LLM.
"""

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

rdflib = pytest.importorskip("rdflib")

from contextgraph.prob.corroboration import corroborate  # noqa: E402

STAGE1 = PROJECT_ROOT / "tests" / "fixtures" / "llm" / "stage1_fixture.ttl"


@pytest.fixture(scope="module")
def stage1():
    graph = rdflib.Graph()
    graph.parse(str(STAGE1), format="turtle")
    return graph


def _claim(subject, predicate, object_, confidence, evidence=None):
    return {"subject": subject, "predicate": predicate, "object": object_,
            "confidence": confidence, "evidence": evidence or []}


def test_corroborated_claim_floors_at_095(stage1):
    (scored,) = corroborate([_claim("createOrder", "hasOutputParam", "createOrder_orderId", 0.74, ["createOrder"])], stage1)
    assert scored["corroborated"] is True
    assert scored["supportType"] == "DIRECT"
    assert scored["confidence"] == 0.95
    assert scored["confidence_rule"] == "corroborated-floor-0.95"
    assert scored["matched_triple"] is not None


def test_corroborated_keeps_higher_raw(stage1):
    (scored,) = corroborate([_claim("OrderServices_createOrder", "calls", "PartyServices_getParty", 0.99)], stage1)
    assert scored["confidence"] == 0.99 and scored["supportType"] == "DIRECT"


def test_uncorroborated_stays_in_band(stage1):
    (scored,) = corroborate([_claim("createOrder", "businessPurpose", "Serve customers well", 0.78, ["OrderHeader"])], stage1)
    assert scored["corroborated"] is False
    assert scored["supportType"] == "INDIRECT"  # OrderHeader is a known node
    assert 0.70 <= scored["confidence"] <= 0.85


def test_support_types_on_fixture_sentences(stage1):
    scored = corroborate([
        _claim("findOrders", "engine", "java", 0.8, ["findOrders"]),       # triple match -> DIRECT
        _claim("findOrders", "owns", "OrderHeader", 0.8, ["findOrders"]),  # endpoint known -> INDIRECT
        _claim("Mystery", "does", "Things", 0.8, ["memo"]),                # evidence only -> SYNTHETIC
        _claim("Nobody", "does", "Nothing", 0.8),                          # nothing -> UNRESOLVED
        _claim("Nobody", "does", "Nothing", 0.99),                         # clamped into band
    ], stage1)
    assert [s["supportType"] for s in scored] == ["DIRECT", "INDIRECT", "SYNTHETIC", "UNRESOLVED", "UNRESOLVED"]
    assert scored[0]["confidence"] == 0.95
    assert scored[4]["confidence"] == 0.85 and scored[4]["confidence_rule"] == "clamped-to-band"


def test_plain_triple_iterables_accepted():
    scored = corroborate([_claim("a", "p", "b", 0.7, ["a"])], [("http://x/A", "http://x/p", "http://x/b")])
    assert scored[0]["supportType"] == "DIRECT"
