"""Cron job: git add + commit de cambios en el vault. Cada hora."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path

log = logging.getLogger(__name__)


def vault_sync() -> dict:
    """Sincroniza el vault con git.

    - git add -A en el vault.
    - Commit si hay cambios.
    - Push si hay remote configurado.
    - Se re-agenda para dentro de 1 hora.
    """
    from brain.settings import get_settings

    settings = get_settings()
    vault_path = Path(settings.vault_path)

    if not (vault_path / ".git").exists():
        _reschedule(settings.redis_url)
        return {"status": "error", "error": "no_git_repo"}

    from git import InvalidGitRepositoryError, Repo

    try:
        repo = Repo(vault_path)
    except InvalidGitRepositoryError:
        _reschedule(settings.redis_url)
        return {"status": "error", "error": "invalid_git_repo"}

    # Stage everything
    repo.git.add("-A")

    # Check if there's anything to commit
    try:
        has_staged = bool(repo.index.diff(repo.head.commit))
    except Exception:
        has_staged = bool(repo.untracked_files or repo.index.diff(None))

    if not has_staged and not repo.untracked_files:
        _reschedule(settings.redis_url)
        return {"status": "ok", "committed": False, "reason": "nothing_to_commit"}

    now_str = datetime.now(timezone.utc).isoformat(timespec="minutes")
    repo.index.commit(f"vault_sync: {now_str}")

    pushed = False
    if settings.git_remote:
        try:
            repo.git.push(settings.git_remote, "main")
            pushed = True
        except Exception as e:
            log.warning("vault_sync: push failed: %s", e)

    _reschedule(settings.redis_url)
    return {"status": "ok", "committed": True, "pushed": pushed}


def _reschedule(redis_url: str) -> None:
    """Re-agenda vault_sync para dentro de 1 hora."""
    import redis
    from rq import Queue
    from rq.job import Job

    conn = redis.Redis.from_url(redis_url)
    q = Queue("brain", connection=conn)
    try:
        Job.fetch("vault_sync_cron", connection=conn).delete()
    except Exception:
        pass
    q.enqueue_in(timedelta(hours=1), vault_sync, job_id="vault_sync_cron", job_timeout=120)
    log.info("vault_sync re-scheduled in 1 hour")
