"""Task 4.4 tests: immutable versioning + manifest (PART4_PLAN Task 4.4, Step 3).

V(n) triple count unchanged; V(n+1) carries the rename (searchOrders in,
findOrders out, partyId in); manifest rows correct; time travel serves V(n).
SQLite + files in tmp_path. No network.
"""

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

rdflib = pytest.importorskip("rdflib")

from contextgraph.drift.versioning import (  # noqa: E402
    create_version,
    load_version,
    manifest_rows,
)

FIX = PROJECT_ROOT / "tests" / "fixtures" / "drift"
CTX = "http://context.example.org/"
FIND_ORDERS = CTX + "findOrders"
SEARCH_ORDERS = CTX + "searchOrders"


def _triples(name):
    graph = rdflib.Graph()
    graph.parse(str(FIX / name), format="turtle")
    return set(graph)


def test_version_chain_with_rename(tmp_path):
    vn = _triples("vn.ttl")
    vn_count = len(vn)
    row0 = create_version(tmp_path, "n", vn, set(), "c0" * 10, "urn:version_n",
                          created_at="2026-01-01T00:00:00+00:00")
    assert row0["triples"] == vn_count
    vn_bytes = (tmp_path / "version_n.ttl").read_bytes()

    reextracted = _triples("reextraction.ttl")
    removed = {FIND_ORDERS, CTX + "findOrders-statusId"}
    row1 = create_version(tmp_path, "n1", reextracted, removed, "c1" * 10, "urn:version_n1",
                          prev_id="n", created_at="2026-01-02T00:00:00+00:00")
    # V(n) file untouched.
    assert (tmp_path / "version_n.ttl").read_bytes() == vn_bytes
    assert len(load_version(tmp_path, "n")) == vn_count
    v1 = load_version(tmp_path, "n1")
    subjects = {str(s) for s, _, _ in v1}
    assert SEARCH_ORDERS in subjects and FIND_ORDERS not in subjects
    assert any(str(o).endswith("partyId") for _, _, o in v1) or \
        any("partyId" in str(s) for s, _, _ in v1)
    # Dangling edge to the renamed subject is gone (object-side removal).
    assert (rdflib.URIRef(CTX + "etl_task"),
            rdflib.URIRef(CTX + "invokesService"),
            rdflib.URIRef(FIND_ORDERS)) not in v1
    assert row1["triples"] == len(v1) > 0


def test_manifest_rows_and_time_travel(tmp_path):
    create_version(tmp_path, "n", _triples("vn.ttl"), set(), "abc123", "urn:version_n")
    create_version(tmp_path, "n1", _triples("reextraction.ttl"), {FIND_ORDERS},
                   "def456", "urn:version_n1", prev_id="n")
    rows = manifest_rows(tmp_path)
    assert [r["version_id"] for r in rows] == ["n", "n1"]
    assert [r["graph_uri"] for r in rows] == ["urn:version_n", "urn:version_n1"]
    assert [r["commit_sha"] for r in rows] == ["abc123", "def456"]
    assert all(r["triples"] > 0 and r["created_at"] for r in rows)
    old = load_version(tmp_path, "n")
    assert (rdflib.URIRef(FIND_ORDERS), rdflib.RDF.type, rdflib.URIRef(CTX + "Service")) in old


def test_versions_are_write_once(tmp_path):
    create_version(tmp_path, "n", _triples("vn.ttl"), set(), "abc123", "urn:version_n")
    with pytest.raises(ValueError):
        create_version(tmp_path, "n", _triples("vn.ttl"), set(), "abc123", "urn:version_n")
