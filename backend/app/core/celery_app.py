from __future__ import annotations

from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

celery_app = Celery(
    "analytics",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.tasks.event_tasks",
        "app.tasks.alert_tasks",
        "app.tasks.report_tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,               # redeliver on worker crash
    worker_prefetch_multiplier=1,      # one task at a time per worker
    result_expires=3600,               # results expire in 1 hour
)

# ── Celery Beat Schedule ───────────────────────────────────────────────────
celery_app.conf.beat_schedule = {
    "evaluate-alerts-every-minute": {
        "task": "app.tasks.alert_tasks.evaluate_all_alerts",
        "schedule": 60.0,
    },
    "cleanup-old-events-daily": {
        "task": "app.tasks.event_tasks.cleanup_old_events",
        "schedule": crontab(hour=2, minute=0),
    },
    # NEW
    "run-scheduled-reports-every-hour": {
        "task": "app.tasks.report_tasks.run_scheduled_reports",
        "schedule": crontab(minute=0),  # top of every hour
    },
}