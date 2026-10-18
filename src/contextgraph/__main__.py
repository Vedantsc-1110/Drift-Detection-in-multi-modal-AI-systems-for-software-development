"""CLI: python -m contextgraph --root <ofbiz-root> --component order --out outputs"""
from __future__ import annotations

import argparse

from .pipeline import run


def main(argv=None):
    parser = argparse.ArgumentParser(description="Deterministic OFBiz context extractor (Part 1).")
    parser.add_argument("--root", required=True, help="OFBiz repository root (read-only).")
    parser.add_argument("--component", default="order", help="Component under applications/.")
    parser.add_argument("--out", required=True, help="Output directory for facts/report.")
    parser.add_argument("--include-dependencies", action="store_true",
                        help="Also parse explicitly declared dependency artifacts (see scanner.COMPONENT_DEPENDENCIES).")
    args = parser.parse_args(argv)
    manifest = run(args.root, args.component, args.out, include_dependencies=args.include_dependencies)
    print("facts: %d unresolved: %d errors: %d" % (sum(manifest["counts"].values()), manifest["unresolved_count"], len(manifest["errors"])))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
