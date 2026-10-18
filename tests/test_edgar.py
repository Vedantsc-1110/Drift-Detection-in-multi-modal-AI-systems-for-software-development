"""Task 2.7 tests: EDGAR processor (PART2_PLAN Task 2.7, §7.2 2.4).

Fixture 10-K text yields typed sections; module references link
(Order, Accounting); mentionsProcess resolves to Stage-1; provenance
complete on every subject. edgartools never imported. Mocked LLM.
"""

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

rdflib = pytest.importorskip("rdflib")

from contextgraph.prob.edgar import (  # noqa: E402
    extract_filing,
    risk_paragraphs,
    split_sections,
)
from contextgraph.prob.router import Router  # noqa: E402
from contextgraph.triple_builder import CTX  # noqa: E402

FILING = PROJECT_ROOT / "tests" / "fixtures" / "edgar" / "sample_10k.txt"
STAGE1 = PROJECT_ROOT / "tests" / "fixtures" / "llm" / "stage1_fixture.ttl"
RECORDED = PROJECT_ROOT / "tests" / "fixtures" / "llm" / "recorded_edgar_semantic.json"


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
def result(stage1):
    router = Router(_FakeClient(RECORDED.read_text(encoding="utf-8")), _FakeClient("[]"))
    return extract_filing("ACME-2025-10K", FILING.read_text(encoding="utf-8"), router, stage1,
                          generated_at="2026-01-01T00:00:00+00:00")


def test_sections_typed():
    sections = split_sections(FILING.read_text(encoding="utf-8"))
    items = [s["item"] for s in sections]
    assert "1" in items and "1A" in items and "7" in items
    body_1a = next(s["text"] for s in sections if s["item"] == "1A")
    assert len(risk_paragraphs(body_1a)) == 3


def test_module_references_linked(result):
    graph = result["graph"]
    assert result["errors"] == [] and result["skipped"] == []
    filing = CTX["Filing/ACME-2025-10K"]
    assert (filing, rdflib.RDF.type, CTX.Filing) in graph
    linked = {str(o).rsplit("/", 1)[-1] for o in graph.objects(filing, CTX.referencesModule)}
    assert linked == {"Order", "Accounting"}
    assert (CTX["Module/Order"], rdflib.RDF.type, CTX.Module) in graph


def test_section_and_risk_nodes(result):
    graph = result["graph"]
    sections = {s for s in graph.subjects(rdflib.RDF.type, CTX.Section)}
    assert len(sections) >= 3
    risks = list(graph.subjects(rdflib.RDF.type, CTX.RiskFactor))
    assert len(risks) == 3
    assert any("cybersecurity" in str(graph.value(r, rdflib.RDFS.label)) for r in risks)


def test_mentions_process_and_provenance(result, stage1):
    graph = result["graph"]
    assert (CTX["Section/ACME-2025-10K/1"], CTX.mentionsProcess, CTX["createOrder"]) in graph
    for subj in set(graph.subjects(rdflib.RDF.type, None)):
        if not str(subj).startswith(str(CTX)):
            continue
        assert next(graph.objects(subj, CTX.confidence), None) is not None, subj
        assert (subj, CTX.factType, rdflib.Literal("probabilistic")) in graph, subj
        assert next(graph.objects(subj, CTX.extractedBy), None) is not None, subj
        assert next(graph.objects(subj, rdflib.URIRef("http://www.w3.org/ns/prov#hadPrimarySource")), None) is not None, subj
        assert next(graph.objects(subj, CTX.supportType), None) is not None, subj


def test_edgartools_import_is_lazy():
    import contextgraph.prob.edgar as module

    top_level_imports = [line for line in open(module.__file__, encoding="utf-8").read().splitlines()
                         if line.startswith("import ") or line.startswith("from ")]
    assert not any(line.split()[-1] == "edgar" or line.startswith("from edgar") for line in top_level_imports)
