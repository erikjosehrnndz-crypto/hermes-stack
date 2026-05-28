"""Ingesta — Phase 1: solo /ingest/text. Async, 202 Accepted."""
from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from rq import Queue

from brain.api.security import require_bearer


router = APIRouter(prefix="/api/v1/ingest", dependencies=[Depends(require_bearer)])


class IngestTextIn(BaseModel):
    text: str = Field(min_length=1, max_length=64_000)
    type: Literal["journal", "knowledge", "memory", "source"] = "knowledge"
    tags: list[str] = Field(default_factory=list, max_length=32)
    source: str = "api"
    title: str | None = None


@router.post("/text", status_code=202)
async def ingest_text(payload: IngestTextIn, request: Request) -> JSONResponse:
    state = request.app.state
    node_id, path = state.vault.write_node(
        node_type=payload.type,
        user_id=state.settings.user_id,
        body=payload.text,
        tags=payload.tags,
        source=payload.source,
        title=payload.title,
    )
    state.events.append(
        event_type="ingest",
        user_id=state.settings.user_id,
        source=payload.source,
        node_id=node_id,
        payload={
            "type": payload.type,
            "tags": payload.tags,
            "title": payload.title,
            "len": len(payload.text),
            "path": str(path.relative_to(state.vault.root)),
        },
    )
    queue: Queue = state.queue
    job = queue.enqueue(
        "brain.workers.jobs.process_node.process_node",
        node_id,
        job_timeout=60,
        result_ttl=300,
    )
    return JSONResponse(
        {
            "id": node_id,
            "status": "queued",
            "path": str(path.relative_to(state.vault.root)),
            "job_id": job.id,
        },
        status_code=202,
    )
