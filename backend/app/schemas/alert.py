from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class AlertCreate(BaseModel):
    name: str
    event_name: str
    metric: str = "count"
    operator: str = "gt"
    threshold: float
    time_window_minutes: int = 10
    notify_inapp: bool = True
    notify_email: bool = False
    notify_webhook: bool = False
    webhook_url: Optional[str] = None


class AlertUpdate(BaseModel):
    name: Optional[str] = None
    threshold: Optional[float] = None
    time_window_minutes: Optional[int] = None
    notify_inapp: Optional[bool] = None
    notify_email: Optional[bool] = None
    notify_webhook: Optional[bool] = None
    webhook_url: Optional[str] = None


class MuteRequest(BaseModel):
    minutes: int = 60


class AlertHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    alert_id: uuid.UUID
    org_id: uuid.UUID
    status: str
    triggered_value: float
    threshold: float
    message: Optional[str] = None
    created_at: datetime


class AlertResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    org_id: uuid.UUID
    created_by: uuid.UUID
    name: str
    event_name: str
    metric: str
    operator: str
    threshold: float
    status: str
    time_window_minutes: int
    notify_inapp: bool
    notify_email: bool
    notify_webhook: bool
    webhook_url: Optional[str] = None
    last_evaluated_at: Optional[datetime] = None
    last_triggered_at: Optional[datetime] = None
    muted_until: Optional[datetime] = None
    history: list[AlertHistoryResponse] = []
    created_at: Optional[datetime] = None