"""Job: fetch URL → extract text → write vault → enqueue process_node."""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path

log = logging.getLogger(__name__)


def fetch_url(url: str, tags: list[str] | None = None, title: str | None = None) -> dict:
    """Descarga una URL, extrae texto limpio con trafilatura y lo ingesta como source."""
    import httpx
    import trafilatura

    from brain.settings import get_settings
    from brain.storage.events import EventLog
    from brain.storage.vault import Vault

    settings = get_settings()
    vault = Vault(settings.vault_path, git_remote=settings.git_remote)
    events = EventLog(f"{settings.events_path}/events.db")

    # Fetch
    try:
        with httpx.Client(timeout=30, follow_redirects=True) as client:
            resp = client.get(url, headers={"User-Agent": "BrainBot/1.0 (Hermes Stack)"})
            resp.raise_for_status()
            html = resp.text
    except Exception as e:
        log.warning("fetch_url failed for %s: %s", url, e)
        events.append(
            event_type="ingest_url_error",
            user_id=settings.user_id,
            source="url",
            node_id=url[:128],
            payload={"url": url, "error": str(e), "step": "fetch"},
        )
        return {"status": "error", "error": str(e), "step": "fetch", "url": url}

    # Extract clean text
    text = trafilatura.extract(
        html,
        include_comments=False,
        include_tables=True,
        output_format="markdown",
        favor_precision=True,
    )
    if not text or len(text.strip()) < 50:
        events.append(
            event_type="ingest_url_error",
            user_id=settings.user_id,
            source="url",
            node_id=url[:128],
            payload={"url": url, "error": "no_content"},
        )
        return {"status": "error", "error": "no_content", "url": url}

    # Get title from metadata if not provided
    if not title:
        try:
            meta = trafilatura.extract_metadata(html)
            title = meta.title if meta and meta.title else None
        except Exception:
            pass

    # Write to vault
    node_id, path = vault.write_node(
        node_type="source",
        user_id=settings.user_id,
        body=text,
        tags=(tags or []) + ["web-clip"],
        source="url",
        title=title,
        extra_meta={"url": url},
    )

    events.append(
        event_type="ingest_url",
        user_id=settings.user_id,
        source="url",
        node_id=node_id,
        payload={"url": url, "title": title, "n_chars": len(text)},
    )

    # Enqueue embedding
    import redis
    from rq import Queue

    conn = redis.Redis.from_url(settings.redis_url)
    q = Queue("brain", connection=conn)
    job = q.enqueue(
        "brain.workers.jobs.process_node.process_node",
        node_id,
        job_timeout=300,
        result_ttl=600,
    )

    return {
        "node_id": node_id,
        "status": "queued",
        "url": url,
        "title": title,
        "n_chars": len(text),
        "job_id": job.id,
    }
