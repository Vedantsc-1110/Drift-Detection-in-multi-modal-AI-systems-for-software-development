"""Experiment CLI: init adjudication templates, score adjudicated runs, write reports.

  python eval.py init --facts <facts.jsonl> --proposals <proposals.jsonl> --sample <manifest.json> --out <template.jsonl> [--max-items N --seed S]
  python eval.py score --template <adjudicated.jsonl> --facts <facts.jsonl> --proposals <proposals.jsonl> --graph <graph.ttl> --shapes <shapes.ttl> --sample <manifest.json> [--timings <json> --facts-repeat F --proposals-repeat P] --out <results.json>
  python eval.py report --results <results.json> --out <report.md>
"""
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "src"))

from contextgraph.validate import validate_graph  # noqa: E402

VERDICTS = ("correct", "incorrect", "")


def _load_jsonl(path):
    return [json.loads(x) for x in Path(path).read_text(encoding="utf-8").splitlines() if x.strip()]


def _write_jsonl(path, items):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        for item in items:
            fh.write(json.dumps(item, sort_keys=True, ensure_ascii=False) + "\n")


def _sample_files(manifest_path):
    return json.loads(Path(manifest_path).read_text(encoding="utf-8"))["files"]


def cmd_init(args):
    sample_files = set(_sample_files(args.sample))
    facts = [f for f in _load_jsonl(args.facts) if f["prov"].get("file") in sample_files]
    facts.sort(key=lambda f: f["id"])
    if args.max_items and len(facts) > args.max_items:
        facts = sorted(random.Random(args.seed).sample(facts, args.max_items), key=lambda f: f["id"])
    items = []
    for fact in facts:
        prov = fact["prov"]
        items.append({
            "key": "A:" + fact["id"], "arm": "A", "kind": fact["kind"],
            "summary": _summarize(fact), "file": prov.get("file"), "line": prov.get("line"),
            "verdict": "", "reviewer": "", "note": "",
        })
    proposals = _load_jsonl(args.proposals) if args.proposals and Path(args.proposals).is_file() else []
    for i, p in enumerate(proposals):
        ev = p.get("evidence") or []
        items.append({
            "key": "B:%d:%s|%s|%s" % (i, p.get("subject"), p.get("predicate"), p.get("object")),
            "arm": "B", "kind": "probabilistic-proposal",
            "summary": "%s --%s--> %s (conf=%s, %s)" % (p.get("subject"), p.get("predicate"), p.get("object"), p.get("confidence"), p.get("model")),
            "file": "(model output; evidence: %s)" % ("; ".join(ev[:2])),
            "line": None, "verdict": "", "reviewer": "", "note": "",
        })
    _write_jsonl(args.out, items)
    print("template items: %d (A=%d B=%d)" % (len(items), sum(1 for x in items if x["arm"] == "A"), sum(1 for x in items if x["arm"] == "B")))


def _summarize(fact):
    kind, props = fact["kind"], fact["props"]
    if kind == "service":
        return "service %s engine=%s invoke=%s" % (props.get("name"), props.get("engine"), props.get("invoke"))
    if kind == "auto_attributes":
        return "auto-attributes %s include=%s mode=%s entity=%s" % (props.get("service"), props.get("include"), props.get("mode"), props.get("entity_ref"))
    if kind == "service_param":
        return "param %s type=%s mode=%s" % (props.get("name"), props.get("type"), props.get("mode"))
    return "%s %s" % (kind, props.get("name", fact["id"].rsplit("/", 1)[-1]))


def _b_key_parts(key: str):
    """Template B key 'B:<i>:<s>|<p>|<o>' -> (s, p, o)."""
    try:
        return tuple(key.split(":", 2)[2].split("|"))
    except Exception:
        return ()


def _arm_metrics(items, fileset_files, facts, proposals, extra_provenance_ok):
    items = list(items)
    adjudicated = [x for x in items if x["verdict"] in ("correct", "incorrect")]
    correct = [x for x in adjudicated if x["verdict"] == "correct"]
    acc = round(len(correct) / len(adjudicated), 4) if adjudicated else None
    return {
        "extracted": len(items),
        "adjudicated": len(adjudicated),
        "correct": len(correct),
        "unsupported": len(adjudicated) - len(correct),
        "pending": len(items) - len(adjudicated),
        "accuracy": acc,
        "provenance_coverage": extra_provenance_ok,
    }


def _prov_ok_deterministic(facts):
    ok = sum(1 for f in facts if f["prov"].get("file") and (f["prov"].get("line") is not None or f["prov"].get("evidence")))
    return {"covered": ok, "total": len(facts), "rate": round(ok / len(facts), 4) if facts else None}


def _prov_ok_probabilistic(proposals):
    ok = sum(1 for p in proposals if p.get("evidence") and p.get("model") and p.get("confidence") is not None)
    return {"covered": ok, "total": len(proposals), "rate": round(ok / len(proposals), 4) if proposals else None}


def _agreement(path_a, path_b):
    if not path_a or not path_b:
        return None
    if not Path(path_a).is_file() or not Path(path_b).is_file():
        return None
    norm_a = _normalized_lines(path_a)
    norm_b = _normalized_lines(path_b)
    if norm_a is not None and norm_b is not None:
        return {"identical_content": norm_a == norm_b, "items_a": len(norm_a), "items_b": len(norm_b)}
    a, b = Path(path_a).read_bytes(), Path(path_b).read_bytes()
    return {"identical_bytes": a == b, "bytes_a": len(a), "bytes_b": len(b)}


def _normalized_lines(path):
    """JSONL with volatile keys (extractedAt) stripped; None if not JSONL."""
    try:
        out = []
        for line in Path(path).read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            obj = json.loads(line)
            if not isinstance(obj, dict):
                return None
            obj.pop("extractedAt", None)
            out.append(json.dumps(obj, sort_keys=True))
        return sorted(out)
    except Exception:
        return None


def cmd_score(args):
    sample_files = set(_sample_files(args.sample))
    template = _load_jsonl(args.template)
    verdict = {x["key"]: x for x in template if x.get("verdict") in ("correct", "incorrect")}
    facts = [f for f in _load_jsonl(args.facts) if f["prov"].get("file") in sample_files]
    proposals = _load_jsonl(args.proposals) if args.proposals and Path(args.proposals).is_file() else []
    accepted = [p for p in proposals if p.get("status") == "accepted"]

    a_items = [x for x in template if x["arm"] == "A"]
    b_items = [x for x in template if x["arm"] == "B"]
    a_metrics = _arm_metrics(a_items, sample_files, facts, proposals, _prov_ok_deterministic(facts))
    b_metrics = _arm_metrics(b_items, sample_files, facts, proposals, _prov_ok_probabilistic(proposals))
    accepted_keys = {(p.get("subject"), p.get("predicate"), p.get("object")) for p in accepted}
    c_items = a_items + [x for x in b_items if _b_key_parts(x["key"]) in accepted_keys]
    c_metrics = _arm_metrics(c_items, sample_files, facts, proposals,
                             {"arms": {"deterministic": _prov_ok_deterministic(facts),
                                       "probabilistic": _prov_ok_probabilistic(proposals)}})
    c_metrics["note"] = ("Hybrid = deterministic facts + accepted proposals sidecar "
                         "(%d accepted of %d proposed; graph unchanged)." % (len(accepted), len(proposals)))

    timings = json.loads(Path(args.timings).read_text(encoding="utf-8")) if args.timings and Path(args.timings).is_file() else {}
    validation = None
    if args.graph and args.shapes and Path(args.graph).is_file():
        v = validate_graph(args.graph, args.shapes)
        validation = {"conforms": v["conforms"], "violations": len(v["violations"]), "warnings": len(v["warnings"])}

    results = {
        "sample": args.sample,
        "adjudication": {"reviewed": len(verdict), "total": len(template),
                         "coverage": round(len(verdict) / len(template), 4) if template else None},
        "arms": {
            "A_deterministic": dict(a_metrics, execution_sec=timings.get("A"), repeatability=_agreement(args.facts, args.facts_repeat), validation=validation),
            "B_probabilistic": dict(b_metrics, execution_sec=timings.get("B"), repeatability=_agreement(args.proposals, args.proposals_repeat), validation=None),
            "C_hybrid": dict(c_metrics, execution_sec=timings.get("C"), repeatability=None, validation=validation),
        },
        "warnings": [
            "Stub-client B numbers measure plumbing only, never LLM quality.",
            "C validation covers the deterministic graph; accepted proposals are not merged into it.",
        ],
    }
    Path(args.out).write_text(json.dumps(results, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("adjudicated %d/%d arms scored" % (len(verdict), len(template)))


def cmd_report(args):
    results = json.loads(Path(args.results).read_text(encoding="utf-8"))
    L = ["# Context Identification Experiment: comparison report", ""]
    adj = results["adjudication"]
    L.append("Adjudication coverage: %d/%d (%.1f%%). Accuracy-style metrics use adjudicated items only." % (
        adj["reviewed"], adj["total"], 100 * (adj["coverage"] or 0)))
    L.append("")
    L.append("| Metric | A deterministic | B probabilistic | C hybrid |")
    L.append("|---|---|---|---|")
    arms = results["arms"]
    def row(label, key, fmt=lambda v: "n/a" if v is None else str(v)):
        L.append("| %s | %s | %s | %s |" % (label, fmt(arms["A_deterministic"].get(key)), fmt(arms["B_probabilistic"].get(key)), fmt(arms["C_hybrid"].get(key))))
    row("Extracted facts", "extracted")
    row("Adjudicated", "adjudicated")
    row("Correct", "correct")
    row("Unsupported", "unsupported")
    row("Pending review", "pending")
    row("Accuracy (adjudicated only)", "accuracy")
    row("Execution time (s)", "execution_sec")
    L.append("")
    L.append("Provenance coverage (all extracted, not just adjudicated):")
    for arm in ("A_deterministic", "B_probabilistic"):
        L.append("- %s: %s" % (arm, json.dumps(arms[arm]["provenance_coverage"], sort_keys=True)))
    L.append("")
    L.append("Repeatability (rerun agreement, volatile timestamps excluded):")
    for arm in ("A_deterministic", "B_probabilistic"):
        L.append("- %s: %s" % (arm, json.dumps(arms[arm]["repeatability"])))
    L.append("")
    L.append("Graph validation (SHACL):")
    for arm in ("A_deterministic", "C_hybrid"):
        L.append("- %s: %s" % (arm, json.dumps(arms[arm]["validation"])))
    L.append("- B_probabilistic: n/a (proposals are not graph triples)")
    L.append("")
    for w in results.get("warnings", []):
        L.append("> " + w)
    L.append("")
    Path(args.out_md).write_text("\n".join(L), encoding="utf-8")
    print("wrote %s" % args.out_md)


def main(argv=None):
    import argparse

    parser = argparse.ArgumentParser(description="Context-identification experiment framework.")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_init = sub.add_parser("init")
    p_init.add_argument("--facts", required=True)
    p_init.add_argument("--proposals", default="")
    p_init.add_argument("--sample", required=True)
    p_init.add_argument("--out", required=True)
    p_init.add_argument("--max-items", type=int, default=0)
    p_init.add_argument("--seed", type=int, default=42)
    p_score = sub.add_parser("score")
    p_score.add_argument("--template", required=True)
    p_score.add_argument("--facts", required=True)
    p_score.add_argument("--proposals", default="")
    p_score.add_argument("--graph", default="")
    p_score.add_argument("--shapes", default="")
    p_score.add_argument("--sample", required=True)
    p_score.add_argument("--timings", default="")
    p_score.add_argument("--facts-repeat", default="")
    p_score.add_argument("--proposals-repeat", default="")
    p_score.add_argument("--out", required=True)
    p_rep = sub.add_parser("report")
    p_rep.add_argument("--results", required=True)
    p_rep.add_argument("--out-md", required=True)
    args = parser.parse_args(argv)
    {"init": cmd_init, "score": cmd_score, "report": cmd_report}[args.cmd](args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
