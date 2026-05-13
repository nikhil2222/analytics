from __future__ import annotations

import uuid
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.webhook import WebhookSource


class WebhookRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, org_id: uuid.UUID, created_by: uuid.UUID, name: str) -> WebhookSource:
        wh = WebhookSource(
            org_id=org_id,
            created_by=created_by,
            name=name,
            is_active=True,
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(wh)
        await self.db.commit()
        await self.db.refresh(wh)
        return wh

    async def get_by_id(self, webhook_id: uuid.UUID) -> WebhookSource | None:
        result = await self.db.execute(
            select(WebhookSource).where(
                WebhookSource.id == webhook_id,
                WebhookSource.is_active == True,
            )
        )
        return result.scalar_one_or_none()

    async def get_by_org(self, org_id: uuid.UUID) -> list[WebhookSource]:
        result = await self.db.execute(
            select(WebhookSource).where(WebhookSource.org_id == org_id)
        )
        return list(result.scalars().all())

    async def revoke(self, webhook_id: uuid.UUID, org_id: uuid.UUID) -> bool:
        wh = await self.db.get(WebhookSource, webhook_id)
        if not wh or wh.org_id != org_id:
            return False
        wh.is_active = False
        await self.db.commit()
        return True