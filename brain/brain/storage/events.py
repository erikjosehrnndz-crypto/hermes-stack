"""Audit log append-only en SQLite, schema simplificado tipo OverCR.

Cada mutación del vault deja huella aquí. Buscable, jamás se borra.
Phase 1 usa una sola tabla; Phase 2+ añadirá `entities`, `links`, etc.
"""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

import orjson


_SCHEMA = """
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL,
    user_id TEXT NOT NULL,
    node_id TEXT,
    event_type TEXT NOT NULL,
    source TEXT NOT NULL,
    provenance_type TEXT NOT NULL,
    provenance_rule TEXT NOT NULL,
    payload_json TEXT
);
CREATE INDEX IF NOT EXISTS idx_events_node ON events(node_id);
CREATE INDEX IF NOT EXISTS idx_events_ts ON events(ts);
CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type);
"""


class EventLog:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._conn() as c:
            c.executescript(_SCHEMA)

    @contextmanager
    def _conn(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.path, isolation_level=None)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        try:
            yield conn
        finally:
            conn.close()

    def append(
        self,
        *,
        event_type: str,
        user_id: str,
        source: str,
        provenance_type: str = "operator_direct",
        provenance_rule: str = "brain.api.v1",
        node_id: str | None = None,
        payload: dict | None = None,
    ) -> int:
        ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
        payload_json = orjson.dumps(payload or {}).decode("utf-8")
        with self._conn() as c:
            cur = c.execute(
                "INSERT INTO events (ts, user_id, node_id, event_type, source, "
                "provenance_type, provenance_rule, payload_json) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    ts,
                    user_id,
                    node_id,
                    event_type,
                    source,
                    provenance_type,
                    provenance_rule,
                    payload_json,
                ),
            )
            return cur.lastrowid or 0

    def recent(self, *, limit: int = 20, node_id: str | None = None) -> list[dict]:
        with self._conn() as c:
            if node_id:
                rows = c.execute(
                    "SELECT id, ts, user_id, node_id, event_type, source, "
                    "provenance_type, provenance_rule, payload_json "
                    "FROM events WHERE node_id = ? ORDER BY id DESC LIMIT ?",
                    (node_id, limit),
                ).fetchall()
            else:
                rows = c.execute(
                    "SELECT id, ts, user_id, node_id, event_type, source, "
                    "provenance_type, provenance_rule, payload_json "
                    "FROM events ORDER BY id DESC LIMIT ?",
                    (limit,),
                ).fetchall()
        cols = [
            "id", "ts", "user_id", "node_id", "event_type", "source",
            "provenance_type", "provenance_rule", "payload_json",
        ]
        return [dict(zip(cols, r)) for r in rows]

    def count(self) -> int:
        with self._conn() as c:
            (n,) = c.execute("SELECT COUNT(*) FROM events").fetchone()
        return int(n)
