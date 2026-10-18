"""Build the RDF Context Graph: python build_graph.py --facts outputs/order-facts.jsonl --manifest outputs/order-manifest.json --out outputs/order-graph.ttl [--as-of TS] [--repo-path P]"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from contextgraph.graph import build  # noqa: E402


def main(argv=None):
    import argparse

    parser = argparse.ArgumentParser(description="Build RDF Context Graph (Turtle) from extractor facts.")
    parser.add_argument("--facts", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--as-of", default=None, help="Fixed extractedAt literal for reproducible builds.")
    parser.add_argument("--repo-path", default="", help="Repository path recorded for audit.")
    args = parser.parse_args(argv)
    stats = build(args.facts, args.manifest, args.out, as_of=args.as_of, repo_path=args.repo_path)
    print("triples: %d path: %s" % (stats["triples"], stats["path"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
