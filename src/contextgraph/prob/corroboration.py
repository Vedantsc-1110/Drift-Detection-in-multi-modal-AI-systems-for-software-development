"""Corroboration + confidence assignment (PART2_PLAN Task 2.3, Algorithm 2).

Each LLM claim is checked against deterministic triples (rdflib Graph or
plain (subject, predicate, object) iterables). Matching is case-insensitive
on URI last-segments, so claim labels ("createOrder") meet deterministic
URIs (".../Service/createOrder").

Frozen rules (OPEN_QUESTIONS Q9 resolution — corroborated floors at 0.95,
keeping a higher raw score; uncorroborated raw scores clamp into the band):
  DIRECT      triple match (+evidence)            -> max(raw, 0.95)
  INDIRECT    endpoint known, triple not         -> clamp(raw, 0.70, 0.85)
  SYNTHETIC   no match, evidence present         -> clamp(raw, 0.70, 0.85)
  UNRESOLVED  no match, no evidence              -> clamp(raw, 0.70, 0.85)

Every scored claim records corroborated, supportType, confidence,
confidence_rule, and the matched triple (or None).
"""

from __future__ import annotations

CORROBORATED_FLOOR = 0.95
RAW_LO, RAW_HI = 0.70, 0.85


def _norm(term) -> str:
    text = str(term).strip().lower()
    return text.rsplit("/", 1)[-1].rsplit("#", 1)[-1]


def _triples(deterministic) -> set:
    """Normalized triple set from an rdflib Graph or (s, p, o) iterables."""
    return {(_norm(s), _norm(p), _norm(o)) for s, p, o in deterministic}


def corroborate(claims: list, deterministic) -> list:
    """Score claims against deterministic evidence. Pure function."""
    known = _triples(deterministic)
    nodes = {s for s, _, _ in known} | {o for _, _, o in known}
    scored = []
    for claim in claims:
        key = (_norm(claim.get("subject", "")), _norm(claim.get("predicate", "")), _norm(claim.get("object", "")))
        raw = claim.get("confidence", 0.0)
        try:
            raw = float(raw)
        except (TypeError, ValueError):
            raw = 0.0
        evidence = list(claim.get("evidence") or [])
        matched = key if key in known else None
        if matched is not None:
            support, confidence, rule = "DIRECT", max(raw, CORROBORATED_FLOOR), "corroborated-floor-0.95"
        else:
            confidence, rule = (min(max(raw, RAW_LO), RAW_HI), "raw-in-band" if RAW_LO <= raw <= RAW_HI else "clamped-to-band")
            if key[0] in nodes or key[2] in nodes:
                support = "INDIRECT"
            elif evidence:
                support = "SYNTHETIC"
            else:
                support = "UNRESOLVED"
        scored.append(
            {**claim, "confidence": confidence, "corroborated": matched is not None,
             "supportType": support, "confidence_rule": rule, "matched_triple": matched}
        )
    return scored
