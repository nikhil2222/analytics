from __future__ import annotations

import uuid
from typing import Optional
from pydantic import BaseModel, ConfigDict


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    org_id: uuid.UUID
    email: str
    full_name: Optional[str] = None
    role: str
    is_active: bool


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None