"""RQ worker entrypoint — `python -m brain.workers.rq_worker`."""
from __future__ import annotations

import logging

import redis
from rq import Queue, Worker

from brain.settings import get_settings


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    settings = get_settings()
    conn = redis.Redis.from_url(settings.redis_url)
    queue = Queue("brain", connection=conn)

    from brain.workers.cron import schedule_all
    schedule_all()

    worker = Worker([queue], connection=conn, name="brain-worker")
    worker.work(with_scheduler=True)


if __name__ == "__main__":
    main()
