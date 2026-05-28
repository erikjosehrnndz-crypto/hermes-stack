"""Search Phase 3: hybrid+graph+rerank+memories."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field

from brain.api.security import require_bearer
from brain.pipeline.embed import embed_query


router = APIRouter(prefix="/api/v1", dependencies=[Depends(require_bearer)])


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class SearchIn(BaseModel):
    q: str = Field(min_length=1, max_length=512)
    k: int = Field(default=5, ge=1, le=50)
    mode: Literal["hybrid", "dense", "bm25", "keyword", "graph"] = "hybrid"
    rerank: bool = False
    include_memories: bool = True


class RememberIn(BaseModel):
    text: str = Field(min_length=1, max_length=4096)
    source: str = "api"


class ForgetIn(BaseModel):
    memory_id: str


@router.post("/search")
async def search(payload: SearchIn, request: Request) -> dict:
    state = request.app.state
    settings = state.settings
    lance = getattr(state, "lance", None)

    if payload.mode == "keyword" or lance is None:
        hits = state.vault.search_by_name(payload.q, k=payload.k)
        return {"q": payload.q, "mode": "keyword", "k": payload.k, "n": len(hits), "hits": hits, "memories": []}

    user_id = settings.user_id

    if payload.mode == "bm25":
        hits = lance.search_bm25(payload.q, k=payload.k, user_id=user_id)
        return {"q": payload.q, "mode": "bm25", "k": payload.k, "n": len(hits), "hits": hits, "memories": []}

    qvec = embed_query(payload.q, model_name=settings.embed_model)

    # Memorias relevantes
    memories: list[dict] = []
    if payload.include_memories:
        try:
            memories = lance.search_memories(qvec, k=3, user_id=user_id, threshold=0.65)
        except Exception:
            memories = []

    if payload.mode == "dense":
        hits = lance.search_dense(qvec, k=payload.k, user_id=user_id)
        return {"q": payload.q, "mode": "dense", "k": payload.k, "n": len(hits), "hits": hits, "memories": memories}

    if payload.mode == "graph":
        graph = getattr(state, "graph", None)
        hits = lance.search_hybrid_graph(
            payload.q, qvec, k=payload.k, user_id=user_id, rerank=payload.rerank, graph=graph
        )
        mode_label = "graph+rerank" if payload.rerank else "graph"
        return {"q": payload.q, "mode": mode_label, "k": payload.k, "n": len(hits), "hits": hits, "memories": memories}

    hits = lance.search_hybrid(payload.q, qvec, k=payload.k, user_id=user_id, rerank=payload.rerank)
    mode_label = "hybrid+rerank" if payload.rerank else "hybrid"
    return {"q": payload.q, "mode": mode_label, "k": payload.k, "n": len(hits), "hits": hits, "memories": memories}


@router.post("/remember")
async def remember(payload: RememberIn, request: Request) -> dict:
    state = request.app.state
    lance = getattr(state, "lance", None)
    if lance is None:
        return {"error": "LanceDB no disponible"}

    memory_id = f"mem-{uuid.uuid4().hex[:12]}"
    qvec = embed_query(payload.text, model_name=state.settings.embed_model)
    lance.remember(
        payload.text,
        vector=qvec,
        user_id=state.settings.user_id,
        memory_id=memory_id,
        source=payload.source,
        created_at=_now_iso(),
    )
    return {"memory_id": memory_id, "status": "stored", "len": len(payload.text)}


@router.delete("/remember/{memory_id}")
async def forget(memory_id: str, request: Request) -> dict:
    state = request.app.state
    lance = getattr(state, "lance", None)
    if lance is None:
        return {"error": "LanceDB no disponible"}
    ok = lance.forget(memory_id)
    return {"memory_id": memory_id, "ok": ok}


@router.get("/memories")
async def list_memories(request: Request) -> dict:
    state = request.app.state
    lance = getattr(state, "lance", None)
    if lance is None:
        return {"memories": [], "n": 0}
    n = lance.count_memories()
    return {"n": n}
