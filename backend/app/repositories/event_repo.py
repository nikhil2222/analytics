from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.event import Event


class EventRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_many(self, events: list[Event]) -> list[Event]:
        self.db.add_all(events)
        await self.db.commit()
        return events

    async def get_by_org(
        self,
        org_id: uuid.UUID,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        event_name: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Event]:
        filters = [Event.org_id == org_id]
        if start:
            filters.append(Event.timestamp >= start)
        if end:
            filters.append(Event.timestamp <= end)
        if event_name:
            filters.append(Event.name == event_name)

        result = await self.db.execute(
            select(Event)
            .where(and_(*filters))
            .order_by(Event.timestamp.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())