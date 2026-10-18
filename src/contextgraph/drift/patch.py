"""Context patches (§7.3 Step 8, PART4 Task 4.8).

Per affected agent: diff summary with specific triples, invalidated
assumptions, recommended remediation with evidence, and the new context
snapshot. Pure data assembly — deterministic, no I/O.
"""

from __future__ import annotations


def build_patch(agent: str, diff: dict, severity: dict, remediation: str,
                snapshot_triples: list) -> dict:
    """Assemble the four documented patch sections."""
    invalidated = []
    for triple in diff.get("removals", []) + [m[:3] for m in diff.get("modifications", [])]:
        invalidated.append("assumed present, now changed: %s %s %s" % tuple(triple))
    evidence = sorted({triple[2] for triple in diff.get("additions", [])}
                      | {triple[2] for triple in diff.get("removals", [])})
    return {
        "agent": agent,
        "diff_summary": {kind: list(diff.get(kind, [])) for kind in ("additions", "removals", "modifications")},
        "invalidated_assumptions": sorted(invalidated),
        "remediation": {"action": remediation, "severity": severity.get("score"),
                        "evidence": evidence},
        "snapshot": {"agent": agent, "triples": sorted(snapshot_triples)},
    }
