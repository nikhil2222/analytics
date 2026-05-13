from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.report import Report, ReportRun


class ReportRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, org_id: uuid.UUID, created_by: uuid.UUID, dashboard_id: uuid.UUID,
                     name: str, frequency: str, recipients: list[str], next_run_at: Optional[datetime] = None) -> Report:
        report = Report(
            org_id=org_id,
            created_by=created_by,
            dashboard_id=dashboard_id,
            name=name,
            frequency=frequency,
            recipients=recipients,
            next_run_at=next_run_at,
        )
        self.db.add(report)
        await self.db.commit()
        await self.db.refresh(report)
        return report

    async def get_by_id(self, report_id: uuid.UUID, org_id: uuid.UUID) -> Optional[Report]:
        result = await self.db.execute(
            select(Report).where(Report.id == report_id, Report.org_id == org_id, Report.is_deleted == False)
        )
        return result.scalar_one_or_none()

    async def list_by_org(self, org_id: uuid.UUID) -> list[Report]:
        result = await self.db.execute(
            select(Report).where(Report.org_id == org_id, Report.is_deleted == False)
            .order_by(Report.created_at.desc())
        )
        return list(result.scalars().all())

    async def update(self, report: Report, **kwargs) -> Report:
        for key, value in kwargs.items():
            setattr(report, key, value)
        await self.db.commit()
        await self.db.refresh(report)
        return report

    async def soft_delete(self, report: Report) -> None:
        report.is_deleted = True
        await self.db.commit()

    async def get_due_reports(self, now: datetime) -> list[Report]:
        result = await self.db.execute(
            select(Report).where(
                Report.is_active == True,
                Report.is_deleted == False,
                Report.frequency != "manual",
                Report.next_run_at <= now,
            )
        )
        return list(result.scalars().all())


class ReportRunRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, report_id: uuid.UUID, org_id: uuid.UUID) -> ReportRun:
        run = ReportRun(
            report_id=report_id,
            org_id=org_id,
            status="pending",
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(run)
        await self.db.commit()
        await self.db.refresh(run)
        return run

    async def update(self, run: ReportRun, **kwargs) -> ReportRun:
        for key, value in kwargs.items():
            setattr(run, key, value)
        await self.db.commit()
        await self.db.refresh(run)
        return run

    async def list_by_report(self, report_id: uuid.UUID) -> list[ReportRun]:
        result = await self.db.execute(
            select(ReportRun).where(ReportRun.report_id == report_id)
            .order_by(ReportRun.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_id(self, run_id: uuid.UUID) -> Optional[ReportRun]:
        result = await self.db.execute(
            select(ReportRun).where(ReportRun.id == run_id)
        )
        return result.scalar_one_or_none()