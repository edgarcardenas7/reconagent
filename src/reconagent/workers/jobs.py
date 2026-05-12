from __future__ import annotations

from redis import Redis
from rq import Queue

from reconagent.config import get_settings
from reconagent.database import SessionLocal
from reconagent.services.reconciliation import ReconciliationService


def process_reconciliation_run(run_id: str) -> str:
    with SessionLocal() as session:
        ReconciliationService().process_run(session, run_id)
    return run_id


def enqueue_reconciliation_run(run_id: str) -> None:
    settings = get_settings()
    if settings.use_rq:
        redis = Redis.from_url(settings.redis_url)
        Queue("reconagent", connection=redis).enqueue(process_reconciliation_run, run_id)
    else:
        process_reconciliation_run(run_id)
