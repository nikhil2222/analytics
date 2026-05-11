from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete

from app.core.celery_app import celery_app
from app.db.session import SyncSessionLocal          # we'll create this below
from app.models.event import Event

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=5,
    name="app.tasks.event_tasks.process_events_batch",
)
def process_events_batch(self, event_ids: list[str], org_id: str):
    """
    Post-processing after bulk event ingestion.
    Currently: logging + hook for future enrichment (geo, UA parsing etc.)
    """
    try:
        logger.info(
            "Processing batch",
            extra={"event_count": len(event_ids), "org_id": org_id},
        )
        # Future: geo enrichment, user-agent parsing, anomaly detection
        return {"processed": len(event_ids)}
    except Exception as exc:
        logger.error(f"Batch processing failed: {exc}")
        raise self.retry(exc=exc)


@celery_app.task(name="app.tasks.event_tasks.cleanup_old_events")
def cleanup_old_events(retention_days: int = 90):
    """Delete events older than retention_days. Runs daily at 2 AM UTC."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
    with SyncSessionLocal() as db:
        result = db.execute(
            delete(Event).where(Event.timestamp < cutoff)
        )
        db.commit()
        deleted = result.rowcount
        logger.info(f"Cleaned up {deleted} events older than {retention_days} days")
        return {"deleted": deleted}