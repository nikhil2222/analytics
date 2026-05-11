from __future__ import annotations

import uuid
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.api_key import APIKey


class APIKeyRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, **kwargs) -> APIKey:
        api_key = APIKey(**kwargs)
        self.db.add(api_key)
        await self.db.commit()
        await self.db.refresh(api_key)
        return api_key

    async def get_by_hash(self, key_hash: str) -> Optional[APIKey]:
        result = await self.db.execute(
            select(APIKey).where(APIKey.key_hash == key_hash, APIKey.is_active == True)
        )
        return result.scalar_one_or_none()

    async def get_by_org(self, org_id: uuid.UUID) -> list[APIKey]:
        result = await self.db.execute(
            select(APIKey).where(APIKey.org_id == org_id).order_by(APIKey.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_id(self, key_id: uuid.UUID, org_id: uuid.UUID) -> Optional[APIKey]:
        result = await self.db.execute(
            select(APIKey).where(APIKey.id == key_id, APIKey.org_id == org_id)
        )
        return result.scalar_one_or_none()

    async def revoke(self, key_id: uuid.UUID, org_id: uuid.UUID) -> bool:
        api_key = await self.get_by_id(key_id, org_id)
        if not api_key:
            return False
        api_key.is_active = False
        await self.db.commit()
        return True