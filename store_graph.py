"""Oxigraph store CLI: python store_graph.py (load|query|export|clear) ..."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from contextgraph.queries import QUERIES  # noqa: E402
from contextgraph.store import ContextStore  # noqa: E402


def main(argv=None):
    import argparse

    parser = argparse.ArgumentParser(description="Local Oxigraph Context Graph store.")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_load = sub.add_parser("load", help="Clear (optional) and bulk-load a Turtle graph.")
    p_load.add_argument("--graph", required=True)
    p_load.add_argument("--store", required=True)
    p_load.add_argument("--no-clear", action="store_true")
    p_query = sub.add_parser("query", help="Run a canned query.")
    p_query.add_argument("--store", required=True)
    p_query.add_argument("--q", required=True, choices=sorted(QUERIES))
    p_query.add_argument("--arg", default="", help="Query argument (service/component/fact).")
    p_exp = sub.add_parser("export", help="Dump the store to Turtle.")
    p_exp.add_argument("--store", required=True)
    p_exp.add_argument("--out", required=True)
    p_clear = sub.add_parser("clear", help="Remove all triples.")
    p_clear.add_argument("--store", required=True)
    args = parser.parse_args(argv)

    if args.cmd == "load":
        store = ContextStore(args.store)
        if not args.no_clear:
            store.clear()
        store.load_turtle(args.graph)
        print("loaded triples: %d" % store.count())
    elif args.cmd == "query":
        store = ContextStore(args.store)
        fn = QUERIES[args.q]
        try:
            sparql = fn(args.arg) if args.arg else fn()
        except TypeError:
            sparql = fn(args.arg)
        for row in store.sparql(sparql):
            print(json.dumps(row, sort_keys=True, ensure_ascii=False))
    elif args.cmd == "export":
        store = ContextStore(args.store)
        store.export_turtle(args.out)
        print("exported to %s" % args.out)
    elif args.cmd == "clear":
        store = ContextStore(args.store)
        store.clear()
        print("cleared triples: %d" % store.count())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
