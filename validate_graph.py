"""Validate a Context Graph: python validate_graph.py --graph outputs/order-graph.ttl --shapes ontology/context-shapes.ttl --out outputs/order-validation.txt"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from contextgraph.validate import validate_graph  # noqa: E402


def main(argv=None):
    import argparse

    parser = argparse.ArgumentParser(description="SHACL-validate the Context Graph.")
    parser.add_argument("--graph", required=True)
    parser.add_argument("--shapes", required=True)
    parser.add_argument("--out", required=True, help="Validation report (.txt).")
    args = parser.parse_args(argv)
    result = validate_graph(args.graph, args.shapes)
    lines = [
        "conforms: %s" % result["conforms"],
        "violations: %d" % len(result["violations"]),
        "warnings: %d" % len(result["warnings"]),
        "",
        "## Violations",
    ]
    lines += ["- %s | %s | %s" % (v["focus"], v["path"], v["message"]) for v in result["violations"]]
    lines += ["", "## Warnings (first 30)"]
    lines += ["- %s | %s | %s" % (w["focus"], w["path"], w["message"]) for w in result["warnings"][:30]]
    lines += [""]
    Path(args.out).write_text("\n".join(lines), encoding="utf-8")
    print("conforms: %s violations: %d warnings: %d" % (result["conforms"], len(result["violations"]), len(result["warnings"])))
    return 0 if result["conforms"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
