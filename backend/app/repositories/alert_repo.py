from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.alert import Alert, AlertHistory


class AlertRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, **kwargs) -> Alert:
        alert = Alert(**kwargs)
        self.db.add(alert)
        await self.db.commit()
        await self.db.refresh(alert)
        return alert

    async def get_by_id(self, alert_id: uuid.UUID, org_id: uuid.UUID) -> Optional[Alert]:
        result = await self.db.execute(
            select(Alert).where(
                and_(Alert.id == alert_id, Alert.org_id == org_id, Alert.is_deleted == False)
            )
        )
        return result.scalar_one_or_none()

    async def list_by_org(self, org_id: uuid.UUID) -> list[Alert]:
        result = await self.db.execute(
            select(Alert)
            .where(and_(Alert.org_id == org_id, Alert.is_deleted == False))
            .order_by(Alert.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_all_active(self) -> list[Alert]:
        """Used by Celery Beat to evaluate all active alerts across all orgs"""
        result = await self.db.execute(
            select(Alert).where(
                and_(Alert.status.in_(["active", "triggered"]), Alert.is_deleted == False)
            )
        )
        return list(result.scalars().all())

    async def update(self, alert: Alert, **kwargs) -> Alert:
        for key, value in kwargs.items():
            setattr(alert, key, value)
        await self.db.commit()
        await self.db.refresh(alert)
        return alert

    async def soft_delete(self, alert: Alert) -> None:
        alert.is_deleted = True
        await self.db.commit()

    async def add_history(self, **kwargs) -> AlertHistory:
        history = AlertHistory(**kwargs)
        self.db.add(history)
        await self.db.commit()
        return history