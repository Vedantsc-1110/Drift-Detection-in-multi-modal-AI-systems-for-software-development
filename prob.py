"""Probabilistic layer CLI (separate from the deterministic pipeline).

  python prob.py propose --facts outputs/order-facts.jsonl --source applications/order/servicedef/services_reservations.xml --out outputs/prob/reservations-proposals.jsonl [--model NAME|--stub]
  python prob.py review --proposals <file> --facts outputs/order-facts.jsonl [--accept N|--reject N --reason R|--auto-reject]
  python prob.py list --proposals <file>
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from contextgraph.prob import prompts  # noqa: E402
from contextgraph.prob.client import OllamaClient, StubClient  # noqa: E402
from contextgraph.prob.propose import collect_example_services, propose  # noqa: E402
from contextgraph.prob.review import (  # noqa: E402
    auto_reject_duplicates,
    deterministic_triples,
    load_proposals,
    review,
    save_proposals,
)


def main(argv=None):
    import argparse

    parser = argparse.ArgumentParser(description="Probabilistic extraction layer (Ollama; never touches deterministic outputs).")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("propose")
    p.add_argument("--facts", required=True)
    p.add_argument("--source", required=True, help="Single controlled source file (repo-relative).")
    p.add_argument("--out", required=True)
    p.add_argument("--model", default="qwen2.5:1.5b")
    p.add_argument("--stub", action="store_true", help="Use labeled stub client (tests/demos).")
    p.add_argument("--stub-response", default="[]")
    p.add_argument("--stub-response-file", default="")

    r = sub.add_parser("review")
    r.add_argument("--proposals", required=True)
    r.add_argument("--facts", default="")
    r.add_argument("--accept", type=int, default=None)
    r.add_argument("--reject", type=int, default=None)
    r.add_argument("--reason", default="")
    r.add_argument("--auto-reject", action="store_true")

    l = sub.add_parser("list")
    l.add_argument("--proposals", required=True)
    args = parser.parse_args(argv)

    if args.cmd == "propose":
        facts = [json.loads(x) for x in Path(args.facts).read_text(encoding="utf-8").splitlines() if x.strip()]
        services = collect_example_services(facts, args.source)
        if not services:
            print("no services found in %s" % args.source)
            return 2
        if args.stub:
            canned = Path(args.stub_response_file).read_text(encoding="utf-8") if args.stub_response_file else args.stub_response
            client, model_name = StubClient(canned), StubClient.name
        else:
            client, model_name = OllamaClient(args.model), "ollama:" + args.model
            if not client.ping():
                print("ollama not reachable at %s (is `ollama serve` running? `ollama pull %s`?)" % (client.host, args.model))
                return 3
        found, errors = propose(client, services, model_name)
        for e in errors:
            print("dropped:", e)
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        save_proposals(args.out, found)
        print("services: %d proposals: %d prompt: %s" % (len(services), len(found), prompts.PROMPT_VERSION))
    elif args.cmd == "review":
        proposals = load_proposals(args.proposals)
        det = deterministic_triples(args.facts) if args.facts else None
        if args.auto_reject:
            n = auto_reject_duplicates(proposals, det or set())
            print("auto-rejected duplicates: %d" % n)
        elif args.accept is not None:
            ok, msg = review(proposals, args.accept, accept=True, deterministic=det, reason=args.reason)
            print(msg)
            if not ok:
                save_proposals(args.proposals, proposals)
                return 4
        elif args.reject is not None:
            ok, msg = review(proposals, args.reject, accept=False, reason=args.reason)
            print(msg)
        else:
            print("specify --accept N, --reject N, or --auto-reject")
            return 2
        save_proposals(args.proposals, proposals)
    elif args.cmd == "list":
        for i, f in enumerate(load_proposals(args.proposals)):
            print("[%d] %s | %s -> %s | conf=%s | %s | %s %s" % (
                i, f["status"], f["subject"], f["object"], f["confidence"],
                f["predicate"], f["model"], f["promptVersion"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
