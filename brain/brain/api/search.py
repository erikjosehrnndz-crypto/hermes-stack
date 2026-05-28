"""Search Phase 2: hybrid (RRF dense + BM25) + fallback keyword sobre vault."""
from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field

from brain.api.security import require_bearer
from brain.pipeline.embed import embed_query


router = APIRouter(prefix="/api/v1", dependencies=[Depends(require_bearer)])


class SearchIn(BaseModel):
    q: str = Field(min_length=1, max_length=512)
    k: int = Field(default=5, ge=1, le=50)
    mode: Literal["hybrid", "dense", "bm25", "keyword", "graph"] = "hybrid"
    rerank: bool = False


@router.post("/search")
async def search(payload: SearchIn, request: Request) -> dict:
    state = request.app.state
    settings = state.settings
    lance = getattr(state, "lance", None)

    # Fallback keyword (Phase 1) si LanceDB no está disponible o el caller lo pide.
    if payload.mode == "keyword" or lance is None:
        hits = state.vault.search_by_name(payload.q, k=payload.k)
        return {
            "q": payload.q,
            "mode": "keyword",
            "k": payload.k,
            "n": len(hits),
            "hits": hits,
        }

    user_id = settings.user_id

    if payload.mode == "bm25":
        hits = lance.search_bm25(payload.q, k=payload.k, user_id=user_id)
        return {"q": payload.q, "mode": "bm25", "k": payload.k, "n": len(hits), "hits": hits}

    qvec = embed_query(payload.q, model_name=settings.embed_model)

    if payload.mode == "dense":
        hits = lance.search_dense(qvec, k=payload.k, user_id=user_id)
        return {"q": payload.q, "mode": "dense", "k": payload.k, "n": len(hits), "hits": hits}

    # hybrid con expansión graph (si mode="graph")
    if payload.mode == "graph":
        graph = getattr(state, "graph", None)
        hits = lance.search_hybrid_graph(
            payload.q, qvec, k=payload.k, user_id=user_id, rerank=payload.rerank, graph=graph
        )
        mode_label = "graph+rerank" if payload.rerank else "graph"
        return {"q": payload.q, "mode": mode_label, "k": payload.k, "n": len(hits), "hits": hits}

    # hybrid (default)
    hits = lance.search_hybrid(payload.q, qvec, k=payload.k, user_id=user_id, rerank=payload.rerank)
    mode_label = "hybrid+rerank" if payload.rerank else "hybrid"
    return {"q": payload.q, "mode": mode_label, "k": payload.k, "n": len(hits), "hits": hits}
