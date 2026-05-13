from __future__ import annotations

import os
import uuid
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.dependencies import get_current_user, require_role
from app.models.user import User, UserRole
from app.schemas.report import ReportCreate, ReportUpdate, ReportResponse, ReportRunResponse
from app.services.report_service import ReportService

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.post("/", response_model=ReportResponse)
async def create_report(
    data: ReportCreate,
    current_user: User = Depends(require_role(UserRole.OWNER, UserRole.ADMIN, UserRole.ANALYST)),
    db: AsyncSession = Depends(get_db),
):
    return await ReportService(db).create_report(data, current_user.org_id, current_user.id)


@router.get("/", response_model=list[ReportResponse])
async def list_reports(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await ReportService(db).list_reports(current_user.org_id)


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await ReportService(db).get_report(report_id, current_user.org_id)


@router.patch("/{report_id}", response_model=ReportResponse)
async def update_report(
    report_id: uuid.UUID,
    data: ReportUpdate,
    current_user: User = Depends(require_role(UserRole.OWNER, UserRole.ADMIN, UserRole.ANALYST)),
    db: AsyncSession = Depends(get_db),
):
    return await ReportService(db).update_report(report_id, current_user.org_id, data)


@router.delete("/{report_id}")
async def delete_report(
    report_id: uuid.UUID,
    current_user: User = Depends(require_role(UserRole.OWNER, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    await ReportService(db).delete_report(report_id, current_user.org_id)
    return {"message": "Report deleted"}


@router.post("/{report_id}/run")
async def trigger_report(
    report_id: uuid.UUID,
    current_user: User = Depends(require_role(UserRole.OWNER, UserRole.ADMIN, UserRole.ANALYST)),
    db: AsyncSession = Depends(get_db),
):
    return await ReportService(db).trigger_report(report_id, current_user.org_id)


@router.get("/{report_id}/runs", response_model=list[ReportRunResponse])
async def list_runs(
    report_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await ReportService(db).list_runs(report_id, current_user.org_id)


@router.get("/{report_id}/runs/{run_id}/download")
async def download_report(
    report_id: uuid.UUID,
    run_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.repositories.report_repo import ReportRunRepository
    run = await ReportRunRepository(db).get_by_id(run_id)
    if not run or run.status != "done" or not run.file_path:
        raise HTTPException(status_code=404, detail="Report file not found")
    if not os.path.exists(run.file_path):
        raise HTTPException(status_code=404, detail="File no longer exists on disk")
    return FileResponse(
        path=run.file_path,
        media_type="image/png",
        filename=os.path.basename(run.file_path),
    )