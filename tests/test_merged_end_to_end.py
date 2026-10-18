"""Merged end-to-end test (MERGE_PLAN.md: produce → build → verify → drift).

Parts compose ONLY through .ttl files: Part 1 pipeline + Part 2 extractors
(recorded LLM) write seven files; Part 3 loads/bridges/validates/serves
them; Part 4 versions the produced structural graph. No network.
"""

import sys
import time
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))
sys.path.insert(0, str(PROJECT_ROOT / "tests"))

rdflib = pytest.importorskip("rdflib")
pytest.importorskip("pyoxigraph")
pytest.importorskip("fastapi")
pytest.importorskip("httpx")
starlette_testclient = pytest.importorskip("starlette.testclient")

from contextgraph.bridges import discover_bridges, insert_bridges  # noqa: E402
from contextgraph.contract_api import create_app  # noqa: E402
from contextgraph.contract_pipeline import machine_spec, run as run_part1  # noqa: E402
from contextgraph.contract_store import GRAPH_FILES, ContractStore  # noqa: E402
from contextgraph.contract_validate import validate  # noqa: E402
from contextgraph.drift.versioning import (  # noqa: E402
    create_version,
    load_version,
    manifest_rows,
)
from contextgraph.prob import code_semantic, cuad, documents, edgar  # noqa: E402
from contextgraph.prob.cuad import load_rows as load_cuad_rows  # noqa: E402
from contextgraph.prob.router import Router  # noqa: E402
from contextgraph.prob.ttl_output import merge_graphs, write_outputs  # noqa: E402
from contextgraph.triple_builder import CTX  # noqa: E402

FIX = PROJECT_ROOT / "tests" / "fixtures"
GENERATED_AT = "2026-01-01T00:00:00+00:00"
SHAPES = PROJECT_ROOT / "ontology" / "contract-shapes.ttl"


class _FakeClient:
    name = "groq:test"

    def __init__(self, text):
        self._text = text

    def complete_json(self, system, user):
        return self._text


def _router(name):
    return Router(_FakeClient((FIX / "llm" / name).read_text(encoding="utf-8")), _FakeClient("[]"))


def _stage1_graph(structural_path):
    graph = rdflib.Graph()
    graph.parse(str(structural_path), format="turtle")
    return graph


def _run_all(workdir):
    workdir = Path(workdir)
    part1_out = workdir / "part1"
    manifest = run_part1(FIX, part1_out, GENERATED_AT)
    assert manifest["errors"] == [] and manifest["skipped"] == []

    stage1 = _stage1_graph(part1_out / "ofbiz_structural.ttl")
    semantic = code_semantic.extract_module_semantics(
        "OrderModule", stage1, _router("recorded_order_semantic.json"), GENERATED_AT)["graph"]
    docs = documents.process_corpus(
        [FIX / "docs" / "procurement_policy.docx", FIX / "docs" / "procurement_notice.pdf"],
        _router("recorded_policy_semantic.json"), ["P01-docx", "P01-pdf"], stage1, GENERATED_AT)["graph"]
    cuad_graph = merge_graphs([
        cuad.extract_contract(row, _router("recorded_cuad_semantic.json"), stage1, GENERATED_AT)["graph"]
        for row in load_cuad_rows(FIX / "cuad" / "sample_contracts.json")])
    filing = edgar.extract_filing(
        "ACME-2025-10K", (FIX / "edgar" / "sample_10k.txt").read_text(encoding="utf-8"),
        _router("recorded_edgar_semantic.json"), stage1, GENERATED_AT)["graph"]
    prob_out = workdir / "part2"
    write_outputs({"ofbiz_semantic.ttl": semantic, "document_semantic.ttl": docs,
                   "cuad.ttl": cuad_graph, "edgar.ttl": filing}, prob_out)

    store = ContractStore(workdir / "store")
    for filename, graph_uri in (("ofbiz_structural.ttl", "urn:ofbiz_structural"),
                                ("airflow.ttl", "urn:airflow"), ("cicd.ttl", "urn:cicd")):
        store.load_file(part1_out / filename, graph_uri)
    for filename, graph_uri in (("ofbiz_semantic.ttl", "urn:ofbiz_semantic"),
                                ("document_semantic.ttl", "urn:document_semantic"),
                                ("cuad.ttl", "urn:cuad"), ("edgar.ttl", "urn:edgar")):
        store.load_file(prob_out / filename, graph_uri)
    union = rdflib.Graph()
    for path in (part1_out / "ofbiz_structural.ttl", part1_out / "airflow.ttl",
                 part1_out / "cicd.ttl", prob_out / "ofbiz_semantic.ttl",
                 prob_out / "document_semantic.ttl", prob_out / "cuad.ttl",
                 prob_out / "edgar.ttl"):
        union.parse(str(path), format="turtle")
    bridges = discover_bridges(union)
    insert_bridges(store, bridges)
    return {"manifest": manifest, "store": store, "union": union, "bridges": bridges,
            "part1_out": part1_out, "prob_out": prob_out}


def test_parts_compose_through_ttl_files(tmp_path):
    ctx = _run_all(tmp_path)
    try:
        assert ctx["store"].graphs() == sorted([*GRAPH_FILES, "urn:bridges"])
        det_subjects = set()
        for det_file in ("ofbiz_structural.ttl", "airflow.ttl", "cicd.ttl"):
            det_graph = rdflib.Graph()
            det_graph.parse(str(ctx["part1_out"] / det_file), format="turtle")
            det_subjects.update(str(s) for s in det_graph.subjects())
        for graph_uri in GRAPH_FILES:
            assert ctx["store"].verify_metadata(graph_uri, borrowed=det_subjects) == [], graph_uri
        types = {b["p"] for b in ctx["bridges"]}
        assert {"mentionsEntity", "referencesModule", "relatedTo"} <= types
    finally:
        ctx["store"].close()


def test_union_validates_and_api_answers(tmp_path):
    ctx = _run_all(tmp_path)
    try:
        report = validate(ctx["union"], SHAPES)
        assert report["conforms"], [v["message"] for v in report["violations"]][:5]
        client = starlette_testclient.TestClient(create_app(ctx["store"]))
        contracts = client.get("/contracts/for-module").json()["rows"]
        assert any("CUAD" in r["contract"] or "Agreement" in r["contract"] for r in contracts)
        strict = client.get("/facts/low-confidence", params={"threshold": 0.5}).json()["rows"]
        assert strict == []
        loose = client.get("/facts/low-confidence", params={"threshold": 0.9}).json()["rows"]
        assert loose, "expected sub-0.9 facts in produced data"
    finally:
        ctx["store"].close()


def test_part4_versions_produced_data(tmp_path):
    ctx = _run_all(tmp_path)
    try:
        structural = rdflib.Graph()
        structural.parse(str(ctx["part1_out"] / "ofbiz_structural.ttl"), format="turtle")
        before = len(structural)
        row = create_version(tmp_path / "versions", "n", set(structural), set(),
                             "c0" * 10, "urn:version_n")
        assert row["triples"] == before
        back = load_version(tmp_path / "versions", "n")
        assert len(back) == before
        assert manifest_rows(tmp_path / "versions")[0]["graph_uri"] == "urn:version_n"
    finally:
        ctx["store"].close()


def _report_text(ctx, elapsed):
    lines = ["# Merged end-to-end report (MERGE_PLAN.md)", ""]
    lines.append("- Part 1 files: %d, errors: %d" % (len(ctx["manifest"]["files"]), len(ctx["manifest"]["errors"])))
    lines.append("- Store graphs: %s" % ", ".join(ctx["store"].graphs()))
    lines.append("- Bridge types: %s" % sorted({b["p"] for b in ctx["bridges"]}))
    lines.append("- Wall-clock: %.2fs" % elapsed)
    lines.append("")
    lines.append("## Machine spec")
    for key, value in machine_spec().items():
        lines.append("- %s: %s" % (key, value))
    lines.append("")
    return "\n".join(lines)


def test_merged_report(tmp_path):
    started = time.perf_counter()
    ctx = _run_all(tmp_path)
    try:
        text = _report_text(ctx, time.perf_counter() - started)
    finally:
        ctx["store"].close()
    (tmp_path / "merged_report.md").write_text(text, encoding="utf-8")
    assert "Bridge types" in text and "Machine spec" in text
