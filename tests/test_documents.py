"""Task 2.5 tests: document processor (PART2_PLAN Task 2.5, §7.2 2.2).

Mocked LLM: every fixture doc yields typed facts; every minted subject has
supportType; the $50,000 threshold and approval chain surface from the
procurement policy. No network.
"""

import json
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

rdflib = pytest.importorskip("rdflib")

from contextgraph.prob.documents import (  # noqa: E402
    process_corpus,
    process_document,
    read_document,
)
from contextgraph.prob.router import Router  # noqa: E402
from contextgraph.triple_builder import CTX  # noqa: E402

DOCS = PROJECT_ROOT / "tests" / "fixtures" / "docs"
STAGE1 = PROJECT_ROOT / "tests" / "fixtures" / "llm" / "stage1_fixture.ttl"
RECORDED = PROJECT_ROOT / "tests" / "fixtures" / "llm" / "recorded_policy_semantic.json"


class _FakeClient:
    name = "groq:test"

    def __init__(self, text):
        self._text = text

    def complete_json(self, system, user):
        return self._text


@pytest.fixture(scope="module")
def stage1():
    graph = rdflib.Graph()
    graph.parse(str(STAGE1), format="turtle")
    return graph


@pytest.fixture(scope="module")
def router():
    return Router(_FakeClient(RECORDED.read_text(encoding="utf-8")), _FakeClient("[]"))


def _subjects_by_type(graph, rdf_class):
    return {s for s in graph.subjects(rdflib.RDF.type, rdf_class) if str(s).startswith(str(CTX))}


def test_text_extraction_per_format():
    assert "Procurement Officer" in read_document(DOCS / "procurement_policy.docx")
    assert "$50,000" in read_document(DOCS / "procurement_notice.pdf")
    assert "Approval thresholds" in read_document(DOCS / "procurement_policy.md")


def test_each_doc_yields_typed_facts_with_support(router, stage1):
    for doc_id, name in (("P01-docx", "procurement_policy.docx"), ("P01-pdf", "procurement_notice.pdf")):
        result = process_document(doc_id, DOCS / name, router, stage1, generated_at="2026-01-01T00:00:00+00:00")
        graph = result["graph"]
        assert result["errors"] == []
        assert _subjects_by_type(graph, CTX.Document) == {CTX["Document/" + doc_id]}
        assert _subjects_by_type(graph, CTX.Policy), name
        for subj in _subjects_by_type(graph, CTX.Document) | _subjects_by_type(graph, CTX.Policy):
            support = list(graph.objects(subj, CTX.supportType))
            assert len(support) == 1 and str(support[0]) in ("DIRECT", "INDIRECT", "SYNTHETIC", "UNRESOLVED"), (name, subj)
            assert (subj, CTX.factType, rdflib.Literal("probabilistic")) in graph
        assert (CTX["Document/" + doc_id], CTX.mentionsEntity, CTX["OrderHeader"]) in graph


def test_threshold_and_approval_chain(router, stage1):
    result = process_document("P01", DOCS / "procurement_policy.docx", router, stage1)
    labels = [str(o) for _, _, o in result["graph"].triples((None, rdflib.RDFS.label, None))]
    assert any("$50,000" in label and "three approvals" in label for label in labels)
    assert any("Finance Administrator" in label for label in labels)


def test_corpus_runner_merges(router, stage1):
    paths = [DOCS / "procurement_policy.docx", DOCS / "procurement_notice.pdf", DOCS / "procurement_policy.md"]
    merged = process_corpus(paths, router, ["P01-docx", "P01-pdf", "P01-md"], stage1)
    assert merged["errors"] == []
    assert len(merged["results"]) == 3
    assert len(merged["graph"]) > 0
    assert len(_subjects_by_type(merged["graph"], CTX.Document)) == 3
