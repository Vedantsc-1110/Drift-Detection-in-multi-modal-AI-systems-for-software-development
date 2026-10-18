"""Developer inspection tool.

Usage: python context.py [--store stores/order] <command> [args]
  services | entities | eca | stats
  service <name> | entity <name> | source <pattern>
  validate [--graph outputs/order-graph.ttl --shapes ontology/context-shapes.ttl]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from contextgraph import inspect as I  # noqa: E402
from contextgraph.store import ContextStore  # noqa: E402

DEFAULT_STORE = "stores/order"


def main(argv=None):
    import argparse

    parser = argparse.ArgumentParser(description="Inspect the Context Graph (developer tool).")
    parser.add_argument("--store", default=DEFAULT_STORE)
    parser.add_argument("--unresolved", default="outputs/order-unresolved.json")
    parser.add_argument("--graph", default="outputs/order-graph.ttl")
    parser.add_argument("--shapes", default="ontology/context-shapes.ttl")
    parser.add_argument("command", choices=["services", "entities", "eca", "service", "entity", "source", "stats", "validate"])
    parser.add_argument("arg", nargs="?", default="")
    args = parser.parse_args(argv)

    if args.command == "validate":
        print(I.cmd_validate(args.graph, args.shapes))
        return 0
    store = ContextStore(args.store)
    if args.command == "services":
        print(I.cmd_services(store))
    elif args.command == "entities":
        print(I.cmd_entities(store))
    elif args.command == "eca":
        print(I.cmd_eca(store))
    elif args.command == "service":
        print(I.cmd_service(store, args.arg))
    elif args.command == "entity":
        print(I.cmd_entity(store, args.arg, args.unresolved))
    elif args.command == "source":
        print(I.cmd_source(store, args.arg))
    elif args.command == "stats":
        print(I.cmd_stats(store))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
