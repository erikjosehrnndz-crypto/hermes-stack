"""Cron job: genera resumen diario y lo escribe como journal entry."""
from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta, timezone

log = logging.getLogger(__name__)

_LITELLM_URL = "http://litellm:4000"
_MODEL = "gemini-flash"


def daily_summary() -> dict:
    """Genera resumen del día y lo añade al journal.

    - Consulta LanceDB por nodos creados hoy.
    - Llama a LiteLLM (gemini-flash) para sintetizar.
    - Escribe entrada journal y encola embedding.
    - Se re-agenda para las 23:00 UTC del día siguiente.
    """
    from brain.settings import get_settings
    from brain.storage.events import EventLog
    from brain.storage.lance import LanceStore
    from brain.storage.vault import Vault

    settings = get_settings()
    lance = LanceStore(settings.lance_path, dim=settings.embed_dim)
    vault = Vault(settings.vault_path, git_remote=settings.git_remote)
    events = EventLog(f"{settings.events_path}/events.db")

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # Obtener nodos creados hoy
    try:
        nodes_arrow = lance.nodes.to_arrow()
        nodes_dict = nodes_arrow.to_pydict()
        today_nodes = []
        for i, created_at in enumerate(nodes_dict.get("created_at", [])):
            if created_at and str(created_at).startswith(today):
                today_nodes.append({
                    "node_id": nodes_dict["node_id"][i],
                    "title": (nodes_dict.get("title") or [None] * len(nodes_dict["node_id"]))[i],
                    "summary": (nodes_dict.get("summary") or [None] * len(nodes_dict["node_id"]))[i],
                    "node_type": nodes_dict["node_type"][i],
                })
    except Exception as e:
        log.warning("daily_summary: error reading nodes: %s", e)
        today_nodes = []

    if not today_nodes:
        _reschedule(settings.redis_url)
        return {"status": "skipped", "reason": "no_nodes_today", "date": today}

    # Construir contexto
    context_lines = []
    for n in today_nodes[:25]:
        title = n["title"] or n["node_id"]
        snippet = (n["summary"] or "")[:200].replace("\n", " ")
        context_lines.append(f"- [{n['node_type']}] {title}: {snippet}")
    context = "\n".join(context_lines)

    # Llamar a LiteLLM
    api_key = os.environ.get("LITELLM_MASTER_KEY", "")
    summary_text = None
    try:
        import httpx

        with httpx.Client(timeout=60) as client:
            resp = client.post(
                f"{_LITELLM_URL}/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={
                    "model": _MODEL,
                    "messages": [
                        {
                            "role": "system",
                            "content": "Eres el asistente personal de Erik. Resume el día de forma concisa y clara en español.",
                        },
                        {
                            "role": "user",
                            "content": (
                                f"Hoy {today} se capturaron estos {len(today_nodes)} items en el segundo cerebro:\n\n"
                                f"{context}\n\n"
                                "Escribe un resumen del día en 3-5 párrafos. Menciona los temas principales, "
                                "conexiones interesantes y qué parece más importante para recordar."
                            ),
                        },
                    ],
                    "max_tokens": 800,
                },
            )
            resp.raise_for_status()
            summary_text = resp.json()["choices"][0]["message"]["content"]
    except Exception as e:
        log.warning("daily_summary: LiteLLM call failed: %s", e)
        summary_text = f"(resumen automático no disponible: {e})\n\n{context}"

    # Escribir en journal
    body = f"## Resumen automático — {today}\n\n{summary_text}"
    node_id, _ = vault.write_node(
        node_type="journal",
        user_id=settings.user_id,
        body=body,
        tags=["daily-summary", "auto"],
        source="cron",
    )

    # Encolar embedding
    import redis
    from rq import Queue

    conn = redis.Redis.from_url(settings.redis_url)
    q = Queue("brain", connection=conn)
    q.enqueue("brain.workers.jobs.process_node.process_node", node_id, job_timeout=300)

    events.append(
        event_type="daily_summary",
        user_id=settings.user_id,
        source="cron",
        node_id=node_id,
        payload={"date": today, "n_items": len(today_nodes)},
    )

    _reschedule(settings.redis_url)
    return {"status": "ok", "date": today, "n_items": len(today_nodes), "node_id": node_id}


def _reschedule(redis_url: str) -> None:
    """Re-agenda daily_summary para las 23:00 UTC del siguiente día."""
    import redis
    from rq import Queue
    from rq.job import Job

    now = datetime.now(timezone.utc)
    candidate = now.replace(hour=23, minute=0, second=0, microsecond=0)
    if candidate <= now:
        candidate += timedelta(days=1)
    delay = candidate - now

    conn = redis.Redis.from_url(redis_url)
    q = Queue("brain", connection=conn)
    try:
        Job.fetch("daily_summary_cron", connection=conn).delete()
    except Exception:
        pass
    q.enqueue_in(delay, daily_summary, job_id="daily_summary_cron", job_timeout=300)
    log.info("daily_summary re-scheduled for %s", candidate.isoformat())
