from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.dependencies import get_current_user, require_role
from app.models.user import User, UserRole
from app.schemas.dashboard import (
    DashboardCreate, DashboardUpdate, DashboardResponse, DashboardListItem,
    WidgetCreate, WidgetUpdate, WidgetResponse,
)
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboards", tags=["Dashboards"])


# ── Dashboard Endpoints ────────────────────────────────────────────────────

@router.post("/", response_model=DashboardResponse)
async def create_dashboard(
    data: DashboardCreate,
    current_user: User = Depends(require_role(UserRole.OWNER, UserRole.ADMIN, UserRole.ANALYST)),
    db: AsyncSession = Depends(get_db),
):
    return await DashboardService(db).create_dashboard(data, current_user.org_id, current_user.id)


@router.get("/", response_model=list[DashboardResponse])
async def list_dashboards(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await DashboardService(db).list_dashboards(current_user.org_id)


@router.get("/public/{slug}", response_model=DashboardResponse)
async def get_public_dashboard(
    slug: str,
    db: AsyncSession = Depends(get_db),
):
    """Public read-only dashboard — no auth required"""
    return await DashboardService(db).get_public_dashboard(slug)


@router.post("/{dashboard_id}/share/public")
async def enable_public_dashboard_share(
    dashboard_id: uuid.UUID,
    current_user: User = Depends(require_role(UserRole.OWNER, UserRole.ADMIN, UserRole.ANALYST)),
    db: AsyncSession = Depends(get_db),
):
    dashboard = await DashboardService(db).enable_public_share(
        dashboard_id, current_user.org_id
    )
    return {
        "id": str(dashboard.id),
        "is_public": dashboard.is_public,
        "public_slug": dashboard.public_slug,
    }


@router.delete("/{dashboard_id}/share/public")
async def disable_public_dashboard_share(
    dashboard_id: uuid.UUID,
    current_user: User = Depends(require_role(UserRole.OWNER, UserRole.ADMIN, UserRole.ANALYST)),
    db: AsyncSession = Depends(get_db),
):
    dashboard = await DashboardService(db).disable_public_share(
        dashboard_id, current_user.org_id
    )
    return {
        "id": str(dashboard.id),
        "is_public": dashboard.is_public,
        "public_slug": dashboard.public_slug,
    }


@router.get("/{dashboard_id}", response_model=DashboardResponse)
async def get_dashboard(
    dashboard_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await DashboardService(db).get_dashboard(dashboard_id, current_user.org_id)


@router.patch("/{dashboard_id}", response_model=DashboardResponse)
async def update_dashboard(
    dashboard_id: uuid.UUID,
    data: DashboardUpdate,
    current_user: User = Depends(require_role(UserRole.OWNER, UserRole.ADMIN, UserRole.ANALYST)),
    db: AsyncSession = Depends(get_db),
):
    return await DashboardService(db).update_dashboard(dashboard_id, current_user.org_id, data)


@router.delete("/{dashboard_id}")
async def delete_dashboard(
    dashboard_id: uuid.UUID,
    current_user: User = Depends(require_role(UserRole.OWNER, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    await DashboardService(db).delete_dashboard(dashboard_id, current_user.org_id)
    return {"message": "Dashboard deleted"}


# ── Widget Endpoints ───────────────────────────────────────────────────────

@router.post("/{dashboard_id}/widgets", response_model=WidgetResponse)
async def create_widget(
    dashboard_id: uuid.UUID,
    data: WidgetCreate,
    current_user: User = Depends(require_role(UserRole.OWNER, UserRole.ADMIN, UserRole.ANALYST)),
    db: AsyncSession = Depends(get_db),
):
    return await DashboardService(db).create_widget(dashboard_id, current_user.org_id, data)


@router.patch("/{dashboard_id}/widgets/{widget_id}", response_model=WidgetResponse)
async def update_widget(
    dashboard_id: uuid.UUID,
    widget_id: uuid.UUID,
    data: WidgetUpdate,
    current_user: User = Depends(require_role(UserRole.OWNER, UserRole.ADMIN, UserRole.ANALYST)),
    db: AsyncSession = Depends(get_db),
):
    return await DashboardService(db).update_widget(widget_id, current_user.org_id, data)


@router.delete("/{dashboard_id}/widgets/{widget_id}")
async def delete_widget(
    dashboard_id: uuid.UUID,
    widget_id: uuid.UUID,
    current_user: User = Depends(require_role(UserRole.OWNER, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    await DashboardService(db).delete_widget(widget_id, current_user.org_id)
    return {"message": "Widget deleted"}


@router.get("/{dashboard_id}/widgets/{widget_id}/data")
async def get_widget_data(
    dashboard_id: uuid.UUID,
    widget_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await DashboardService(db).get_widget_data(widget_id, current_user.org_id)