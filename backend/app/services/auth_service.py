from __future__ import annotations
import re
import uuid
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token, decode_token
from app.models.user import User, UserRole
from app.models.invite import Invite
from app.repositories.user_repo import UserRepository
from app.repositories.org_repo import OrgRepository
from app.schemas.auth import RegisterRequest, LoginRequest
from app.schemas.invite import InviteRequest, InviteAcceptRequest


def slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repo = UserRepository(db)
        self.org_repo = OrgRepository(db)

    async def register(self, data: RegisterRequest) -> tuple[User, str, str]:
        if await self.user_repo.get_by_email(data.email):
            raise HTTPException(status_code=400, detail="Email already registered")

        base_slug = slugify(data.org_name)
        slug = base_slug
        counter = 1
        while await self.org_repo.get_by_slug(slug):
            slug = f"{base_slug}-{counter}"
            counter += 1

        org = await self.org_repo.create(name=data.org_name, slug=slug)
        user = await self.user_repo.create(
            email=data.email,
            hashed_password=hash_password(data.password),
            full_name=data.full_name,
            role=UserRole.OWNER,
            org_id=org.id,
        )
        return user, create_access_token(str(user.id)), create_refresh_token(str(user.id))

    async def login(self, data: LoginRequest) -> tuple[User, str, str]:
        user = await self.user_repo.get_by_email(data.email)
        if not user or not verify_password(data.password, user.hashed_password):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
        if not user.is_active:
            raise HTTPException(status_code=400, detail="Account is disabled")
        return user, create_access_token(str(user.id)), create_refresh_token(str(user.id))

    async def refresh(self, refresh_token: str) -> str:
        user_id = decode_token(refresh_token)
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid refresh token")
        return create_access_token(user_id)

    async def invite_user(self, data: InviteRequest, inviter: User) -> Invite:
        invite = Invite(
            email=data.email,
            role=data.role,
            token=str(uuid.uuid4()),
            org_id=inviter.org_id,
            invited_by=inviter.id,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )
        self.db.add(invite)
        await self.db.commit()
        await self.db.refresh(invite)
        return invite

    async def accept_invite(self, data: InviteAcceptRequest) -> tuple[User, str, str]:
        result = await self.db.execute(
            select(Invite).where(Invite.token == data.token, Invite.accepted == False)
        )
        invite = result.scalar_one_or_none()
        if not invite:
            raise HTTPException(status_code=404, detail="Invalid or expired invite")
        if invite.expires_at < datetime.now(timezone.utc):
            raise HTTPException(status_code=400, detail="Invite has expired")

        user = await self.user_repo.create(
            email=invite.email,
            hashed_password=hash_password(data.password),
            full_name=data.full_name,
            role=invite.role,
            org_id=invite.org_id,
        )
        invite.accepted = True
        await self.db.commit()
        return user, create_access_token(str(user.id)), create_refresh_token(str(user.id))