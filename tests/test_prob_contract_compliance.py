"""Task 2.11 tests: Part 2 CONTRACT.md compliance handoff (PART2_PLAN Task 2.11).

Four §6 output files parse; §5 metadata on every probabilistic subject
(confidence, factType, extractedBy, generatedAtTime, hadPrimarySource);
§4 Named Graph targets proven by family routing; vocabulary within §2–§3;
plain Turtle with no GRAPH blocks (Q6). Mocked LLM, no network.
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
    CONTRACT_CLASSES,
    CONTRACT_PROPS,
    merge_graphs,
    validate_prob_graph,
)
from contextgraph.triple_builder import CTX  # noqa: E402

FIX = PROJECT_ROOT / "tests" / "fixtures"
GENERATED_AT = "2026-01-01T00:00:00+00:00"
EXPECTED_FILES = ("ofbiz_semantic.ttl", "document_semantic.ttl", "cuad.ttl", "edgar.ttl")
PROV = "http://www.w3.org/ns/prov#"


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
def outputs(tmp_path_factory, stage1):
    out = tmp_path_factory.mktemp("prob")
    semantic = code_semantic.extract_module_semantics(
        "OrderModule", stage1, _router("recorded_order_semantic.json"), GENERATED_AT)["graph"]
    docs = documents.process_corpus(
        [FIX / "docs" / "procurement_policy.docx", FIX / "docs" / "procurement_notice.pdf"],
        _router("recorded_policy_semantic.json"), ["P01-docx", "P01-pdf"], stage1, GENERATED_AT)["graph"]
    cuad_graph = merge_graphs([
        cuad.extract_contract(row, _router("recorded_cuad_semantic.json"), stage1, GENERATED_AT)["graph"]
        for row in cuad.load_rows(FIX / "cuad" / "sample_contracts.json")])
    filing = edgar.extract_filing(
        "ACME-2025-10K", (FIX / "edgar" / "sample_10k.txt").read_text(encoding="utf-8"),
        _router("recorded_edgar_semantic.json"), stage1, GENERATED_AT)["graph"]
    graphs = {"ofbiz_semantic.ttl": semantic, "document_semantic.ttl": docs,
              "cuad.ttl": cuad_graph, "edgar.ttl": filing}
    for name, graph in graphs.items():
        (out / name).write_text(graph.serialize(format="turtle"), encoding="utf-8")
    return out, graphs


def test_file_names_match_section_6(outputs):
    out, _ = outputs
    assert sorted(p.name for p in out.glob("*.ttl")) == sorted(EXPECTED_FILES)
    for name in EXPECTED_FILES:
        assert "GRAPH" not in (out / name).read_text(encoding="utf-8"), name


def test_section_5_metadata_on_every_probabilistic_subject(outputs):
    _, graphs = outputs
    borrowed_markers = set()
    for name, graph in graphs.items():
        assert validate_prob_graph(graph) == [], (name, validate_prob_graph(graph))
        subjects = {s for s in graph.subjects(rdflib.RDF.type, None) if str(s).startswith(str(CTX))}
        assert subjects, name
        for subj in subjects:
            conf = list(graph.objects(subj, CTX.confidence))
            assert len(conf) == 1 and 0.0 <= float(conf[0]) <= 1.0, (name, subj)
            assert (subj, CTX.factType, rdflib.Literal("probabilistic")) in graph, (name, subj)
            assert next(graph.objects(subj, CTX.extractedBy), None) is not None, (name, subj)
            assert next(graph.objects(subj, rdflib.URIRef(PROV + "generatedAtTime")), None) is not None, (name, subj)
            assert next(graph.objects(subj, rdflib.URIRef(PROV + "hadPrimarySource")), None) is not None, (name, subj)
            borrowed_markers.add(name)
    assert borrowed_markers == set(EXPECTED_FILES)


def test_named_graph_targets_per_section_4(outputs):
    _, graphs = outputs
    routing = {
        "ofbiz_semantic.ttl": {CTX.Module, CTX.BusinessConcept},
        "document_semantic.ttl": {CTX.Document, CTX.Policy},
        "cuad.ttl": {CTX.Contract, CTX.Clause, CTX.Party},
        "edgar.ttl": {CTX.Filing, CTX.Section, CTX.RiskFactor},
    }
    for name, expected in routing.items():
        present = set(graphs[name].objects(None, rdflib.RDF.type))
        assert expected <= present, (name, expected - present)


def test_vocabulary_within_sections_2_and_3(outputs):
    _, graphs = outputs
    for name, graph in graphs.items():
        for _, pred, _ in graph:
            if str(pred).startswith(str(CTX)):
                assert str(pred)[len(str(CTX)):] in CONTRACT_PROPS, (name, pred)
        for rdf_class in set(graph.objects(None, rdflib.RDF.type)):
            if str(rdf_class).startswith(str(CTX)):
                assert str(rdf_class)[len(str(CTX)):] in CONTRACT_CLASSES, (name, rdf_class)
