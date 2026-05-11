from __future__ import annotations

import uuid
from typing import Optional
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.dashboard import Dashboard, Widget


class DashboardRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, **kwargs) -> Dashboard:
        dashboard = Dashboard(**kwargs)
        self.db.add(dashboard)
        await self.db.commit()
        await self.db.refresh(dashboard)
        return dashboard

    async def get_by_id(self, dashboard_id: uuid.UUID, org_id: uuid.UUID) -> Optional[Dashboard]:
        result = await self.db.execute(
            select(Dashboard).where(
                and_(
                    Dashboard.id == dashboard_id,
                    Dashboard.org_id == org_id,
                    Dashboard.is_deleted == False,
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_by_public_slug(self, slug: str) -> Optional[Dashboard]:
        result = await self.db.execute(
            select(Dashboard).where(
                and_(
                    Dashboard.public_slug == slug,
                    Dashboard.is_public == True,
                    Dashboard.is_deleted == False,
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def get_public_by_slug(self, slug: str):
        result = await self.db.execute(
            select(Dashboard)
            .where(Dashboard.public_slug == slug, Dashboard.is_public == True)
        )
        return result.scalar_one_or_none()

    async def list_by_org(self, org_id: uuid.UUID) -> list[Dashboard]:
        result = await self.db.execute(
            select(Dashboard).where(
                and_(Dashboard.org_id == org_id, Dashboard.is_deleted == False)
            ).order_by(Dashboard.created_at.desc())
        )
        return list(result.scalars().all())

    async def update(self, dashboard: Dashboard, **kwargs) -> Dashboard:
        for key, value in kwargs.items():
            if value is not None:
                setattr(dashboard, key, value)
        await self.db.commit()
        await self.db.refresh(dashboard)
        return dashboard

    async def soft_delete(self, dashboard: Dashboard) -> None:
        dashboard.is_deleted = True
        await self.db.commit()


class WidgetRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, **kwargs) -> Widget:
        widget = Widget(**kwargs)
        self.db.add(widget)
        await self.db.commit()
        await self.db.refresh(widget)
        return widget

    async def get_by_id(self, widget_id: uuid.UUID, org_id: uuid.UUID) -> Optional[Widget]:
        result = await self.db.execute(
            select(Widget).where(
                and_(
                    Widget.id == widget_id,
                    Widget.org_id == org_id,
                    Widget.is_deleted == False,
                )
            )
        )
        return result.scalar_one_or_none()

    async def update(self, widget: Widget, **kwargs) -> Widget:
        for key, value in kwargs.items():
            if value is not None:
                setattr(widget, key, value)
        await self.db.commit()
        await self.db.refresh(widget)
        return widget

    async def soft_delete(self, widget: Widget) -> None:
        widget.is_deleted = True
        await self.db.commit()