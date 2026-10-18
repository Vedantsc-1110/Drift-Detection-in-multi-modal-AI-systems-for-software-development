"""Drift-detection package (PART4_PLAN, proposal Part 2 §7.3, Algorithm 3).

EXACT CONTRACT.md §7 constants live in severity.py / remediation.py and are
tested verbatim in test_drift_severity.py / test_drift_remediation.py — do
not tune them. SQLite manifests/logs, GitPython change detection, and the
re-extraction hook (external command, never an import) round out the stack.
"""
