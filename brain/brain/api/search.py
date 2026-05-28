"""Search Phase 1: filename + body substring. Phase 2 reemplaza con LanceDB."""
from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field

from brain.api.security import require_bearer


router = APIRouter(prefix="/api/v1", dependencies=[Depends(require_bearer)])


class SearchIn(BaseModel):
    q: str = Field(min_length=1, max_length=512)
    k: int = Field(default=5, ge=1, le=50)
    mode: Literal["keyword"] = "keyword"


@router.post("/search")
async def search(payload: SearchIn, request: Request) -> dict:
    state = request.app.state
    hits = state.vault.search_by_name(payload.q, k=payload.k)
    return {"q": payload.q, "mode": payload.mode, "hits": hits, "n": len(hits)}
