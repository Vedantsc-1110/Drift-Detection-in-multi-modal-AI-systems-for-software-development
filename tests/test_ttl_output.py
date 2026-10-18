"""Task 2.8 tests: TTL output (PART2_PLAN Task 2.8).

Runs extractors 2.4–2.7 over fixtures with recorded LLM responses, merges
per family, writes the four §6 files, and validates: rdflib round-trip,
per-subject metadata (confidence range, factType, extractedBy,
generatedAtTime, hadPrimarySource), contract-only vocabulary, no GRAPH.
"""

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

rdflib = pytest.importorskip("rdflib")

from contextgraph.prob import code_semantic, cuad, documents, edgar  # noqa: E402
from contextgraph.prob.router import Router  # noqa: E402
from contextgraph.prob.ttl_output import (  # noqa: E402
    OUTPUT_FILES,
    merge_graphs,
    validate_prob_graph,
    write_outputs,
)
from contextgraph.triple_builder import CTX  # noqa: E402

FIX = PROJECT_ROOT / "tests" / "fixtures"
GENERATED_AT = "2026-01-01T00:00:00+00:00"


class _FakeClient:
    name = "groq:test"

    def __init__(self, text):
        self._text = text

    def complete_json(self, system, user):
        return self._text


def _router(name):
    return Router(_FakeClient((FIX / "llm" / name).read_text(encoding="utf-8")), _FakeClient("[]"))


@pytest.fixture(scope="module")
def stage1():
    graph = rdflib.Graph()
    graph.parse(str(FIX / "llm" / "stage1_fixture.ttl"), format="turtle")
    return graph


@pytest.fixture(scope="module")
def family_graphs(stage1):
    semantic = code_semantic.extract_module_semantics(
        "OrderModule", stage1, _router("recorded_order_semantic.json"), GENERATED_AT)["graph"]
    docs = documents.process_corpus(
        [FIX / "docs" / "procurement_policy.docx", FIX / "docs" / "procurement_notice.pdf"],
        _router("recorded_policy_semantic.json"), ["P01-docx", "P01-pdf"], stage1, GENERATED_AT)["graph"]
    cuad_graphs = [cuad.extract_contract(row, _router("recorded_cuad_semantic.json"), stage1, GENERATED_AT)["graph"]
                   for row in cuad.load_rows(FIX / "cuad" / "sample_contracts.json")]
    filing = edgar.extract_filing(
        "ACME-2025-10K", (FIX / "edgar" / "sample_10k.txt").read_text(encoding="utf-8"),
        _router("recorded_edgar_semantic.json"), stage1, GENERATED_AT)["graph"]
    return {"ofbiz_semantic.ttl": semantic, "document_semantic.ttl": docs,
            "cuad.ttl": merge_graphs(cuad_graphs), "edgar.ttl": filing}


def test_all_families_validate_clean(family_graphs, stage1):
    for name, graph in family_graphs.items():
        assert len(graph) > 0, name
        assert validate_prob_graph(graph, stage1) == [], (name, validate_prob_graph(graph, stage1))


def test_files_round_trip_and_no_graph_blocks(family_graphs, stage1, tmp_path):
    result = write_outputs(family_graphs, tmp_path)
    assert sorted(result) == sorted(OUTPUT_FILES)
    for name in OUTPUT_FILES:
        assert "GRAPH" not in (tmp_path / name).read_text(encoding="utf-8"), name
        reparsed = rdflib.Graph()
        reparsed.parse(str(tmp_path / name), format="turtle")
        assert len(reparsed) == len(family_graphs[name]) == result[name]["triples"]
        assert validate_prob_graph(reparsed, stage1) == [], name


def test_expected_individuals_present(family_graphs):
    assert (CTX["Module/OrderModule"], rdflib.RDF.type, CTX.Module) in family_graphs["ofbiz_semantic.ttl"]
    assert (CTX["Document/P01-docx"], rdflib.RDF.type, CTX.Document) in family_graphs["document_semantic.ttl"]
    assert (CTX["Contract/CUAD-SVC-001"], rdflib.RDF.type, CTX.Contract) in family_graphs["cuad.ttl"]
    assert (CTX["Filing/ACME-2025-10K"], rdflib.RDF.type, CTX.Filing) in family_graphs["edgar.ttl"]
