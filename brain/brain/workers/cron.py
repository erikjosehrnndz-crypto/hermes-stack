"""Registra los cron jobs al arrancar el worker.

Patrón: cada job se auto-reagenda al finalizar (ver jobs/daily_summary.py y
jobs/vault_sync.py). Este módulo solo registra la primera ejecución si no
existe ya un job con el mismo ID en Redis.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

import redis
from rq import Queue
from rq.job import Job

from brain.settings import get_settings

log = logging.getLogger(__name__)


def _job_is_active(conn, job_id: str) -> bool:
    try:
        job = Job.fetch(job_id, connection=conn)
        return job.get_status() in ("scheduled", "queued", "started")
    except Exception:
        return False


def _next_daily_run(hour: int) -> datetime:
    now = datetime.now(timezone.utc)
    candidate = now.replace(hour=hour, minute=0, second=0, microsecond=0)
    if candidate <= now:
        candidate += timedelta(days=1)
    return candidate


def schedule_all() -> None:
    """Llamado al inicio del worker. Registra crons si no están activos."""
    settings = get_settings()
    conn = redis.Redis.from_url(settings.redis_url)
    q = Queue("brain", connection=conn)

    # daily_summary a las 23:00 UTC
    if not _job_is_active(conn, "daily_summary_cron"):
        next_run = _next_daily_run(hour=23)
        delay = next_run - datetime.now(timezone.utc)
        q.enqueue_in(
            delay,
            "brain.workers.jobs.daily_summary.daily_summary",
            job_id="daily_summary_cron",
            job_timeout=300,
        )
        log.info("cron: daily_summary scheduled for %s", next_run.isoformat())
    else:
        log.info("cron: daily_summary already scheduled")

    # vault_sync cada hora
    if not _job_is_active(conn, "vault_sync_cron"):
        q.enqueue_in(
            timedelta(hours=1),
            "brain.workers.jobs.vault_sync.vault_sync",
            job_id="vault_sync_cron",
            job_timeout=120,
        )
        log.info("cron: vault_sync scheduled in 1 hour")
    else:
        log.info("cron: vault_sync already scheduled")
