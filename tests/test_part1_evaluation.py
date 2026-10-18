"""Part 1 deterministic evaluation tests: structural gold + negative controls.

All tests run against the real OFBiz sources via the committed
outputs-deps/ + stores/order-deps/ pipeline outputs (read-only).
No LLM, no network, deterministic.
"""
import json
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from contextgraph.evaluate import (  # noqa: E402
    _load_json,
    _load_jsonl,
    _load_yaml,
    compute_metrics,
    evaluate_questions,
    evaluate_structural,
    normalized_hash,
)
from contextgraph.store import ContextStore  # noqa: E402

NB = "http://example.org/ofbiz/0.1/"
P = "PREFIX ofbiz: <http://example.org/ofbiz/0.1/>\n"
STORE = PROJECT_ROOT / "stores" / "order-deps"
FACTS = PROJECT_ROOT / "outputs-deps" / "order-facts.jsonl"
MANIFEST = PROJECT_ROOT / "outputs-deps" / "order-manifest.json"
UNRESOLVED = PROJECT_ROOT / "outputs-deps" / "order-unresolved.json"
QUESTIONS = PROJECT_ROOT / "evaluation" / "questions.yaml"
STRUCTURAL = PROJECT_ROOT / "evaluation" / "structural-gold.yaml"

needs_store = pytest.mark.skipif(not STORE.is_dir(), reason="stores/order-deps missing; run pipeline first")


@pytest.fixture(scope="module")
def bundle():
    store = ContextStore(str(STORE))
    facts = _load_jsonl(str(FACTS))
    manifest = _load_json(str(MANIFEST))
    unresolved = _load_json(str(UNRESOLVED))
    questions = _load_yaml(str(QUESTIONS))["questions"]
    gold = _load_yaml(str(STRUCTURAL))
    return store, facts, manifest, unresolved, questions, gold


@needs_store
def test_question_count_and_coverage(bundle):
    _store, _facts, _manifest, _unresolved, questions, _gold = bundle
    assert len(questions) == 15
    cats = {q["category"] for q in questions}
    for required in ("component", "service", "entity", "relation", "eca", "provenance", "scope"):
        assert required in cats, "missing category %s" % required


@needs_store
def test_evaluation_statuses(bundle):
    store, facts, manifest, unresolved, questions, _gold = bundle
    results, _ev = evaluate_questions(store, facts, manifest, unresolved, questions)
    by_id = {r["id"]: r for r in results}
    # Grounded expectations: 13 CORRECT + 2 honest UNRESOLVED, zero failures.
    assert by_id["Q-SVC-001"]["status"] == "CORRECT"
    assert by_id["Q-SVC-002"]["status"] == "CORRECT"
    assert by_id["Q-DATA-001"]["status"] == "CORRECT"
    assert by_id["Q-ECA-002"]["status"] == "CORRECT"
    assert by_id["Q-ECA-001"]["status"] == "UNRESOLVED"
    assert by_id["Q-ECA-003"]["status"] == "UNRESOLVED"
    assert by_id["Q-SCOPE-001"]["status"] == "CORRECT"
    metrics = compute_metrics(results)
    assert metrics["total"] == 15
    assert metrics["correct"] == 13
    assert metrics["incorrect"] == 0
    assert metrics["unresolved"] == 2
    assert metrics["answer_coverage"] == round(13 / 15, 4)
    assert metrics["resolved_correctness"] == 1.0
    assert metrics["provenance_coverage"] == 1.0


@needs_store
def test_structural_gold_sampled(bundle):
    store, facts, _manifest, unresolved, _q, gold = bundle
    structural = evaluate_structural(store, facts, unresolved, gold)
    assert structural["label"] == "sampled structural gold-set evaluation"
    assert structural["total"] == 35  # 10+10+10+5
    assert structural["found"] == 35
    assert structural["precision"] == 1.0
    assert structural["recall"] == 1.0
    for kind in ("service", "base_entity", "relation", "eca"):
        assert structural["by_kind"][kind]["precision"] == 1.0


@needs_store
def test_evaluation_deterministic(bundle, tmp_path):
    store, facts, manifest, unresolved, questions, gold = bundle
    r1, _ = evaluate_questions(store, facts, manifest, unresolved, questions)
    r2, _ = evaluate_questions(store, facts, manifest, unresolved, questions)
    h1 = normalized_hash({"results": sorted(r1, key=lambda r: r["id"])})
    h2 = normalized_hash({"results": sorted(r2, key=lambda r: r["id"])})
    assert h1 == h2


# ---------------- negative controls ----------------

@needs_store
def test_negative_arbitrary_string_creates_no_entity(bundle):
    """An arbitrary string value (e.g. status ORDER_COMPLETED) must NOT become a BaseEntity."""
    store, _facts, _manifest, unresolved, _q, _gold = bundle
    rows = store.sparql(P + "SELECT ?c WHERE { <%s> a ?c } " % (NB + "entity/ORDER_COMPLETED"))
    assert rows == [], "hallucinated entity for arbitrary string value"
    # Same for a plausible-but-absent name.
    rows2 = store.sparql(P + "SELECT ?c WHERE { <%s> a ?c } " % (NB + "entity/OrderHeaderMentionedOnlyAsString"))
    assert rows2 == []


@needs_store
def test_negative_external_service_unresolved_not_minted(bundle):
    """issueImmediatelyFulfilledOrder lives outside scope: no node, but a dangling report."""
    store, _facts, _manifest, unresolved, questions, _gold = bundle
    from contextgraph.evaluate import Evaluator

    ev = Evaluator(store, _facts, _manifest, unresolved)
    q = next(q for q in questions if q["id"] == "Q-ECA-003")
    graph_answer, status, fact_type, _evd, _note = ev.check_eca_action(q)
    assert status == "UNRESOLVED"
    assert fact_type == "UNRESOLVED"
    assert graph_answer["node_exists"] is False
    assert graph_answer["unresolved_reported"] is True


@needs_store
def test_negative_view_vs_base_not_confused(bundle):
    """OrderHeader is Entity-only; OrderHeaderAndItems is ViewEntity-only."""
    store, _facts, _manifest, _unresolved, _q, _gold = bundle
    oh = sorted(r["c"].rsplit("/", 1)[-1] for r in store.sparql(P + "SELECT ?c WHERE { <%s> a ?c } " % (NB + "entity/OrderHeader")))
    assert "Entity" in oh and "ViewEntity" not in oh
    view = sorted(r["c"].rsplit("/", 1)[-1] for r in store.sparql(P + "SELECT ?c WHERE { <%s> a ?c } " % (NB + "entity/OrderHeaderAndItems")))
    assert "ViewEntity" in view and "Entity" not in view


@needs_store
def test_negative_provenance_missing_detected(bundle):
    """Evaluation must detect broken provenance: wrong file/line must not be CORRECT."""
    store, facts, manifest, unresolved, questions, _gold = bundle
    from contextgraph.evaluate import Evaluator
    import copy

    ev = Evaluator(store, facts, manifest, unresolved)
    q = copy.deepcopy(next(q for q in questions if q["id"] == "Q-PROV-001"))
    _ga, status_ok, _ft, _evd, _note = ev.check_provenance(q)
    assert status_ok == "CORRECT"
    q["expected_answer"] = dict(q["expected_answer"])
    q["expected_answer"]["file"] = "applications/order/servicedef/WRONG.xml"
    _ga2, status_bad, _ft2, _evd2, _note2 = ev.check_provenance(q)
    assert status_bad == "INCORRECT", "provenance check must fail on wrong file"


@needs_store
def test_negative_wrong_expected_is_incorrect(bundle):
    """A deliberately wrong expected answer must produce INCORRECT (evaluation is meaningful)."""
    store, facts, manifest, unresolved, questions, _gold = bundle
    from contextgraph.evaluate import Evaluator
    import copy

    ev = Evaluator(store, facts, manifest, unresolved)
    q = copy.deepcopy(next(q for q in questions if q["id"] == "Q-SVC-001"))
    q["expected_answer"] = dict(q["expected_answer"])
    q["expected_answer"]["description"] = "Deliberately wrong description"
    _ga, status, _ft, _evd, _note = ev.check_service_description(q)
    assert status == "INCORRECT"
