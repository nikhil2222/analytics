from __future__ import annotations

import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional

import httpx
from fastapi import HTTPException
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.websocket_manager import ws_manager
from app.models.alert import Alert, AlertHistory
from app.models.event import Event
from app.repositories.alert_repo import AlertRepository
from app.schemas.alert import AlertCreate, AlertUpdate, MuteRequest


OPERATOR_MAP = {
    "gt": lambda a, b: a > b,
    "lt": lambda a, b: a < b,
    "gte": lambda a, b: a >= b,
    "lte": lambda a, b: a <= b,
    "eq": lambda a, b: a == b,
}


class AlertService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = AlertRepository(db)

    async def create_alert(self, data: AlertCreate, org_id: uuid.UUID, user_id: uuid.UUID) -> Alert:
        return await self.repo.create(
            org_id=org_id,
            created_by=user_id,
            **data.model_dump()
        )

    async def list_alerts(self, org_id: uuid.UUID) -> list[Alert]:
        return await self.repo.list_by_org(org_id)

    async def get_alert(self, alert_id: uuid.UUID, org_id: uuid.UUID) -> Alert:
        alert = await self.repo.get_by_id(alert_id, org_id)
        if not alert:
            raise HTTPException(status_code=404, detail="Alert not found")
        return alert

    async def update_alert(self, alert_id: uuid.UUID, org_id: uuid.UUID, data: AlertUpdate) -> Alert:
        alert = await self.get_alert(alert_id, org_id)
        updates = data.model_dump(exclude_none=True)
        return await self.repo.update(alert, **updates)

    async def delete_alert(self, alert_id: uuid.UUID, org_id: uuid.UUID) -> None:
        alert = await self.get_alert(alert_id, org_id)
        await self.repo.soft_delete(alert)

    async def mute_alert(self, alert_id: uuid.UUID, org_id: uuid.UUID, data: MuteRequest) -> Alert:
        alert = await self.get_alert(alert_id, org_id)
        muted_until = datetime.now(timezone.utc) + timedelta(minutes=data.minutes)
        return await self.repo.update(alert, status="muted", muted_until=muted_until)

    async def unmute_alert(self, alert_id: uuid.UUID, org_id: uuid.UUID) -> Alert:
        alert = await self.get_alert(alert_id, org_id)
        return await self.repo.update(alert, status="active", muted_until=None)

    # ── Alert Evaluation ──────────────────────────────────────────────────

    async def evaluate_alert(self, alert: Alert) -> None:
        now = datetime.now(timezone.utc)

        # Skip muted alerts
        if alert.status == "muted":
            if alert.muted_until and alert.muted_until > now:
                return
            else:
                await self.repo.update(alert, status="active", muted_until=None)

        window_start = now - timedelta(minutes=alert.time_window_minutes)

        # Calculate metric value
        if alert.metric == "count":
            result = await self.db.execute(
                select(func.count(Event.id)).where(
                    and_(
                        Event.org_id == alert.org_id,
                        Event.name == alert.event_name,
                        Event.timestamp >= window_start,
                    )
                )
            )
            current_value = float(result.scalar() or 0)
        else:
            current_value = 0.0

        comparator = OPERATOR_MAP.get(alert.operator)
        is_triggered = comparator(current_value, alert.threshold)

        await self.repo.update(alert, last_evaluated_at=now)

        if is_triggered and alert.status != "triggered":
            message = (
                f"Alert '{alert.name}' triggered: "
                f"{alert.event_name} {alert.metric} is {current_value} "
                f"(threshold: {alert.operator} {alert.threshold})"
            )
            await self.repo.update(alert, status="triggered", last_triggered_at=now)
            await self.repo.add_history(
                alert_id=alert.id,
                org_id=alert.org_id,
                status="triggered",
                triggered_value=current_value,
                threshold=alert.threshold,
                message=message,
                created_at=now,
            )
            await self._send_notifications(alert, message, current_value)

        elif not is_triggered and alert.status == "triggered":
            message = f"Alert '{alert.name}' resolved: value is now {current_value}"
            await self.repo.update(alert, status="active")
            await self.repo.add_history(
                alert_id=alert.id,
                org_id=alert.org_id,
                status="resolved",
                triggered_value=current_value,
                threshold=alert.threshold,
                message=message,
                created_at=now,
            )
            # 🔴 Broadcast resolution via WebSocket
            await ws_manager.broadcast_to_org(
                f"alerts:{str(alert.org_id)}",
                {
                    "type": "alert_resolved",
                    "alert_id": str(alert.id),
                    "alert_name": alert.name,
                    "message": message,
                    "current_value": current_value,
                },
            )

    async def evaluate_all(self) -> None:
        alerts = await self.repo.get_all_active()
        for alert in alerts:
            try:
                await self.evaluate_alert(alert)
            except Exception as e:
                print(f"Error evaluating alert {alert.id}: {e}")

    # ── Notification Dispatch ─────────────────────────────────────────────

    async def _send_notifications(self, alert: Alert, message: str, value: float) -> None:
        # 🔴 Real-time WebSocket push
        await ws_manager.broadcast_to_org(
            f"alerts:{str(alert.org_id)}",
            {
                "type": "alert_triggered",
                "alert_id": str(alert.id),
                "alert_name": alert.name,
                "message": message,
                "triggered_value": value,
                "threshold": alert.threshold,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )
        if alert.notify_webhook and alert.webhook_url:
            await self._send_webhook(alert, message, value)

    async def _send_webhook(self, alert: Alert, message: str, value: float) -> None:
        payload = {
            "alert_id": str(alert.id),
            "alert_name": alert.name,
            "message": message,
            "triggered_value": value,
            "threshold": alert.threshold,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                await client.post(alert.webhook_url, json=payload)
        except Exception as e:
            print(f"Webhook delivery failed for alert {alert.id}: {e}")