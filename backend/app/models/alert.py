from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, ForeignKey, Boolean, JSON, Float, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin


class Alert(Base, TimestampMixin):
    __tablename__ = "alerts"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"), nullable=False, index=True)
    created_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)

    # Rule config — e.g. event_name=error, metric=count, operator=gt, threshold=100
    event_name: Mapped[str] = mapped_column(String(255), nullable=False)
    metric: Mapped[str] = mapped_column(String(50), nullable=False, default="count")  # count | sum | avg
    operator: Mapped[str] = mapped_column(String(10), nullable=False)                 # gt | lt | gte | lte | eq
    threshold: Mapped[float] = mapped_column(Float, nullable=False)
    time_window_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=10)

    # Notification channels
    notify_email: Mapped[bool] = mapped_column(Boolean, default=False)
    notify_webhook: Mapped[bool] = mapped_column(Boolean, default=False)
    notify_inapp: Mapped[bool] = mapped_column(Boolean, default=True)
    webhook_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    email_recipients: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)  # list of emails

    # Status
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    # active | triggered | resolved | muted
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    muted_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_evaluated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_triggered_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    history: Mapped[list[AlertHistory]] = relationship("AlertHistory", back_populates="alert", lazy="selectin")


class AlertHistory(Base):
    __tablename__ = "alert_history"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    alert_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("alerts.id"), nullable=False, index=True)
    org_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)   # triggered | resolved
    triggered_value: Mapped[float] = mapped_column(Float, nullable=False)
    threshold: Mapped[float] = mapped_column(Float, nullable=False)
    message: Mapped[str] = mapped_column(String(500), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    alert: Mapped[Alert] = relationship("Alert", back_populates="history")