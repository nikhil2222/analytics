from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

import httpx
from sqlalchemy import select, func

from app.core.celery_app import celery_app
from app.db.session import SyncSessionLocal
from app.models.alert import Alert, AlertHistory
from app.models.event import Event

logger = logging.getLogger(__name__)

OPERATORS = {
    "gt": lambda a, b: a > b,
    "gte": lambda a, b: a >= b,
    "lt": lambda a, b: a < b,
    "lte": lambda a, b: a <= b,
    "eq": lambda a, b: a == b,
}


@celery_app.task(name="app.tasks.alert_tasks.evaluate_all_alerts")
def evaluate_all_alerts():
    """Evaluate every active alert. Runs every 60 seconds via Celery Beat."""
    with SyncSessionLocal() as db:
        now = datetime.now(timezone.utc)

        alerts = db.execute(
            select(Alert).where(
                Alert.status.in_(["active", "triggered"]),
                Alert.is_deleted == False,
            )
        ).scalars().all()

        alerts = [
            alert for alert in alerts
            if alert.muted_until is None or alert.muted_until < now
        ]

        results = {"evaluated": 0, "triggered": 0, "resolved": 0}

        for alert in alerts:
            try:
                outcome = _evaluate_single_alert(db, alert, now)
                results["evaluated"] += 1
                if outcome == "triggered":
                    results["triggered"] += 1
                elif outcome == "resolved":
                    results["resolved"] += 1
            except Exception as e:
                logger.exception(f"Failed to evaluate alert {alert.id}: {e}")

        db.commit()
        logger.info(f"Alert evaluation complete: {results}")
        return results


def _evaluate_single_alert(db, alert: Alert, now: datetime) -> str:
    """Core evaluation logic for a single alert."""
    window_start = now - timedelta(minutes=alert.time_window_minutes)

    count = db.execute(
        select(func.count(Event.id)).where(
            Event.org_id == alert.org_id,
            Event.name == alert.event_name,
            Event.timestamp >= window_start,
            Event.timestamp <= now,
        )
    ).scalar() or 0

    compare = OPERATORS.get(alert.operator, lambda a, b: False)
    is_triggered = compare(count, alert.threshold)

    history = AlertHistory(
        alert_id=alert.id,
        org_id=alert.org_id,
        status="triggered" if is_triggered else "resolved",
        triggered_value=float(count),
        threshold=alert.threshold,
        message=(
            f"{alert.event_name} count={count} {alert.operator} "
            f"{alert.threshold} in last {alert.time_window_minutes} min"
        ),
        created_at=now,
    )
    db.add(history)

    outcome = "noop"

    if is_triggered and alert.status != "triggered":
        alert.status = "triggered"
        alert.last_triggered_at = now
        _send_notifications(alert, count)
        outcome = "triggered"
    elif not is_triggered and alert.status == "triggered":
        alert.status = "resolved"
        outcome = "resolved"
    elif not is_triggered and alert.status == "resolved":
        alert.status = "active"
        outcome = "active"

    alert.last_evaluated_at = now
    return outcome


def _send_notifications(alert: Alert, triggered_value: float):
    """Fire notification channels — webhook and email stub."""
    message = (
        f"🚨 Alert triggered: {alert.name}\n"
        f"Event '{alert.event_name}' count={triggered_value} "
        f"{alert.operator} {alert.threshold} "
        f"in last {alert.time_window_minutes} min"
    )

    if alert.notify_webhook and alert.webhook_url:
        try:
            with httpx.Client(timeout=5) as client:
                client.post(alert.webhook_url, json={"text": message})
            logger.info(f"Webhook sent for alert {alert.id}")
        except Exception as e:
            logger.exception(f"Webhook failed for alert {alert.id}: {e}")

    if alert.notify_email:
        logger.info(f"[EMAIL STUB] Would send email for alert {alert.id}: {message}")

    if alert.notify_inapp:
        logger.info(f"[IN-APP] Alert triggered for org {alert.org_id}: {alert.name}")