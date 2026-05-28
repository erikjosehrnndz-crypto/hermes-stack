"""MCP tools — Phase 1: brain_capture, brain_search.

Las tools delegan en los mismos componentes (vault, events, queue) que la
API REST. Una sola implementación, dos transportes.
"""
from __future__ import annotations

from typing import Literal


def register_tools(mcp, state) -> None:
    """`state` es el `app.state` de FastAPI (vault, events, queue, settings)."""

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
            job_timeout=60,
            result_ttl=300,
        )
        return {
            "id": node_id,
            "status": "queued",
            "path": str(path.relative_to(state.vault.root)),
            "job_id": job.id,
        }

    @mcp.tool
    def brain_search(q: str, k: int = 5) -> dict:
        """Búsqueda Phase 1: filename + body substring sobre el vault.

        Phase 2 reemplaza con BM25 + dense embeddings + RRF + rerank.
        """
        hits = state.vault.search_by_name(q, k=k)
        return {"q": q, "k": k, "hits": hits, "n": len(hits), "mode": "keyword-stub"}
