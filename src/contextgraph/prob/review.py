"""Review flow: accept/reject proposals. The never-overwrite guard lives here.

A proposal is auto-rejected (reason=duplicates-deterministic) when its
(subject, predicate, object) already exists as a deterministic triple.
Accepted proposals stay in the proposals file with status=accepted; they are
NEVER written into facts.jsonl or the deterministic graph.
"""
from __future__ import annotations

import json
from pathlib import Path


def load_proposals(path):
    path = Path(path)
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def save_proposals(path, proposals):
    with open(path, "w", encoding="utf-8") as fh:
        for fact in proposals:
            fh.write(json.dumps(fact, sort_keys=True, ensure_ascii=False) + "\n")


def deterministic_triples(facts_path):
    """(subject-id, predicate, object-id) for resolved deterministic edges."""
    triples = set()
    with open(facts_path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            fact = json.loads(line)
            if fact.get("kind") == "edge":
                props = fact.get("props", {})
                triples.add((props.get("from"), props.get("predicate"), props.get("to")))
    return triples


def review(proposals, index: int, accept: bool, deterministic=None, reason=""):
    """Set status on proposals[index]. Returns (ok, message)."""
    if not (0 <= index < len(proposals)):
        return False, "no proposal at index %d" % index
    fact = proposals[index]
    if accept and deterministic is not None:
        key = (fact.get("subject"), fact.get("predicate"), fact.get("object"))
        if key in deterministic:
            fact["status"] = "rejected"
            fact["reviewReason"] = "duplicates-deterministic"
            return False, "refused: duplicates a deterministic triple; marked rejected"
    fact["status"] = "accepted" if accept else "rejected"
    if reason:
        fact["reviewReason"] = reason
    else:
        fact.pop("reviewReason", None)
    return True, fact["status"]


def auto_reject_duplicates(proposals, deterministic):
    """Mark any proposal colliding with deterministic triples as rejected."""
    count = 0
    for fact in proposals:
        if fact.get("status") != "proposed":
            continue
        if (fact.get("subject"), fact.get("predicate"), fact.get("object")) in deterministic:
            fact["status"] = "rejected"
            fact["reviewReason"] = "duplicates-deterministic"
            count += 1
    return count
