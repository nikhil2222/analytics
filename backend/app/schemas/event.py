from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, ConfigDict, Field


class EventPayload(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    timestamp: Optional[datetime] = None
    properties: Optional[dict[str, Any]] = None


class BatchEventRequest(BaseModel):
    events: list[EventPayload] = Field(..., min_length=1, max_length=1000)


class EventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    source: str
    timestamp: datetime
    properties: Optional[dict[str, Any]] = None
    org_id: uuid.UUID


class APIKeyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)


class APIKeyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    prefix: str
    is_active: bool
    created_at: datetime


class APIKeyCreatedResponse(APIKeyResponse):
    """Only returned once at creation — includes the raw key"""
    raw_key: str