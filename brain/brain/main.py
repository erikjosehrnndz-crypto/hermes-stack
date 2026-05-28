"""Brain FastAPI app — Phase 1.

Patrón:
- Settings + vault + events + redis + queue → singletons de módulo (eager init).
- FastMCP construido al import y montado en `/mcp` con lifespan combinado.
- `app.state.*` apunta a los mismos singletons (compartido API REST ↔ MCP).
"""
from __future__ import annotations

from contextlib import asynccontextmanager

import redis
from fastapi import FastAPI
from rq import Queue

from brain.api import health, ingest, search
from brain.mcp.server import build_mcp
from brain.settings import get_settings
from brain.storage.events import EventLog
from brain.storage.vault import Vault


# --- Singletons eager-init ---------------------------------------------
settings = get_settings()
vault = Vault(settings.vault_path, git_remote=settings.git_remote)
events = EventLog(f"{settings.events_path}/events.db")
redis_conn = redis.Redis.from_url(settings.redis_url)
queue = Queue("brain", connection=redis_conn)


class _State:
    """Contenedor ligero — lo que ven endpoints y MCP tools."""

    def __init__(self) -> None:
        self.settings = settings
        self.vault = vault
        self.events = events
        self.redis = redis_conn
        self.queue = queue


_state = _State()

# --- MCP sub-app -------------------------------------------------------
mcp = build_mcp(_state)
mcp_app = mcp.http_app(path="/")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Propaga el lifespan del MCP sub-app (FastMCP 2.x lo exige para HTTP Streamable)
    async with mcp_app.lifespan(app):
        yield


app = FastAPI(
    title="Brain",
    description="Segundo cerebro Hermes Stack — Phase 1 skeleton",
    version="0.1.0",
    lifespan=lifespan,
)

# Expone los singletons en app.state para que los endpoints existentes
# (que usan `request.app.state.*`) sigan funcionando sin cambios.
app.state.settings = _state.settings
app.state.vault = _state.vault
app.state.events = _state.events
app.state.redis = _state.redis
app.state.queue = _state.queue

app.include_router(health.router)
app.include_router(ingest.router)
app.include_router(search.router)

app.mount("/mcp", mcp_app)
