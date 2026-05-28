"""MCP tools — Phase 2: brain_capture, brain_search (hybrid por defecto).

Las tools delegan en los mismos componentes (vault, lance, events, queue) que la
API REST. Una sola implementación, dos transportes.
"""
from __future__ import annotations

from typing import Literal


def register_tools(mcp, state) -> None:
    """`state` es el `app.state` de FastAPI (vault, lance, events, queue, settings)."""

    @mcp.tool
    def brain_capture(
        text: str,
        type: Literal["journal", "knowledge", "memory", "source"] = "knowledge",
        tags: list[str] | None = None,
        title: str | None = None,
        source: str = "mcp",
    ) -> dict:
        """Captura una nota en el vault y encola el procesado.

        Devuelve el id del nodo creado y la ruta relativa en el vault.
        """
        node_id, path = state.vault.write_node(
            node_type=type,
            user_id=state.settings.user_id,
            body=text,
            tags=tags or [],
            source=source,
            title=title,
        )
        state.events.append(
            event_type="ingest",
            user_id=state.settings.user_id,
            source=source,
            node_id=node_id,
            payload={
                "type": type,
                "tags": tags or [],
                "title": title,
                "len": len(text),
                "via": "mcp",
            },
        )
        job = state.queue.enqueue(
            "brain.workers.jobs.process_node.process_node",
            node_id,
            job_timeout=300,
            result_ttl=600,
        )
        return {
            "id": node_id,
            "status": "queued",
            "path": str(path.relative_to(state.vault.root)),
            "job_id": job.id,
        }

    @mcp.tool
    def brain_search(
        q: str,
        k: int = 5,
        mode: Literal["hybrid", "dense", "bm25", "keyword"] = "hybrid",
    ) -> dict:
        """Búsqueda Phase 2: hybrid RRF (dense BGE-M3 + BM25) sobre LanceDB.

        Modos:
          - hybrid (default): RRF de dense + BM25.
          - dense:  solo BGE-M3 (cosine sim).
          - bm25:   solo lexical (tantivy FTS).
          - keyword: fallback Phase 1 sobre nombres de archivo del vault.
        """
        lance = getattr(state, "lance", None)
        if mode == "keyword" or lance is None:
            hits = state.vault.search_by_name(q, k=k)
            return {"q": q, "k": k, "mode": "keyword", "n": len(hits), "hits": hits}

        user_id = state.settings.user_id
        if mode == "bm25":
            hits = lance.search_bm25(q, k=k, user_id=user_id)
            return {"q": q, "k": k, "mode": "bm25", "n": len(hits), "hits": hits}

        # dense / hybrid requieren embedding de la query
        from brain.pipeline.embed import embed_query

        qvec = embed_query(q, model_name=state.settings.embed_model)
        if mode == "dense":
            hits = lance.search_dense(qvec, k=k, user_id=user_id)
            return {"q": q, "k": k, "mode": "dense", "n": len(hits), "hits": hits}

        hits = lance.search_hybrid(q, qvec, k=k, user_id=user_id)
        return {"q": q, "k": k, "mode": "hybrid", "n": len(hits), "hits": hits}
