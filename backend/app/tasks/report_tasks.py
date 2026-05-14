from __future__ import annotations

import logging
import os
import smtplib
import uuid
from datetime import datetime, timedelta, timezone
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from app.models.dashboard import Dashboard
from app.core.celery_app import celery_app
from app.db.session import SyncSessionLocal
from app.models.report import Report, ReportRun
from app.core.config import settings
logger = logging.getLogger(__name__)

REPORTS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)


def _send_email_with_attachment(
    recipients: list[str], subject: str, body: str, file_path: str
): 
    print(f"Sending email to {recipients} with attachment {file_path}")
    smtp_host = settings.SMTP_HOST
    smtp_port = settings.SMTP_PORT
    smtp_user = settings.SMTP_USER
    smtp_pass = settings.SMTP_PASS
    from_email = os.getenv("SMTP_FROM", smtp_user)
    print(f"SMTP config - Host: {smtp_host}, Port: {smtp_port}, User: {smtp_user}")
    if not smtp_host or not smtp_user:
        logger.warning("SMTP not configured — skipping email")
        return

    msg = MIMEMultipart()
    msg["From"] = from_email
    msg["To"] = ", ".join(recipients)
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    with open(file_path, "rb") as f:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header(
            "Content-Disposition",
            f"attachment; filename={os.path.basename(file_path)}",
        )
        msg.attach(part)

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.sendmail(from_email, recipients, msg.as_string())


@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=10,
    name="app.tasks.report_tasks.generate_report_snapshot",
)
def generate_report_snapshot(
    self, run_id: str, dashboard_id: str, org_id: str, recipients: list[str]
):
    with SyncSessionLocal() as db:
        run = db.get(ReportRun, uuid.UUID(run_id))
        if not run:
            return

        run.status = "running"
        db.commit()

        try:
            from playwright.sync_api import sync_playwright
            report = db.get(Report, run.report_id)
            if not report:
                raise ValueError("Report not found")
            dashboard = db.get(Dashboard, report.dashboard_id)
            if not dashboard or not dashboard.is_public or not dashboard.public_slug:
                raise ValueError("Dashboard is not public or slug missing")
            frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
            dashboard_url = f"{frontend_url}/public-dashboard/{dashboard.public_slug}"
            print(f"Generating report snapshot for dashboard {dashboard_url}")
            file_name = f"report_{run_id}.png"
            file_path = os.path.join(REPORTS_DIR, file_name)

            with sync_playwright() as p:
                browser = p.chromium.launch()
                page = browser.new_page(viewport={"width": 1440, "height": 900})
                page.goto(dashboard_url, wait_until="networkidle", timeout=30000)
                page.wait_for_timeout(2000)
                page.screenshot(path=file_path, full_page=True)
                browser.close()

            run.status = "done"
            run.file_path = file_path
            run.file_type = "png"
            run.completed_at = datetime.now(timezone.utc)
            db.commit()

            report = db.get(Report, run.report_id)
            if recipients and report:
                _send_email_with_attachment(
                    recipients=recipients,
                    subject=f"Report: {report.name}",
                    body=f"Your dashboard report is attached.\n\nDashboard: {dashboard_url}",
                    file_path=file_path,
                )
                run.emailed = True
                db.commit()

            logger.info(f"Report run {run_id} completed")
            return {"run_id": run_id, "status": "done", "file": file_path}

        except Exception as exc:
            run.status = "failed"
            run.error = str(exc)
            run.completed_at = datetime.now(timezone.utc)
            db.commit()
            logger.error(f"Report run {run_id} failed: {exc}")
            raise self.retry(exc=exc)


@celery_app.task(name="app.tasks.report_tasks.run_scheduled_reports")
def run_scheduled_reports():
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session

    from app.core.config import settings

    engine = create_engine(settings.DATABASE_URL.replace("+asyncpg", "+psycopg2"))
    with Session(engine) as db:
        now = datetime.now(timezone.utc)
        reports = (
            db.query(Report)
            .filter(
                Report.is_active == True,
                Report.is_deleted == False,
                Report.frequency != "manual",
                Report.next_run_at <= now,
            )
            .all()
        )

        for report in reports:
            run = ReportRun(
                report_id=report.id,
                org_id=report.org_id,
                status="pending",
                created_at=now,
            )
            db.add(run)
            db.flush()

            generate_report_snapshot.delay(
                str(run.id),
                str(report.dashboard_id),
                str(report.org_id),
                report.recipients,
            )

            if report.frequency == "daily":
                report.next_run_at = now + timedelta(days=1)
            elif report.frequency == "weekly":
                report.next_run_at = now + timedelta(weeks=1)
            elif report.frequency == "monthly":
                report.next_run_at = now + timedelta(days=30)

            report.last_run_at = now

        db.commit()
        logger.info(f"Scheduled {len(reports)} reports")
        return {"triggered": len(reports)}