"""Task 4.11 tests: Part 4 CONTRACT.md §7 compliance handoff.

Version/agent-snapshot URI schemes, the §7.3 diff query shape, exact
weights/scales/thresholds, and the canonical scenario values match §7.
No network.
"""

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

rdflib = pytest.importorskip("rdflib")

from contextgraph.drift import drift_pipeline, severity, sparql_diff  # noqa: E402
from contextgraph.drift.remediation import remediate  # noqa: E402
from contextgraph.drift.severity import BREAKAGE, CRITICALITY, WEIGHTS  # noqa: E402
from contextgraph.drift.versioning import create_version, load_version  # noqa: E402

FIX = PROJECT_ROOT / "tests" / "fixtures" / "drift"
CTX = "http://context.example.org/"
VERSION = "urn:version_n1"


def test_uri_schemes():
    import inspect

    params = inspect.signature(drift_pipeline.run).parameters
    assert params["snapshot_id_prefix"].default == "urn:agent_snapshot"
    assert VERSION.startswith("urn:version_")


def test_diff_query_shape_matches_section_73():
    assert "GRAPH <%(version)s>" in sparql_diff.ADDITIONS_QUERY
    assert "GRAPH <%(snapshot)s>" in sparql_diff.ADDITIONS_QUERY
    assert "MINUS" in sparql_diff.ADDITIONS_QUERY and "MINUS" in sparql_diff.REMOVALS_QUERY
    assert "FILTER(?newObject != ?oldObject)" in sparql_diff.MODIFICATIONS_QUERY


def test_weights_and_scales_match_section_7():
    assert WEIGHTS == {"criticality": 0.15, "breakage": 0.35, "directness": 0.20,
                       "assumption": 0.10, "constraint": 0.10, "conflicting": 0.10}
    assert CRITICALITY == {"critical": 1.0, "high": 0.8, "normal": 0.5, "low": 0.2}
    assert BREAKAGE == {"signature": 1.0, "additive": 0.3, "cosmetic": 0.0}
    assert severity.score(criticality="normal", breakage="signature", directness=1,
                          assumption=True)["score"] == 0.725


def test_thresholds_match_section_7():
    assert {s: remediate(s) for s in (0.0, 0.3499, 0.35, 0.5999, 0.6, 0.8499, 0.85)} == \
        {0.0: "CONTINUE", 0.3499: "REFRESH", 0.35: "RE-BRIEF", 0.5999: "RE-BRIEF",
         0.6: "RE-PLAN", 0.8499: "RE-PLAN", 0.85: "ROLLBACK"}


def _load(name):
    graph = rdflib.Graph()
    graph.parse(str(FIX / name), format="turtle")
    return graph


def test_canonical_scenario_values_match_section_7(tmp_path):
    create_version(tmp_path, "n", set(_load("vn.ttl")), set(), "c0" * 10, "urn:version_n")
    create_version(tmp_path, "n1", set(_load("reextraction.ttl")),
                   {CTX + "findOrders", CTX + "findOrders-statusId"},
                   "c1" * 10, VERSION, prev_id="n")
    version = load_version(tmp_path, "n1")
    snapshots = {"A": _load("snap_a.ttl"), "B": _load("snap_b.ttl"), "C": _load("snap_c.ttl")}
    labels = {"A": {"criticality": "normal", "constraint": False, "conflicting": False},
              "C": {"criticality": "high", "constraint": True, "conflicting": True}}
    result = drift_pipeline.run(version, VERSION, snapshots, labels)
    assert (result["agents"]["A"]["severity"]["score"], result["agents"]["A"]["remediation"]) == (0.725, "RE-PLAN")
    assert (result["agents"]["B"]["severity"]["score"], result["agents"]["B"]["remediation"]) == (0.0, "CONTINUE")
    assert (result["agents"]["C"]["severity"]["score"], result["agents"]["C"]["remediation"]) == (0.82, "RE-PLAN")
