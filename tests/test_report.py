"""Report tests: JSON+Markdown generation on the real order store."""
import json
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent

pyoxigraph = pytest.importorskip("pyoxigraph")

REQUIRED_KEYS = {
    "repository", "component", "source_files_analyzed", "facts_extracted",
    "direct_facts", "inferred_facts", "graph_triples", "services_discovered",
    "service_names", "entities_discovered", "eca_rules_discovered",
    "input_links", "output_links", "unresolved_total", "source_files",
}


@pytest.fixture(scope="module")
def reports(tmp_path_factory):
    work = tmp_path_factory.mktemp("report")
    fx = work / "fx"
    repo = PROJECT_ROOT / "dataset" / "apache-ofbiz-24.09.07"
    assert repo.is_dir(), "OFBiz dataset missing"
    subprocess.run(
        [sys.executable, "extract.py", "--root", str(repo), "--component", "order", "--out", str(fx)],
        cwd=PROJECT_ROOT, check=True,
    )
    subprocess.run(
        [sys.executable, "build_graph.py", "--facts", str(fx / "order-facts.jsonl"),
         "--manifest", str(fx / "order-manifest.json"), "--out", str(work / "g.ttl"),
         "--as-of", "2026-01-01T00:00:00+00:00"],
        cwd=PROJECT_ROOT, check=True,
    )
    subprocess.run(
        [sys.executable, "store_graph.py", "load", "--graph", str(work / "g.ttl"),
         "--store", str(work / "oxi")],
        cwd=PROJECT_ROOT, check=True,
    )
    out_json, out_md = work / "report.json", work / "report.md"
    subprocess.run(
        [sys.executable, "report_graph.py", "--store", str(work / "oxi"),
         "--manifest", str(fx / "order-manifest.json"), "--facts", str(fx / "order-facts.jsonl"),
         "--unresolved", str(fx / "order-unresolved.json"),
         "--out-json", str(out_json), "--out-md", str(out_md)],
        cwd=PROJECT_ROOT, check=True,
    )
    return json.loads(out_json.read_text(encoding="utf-8")), out_md.read_text(encoding="utf-8")


def test_report_sections_and_counts(reports):
    report, _md = reports
    assert REQUIRED_KEYS <= set(report)
    assert report["repository"] == "apache-ofbiz-24.09.07"
    assert report["component"] == "order"
    assert report["services_discovered"] == 467
    assert report["entities_discovered"] == 53
    assert report["eca_rules_discovered"] == 111
    assert report["source_files_analyzed"] == 17
    assert report["facts_extracted"] == report["direct_facts"] + report["inferred_facts"]
    assert report["direct_facts"] > 3000 and report["inferred_facts"] > 100
    assert "storeOrder" in report["service_names"]


def test_markdown_covers_all_sections_and_separates_evidence(reports):
    _report, md = reports
    for section in ["Repository overview", "Components discovered", "Entities discovered",
                    "Services discovered", "implementations", "inputs/outputs",
                    "Entity relationships", "ECA rules", "Service-to-entity",
                    "dependencies", "Provenance", "statistics"]:
        assert section in md
    assert "DIRECTLY EXTRACTED" in md and "INFERRED" in md
    assert "Services: 467" in md or "Total: 467" in md
    assert "understand" not in md.lower()


def test_report_honesty_bounds(reports):
    report, _md = reports
    # In-scope implementation bindings only; entity-auto services have none.
    assert report["services_with_implementation"] + report["services_without_implementation"] == 467
    # Out-of-scope entity references reported, not graphed as entities.
    assert report["unresolved_total"] > 400
