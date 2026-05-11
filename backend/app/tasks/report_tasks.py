from __future__ import annotations

import logging

from app.core.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.report_tasks.generate_report")
def generate_report(dashboard_id: str, org_id: str, format: str = "pdf"):
    """
    Scheduled report generation stub.
    Future: use playwright or weasyprint to snapshot the dashboard.
    """
    logger.info(
        f"[REPORT STUB] Generating {format} report "
        f"for dashboard {dashboard_id}, org {org_id}"
    )
    return {"status": "stub", "dashboard_id": dashboard_id, "format": format}