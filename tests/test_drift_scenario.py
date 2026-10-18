"""Task 4.9 tests: canonical 3-agent scenario (PART4_PLAN Task 4.9, §7.3).

A: diff found, direct impact, 0.725 → RE-PLAN. B: no diff → CONTINUE.
C: dangling reference, 0.82 → RE-PLAN. Report sentence is exact. Offline.
"""

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

rdflib = pytest.importorskip("rdflib")

from contextgraph.drift.drift_pipeline import run  # noqa: E402
from contextgraph.drift.versioning import create_version, load_version  # noqa: E402

FIX = PROJECT_ROOT / "tests" / "fixtures" / "drift"
CTX = "http://context.example.org/"
VERSION = "urn:version_n1"

LABELS = {"A": {"criticality": "normal", "constraint": False, "conflicting": False},
          "C": {"criticality": "high", "constraint": True, "conflicting": True}}


def _load(name):
    graph = rdflib.Graph()
    graph.parse(str(FIX / name), format="turtle")
    return graph


@pytest.fixture(scope="module")
def scenario(tmp_path_factory):
    store = tmp_path_factory.mktemp("versions")
    create_version(store, "n", set(_load("vn.ttl")), set(), "c0" * 10, "urn:version_n")
    create_version(store, "n1", set(_load("reextraction.ttl")),
                   {CTX + "findOrders", CTX + "findOrders-statusId"},
                   "c1" * 10, VERSION, prev_id="n")
    version = load_version(store, "n1")
    snapshots = {"A": _load("snap_a.ttl"), "B": _load("snap_b.ttl"), "C": _load("snap_c.ttl")}
    return run(version, VERSION, snapshots, LABELS)


def test_agent_a_replan(scenario):
    agent = scenario["agents"]["A"]
    assert agent["diff"]["removals"], "expected findOrders removals"
    assert agent["severity"]["score"] == 0.725
    assert agent["severity_inputs"]["derived"] == {"breakage": "signature", "directness": 1, "assumption": True}
    assert agent["remediation"] == "RE-PLAN"
    assert agent["patch"]["agent"] == "A" and agent["patch"]["remediation"]["action"] == "RE-PLAN"
    assert agent["impact"], "expected blast-radius impact"


def test_agent_b_continues_undisturbed(scenario):
    agent = scenario["agents"]["B"]
    assert agent["diff"] == {"additions": [], "removals": [], "modifications": []}
    assert agent["severity"]["score"] == 0.0
    assert agent["remediation"] == "CONTINUE"
    assert agent["patch"] is None


def test_agent_c_replan(scenario):
    agent = scenario["agents"]["C"]
    assert (CTX + "etl_task", CTX + "invokesService", CTX + "findOrders") in agent["diff"]["removals"]
    assert agent["severity_inputs"]["derived"] == {"breakage": "signature", "directness": 3, "assumption": True}
    assert agent["severity"]["score"] == 0.82
    assert agent["remediation"] == "RE-PLAN"
    assert agent["patch"] is not None


def test_report_sentence(scenario):
    assert scenario["report"] == "Agent B continues undisturbed; A and C receive context patches."
