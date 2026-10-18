"""Task 2.10 tests: Part 2 integration run (§11.1 metrics).

Adaptation: no live Groq key / Ollama here, so this runs end to end on
fixtures with recorded (mocked) LLM responses and documents deviations.
Metrics: corroboration rate, triple counts per graph, and a 50-claim human
rating sample table (accuracy verdict stays N/A until a human rates it).
"""

import sys
import time
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

rdflib = pytest.importorskip("rdflib")

from contextgraph.contract_pipeline import machine_spec  # noqa: E402
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
ACCURACY_SAMPLE = 50


class _FakeClient:
    name = "groq:test"

    def __init__(self, text):
        self._text = text

    def complete_json(self, system, user):
        return self._text


def _router(name):
    return Router(_FakeClient((FIX / "llm" / name).read_text(encoding="utf-8")), _FakeClient("[]"))


def _run_all(out_dir):
    out_dir = Path(out_dir)
    stage1 = rdflib.Graph()
    stage1.parse(str(FIX / "llm" / "stage1_fixture.ttl"), format="turtle")
    started = time.perf_counter()

    semantic_result = code_semantic.extract_module_semantics(
        "OrderModule", stage1, _router("recorded_order_semantic.json"), GENERATED_AT)
    semantic = semantic_result["graph"]
    semantic_scored = semantic_result["scored"]
    docs = documents.process_corpus(
        [FIX / "docs" / "procurement_policy.docx", FIX / "docs" / "procurement_notice.pdf",
         FIX / "docs" / "procurement_policy.md"],
        _router("recorded_policy_semantic.json"), ["P01-docx", "P01-pdf", "P01-md"], stage1, GENERATED_AT)
    cuad_graphs, cuad_scored = [], []
    for row in cuad.load_rows(FIX / "cuad" / "sample_contracts.json"):
        result = cuad.extract_contract(row, _router("recorded_cuad_semantic.json"), stage1, GENERATED_AT)
        cuad_graphs.append(result["graph"])
        cuad_scored.extend(result["scored"])
    filing = edgar.extract_filing(
        "ACME-2025-10K", (FIX / "edgar" / "sample_10k.txt").read_text(encoding="utf-8"),
        _router("recorded_edgar_semantic.json"), stage1, GENERATED_AT)

    families = {"ofbiz_semantic.ttl": semantic, "document_semantic.ttl": docs["graph"],
                "cuad.ttl": merge_graphs(cuad_graphs), "edgar.ttl": filing["graph"]}
    scored_all = (
        semantic_scored
        + [s for r in docs["results"] for s in r["scored"]] + cuad_scored + filing["scored"]
    )
    write_outputs(families, out_dir)
    elapsed = time.perf_counter() - started
    return stage1, families, scored_all, elapsed


def _report(families, scored_all, elapsed):
    total_triples = sum(len(g) for g in families.values())
    direct = sum(1 for s in scored_all if s["corroborated"])
    supported = sum(1 for s in scored_all if s["supportType"] in ("DIRECT", "INDIRECT"))
    n = len(scored_all)
    sample = sorted(scored_all, key=lambda s: (s["predicate"], s["subject"], s["object"]))[:ACCURACY_SAMPLE]
    lines = ["# Part 2 integration run report (§11.1)", ""]
    lines.append("- LLM layer: RECORDED (mocked) responses — no live Groq key / Ollama in this run.")
    lines.append("- Stage-1 input: tests/fixtures/llm/stage1_fixture.ttl (hand-made, fixture tree).")
    lines.append("- Wall-clock: %.2fs" % elapsed)
    lines.append("")
    lines.append("## Triples per graph (metric: ~500+ on real data)")
    for name in OUTPUT_FILES:
        lines.append("- %s: %d" % (name, len(families[name])))
    lines.append("- Total: %d — %s" % (total_triples, "PASS" if total_triples >= 500 else "FAIL (fixture scale; see deviation)"))
    lines.append("")
    lines.append("## Corroboration (metric: > 60% supported)")
    lines.append("- DIRECT rate: %d/%d = %.4f" % (direct, n, direct / n if n else 1.0))
    lines.append("- DIRECT+INDIRECT rate: %d/%d = %.4f — %s"
                 % (supported, n, supported / n if n else 1.0,
                    "PASS" if n and supported / n > 0.60 else "FAIL (recorded claims are novel by design; see deviation)"))
    lines.append("")
    lines.append("## Accuracy sample (metric: > 80%% of 50 human-rated facts)")
    lines.append("- Verdict: N/A — requires human rating. Sample table for raters:")
    lines.append("| # | subject | predicate | object | confidence | support | rating |")
    lines.append("|---|---------|-----------|--------|------------|---------|--------|")
    for i, claim in enumerate(sample):
        lines.append("| %d | %s | %s | %s | %.2f | %s | _ |"
                     % (i + 1, claim["subject"][:40], claim["predicate"], claim["object"][:40],
                        claim["confidence"], claim["supportType"]))
    lines.append("")
    lines.append("## Machine spec")
    for key, value in machine_spec().items():
        lines.append("- %s: %s" % (key, value))
    lines.append("")
    lines.append("## Deviation notes")
    lines.append("- No live LLM: recorded fixtures stand in; the corroborated path (>=0.95)")
    lines.append("  is proven by Task 2.3 unit tests with matched claims.")
    lines.append("- Fixture scale (2 contracts, 1 filing, 3 docs) cannot hit ~500 triples;")
    lines.append("  per-graph outputs validate clean under Task 2.8 rules.")
    lines.append("")
    return "\n".join(lines)


def _run_with_report(out_dir):
    out_dir = Path(out_dir)
    stage1, families, scored_all, elapsed = _run_all(out_dir)
    report = _report(families, scored_all, elapsed)
    (out_dir / "run_report.md").write_text(report, encoding="utf-8")
    return stage1, families, scored_all, elapsed, report


def test_integration_end_to_end(tmp_path):
    stage1, families, scored_all, elapsed, report = _run_with_report(tmp_path)
    assert elapsed < 300
    assert scored_all, "expected scored claims from every family"
    for name in OUTPUT_FILES:
        path = tmp_path / name
        assert path.is_file()
        graph = rdflib.Graph()
        graph.parse(str(path), format="turtle")
        assert len(graph) == len(families[name]) > 0
        assert validate_prob_graph(graph, stage1) == [], name
    text = (tmp_path / "run_report.md").read_text(encoding="utf-8")
    assert "Corroboration" in text and "Accuracy sample" in text and "Machine spec" in text
    assert "| rating |" in text
