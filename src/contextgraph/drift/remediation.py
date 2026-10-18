"""Remediation levels (§7.3 Step 7, PART4 Task 4.8).

EXACT CONTRACT.md §7 thresholds — do not tune:
  score = 0.0         -> CONTINUE
  0.0 < score < 0.35  -> REFRESH
  0.35 <= score < 0.60 -> RE-BRIEF
  0.60 <= score < 0.85 -> RE-PLAN
  score >= 0.85       -> ROLLBACK
"""

from __future__ import annotations

CONTINUE, REFRESH, RE_BRIEF, RE_PLAN, ROLLBACK = (
    "CONTINUE", "REFRESH", "RE-BRIEF", "RE-PLAN", "ROLLBACK")


def remediate(score: float) -> str:
    """Map a severity score to its remediation action (exact boundaries)."""
    score = float(score)
    if score == 0.0:
        return CONTINUE
    if 0.0 < score < 0.35:
        return REFRESH
    if 0.35 <= score < 0.60:
        return RE_BRIEF
    if 0.60 <= score < 0.85:
        return RE_PLAN
    return ROLLBACK
