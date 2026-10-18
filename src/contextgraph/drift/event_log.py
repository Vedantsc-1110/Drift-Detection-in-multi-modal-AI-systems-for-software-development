"""Append-only SQLite event log (§7.3 Step 9, PART4 Task 4.8).

Rows: change event details (commit SHA, file paths, timestamp), new version
ID, affected agents with severity scores and remediation actions. The class
exposes NO delete or update path — append-only by construction. No network.
"""

from __future__ import annotations

import datetime
import json
import sqlite3
from pathlib import Path

SCHEMA = """CREATE TABLE IF NOT EXISTS events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  commit_sha TEXT NOT NULL,
  files TEXT NOT NULL,
  timestamp TEXT NOT NULL,
  version_id TEXT NOT NULL,
  agent TEXT NOT NULL,
  severity REAL NOT NULL,
  remediation TEXT NOT NULL
)"""


class EventLog:
    """Append-only log. Reader: rows(). No writers besides log_event()."""

    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.path) as connection:
            connection.execute(SCHEMA)
            connection.commit()

    def log_event(self, commit_sha: str, files: list, version_id: str,
                  agent: str, severity: float, remediation: str,
                  timestamp: str = "") -> int:
        """Append one row; return its id."""
        with sqlite3.connect(self.path) as connection:
            cursor = connection.execute(
                "INSERT INTO events (commit_sha, files, timestamp, version_id,"
                " agent, severity, remediation) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (commit_sha, json.dumps(sorted(files)),
                 timestamp or datetime.datetime.now(datetime.timezone.utc).isoformat(),
                 version_id, agent, float(severity), remediation))
            connection.commit()
            return int(cursor.lastrowid)

    def rows(self) -> list:
        """All rows in append order."""
        with sqlite3.connect(self.path) as connection:
            data = connection.execute(
                "SELECT id, commit_sha, files, timestamp, version_id, agent,"
                " severity, remediation FROM events ORDER BY id").fetchall()
        return [{"id": r[0], "commit_sha": r[1], "files": json.loads(r[2]),
                 "timestamp": r[3], "version_id": r[4], "agent": r[5],
                 "severity": r[6], "remediation": r[7]} for r in data]
