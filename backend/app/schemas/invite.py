from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr

from app.models.user import UserRole


class InviteRequest(BaseModel):
    email: EmailStr
    role: UserRole = UserRole.VIEWER


class InviteAcceptRequest(BaseModel):
    token: str
    full_name: str
    password: str


class InviteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    org_id: uuid.UUID
    invited_by: uuid.UUID
    email: str
    role: str
    status: str
    expires_at: Optional[datetime] = None
    created_at: Optional[datetime] = None