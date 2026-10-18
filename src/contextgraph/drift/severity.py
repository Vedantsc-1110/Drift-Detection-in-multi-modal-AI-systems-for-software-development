"""Severity scoring (§7.3 Step 6, PART4 Task 4.7).

Severity = Σ(weight × factor_score) with the EXACT CONTRACT.md §7 weights
and value scales — do not tune these. Scores round to 9 decimals (binary
float hygiene; values stay exact at the documented precision).

OPEN Q1 resolution: the canonical Agent C 0.82 is exact for inputs
high / signature-break / 3+-hop / yes / yes / yes
(0.15×0.8 + 0.35×1.0 + 0.20×0.25 + 0.10×1.0 + 0.10×1.0 + 0.10×1.0 = 0.82).
The 0.825 in the question comes from a different factor reading (five
nonzero factors); the documented 0.82 stands with the inputs above.
"""

from __future__ import annotations

import math

WEIGHTS = {"criticality": 0.15, "breakage": 0.35, "directness": 0.20,
           "assumption": 0.10, "constraint": 0.10, "conflicting": 0.10}

CRITICALITY = {"critical": 1.0, "high": 0.8, "normal": 0.5, "low": 0.2}
BREAKAGE = {"signature": 1.0, "additive": 0.3, "cosmetic": 0.0}
DIRECTNESS = {1: 1.0, 2: 0.5}


def _directness(hops) -> float:
    if isinstance(hops, str):
        key = hops.strip().lower().replace("-", "").replace(" ", "")
        table = {"1hop": 1.0, "2hop": 0.5, "3hop": 0.25, "3plushop": 0.25}
        if key not in table:
            raise ValueError("unknown directness: %r" % hops)
        return table[key]
    if hops == 1:
        return 1.0
    if hops == 2:
        return 0.5
    if isinstance(hops, int) and hops >= 3:
        return 0.25
    raise ValueError("unknown directness: %r" % (hops,))


def _yes_no(value, name: str) -> float:
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    key = str(value).strip().lower()
    if key in ("yes", "true", "1"):
        return 1.0
    if key in ("no", "false", "0"):
        return 0.0
    raise ValueError("unknown %s flag: %r" % (name, value))


def score(criticality: str = "low", breakage: str = "cosmetic", directness=3,
          assumption=False, constraint=False, conflicting=False) -> dict:
    """Score one agent. Symbolic inputs per §7 scales; returns {score, factors}."""
    try:
        factors = {"criticality": CRITICALITY[criticality.strip().lower()],
                   "breakage": BREAKAGE[breakage.strip().lower()],
                   "directness": _directness(directness),
                   "assumption": _yes_no(assumption, "assumption"),
                   "constraint": _yes_no(constraint, "constraint"),
                   "conflicting": _yes_no(conflicting, "conflicting")}
    except KeyError as exc:
        raise ValueError("unknown factor value: %s" % exc) from exc
    total = round(math.fsum(WEIGHTS[k] * factors[k] for k in WEIGHTS), 9)
    return {"score": total, "factors": factors, "weights": dict(WEIGHTS)}


def verdict(has_diff: bool, **factors) -> dict:
    """Agent severity: no diffs → exactly 0.0 (never scored); else score()."""
    if not has_diff:
        return {"score": 0.0, "factors": {}, "weights": dict(WEIGHTS), "rule": "empty-diff"}
    result = score(**factors)
    result["rule"] = "factor-sum"
    return result
