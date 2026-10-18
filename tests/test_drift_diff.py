"""Task 4.5 tests: SPARQL cross-graph diff (PART4_PLAN Task 4.5, Step 4).

V(n+1) is built with the 4.4 versioning path; A shows the rename as
removal+addition, B is empty (undisturbed), C flags the invokesService
removal. A synthetic label change proves the modification category.
"""

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

rdflib = pytest.importorskip("rdflib")

from contextgraph.drift.sparql_diff import diff_snapshot  # noqa: E402
from contextgraph.drift.versioning import create_version, load_version  # noqa: E402

FIX = PROJECT_ROOT / "tests" / "fixtures" / "drift"
CTX = "http://context.example.org/"
VERSION = "urn:version_n1"
SNAP = "urn:agent_snapshot"


def _load(name):
    graph = rdflib.Graph()
    graph.parse(str(FIX / name), format="turtle")
    return graph


@pytest.fixture(scope="module")
def v1(tmp_path_factory):
    store = tmp_path_factory.mktemp("versions")
    vn = set(_load("vn.ttl"))
    create_version(store, "n", vn, set(), "c0" * 10, "urn:version_n")
    reextracted = set(_load("reextraction.ttl"))
    create_version(store, "n1", reextracted,
                   {CTX + "findOrders", CTX + "findOrders-statusId"},
                   "c1" * 10, VERSION, prev_id="n")
    return load_version(store, "n1")


def _subjects(triples):
    return {t[0] for t in triples}


def test_agent_a_rename_detected(v1):
    diff = diff_snapshot(v1, VERSION, _load("snap_a.ttl"), SNAP + "_A")
    # The rename surfaces as removals of the findOrders block; the new
    # searchOrders subject is outside A's tracked scope by the scoping rule.
    assert any(CTX + "findOrders" in s for s in _subjects(diff["removals"]))
    assert diff["additions"] == []
    assert (CTX + "createOrder", CTX + "sourceHash") in \
        {(s, p) for s, p, _, _ in diff["modifications"]}


def test_agent_b_empty_diff(v1):
    diff = diff_snapshot(v1, VERSION, _load("snap_b.ttl"), SNAP + "_B")
    assert diff == {"additions": [], "removals": [], "modifications": []}


def test_agent_c_edge_removal_flagged(v1):
    diff = diff_snapshot(v1, VERSION, _load("snap_c.ttl"), SNAP + "_C")
    assert (CTX + "etl_task", CTX + "invokesService", CTX + "findOrders") in diff["removals"]


def test_modification_category():
    old = rdflib.Graph()
    old.parse(data="PREFIX ctx: <http://context.example.org/> PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> ctx:X rdfs:label \"a\" .", format="turtle")
    new = rdflib.Graph()
    new.parse(data="PREFIX ctx: <http://context.example.org/> PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> ctx:X rdfs:label \"b\" .", format="turtle")
    diff = diff_snapshot(new, VERSION, old, SNAP + "_X")
    assert diff["modifications"] == [(CTX + "X", str(rdflib.RDFS.label), "b", "a")]
    assert diff["additions"] == [] and diff["removals"] == []


def test_modification_query_matches_derivation():
    """The literal documented FILTER query agrees with the fast derivation."""
    import warnings

    from contextgraph.drift.sparql_diff import MODIFICATIONS_QUERY, _dataset_s

    old = rdflib.Graph()
    old.parse(data="PREFIX ctx: <http://context.example.org/> PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> ctx:X rdfs:label \"a\" . ctx:Y rdfs:label \"same\" .", format="turtle")
    new = rdflib.Graph()
    new.parse(data="PREFIX ctx: <http://context.example.org/> PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> ctx:X rdfs:label \"b\" . ctx:Y rdfs:label \"same\" .", format="turtle")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        dataset = _dataset_s(set(new), VERSION, set(old), SNAP + "_X")
        literal = sorted(tuple(str(t) for t in row)
                         for row in dataset.query(MODIFICATIONS_QUERY % {"version": VERSION, "snapshot": SNAP + "_X"}))
    derived = diff_snapshot(new, VERSION, old, SNAP + "_X")["modifications"]
    assert literal == derived == [(CTX + "X", str(rdflib.RDFS.label), "b", "a")]
