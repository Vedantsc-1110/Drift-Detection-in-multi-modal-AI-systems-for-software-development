"""Task 4.6 tests: impact traversal (PART4_PLAN Task 4.6, §7.3 Step 5).

From the changed findOrders symbol the invoking Airflow task is reached at
distance 1 via invokedBy; a synthetic chain proves multi-hop paths, hop
counts, and off-path exclusion. No network.
"""

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

rdflib = pytest.importorskip("rdflib")

from contextgraph.drift.traversal import traverse  # noqa: E402

FIX = PROJECT_ROOT / "tests" / "fixtures" / "drift"
CTX = "http://context.example.org/"
FIND_ORDERS = CTX + "findOrders"
ETL_TASK = CTX + "etl_task"


def _load(name):
    graph = rdflib.Graph()
    graph.parse(str(FIX / name), format="turtle")
    return graph


def test_reaches_invoking_task_at_distance_one():
    reached = traverse(_load("vn.ttl"), [FIND_ORDERS])
    assert reached[ETL_TASK]["distance"] == 1
    assert reached[ETL_TASK]["via"] == ["invokedBy"]
    assert reached[FIND_ORDERS] == {"distance": 0, "via": []}


def test_multihop_chain_and_distances():
    data = ("PREFIX ctx: <http://context.example.org/> "
            "ctx:M1 ctx:calls ctx:M2 . ctx:M2 ctx:calls ctx:M3 . "
            "ctx:Svc ctx:implementedBy ctx:M2 . ctx:Pol ctx:constrains ctx:Svc . "
            "ctx:M1 ctx:comment \"ignored literal hop\" . "
            "ctx:M1 ctx:relatesTo ctx:Other .")
    graph = rdflib.Graph()
    graph.parse(data=data, format="turtle")
    reached = traverse(graph, [CTX + "M1"])
    assert reached[CTX + "M2"] == {"distance": 1, "via": ["calls"]}
    assert reached[CTX + "M3"] == {"distance": 2, "via": ["calls", "calls"]}
    assert reached[CTX + "Svc"] == {"distance": 2, "via": ["calls", "implementedByOf"]}
    assert reached[CTX + "Pol"] == {"distance": 3, "via": ["calls", "implementedByOf", "constrainedBy"]}
    # Off-path predicates never traversed; literals never entities.
    assert CTX + "Other" not in reached
    assert not [uri for uri in reached if uri.startswith('"')]


def test_max_hops_bounds():
    graph = _load("vn.ttl")
    assert traverse(graph, [FIND_ORDERS], max_hops=0) == {FIND_ORDERS: {"distance": 0, "via": []}}
