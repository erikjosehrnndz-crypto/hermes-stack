"""MCP tools — Phase 3+6: brain_capture, brain_search, brain_remember, brain_forget,
brain_ingest_url, brain_recall, brain_conversation.

Las tools delegan en los mismos componentes (vault, lance, events, queue, graph) que la
API REST. Una sola implementación, dos transportes.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Literal


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def register_tools(mcp, state) -> None:
    """`state` es el `app.state` de FastAPI (vault, lance, events, queue, settings, graph)."""

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
    def brain_remember(
        text: str,
        source: str = "mcp",
    ) -> dict:
        """Guarda una memoria persistente del usuario en el segundo cerebro.

        Las memorias son texto libre que se almacena embedido y se recupera
        automáticamente cuando es relevante para una búsqueda (brain_search).

        Retorna el memory_id para poder borrarla después con brain_forget.
        """
        from brain.pipeline.embed import embed_query

        lance = getattr(state, "lance", None)
        if lance is None:
            return {"error": "LanceDB no disponible"}

        memory_id = f"mem-{uuid.uuid4().hex[:12]}"
        vec = embed_query(text, model_name=state.settings.embed_model)
        lance.remember(
            text,
            vector=vec,
            user_id=state.settings.user_id,
            memory_id=memory_id,
            source=source,
            created_at=_now_iso(),
        )
        state.events.append(
            event_type="remember",
            user_id=state.settings.user_id,
            source=source,
            node_id=memory_id,
            payload={"len": len(text), "via": "mcp"},
        )
        return {
            "memory_id": memory_id,
            "status": "stored",
            "len": len(text),
        }

    @mcp.tool
    def brain_forget(memory_id: str) -> dict:
        """Elimina una memoria del segundo cerebro por su memory_id.

        Retorna ok=True si la memoria existía y fue borrada.
        """
        lance = getattr(state, "lance", None)
        if lance is None:
            return {"error": "LanceDB no disponible"}

        ok = lance.forget(memory_id)
        state.events.append(
            event_type="forget",
            user_id=state.settings.user_id,
            source="mcp",
            node_id=memory_id,
            payload={"ok": ok},
        )
        return {"memory_id": memory_id, "ok": ok}

    @mcp.tool
    def brain_ingest_url(
        url: str,
        tags: list[str] | None = None,
        title: str | None = None,
    ) -> dict:
        """Ingesta una URL web en el vault.

        Descarga el contenido, extrae el texto limpio y lo guarda como source node.
        El procesado (chunks + embeddings) ocurre en background.
        Devuelve el job_id para seguimiento.
        """
        job = state.queue.enqueue(
            "brain.workers.jobs.fetch_url.fetch_url",
            url,
            tags,
            title,
            job_timeout=120,
            result_ttl=600,
        )
        state.events.append(
            event_type="ingest_url_queued",
            user_id=state.settings.user_id,
            source="mcp",
            node_id=job.id,
            payload={"url": url, "tags": tags or [], "via": "mcp"},
        )
        return {"status": "queued", "job_id": job.id, "url": url}

    @mcp.tool
    def brain_search(
        q: str,
        k: int = 5,
        mode: Literal["hybrid", "dense", "bm25", "keyword", "graph"] = "hybrid",
        rerank: bool = False,
        include_memories: bool = True,
    ) -> dict:
        """Búsqueda Phase 3: hybrid RRF (dense + BM25) + reranking + graph expansion + memorias.

        Modos:
          - hybrid (default): RRF de dense + BM25, opcionalmente rerankeado.
          - dense:  solo embedding cosine sim.
          - bm25:   solo lexical (tantivy FTS).
          - graph:  hybrid + expansión 1-hop via grafo de menciones.
          - keyword: fallback sobre nombres de archivo del vault.

        rerank=True: aplica Jina jina-reranker-v2-base-multilingual (~200ms extra).
        include_memories=True (default): antepone memorias relevantes al contexto si las hay.
        """
        lance = getattr(state, "lance", None)
        if mode == "keyword" or lance is None:
            hits = state.vault.search_by_name(q, k=k)
            return {"q": q, "k": k, "mode": "keyword", "n": len(hits), "hits": hits, "memories": []}

        user_id = state.settings.user_id
        if mode == "bm25":
            hits = lance.search_bm25(q, k=k, user_id=user_id)
            return {"q": q, "k": k, "mode": "bm25", "n": len(hits), "hits": hits, "memories": []}

        from brain.pipeline.embed import embed_query

        qvec = embed_query(q, model_name=state.settings.embed_model)

        # Memorias relevantes (si include_memories=True)
        memories: list[dict] = []
        if include_memories:
            try:
                memories = lance.search_memories(qvec, k=3, user_id=user_id, threshold=0.65)
            except Exception:
                memories = []

        if mode == "dense":
            hits = lance.search_dense(qvec, k=k, user_id=user_id)
            return {"q": q, "k": k, "mode": "dense", "n": len(hits), "hits": hits, "memories": memories}

        if mode == "graph":
            graph = getattr(state, "graph", None)
            hits = lance.search_hybrid_graph(q, qvec, k=k, user_id=user_id, rerank=rerank, graph=graph)
            mode_label = "graph+rerank" if rerank else "graph"
            return {"q": q, "k": k, "mode": mode_label, "n": len(hits), "hits": hits, "memories": memories}

        hits = lance.search_hybrid(q, qvec, k=k, user_id=user_id, rerank=rerank)
        mode_label = "hybrid+rerank" if rerank else "hybrid"
        return {"q": q, "k": k, "mode": mode_label, "n": len(hits), "hits": hits, "memories": memories}

    @mcp.tool
    def brain_recall(topic: str, k: int = 6) -> dict:
        """Recupera memorias y contexto relevante sobre un tema.

        Busca en memorias persistentes + nodos del vault. Ideal para
        "¿qué discutimos sobre X?" o "¿qué sé sobre Y?".
        Devuelve memorias ordenadas por relevancia + nodos relacionados.
        """
        from brain.pipeline.embed import embed_query

        lance = getattr(state, "lance", None)
        if lance is None:
            return {"topic": topic, "memories": [], "nodes": []}

        user_id = state.settings.user_id
        qvec = embed_query(topic, model_name=state.settings.embed_model)

        memories = lance.search_memories(qvec, k=k, user_id=user_id, threshold=0.5)
        nodes = lance.search_dense(qvec, k=min(k, 5), user_id=user_id)

        return {
            "topic": topic,
            "memories": memories,
            "nodes": nodes,
            "total_memories": len(memories),
            "total_nodes": len(nodes),
        }

    @mcp.tool
    def brain_conversation(
        text: str,
        session_id: str | None = None,
        source: str = "claude_code",
        extract: bool = True,
    ) -> dict:
        """Ingesta un extracto de conversación en el vault y extrae hechos clave.

        - Escribe el texto como memory node en el vault.
        - Si extract=True, encola extracción de hechos vía LLM (gemini-flash).
        - Los hechos extraídos quedan disponibles para brain_recall.

        Úsalo al cerrar una sesión importante o capturar insights de una conversación.
        """
        node_id, path = state.vault.write_node(
            node_type="memory",
            user_id=state.settings.user_id,
            body=text,
            tags=["conversation", source],
            source=source,
            title=f"conv-{session_id or _now_iso()[:10]}",
        )
        state.events.append(
            event_type="ingest_conversation",
            user_id=state.settings.user_id,
            source=source,
            node_id=node_id,
            payload={"session_id": session_id, "len": len(text), "extract": extract},
        )
        # Embed del nodo completo
        state.queue.enqueue(
            "brain.workers.jobs.process_node.process_node",
            node_id,
            job_timeout=300,
            result_ttl=600,
        )
        job_extract = None
        if extract:
            job = state.queue.enqueue(
                "brain.workers.jobs.extract_memories.extract_memories",
                text,
                node_id,
                job_timeout=120,
                result_ttl=600,
            )
            job_extract = job.id

        return {
            "id": node_id,
            "status": "queued",
            "path": str(path.relative_to(state.vault.root)),
            "extract_job": job_extract,
        }
