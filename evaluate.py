"""Part 1 deterministic evaluation CLI.

Usage:
  python evaluate.py --store stores/order-deps --evaluation evaluation/questions.yaml --out outputs/evaluation
  python evaluate.py --help

Deterministic: no LLM, no network, no clock in output hashes (sorted JSON).
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

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


def _ev_str(ev):
    if not ev:
        return "-"
    parts = []
    if ev.get("file"):
        parts.append(str(ev["file"]))
    if ev.get("line") is not None:
        parts.append("line %s" % ev["line"])
    if ev.get("xpath"):
        parts.append(str(ev["xpath"]))
    if ev.get("extraction_type"):
        parts.append(str(ev["extraction_type"]))
    return "; ".join(parts) if parts else "-"


def _short_answer(ans):
    if ans is None:
        return "-"
    text = json.dumps(ans, sort_keys=True, ensure_ascii=False)
    if len(text) > 400:
        return text[:397] + "..."
    return text


def to_markdown(results, metrics, structural, meta) -> str:
    L = []
    A = L.append
    A("# Part 1 Deterministic Evaluation: Order Context Graph")
    A("")
    A("_Scope: component `order` + explicit dependency `applications/datamodel/entitydef/order-entitymodel.xml`._")
    A("_Method: SOURCE/GOLD (dataset XML) -> EXPECTED CONTEXT -> CONTEXT GRAPH ANSWER (Oxigraph SPARQL). No LLM._")
    A("")
    A("## Metrics")
    A("- Total questions: %d" % metrics["total"])
    A("- Correct: %d" % metrics["correct"])
    A("- Partial: %d" % metrics["partial"])
    A("- Incorrect: %d" % metrics["incorrect"])
    A("- Unresolved (honest, outside scope): %d" % metrics["unresolved"])
    A("- Answer coverage (CORRECT+PARTIAL)/total: %s" % metrics["answer_coverage"])
    A("- Resolved-question correctness CORRECT/(CORRECT+PARTIAL+INCORRECT): %s" % metrics["resolved_correctness"])
    A("- Provenance coverage: %s (%d/%d)" % (metrics["provenance_coverage"], metrics["provenance_covered"], metrics["total"]))
    A("- Direct: %d (%s); Inferred: %d (%s); Unresolved facts: %d (%s)" % (
        metrics["direct_count"], metrics["direct_coverage"], metrics["inferred_count"],
        metrics["inferred_coverage"], metrics["unresolved_count"], metrics["unresolved_fact_coverage"]))
    A("")
    A("## Structural gold set (sampled, NOT repository-wide)")
    A("- Label: %s" % structural["label"])
    A("- Precision: %s (%d/%d)" % (structural["precision"], structural["found"], structural["total"]))
    A("- Recall: %s (%d/%d)" % (structural["recall"], structural["found"], structural["total"]))
    for kind, v in sorted(structural["by_kind"].items()):
        A("- %s: precision %s recall %s (%d/%d)" % (kind, v["precision"], v["recall"], v["found"], v["total"]))
    A("")
    A("## Store / pipeline")
    for k in ("store", "facts", "manifest", "unresolved", "graph", "triples", "facts_count", "unresolved_count"):
        A("- %s: %s" % (k, meta.get(k, "-")))
    A("- evaluation_hash: %s" % meta.get("evaluation_hash", "-"))
    A("")
    A("| ID | Category | Question | Expected | Graph Answer | Status | Fact Type | Evidence |")
    A("|----|----------|----------|----------|--------------|--------|-----------|----------|")
    for r in results:
        A("| %s | %s | %s | %s | %s | %s | %s | %s |" % (
            r["id"], r["category"], r["question"].replace("|", "/"),
            _short_answer(r["expected"]).replace("|", "/"),
            _short_answer(r["graph_answer"]).replace("|", "/"),
            r["status"], r["fact_type"], _ev_str(r.get("evidence")).replace("|", "/")))
    A("")
    for r in results:
        A("### %s — %s" % (r["id"], r["question"]))
        A("- Category: %s; Status: **%s**; Fact type: %s" % (r["category"], r["status"], r["fact_type"]))
        A("- Expected: `%s`" % _short_answer(r["expected"]))
        A("- Graph answer: `%s`" % _short_answer(r["graph_answer"]))
        A("- Evidence: %s" % _ev_str(r.get("evidence")))
        A("- Note: %s" % r.get("note", ""))
        if r.get("source_files"):
            A("- Sources: %s" % ", ".join(r["source_files"]))
        A("")
    A("## Structural details")
    for d in structural["details"]:
        A("- [%s] %s: %s" % (d["kind"], d["name"], "FOUND" if d["found"] else "MISSING"))
    A("")
    return "\n".join(L)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Part 1 deterministic evaluation (no LLM).")
    parser.add_argument("--store", default="stores/order-deps", help="Oxigraph store directory.")
    parser.add_argument("--evaluation", default="evaluation/questions.yaml", help="Question spec.")
    parser.add_argument("--structural", default="evaluation/structural-gold.yaml", help="Structural gold set.")
    parser.add_argument("--facts", default="outputs-deps/order-facts.jsonl")
    parser.add_argument("--manifest", default="outputs-deps/order-manifest.json")
    parser.add_argument("--unresolved", default="outputs-deps/order-unresolved.json")
    parser.add_argument("--graph", default="outputs-deps/order-graph.ttl")
    parser.add_argument("--out", default="outputs/evaluation", help="Output directory.")
    args = parser.parse_args(argv)

    store = ContextStore(args.store)
    facts = _load_jsonl(args.facts)
    manifest = _load_json(args.manifest)
    unresolved = _load_json(args.unresolved)
    questions = _load_yaml(args.evaluation)["questions"]
    gold = _load_yaml(args.structural)

    results, _ev = evaluate_questions(store, facts, manifest, unresolved, questions)
    results = sorted(results, key=lambda r: r["id"])
    metrics = compute_metrics(results)
    structural = evaluate_structural(store, facts, unresolved, gold)

    # triple count: prefer live store count (deterministic), fall back to 0
    try:
        triples = store.count()
    except Exception:
        triples = 0
    meta = {"store": args.store, "facts": args.facts, "manifest": args.manifest,
            "unresolved": args.unresolved, "graph": args.graph, "triples": triples,
            "facts_count": len(facts), "unresolved_count": len(unresolved)}

    payload = {"meta": meta, "metrics": metrics, "results": results, "structural": structural,
               "extractor": "%s %s" % (manifest.get("extractor"), manifest.get("extractor_version")),
               "repository": manifest.get("repository"), "component": manifest.get("component"),
               "scope": manifest.get("scope")}
    meta["evaluation_hash"] = normalized_hash({"results": results, "metrics": metrics, "structural": structural})
    payload["meta"] = meta

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "part1-evaluation.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out / "part1-evaluation.md").write_text(to_markdown(results, metrics, structural, meta), encoding="utf-8")
    (out / "part1-evaluation-summary.json").write_text(
        json.dumps({"metrics": metrics, "structural": {k: structural[k] for k in ("label", "total", "found", "missing", "precision", "recall", "by_kind")},
                    "meta": meta}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("questions: %d correct: %d partial: %d incorrect: %d unresolved: %d hash: %s" % (
        metrics["total"], metrics["correct"], metrics["partial"], metrics["incorrect"], metrics["unresolved"], meta["evaluation_hash"]))
    print("structural: precision %s recall %s (%d/%d)" % (structural["precision"], structural["recall"], structural["found"], structural["total"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
