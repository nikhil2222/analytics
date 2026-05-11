from __future__ import annotations

import uuid
from typing import Optional
from sqlalchemy import String, ForeignKey, Boolean, JSON, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin


class Dashboard(Base, TimestampMixin):
    __tablename__ = "dashboards"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"), nullable=False, index=True)
    created_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)
    public_slug: Mapped[Optional[str]] = mapped_column(String(100), unique=True, nullable=True)
    refresh_interval: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # seconds: 30, 60, 300
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)  # soft delete

    widgets: Mapped[list[Widget]] = relationship("Widget", back_populates="dashboard", lazy="selectin")


class Widget(Base, TimestampMixin):
    __tablename__ = "widgets"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    dashboard_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("dashboards.id"), nullable=False, index=True)
    org_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)   # line | bar | pie | kpi | table
    query_config: Mapped[dict] = mapped_column(JSON, nullable=False) # event_name, filters, aggregation etc
    position: Mapped[dict] = mapped_column(JSON, nullable=False)     # {x, y, w, h} for drag-drop grid
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)

    dashboard: Mapped[Dashboard] = relationship("Dashboard", back_populates="widgets")