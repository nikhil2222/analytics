from __future__ import annotations

import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.dependencies import get_current_user, require_role
from app.models.user import User, UserRole
from app.schemas.alert import AlertCreate, AlertUpdate, AlertResponse, MuteRequest
from app.services.alert_service import AlertService

router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.post("/", response_model=AlertResponse)
async def create_alert(
    data: AlertCreate,
    current_user: User = Depends(require_role(UserRole.OWNER, UserRole.ADMIN, UserRole.ANALYST)),
    db: AsyncSession = Depends(get_db),
):
    return await AlertService(db).create_alert(data, current_user.org_id, current_user.id)


@router.get("/", response_model=list[AlertResponse])
async def list_alerts(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await AlertService(db).list_alerts(current_user.org_id)


@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert(
    alert_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await AlertService(db).get_alert(alert_id, current_user.org_id)


@router.patch("/{alert_id}", response_model=AlertResponse)
async def update_alert(
    alert_id: uuid.UUID,
    data: AlertUpdate,
    current_user: User = Depends(require_role(UserRole.OWNER, UserRole.ADMIN, UserRole.ANALYST)),
    db: AsyncSession = Depends(get_db),
):
    return await AlertService(db).update_alert(alert_id, current_user.org_id, data)


@router.delete("/{alert_id}")
async def delete_alert(
    alert_id: uuid.UUID,
    current_user: User = Depends(require_role(UserRole.OWNER, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    await AlertService(db).delete_alert(alert_id, current_user.org_id)
    return {"message": "Alert deleted"}


@router.post("/{alert_id}/mute", response_model=AlertResponse)
async def mute_alert(
    alert_id: uuid.UUID,
    data: MuteRequest,
    current_user: User = Depends(require_role(UserRole.OWNER, UserRole.ADMIN, UserRole.ANALYST)),
    db: AsyncSession = Depends(get_db),
):
    return await AlertService(db).mute_alert(alert_id, current_user.org_id, data)


@router.post("/{alert_id}/unmute", response_model=AlertResponse)
async def unmute_alert(
    alert_id: uuid.UUID,
    current_user: User = Depends(require_role(UserRole.OWNER, UserRole.ADMIN, UserRole.ANALYST)),
    db: AsyncSession = Depends(get_db),
):
    return await AlertService(db).unmute_alert(alert_id, current_user.org_id)


@router.post("/{alert_id}/evaluate")
async def manually_evaluate_alert(
    alert_id: uuid.UUID,
    current_user: User = Depends(require_role(UserRole.OWNER, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Manually trigger alert evaluation — useful for testing"""
    alert = await AlertService(db).get_alert(alert_id, current_user.org_id)
    await AlertService(db).evaluate_alert(alert)
    return {"message": "Alert evaluated", "status": alert.status}