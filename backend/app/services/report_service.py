from __future__ import annotations

import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.report import Report
from app.repositories.report_repo import ReportRepository, ReportRunRepository
from app.schemas.report import ReportCreate, ReportUpdate


def _next_run(frequency: str) -> Optional[datetime]:
    now = datetime.now(timezone.utc)
    if frequency == "daily":
        return now + timedelta(days=1)
    elif frequency == "weekly":
        return now + timedelta(weeks=1)
    elif frequency == "monthly":
        return now + timedelta(days=30)
    return None


class ReportService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = ReportRepository(db)
        self.run_repo = ReportRunRepository(db)

    async def create_report(self, data: ReportCreate, org_id: uuid.UUID, user_id: uuid.UUID) -> Report:
        next_run = _next_run(data.frequency)
        return await self.repo.create(
            org_id=org_id,
            created_by=user_id,
            dashboard_id=data.dashboard_id,
            name=data.name,
            frequency=data.frequency,
            recipients=data.recipients,
            next_run_at=next_run,
        )

    async def list_reports(self, org_id: uuid.UUID) -> list[Report]:
        return await self.repo.list_by_org(org_id)

    async def get_report(self, report_id: uuid.UUID, org_id: uuid.UUID) -> Report:
        report = await self.repo.get_by_id(report_id, org_id)
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        return report

    async def update_report(self, report_id: uuid.UUID, org_id: uuid.UUID, data: ReportUpdate) -> Report:
        report = await self.get_report(report_id, org_id)
        updates = data.model_dump(exclude_none=True)
        if "frequency" in updates:
            updates["next_run_at"] = _next_run(updates["frequency"])
        return await self.repo.update(report, **updates)

    async def delete_report(self, report_id: uuid.UUID, org_id: uuid.UUID) -> None:
        report = await self.get_report(report_id, org_id)
        await self.repo.soft_delete(report)

    async def trigger_report(self, report_id: uuid.UUID, org_id: uuid.UUID) -> dict:
        report = await self.get_report(report_id, org_id)
        run = await self.run_repo.create(report_id=report.id, org_id=org_id)

        try:
            from app.tasks.report_tasks import generate_report_snapshot
            generate_report_snapshot.delay(str(run.id), str(report.dashboard_id), str(org_id), report.recipients)
        except Exception:
            pass

        return {"run_id": str(run.id), "status": "queued"}

    async def list_runs(self, report_id: uuid.UUID, org_id: uuid.UUID) -> list:
        await self.get_report(report_id, org_id)
        return await self.run_repo.list_by_report(report_id)