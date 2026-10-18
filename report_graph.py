"""Context Identification Report: python report_graph.py --store stores/order --manifest outputs/order-manifest.json --facts outputs/order-facts.jsonl --unresolved outputs/order-unresolved.json --out-json outputs/order-context-report.json --out-md outputs/order-context-report.md"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from contextgraph.report import build_report, write_reports  # noqa: E402
from contextgraph.store import ContextStore  # noqa: E402


def main(argv=None):
    import argparse

    parser = argparse.ArgumentParser(description="Generate the Context Identification Report (JSON + Markdown).")
    parser.add_argument("--store", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--facts", required=True)
    parser.add_argument("--unresolved", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-md", required=True)
    args = parser.parse_args(argv)
    store = ContextStore(args.store)
    manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    facts = [json.loads(line) for line in Path(args.facts).read_text(encoding="utf-8").splitlines() if line.strip()]
    unresolved = json.loads(Path(args.unresolved).read_text(encoding="utf-8"))
    report = build_report(store, manifest, facts, unresolved)
    write_reports(report, args.out_json, args.out_md)
    print("services: %d entities: %d ecas: %d facts: %d (direct %d / inferred %d)" % (
        report["services_discovered"], report["entities_discovered"], report["eca_rules_discovered"],
        report["facts_extracted"], report["direct_facts"], report["inferred_facts"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
