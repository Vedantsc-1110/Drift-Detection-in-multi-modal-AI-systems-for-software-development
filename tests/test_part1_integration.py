"""Task 1.9 tests: Part 1 integration run (PART1_PLAN Task 1.9, §11.1 metrics).

Gate adaptation: the real OFBiz dataset (datasets/ofbiz/, gate marker) is
absent, so per the plan's fallback this runs end to end on the fixture tree
and records which dataset was used. Metrics: coverage > 0.95 per area vs an
independent manual inventory, wall-clock < 300s, triple counts reported
(~5000+ is a real-repo number — deviation documented in the report).
"""

import sys
import time
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

rdflib = pytest.importorskip("rdflib")

from contextgraph.contract_pipeline import (  # noqa: E402
    machine_spec,
    manual_inventory,
    run,
    write_run_report,
)

FIXTURES = PROJECT_ROOT / "tests" / "fixtures"
GENERATED_AT = "2026-01-01T00:00:00+00:00"

COUNT_KEY = {"services": "service", "entities": "entity", "methods": "java_method",
             "tasks": "airflow_task", "jobs": "cicd_job", "steps": "cicd_step"}


def _run_with_report(out_dir):
    started = time.perf_counter()
    manifest = run(FIXTURES, out_dir, GENERATED_AT)
    elapsed = time.perf_counter() - started
    rows = manual_inventory(FIXTURES)
    for row in rows:
        row["extracted"] = manifest["counts"].get(COUNT_KEY[row["area"]], 0)
        row["ratio"] = (row["extracted"] / row["expected"]) if row["expected"] else 1.0
    report = write_run_report(manifest, elapsed, rows, machine_spec())
    (out_dir / "run_report.md").write_text(report, encoding="utf-8")
    return manifest, elapsed, rows, report


def test_integration_metrics_and_report(tmp_path):
    manifest, elapsed, rows, report = _run_with_report(tmp_path)
    assert manifest["errors"] == []
    assert manifest["skipped"] == []
    assert elapsed < 300, "extraction exceeded 5 minutes: %.2fs" % elapsed
    assert rows and all(r["expected"] > 0 for r in rows)
    for row in rows:
        assert row["ratio"] > 0.95, "%s coverage %.4f" % (row["area"], row["ratio"])
    text = (tmp_path / "run_report.md").read_text(encoding="utf-8")
    assert "Wall-clock" in text and "Coverage" in text and "Machine spec" in text
    assert "fixture tree" in text
    for name in ("ofbiz_structural.ttl", "airflow.ttl", "cicd.ttl"):
        assert (tmp_path / name).is_file()
        g = rdflib.Graph()
        g.parse(str(tmp_path / name), format="turtle")
        assert len(g) == manifest["outputs"][name] > 0
