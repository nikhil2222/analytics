from __future__ import annotations

import secrets
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, Any

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func

from app.models.dashboard import Dashboard, Widget
from app.models.event import Event
from app.repositories.dashboard_repo import DashboardRepository, WidgetRepository
from app.schemas.dashboard import DashboardCreate, DashboardUpdate, WidgetCreate, WidgetUpdate


class DashboardService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.dash_repo = DashboardRepository(db)
        self.widget_repo = WidgetRepository(db)


    # ── Dashboard CRUD ─────────────────────────────────────────────────────

    async def create_dashboard(
        self, data: DashboardCreate, org_id: uuid.UUID, user_id: uuid.UUID
    ) -> Dashboard:
        return await self.dash_repo.create(
            org_id=org_id,
            created_by=user_id,
            name=data.name,
            description=data.description,
            refresh_interval=data.refresh_interval,
        )

    async def list_dashboards(self, org_id: uuid.UUID) -> list[Dashboard]:
        return await self.dash_repo.list_by_org(org_id)

    async def get_dashboard(self, dashboard_id: uuid.UUID, org_id: uuid.UUID) -> Dashboard:
        dashboard = await self.dash_repo.get_by_id(dashboard_id, org_id)
        if not dashboard:
            raise HTTPException(status_code=404, detail="Dashboard not found")
        return dashboard

    async def get_public_dashboard(self, slug: str) -> Dashboard:
        dashboard = await self.dash_repo.get_by_public_slug(slug)
        if not dashboard:
            raise HTTPException(status_code=404, detail="Dashboard not found")
        return dashboard

    async def update_dashboard(
        self, dashboard_id: uuid.UUID, org_id: uuid.UUID, data: DashboardUpdate
    ) -> Dashboard:
        dashboard = await self.get_dashboard(dashboard_id, org_id)
        updates = data.model_dump(exclude_none=True)

        if updates.get("is_public") and not dashboard.public_slug:
            updates["public_slug"] = secrets.token_urlsafe(10)

        return await self.dash_repo.update(dashboard, **updates)

    async def delete_dashboard(self, dashboard_id: uuid.UUID, org_id: uuid.UUID) -> None:
        dashboard = await self.get_dashboard(dashboard_id, org_id)
        await self.dash_repo.soft_delete(dashboard)

    async def enable_public_share(
        self, dashboard_id: uuid.UUID, org_id: uuid.UUID
    ) -> Dashboard:
        dashboard = await self.dash_repo.get_by_id(dashboard_id, org_id)
        if not dashboard:
            raise HTTPException(status_code=404, detail="Dashboard not found")

        if not dashboard.public_slug:
            dashboard.public_slug = secrets.token_urlsafe(16)

        dashboard.is_public = True
        await self.db.commit()
        await self.db.refresh(dashboard)
        return dashboard

    async def disable_public_share(
        self, dashboard_id: uuid.UUID, org_id: uuid.UUID
    ) -> Dashboard:
        dashboard = await self.dash_repo.get_by_id(dashboard_id, org_id)
        if not dashboard:
            raise HTTPException(status_code=404, detail="Dashboard not found")

        dashboard.is_public = False
        await self.db.commit()
        await self.db.refresh(dashboard)
        return dashboard


    # ── Widget CRUD ────────────────────────────────────────────────────────

    async def create_widget(
        self, dashboard_id: uuid.UUID, org_id: uuid.UUID, data: WidgetCreate
    ) -> Widget:
        await self.get_dashboard(dashboard_id, org_id)
        return await self.widget_repo.create(
            dashboard_id=dashboard_id,
            org_id=org_id,
            title=data.title,
            type=data.type,
            query_config=data.query_config.model_dump(),
            position=data.position.model_dump(),
        )

    async def update_widget(
        self, widget_id: uuid.UUID, org_id: uuid.UUID, data: WidgetUpdate
    ) -> Widget:
        widget = await self.widget_repo.get_by_id(widget_id, org_id)
        if not widget:
            raise HTTPException(status_code=404, detail="Widget not found")
        updates = data.model_dump(exclude_none=True)
        if "query_config" in updates:
            updates["query_config"] = data.query_config.model_dump()
        if "position" in updates:
            updates["position"] = data.position.model_dump()
        return await self.widget_repo.update(widget, **updates)

    async def delete_widget(self, widget_id: uuid.UUID, org_id: uuid.UUID) -> None:
        widget = await self.widget_repo.get_by_id(widget_id, org_id)
        if not widget:
            raise HTTPException(status_code=404, detail="Widget not found")
        await self.widget_repo.soft_delete(widget)


    # ── Widget Data Query ──────────────────────────────────────────────────

    async def get_widget_data(self, widget_id: uuid.UUID, org_id: uuid.UUID) -> dict:
        widget = await self.widget_repo.get_by_id(widget_id, org_id)
        if not widget:
            raise HTTPException(status_code=404, detail="Widget not found")

        config = widget.query_config
        time_range = config.get("time_range", "7d")
        start = self._parse_time_range(time_range)

        filters = [
            Event.org_id == org_id,
            Event.name == config["event_name"],
            Event.timestamp >= start,
        ]

        if widget.type == "kpi":
            result = await self.db.execute(
                select(func.count(Event.id)).where(and_(*filters))
            )
            count = result.scalar()
            return {"type": "kpi", "value": count, "label": config["event_name"]}

        elif widget.type in ("line", "bar"):
            result = await self.db.execute(
                select(
                    func.date_trunc("hour", Event.timestamp).label("bucket"),
                    func.count(Event.id).label("count"),
                )
                .where(and_(*filters))
                .group_by("bucket")
                .order_by("bucket")
            )
            rows = result.all()
            return {
                "type": widget.type,
                "data": [{"timestamp": str(r.bucket), "count": r.count} for r in rows],
            }

        elif widget.type == "pie":
            result = await self.db.execute(
                select(Event.name, func.count(Event.id).label("count"))
                .where(and_(*filters))
                .group_by(Event.name)
                .order_by(func.count(Event.id).desc())
                .limit(10)
            )
            rows = result.all()
            return {
                "type": "pie",
                "data": [{"label": r.name, "value": r.count} for r in rows],
            }

        elif widget.type == "table":
            from app.repositories.event_repo import EventRepository
            events = await EventRepository(self.db).get_by_org(
                org_id, start=start, event_name=config["event_name"], limit=100
            )
            return {
                "type": "table",
                "data": [
                    {
                        "id": str(e.id),
                        "name": e.name,
                        "timestamp": str(e.timestamp),
                        "properties": e.properties,
                    }
                    for e in events
                ],
            }

        return {"type": widget.type, "data": []}

    @staticmethod
    def _parse_time_range(time_range: str) -> datetime:
        now = datetime.now(timezone.utc)
        mapping = {
            "1h": timedelta(hours=1),
            "24h": timedelta(hours=24),
            "7d": timedelta(days=7),
            "30d": timedelta(days=30),
            "90d": timedelta(days=90),
        }
        return now - mapping.get(time_range, timedelta(days=7))