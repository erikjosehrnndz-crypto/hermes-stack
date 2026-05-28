"""GraphStore — Phase 3b: grafo de menciones [[wikilink]] entre nodos.

Implementación: SQLite con WAL mode.
Permite acceso multi-proceso: worker escribe, API lee concurrentemente.

Tablas:
  nodes(node_id TEXT PK, node_type TEXT, title TEXT)
  edges(from_id TEXT, to_id TEXT, weight REAL, PK(from_id, to_id))

Path: /data/graph/brain.db  (archivo único)
"""
from __future__ import annotations

import sqlite3
import threading
from pathlib import Path

_LOCK = threading.Lock()

_DDL = """
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;

CREATE TABLE IF NOT EXISTS nodes (
    node_id   TEXT PRIMARY KEY,
    node_type TEXT NOT NULL DEFAULT 'knowledge',
    title     TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS edges (
    from_id TEXT NOT NULL,
    to_id   TEXT NOT NULL,
    weight  REAL NOT NULL DEFAULT 1.0,
    PRIMARY KEY (from_id, to_id)
);

CREATE INDEX IF NOT EXISTS idx_edges_from ON edges(from_id);
CREATE INDEX IF NOT EXISTS idx_edges_to   ON edges(to_id);
"""


class KuzuGraph:
    """Grafo de menciones. Nombre KuzuGraph mantenido por compatibilidad con main.py/worker."""

    def __init__(self, db_path: str | Path):
        self._path = Path(db_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self._path), timeout=30, check_same_thread=False)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        with _LOCK:
            conn = self._conn()
            conn.executescript(_DDL)
            conn.commit()
            conn.close()

    # ----- Mutaciones ---------------------------------------------------

    def upsert_node(self, node_id: str, node_type: str, title: str) -> None:
        with _LOCK:
            conn = self._conn()
            conn.execute(
                "INSERT INTO nodes(node_id, node_type, title) VALUES(?,?,?)"
                " ON CONFLICT(node_id) DO UPDATE SET node_type=excluded.node_type, title=excluded.title",
                (node_id, node_type or "knowledge", title or ""),
            )
            conn.commit()
            conn.close()

    def delete_node(self, node_id: str) -> None:
        with _LOCK:
            conn = self._conn()
            conn.execute("DELETE FROM edges WHERE from_id=? OR to_id=?", (node_id, node_id))
            conn.execute("DELETE FROM nodes WHERE node_id=?", (node_id,))
            conn.commit()
            conn.close()

    def upsert_mention(self, from_id: str, to_id: str, *, weight: float = 1.0) -> None:
        with _LOCK:
            conn = self._conn()
            conn.execute(
                "INSERT INTO edges(from_id, to_id, weight) VALUES(?,?,?)"
                " ON CONFLICT(from_id, to_id) DO UPDATE SET weight=excluded.weight",
                (from_id, to_id, float(weight)),
            )
            conn.commit()
            conn.close()

    # ----- Consultas ----------------------------------------------------

    def expand_1hop(self, node_ids: list[str]) -> list[tuple[str, float]]:
        """Retorna (neighbor_node_id, weight) para vecinos 1-hop (salientes + entrantes)."""
        if not node_ids:
            return []
        placeholders = ",".join("?" * len(node_ids))
        results: list[tuple[str, float]] = []
        conn = self._conn()
        try:
            # Salientes: nodos que los hits mencionan
            cur = conn.execute(
                f"SELECT to_id, weight FROM edges WHERE from_id IN ({placeholders})",
                node_ids,
            )
            for row in cur.fetchall():
                results.append((str(row[0]), float(row[1])))
            # Entrantes: nodos que mencionan los hits (peso × 0.5)
            cur = conn.execute(
                f"SELECT from_id, weight * 0.5 FROM edges WHERE to_id IN ({placeholders})",
                node_ids,
            )
            for row in cur.fetchall():
                results.append((str(row[0]), float(row[1])))
        finally:
            conn.close()
        return results

    # ----- Utilidades ---------------------------------------------------

    def count_nodes(self) -> int:
        try:
            conn = self._conn()
            row = conn.execute("SELECT count(*) FROM nodes").fetchone()
            conn.close()
            return int(row[0]) if row else 0
        except Exception:
            return 0

    def count_edges(self) -> int:
        try:
            conn = self._conn()
            row = conn.execute("SELECT count(*) FROM edges").fetchone()
            conn.close()
            return int(row[0]) if row else 0
        except Exception:
            return 0
