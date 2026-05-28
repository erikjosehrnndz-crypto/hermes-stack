"""Ingesta — Phase 1+5: /ingest/text y /ingest/url. Async, 202 Accepted."""
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
    node_id: str | None = Field(
        default=None,
        max_length=128,
        description="ID externo estable para idempotencia (re-ingest sobrescribe).",
    )


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
        node_id=payload.node_id,
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
        job_timeout=300,
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


class IngestUrlIn(BaseModel):
    url: str = Field(min_length=10, max_length=2048)
    tags: list[str] = Field(default_factory=list)
    title: str | None = None


@router.post("/url", status_code=202)
async def ingest_url(payload: IngestUrlIn, request: Request) -> JSONResponse:
    """Ingesta una URL: descarga + extrae texto en background, escribe al vault."""
    state = request.app.state
    queue: Queue = state.queue
    job = queue.enqueue(
        "brain.workers.jobs.fetch_url.fetch_url",
        payload.url,
        payload.tags,
        payload.title,
        job_timeout=120,
        result_ttl=600,
    )
    state.events.append(
        event_type="ingest_url_queued",
        user_id=state.settings.user_id,
        source="api",
        node_id=job.id,
        payload={"url": payload.url, "tags": payload.tags},
    )
    return JSONResponse(
        {"status": "queued", "job_id": job.id, "url": payload.url},
        status_code=202,
    )
