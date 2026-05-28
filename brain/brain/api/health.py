"""Health endpoint — sin auth, sin cache."""
from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse


router = APIRouter()


@router.get("/health", include_in_schema=False)
async def health(request: Request) -> JSONResponse:
    state = request.app.state
    vault_ok = state.vault.root.exists()
    events_ok = state.events.path.exists()
    redis_ok = True
    redis_err: str | None = None
    try:
        state.redis.ping()
    except Exception as exc:
        redis_ok = False
        redis_err = str(exc)

    status = "ok" if (vault_ok and events_ok and redis_ok) else "degraded"
    body = {
        "status": status,
        "vault": {"path": str(state.vault.root), "ok": vault_ok},
        "events": {"path": str(state.events.path), "ok": events_ok, "n": state.events.count()},
        "redis": {"ok": redis_ok, "error": redis_err},
        "phase": 1,
    }
    return JSONResponse(body, status_code=200 if status == "ok" else 503)
