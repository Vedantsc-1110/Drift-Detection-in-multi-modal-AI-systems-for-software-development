"""Immutable context versions + SQLite manifest (§7.3 Step 3, PART4 Task 4.4).

Versioning discipline: V(n+1) is a NEW Turtle file; unchanged triples copy
from V(n); triples touching removed subjects (as subject OR object, so
dangling edges cannot survive a rename) drop; V(n) files are never mutated
(write-once guard). The SQLite manifest records {version_id, graph_uri,
file, commit_sha, created_at, triples}. Time travel = parse the version
file back. No network access.
"""

from __future__ import annotations

import datetime
import sqlite3
from pathlib import Path

import rdflib

SCHEMA = """CREATE TABLE IF NOT EXISTS versions (
  version_id TEXT PRIMARY KEY,
  graph_uri TEXT NOT NULL,
  file TEXT NOT NULL,
  commit_sha TEXT NOT NULL,
  created_at TEXT NOT NULL,
  triples INTEGER NOT NULL
)"""


def _connect(manifest_path: Path) -> sqlite3.Connection:
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(manifest_path)
    connection.execute(SCHEMA)
    return connection


def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def create_version(store_dir, version_id: str, new_triples, removed: set,
                   commit_sha: str, graph_uri: str, prev_id: str | None = None,
                   created_at: str = "") -> dict:
    """Write V(version_id). new_triples: iterable of (s, p, o) rdflib terms.

    removed: subject URIs (strings) dropped as subject or object.
    Returns the manifest row dict.
    """
    store_dir = Path(store_dir)
    store_dir.mkdir(parents=True, exist_ok=True)
    path = store_dir / ("version_%s.ttl" % version_id)
    if path.exists():
        raise ValueError("version %s already exists: versions are immutable" % version_id)
    removed = set(removed)
    merged = rdflib.Graph()
    new_pairs = {(str(s), str(p)) for s, p, _ in new_triples}
    if prev_id is not None:
        previous = load_version(store_dir, prev_id)
        for triple in previous:
            if str(triple[0]) not in removed and str(triple[2]) not in removed:
                # Overlay: a re-stated subject+predicate wins over the carried
                # value (e.g. refreshed file hash), so stale values cannot
                # linger alongside new ones.
                if (str(triple[0]), str(triple[1])) not in new_pairs:
                    merged.add(triple)
    for triple in new_triples:
        merged.add(triple)
    path.write_text(merged.serialize(format="turtle"), encoding="utf-8")
    row = {"version_id": version_id, "graph_uri": graph_uri, "file": path.name,
           "commit_sha": commit_sha, "created_at": created_at or _now(),
           "triples": len(merged)}
    with _connect(store_dir / "manifest.sqlite") as connection:
        connection.execute(
            "INSERT INTO versions VALUES (:version_id, :graph_uri, :file, :commit_sha, :created_at, :triples)", row)
        connection.commit()
    return row


def load_version(store_dir, version_id: str) -> rdflib.Graph:
    """Time travel: parse a version file back (read-only)."""
    path = Path(store_dir) / ("version_%s.ttl" % version_id)
    graph = rdflib.Graph()
    graph.parse(str(path), format="turtle")
    return graph


def manifest_rows(store_dir) -> list:
    """Manifest rows sorted by version_id (oldest first by construction)."""
    with _connect(Path(store_dir) / "manifest.sqlite") as connection:
        rows = connection.execute(
            "SELECT version_id, graph_uri, file, commit_sha, created_at, triples FROM versions ORDER BY rowid").fetchall()
    return [{"version_id": r[0], "graph_uri": r[1], "file": r[2],
             "commit_sha": r[3], "created_at": r[4], "triples": r[5]} for r in rows]
