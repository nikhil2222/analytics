from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, EmailStr, ConfigDict
import uuid


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    org_name: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class RefreshResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# Re-export for convenience — auth routes use this
from app.schemas.user import UserResponse  # noqa: E402