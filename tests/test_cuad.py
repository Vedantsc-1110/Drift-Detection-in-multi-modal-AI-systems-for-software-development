"""Task 2.6 tests: CUAD processor (PART2_PLAN Task 2.6, §7.2 2.3).

Loader consumes fixture CUAD rows (offsets verified); each span yields a
Clause with clauseType; NER finds parties/dates/jurisdictions; entity links
(payment terms -> Invoice) resolve against Stage-1. Mocked LLM, no network.
"""

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

rdflib = pytest.importorskip("rdflib")

from contextgraph.prob.cuad import extract_contract, load_rows  # noqa: E402
from contextgraph.prob.router import Router  # noqa: E402
from contextgraph.triple_builder import CTX  # noqa: E402

CUAD = PROJECT_ROOT / "tests" / "fixtures" / "cuad" / "sample_contracts.json"
STAGE1 = PROJECT_ROOT / "tests" / "fixtures" / "llm" / "stage1_fixture.ttl"
RECORDED = PROJECT_ROOT / "tests" / "fixtures" / "llm" / "recorded_cuad_semantic.json"


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
def rows():
    return load_rows(CUAD)


def test_loader_consumes_fixture_rows(rows):
    assert len(rows) == 2
    first = rows[0]
    assert first["contract_id"] == "CUAD-SVC-001"
    assert len(first["clauses"]) == 3
    for row in rows:
        for clause in row["clauses"]:
            assert row["text"][clause["start"]:clause["end"]] == clause["text"]


def test_spans_yield_typed_clauses(rows, stage1):
    router = Router(_FakeClient("[]"), _FakeClient("[]"))
    result = extract_contract(rows[0], router, stage1, generated_at="2026-01-01T00:00:00+00:00")
    graph = result["graph"]
    assert result["errors"] == []
    clauses = {s for s in graph.subjects(rdflib.RDF.type, CTX.Clause)}
    assert len(clauses) == 3
    types = {str(o) for _, _, o in graph.triples((None, CTX.clauseType, None))}
    assert types == {"Payment Terms", "Term", "Governing Law"}
    contract = CTX["Contract/CUAD-SVC-001"]
    assert len(list(graph.objects(contract, CTX.hasClause))) == 3
    parties = {str(o) for s in graph.subjects(rdflib.RDF.type, CTX.Party) for o in graph.objects(s, rdflib.RDFS.label)}
    assert {"Acme Corporation", "Globex Ltd"} <= parties


def test_ner_parties_dates_jurisdictions(rows, stage1):
    router = Router(_FakeClient("[]"), _FakeClient("[]"))
    result = extract_contract(rows[0], router, stage1)
    roles = {e["role"] for e in result["entities"]}
    assert "organization" in roles and "date" in roles and "jurisdiction" in roles


def test_entity_links_to_stage1(rows, stage1):
    router = Router(_FakeClient(RECORDED.read_text(encoding="utf-8")), _FakeClient("[]"))
    result = extract_contract(rows[0], router, stage1)
    graph = result["graph"]
    assert result["errors"] == [] and result["skipped"] == []
    assert (CTX["Clause/CUAD-SVC-001/Payment%20Terms"], CTX.mentionsEntity, CTX["Invoice"]) in graph
