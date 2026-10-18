"""Task 4.8 tests: remediation + patch + event log (PART4_PLAN Task 4.8, Steps 7–9).

Canonical scores map to RE-PLAN/CONTINUE; every boundary probed exactly;
patch carries the four documented sections; the log appends and never
deletes. No network.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from contextgraph.drift.event_log import EventLog  # noqa: E402
from contextgraph.drift.patch import build_patch  # noqa: E402
from contextgraph.drift.remediation import remediate  # noqa: E402


def test_canonical_scores():
    assert remediate(0.725) == "RE-PLAN"
    assert remediate(0.0) == "CONTINUE"
    assert remediate(0.82) == "RE-PLAN"


def test_boundaries_exact():
    assert remediate(0.3499) == "REFRESH"
    assert remediate(0.35) == "RE-BRIEF"
    assert remediate(0.5999) == "RE-BRIEF"
    assert remediate(0.60) == "RE-PLAN"
    assert remediate(0.8499) == "RE-PLAN"
    assert remediate(0.85) == "ROLLBACK"
    assert remediate(0.0001) == "REFRESH"
    assert remediate(1.0) == "ROLLBACK"


def test_patch_has_four_sections():
    diff = {"additions": [("s", "p", "new")], "removals": [("s", "p", "old")],
            "modifications": [("x", "label", "b", "a")]}
    patch = build_patch("A", diff, {"score": 0.725}, "RE-PLAN", [("s", "p", "new")])
    assert patch["agent"] == "A"
    assert patch["diff_summary"] == diff
    assert patch["invalidated_assumptions"] == [
        "assumed present, now changed: s p old",
        "assumed present, now changed: x label b"]
    assert patch["remediation"] == {"action": "RE-PLAN", "severity": 0.725,
                                    "evidence": ["new", "old"]}
    assert patch["snapshot"] == {"agent": "A", "triples": [("s", "p", "new")]}


def test_event_log_appends_never_deletes(tmp_path):
    log = EventLog(tmp_path / "events.sqlite")
    assert not hasattr(log, "delete") and not hasattr(log, "update") and not hasattr(log, "clear")
    first = log.log_event("c0" * 10, ["services.xml"], "n1", "A", 0.725, "RE-PLAN",
                          timestamp="2026-01-02T00:00:00+00:00")
    second = log.log_event("c0" * 10, ["services.xml"], "n1", "C", 0.82, "RE-PLAN",
                           timestamp="2026-01-02T00:00:00+00:00")
    assert (first, second) == (1, 2)
    rows = log.rows()
    assert [r["agent"] for r in rows] == ["A", "C"]
    assert rows[0]["files"] == ["services.xml"] and rows[0]["severity"] == 0.725
    assert rows[0]["timestamp"] == "2026-01-02T00:00:00+00:00"
    assert EventLog(tmp_path / "events.sqlite").rows() == rows
