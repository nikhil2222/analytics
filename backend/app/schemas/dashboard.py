from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, ConfigDict, Field


# ── Widget Schemas ─────────────────────────────────────────────────────────

class WidgetPosition(BaseModel):
    x: int = 0
    y: int = 0
    w: int = 4
    h: int = 3


class QueryConfig(BaseModel):
    event_name: str
    aggregation: str = "count"
    group_by: Optional[str] = None
    time_range: str = "7d"
    filters: Optional[dict[str, Any]] = None


class WidgetCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    type: str = Field(..., pattern="^(line|bar|pie|kpi|table)$")
    query_config: QueryConfig
    position: WidgetPosition = WidgetPosition()


class WidgetUpdate(BaseModel):
    title: Optional[str] = None
    type: Optional[str] = None
    query_config: Optional[QueryConfig] = None
    position: Optional[WidgetPosition] = None


class WidgetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    type: str
    query_config: dict
    position: dict
    dashboard_id: uuid.UUID
    created_at: datetime


# ── Dashboard Schemas ──────────────────────────────────────────────────────

class DashboardCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    refresh_interval: Optional[int] = Field(None, description="Seconds: 30, 60, 300")


class DashboardUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_public: Optional[bool] = None
    refresh_interval: Optional[int] = None


class DashboardResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    description: Optional[str] = None
    is_public: bool
    public_slug: Optional[str] = None
    refresh_interval: Optional[int] = None
    widgets: list[WidgetResponse] = []
    created_at: datetime
    created_by: uuid.UUID


class DashboardListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    description: Optional[str] = None
    is_public: bool
    refresh_interval: Optional[int] = None
    widget_count: int = 0
    created_at: datetime