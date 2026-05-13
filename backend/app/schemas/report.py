from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ReportCreate(BaseModel):
    dashboard_id: uuid.UUID
    name: str = Field(..., min_length=1, max_length=255)
    frequency: str = Field(..., pattern="^(manual|daily|weekly|monthly)$")
    recipients: list[str] = Field(default_factory=list)


class ReportUpdate(BaseModel):
    name: Optional[str] = None
    frequency: Optional[str] = Field(None, pattern="^(manual|daily|weekly|monthly)$")
    recipients: Optional[list[str]] = None
    is_active: Optional[bool] = None


class ReportRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    report_id: uuid.UUID
    status: str
    file_path: Optional[str] = None
    file_type: Optional[str] = None
    error: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    emailed: bool


class ReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    org_id: uuid.UUID
    dashboard_id: uuid.UUID
    name: str
    frequency: str
    recipients: list[str]
    is_active: bool
    last_run_at: Optional[datetime] = None
    next_run_at: Optional[datetime] = None
    created_at: datetime
    runs: list[ReportRunResponse] = []