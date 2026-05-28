"""LanceDB store — Phase 2 retrieval.

Dos tablas:

- `chunks`: granularidad de búsqueda dense + FTS (BM25 vía tantivy).
- `nodes`:  resumen por nodo (título, tags, vector del título, body_path).
            Útil para boost por título y para mostrar metadatos sin abrir el .md.

Convención: el cliente es responsable de borrar (`delete_node`) antes de
reinsertar para mantener idempotencia. Ahorra implementar upsert real
(LanceDB lo soporta pero la API cambia entre versiones).
"""
from __future__ import annotations

import math
import threading
from pathlib import Path
from typing import Iterable

import lancedb
import pyarrow as pa


_LOCK = threading.Lock()


def _chunks_schema(dim: int) -> pa.Schema:
    return pa.schema(
        [
            pa.field("chunk_id", pa.string(), nullable=False),
            pa.field("node_id", pa.string(), nullable=False),
            pa.field("user_id", pa.string(), nullable=False),
            pa.field("text", pa.string(), nullable=False),
            pa.field("vector", pa.list_(pa.float32(), dim), nullable=False),
            pa.field("tokens", pa.int32(), nullable=False),
            pa.field("position", pa.int32(), nullable=False),
            pa.field("node_type", pa.string(), nullable=False),
            pa.field("title", pa.string(), nullable=True),
            pa.field("tags", pa.list_(pa.string()), nullable=True),
            pa.field("path", pa.string(), nullable=False),
            pa.field("created_at", pa.string(), nullable=False),
        ]
    )


def _nodes_schema(dim: int) -> pa.Schema:
    return pa.schema(
        [
            pa.field("node_id", pa.string(), nullable=False),
            pa.field("user_id", pa.string(), nullable=False),
            pa.field("node_type", pa.string(), nullable=False),
            pa.field("title", pa.string(), nullable=True),
            pa.field("title_vector", pa.list_(pa.float32(), dim), nullable=False),
            pa.field("tags", pa.list_(pa.string()), nullable=True),
            pa.field("path", pa.string(), nullable=False),
            pa.field("summary", pa.string(), nullable=True),
            pa.field("n_chunks", pa.int32(), nullable=False),
            pa.field("created_at", pa.string(), nullable=False),
            pa.field("updated_at", pa.string(), nullable=False),
        ]
    )


class LanceStore:
    def __init__(self, root: str | Path, *, dim: int = 1024):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.dim = dim
        self._db = lancedb.connect(str(self.root))
        self._ensure_tables()

    def _ensure_tables(self) -> None:
        names = set(self._db.table_names())
        if "chunks" not in names:
            self._db.create_table("chunks", schema=_chunks_schema(self.dim))
        if "nodes" not in names:
            self._db.create_table("nodes", schema=_nodes_schema(self.dim))

    @property
    def chunks(self):
        return self._db.open_table("chunks")

    @property
    def nodes(self):
        return self._db.open_table("nodes")

    # ----- Mutaciones --------------------------------------------------

    def delete_node(self, node_id: str) -> None:
        # LanceDB acepta predicados SQL-like sobre columnas string.
        node_id_safe = node_id.replace("'", "''")
        with _LOCK:
            self.chunks.delete(f"node_id = '{node_id_safe}'")
            self.nodes.delete(f"node_id = '{node_id_safe}'")

    def upsert_chunks(self, rows: list[dict]) -> int:
        if not rows:
            return 0
        with _LOCK:
            self.chunks.add(rows)
        return len(rows)

    def upsert_node(self, row: dict) -> None:
        with _LOCK:
            self.nodes.add([row])

    # ----- Índices ----------------------------------------------------

    def ensure_fts_index(self) -> None:
        """Crea el índice FTS (tantivy) sobre `text`. Idempotente best-effort.

        Algunas versiones de LanceDB lanzan si el índice ya existe; capturamos.
        """
        try:
            self.chunks.create_fts_index(["text"], replace=True)
        except Exception:
            pass

    # ----- Búsqueda ---------------------------------------------------

    def _row_to_hit(self, row: dict, *, score: float, source: str) -> dict:
        return {
            "chunk_id": row.get("chunk_id"),
            "id": row.get("node_id"),
            "type": row.get("node_type", "unknown"),
            "path": row.get("path"),
            "title": row.get("title"),
            "tags": row.get("tags") or [],
            "position": row.get("position", 0),
            "snippet": (row.get("text") or "")[:240].strip(),
            "score": round(float(score), 4),
            "source": source,
        }

    def search_dense(self, query_vec, *, k: int = 10, user_id: str | None = None) -> list[dict]:
        q = self.chunks.search(query_vec).limit(k)
        if user_id:
            q = q.where(f"user_id = '{user_id}'", prefilter=True)
        rows = q.to_list()
        hits: list[dict] = []
        for r in rows:
            # LanceDB devuelve `_distance` (menor = mejor). Convertimos a similitud cosine.
            dist = float(r.get("_distance", 0.0))
            sim = max(0.0, 1.0 - dist / 2.0)  # cosine distance ∈ [0,2] → sim ∈ [0,1]
            hits.append(self._row_to_hit(r, score=sim, source="dense"))
        return hits

    def search_bm25(self, query: str, *, k: int = 10, user_id: str | None = None) -> list[dict]:
        try:
            q = self.chunks.search(query, query_type="fts").limit(k)
            if user_id:
                q = q.where(f"user_id = '{user_id}'", prefilter=True)
            rows = q.to_list()
        except Exception:
            return []
        hits: list[dict] = []
        for r in rows:
            raw = float(r.get("_score", r.get("score", 0.0)) or 0.0)
            # Normaliza BM25 a (0,1) con sigmoide suave; útil sólo para mostrar.
            sim = 1.0 / (1.0 + math.exp(-raw / 3.0))
            hits.append(self._row_to_hit(r, score=sim, source="bm25"))
        return hits

    def search_hybrid(
        self,
        query: str,
        query_vec,
        *,
        k: int = 10,
        rrf_k: int = 60,
        user_id: str | None = None,
        rerank: bool = False,
    ) -> list[dict]:
        """Fusión RRF de dense + BM25, con reranking opcional (Jina v2 multilingual).

        Con rerank=True: candidatos = k*3 → RRF → Jina cross-encoder → top-k.
        """
        fetch_k = max(k * 3, 20)
        dense = self.search_dense(query_vec, k=fetch_k, user_id=user_id)
        bm25 = self.search_bm25(query, k=fetch_k, user_id=user_id)

        fused: dict[str, dict] = {}

        def _add(hits: list[dict]) -> None:
            for rank, hit in enumerate(hits, start=1):
                key = hit.get("chunk_id") or f"{hit.get('id')}::{hit.get('position')}"
                contrib = 1.0 / (rrf_k + rank)
                cur = fused.get(key)
                if cur is None:
                    h = dict(hit)
                    h["rrf"] = contrib
                    h["sources"] = [hit["source"]]
                    h["component_scores"] = {hit["source"]: hit["score"]}
                    fused[key] = h
                else:
                    cur["rrf"] += contrib
                    if hit["source"] not in cur["sources"]:
                        cur["sources"].append(hit["source"])
                    cur["component_scores"][hit["source"]] = hit["score"]

        _add(dense)
        _add(bm25)

        out = list(fused.values())
        out.sort(key=lambda x: x["rrf"], reverse=True)
        for h in out:
            h.pop("rrf")
            h["score"] = round(max(h["component_scores"].values()), 4)
            h["source"] = "+".join(h.pop("sources"))

        candidates = out  # ya ordenados por RRF

        if rerank:
            from brain.pipeline.rerank import rerank as _rerank

            candidates = _rerank(query, candidates, top_k=k)
            for h in candidates:
                # Sustituir score por rerank_score para que el caller reciba un valor semánticamente coherente
                h["score"] = round(h.pop("rerank_score"), 4)
            return candidates

        return candidates[:k]

    # ----- Utilidades --------------------------------------------------

    def count_chunks(self) -> int:
        try:
            return int(self.chunks.count_rows())
        except Exception:
            return 0

    def count_nodes(self) -> int:
        try:
            return int(self.nodes.count_rows())
        except Exception:
            return 0
