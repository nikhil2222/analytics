from __future__ import annotations

import csv
import hashlib
import io
import secrets
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.websocket_manager import ws_manager
from app.models.api_key import APIKey
from app.models.event import Event
from app.repositories.api_key_repo import APIKeyRepository
from app.repositories.event_repo import EventRepository
from app.schemas.event import EventPayload, APIKeyCreate


class EventService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.event_repo = EventRepository(db)
        self.api_key_repo = APIKeyRepository(db)

    # ── API Key Management ─────────────────────────────────────────────────

    @staticmethod
    def _hash_key(raw_key: str) -> str:
        return hashlib.sha256(raw_key.encode()).hexdigest()

    async def create_api_key(
        self, data: APIKeyCreate, org_id: uuid.UUID, user_id: uuid.UUID
    ):
        raw_key = f"ak_{secrets.token_urlsafe(32)}"
        prefix = raw_key[:12]
        key_hash = self._hash_key(raw_key)
        api_key = await self.api_key_repo.create(
            name=data.name,
            key_hash=key_hash,
            prefix=prefix,
            org_id=org_id,
            created_by=user_id,
        )
        return api_key, raw_key  # raw_key shown ONCE only

    async def list_api_keys(self, org_id: uuid.UUID):
        return await self.api_key_repo.get_by_org(org_id)

    async def revoke_api_key(self, key_id: uuid.UUID, org_id: uuid.UUID):
        revoked = await self.api_key_repo.revoke(key_id, org_id)
        if not revoked:
            raise HTTPException(status_code=404, detail="API key not found")

    async def get_org_by_api_key(self, raw_key: str) -> Optional[APIKey]:
        key_hash = self._hash_key(raw_key)
        return await self.api_key_repo.get_by_hash(key_hash)

    # ── Event Ingestion ────────────────────────────────────────────────────

    async def ingest_events(
        self,
        payloads: list[EventPayload],
        org_id: uuid.UUID,
        source: str = "api",
    ) -> list[Event]:
        now = datetime.now(timezone.utc)
        events = [
            Event(
                org_id=org_id,
                name=p.name,
                source=source,
                properties=p.properties,
                timestamp=p.timestamp or now,
                ingested_at=now,
            )
            for p in payloads
        ]
        saved = await self.event_repo.create_many(events)

        # ── Fire Celery background task (non-blocking) ─────────────────────
        try:
            from app.tasks.event_tasks import process_events_batch
            process_events_batch.delay(
                event_ids=[str(e.id) for e in saved],
                org_id=str(org_id),
            )
        except Exception:
            # Celery not running — fail silently, ingestion still succeeds
            pass

        # ── Broadcast to WebSocket connections ─────────────────────────────
        org_str = str(org_id)
        broadcast_data = {
            "type": "new_events",
            "count": len(saved),
            "events": [
                {
                    "id": str(e.id),
                    "name": e.name,
                    "timestamp": str(e.timestamp),
                    "source": e.source,
                    "properties": e.properties,
                }
                for e in saved
            ],
        }
        try:
            await ws_manager.broadcast_to_org(org_str, broadcast_data)
            await ws_manager.broadcast_to_org(f"stream:{org_str}", broadcast_data)
        except Exception:
            pass  # WS broadcast failure must never break ingestion

        return saved

    async def ingest_csv(self, file: UploadFile, org_id: uuid.UUID) -> dict:
        contents = await file.read()
        text = contents.decode("utf-8")
        reader = csv.DictReader(io.StringIO(text))

        payloads: list[EventPayload] = []
        errors: list[str] = []

        for i, row in enumerate(reader, start=1):
            if "name" not in row or not row["name"].strip():
                errors.append(f"Row {i}: missing 'name' column")
                continue
            try:
                ts = None
                if row.get("timestamp"):
                    ts = datetime.fromisoformat(row["timestamp"])
                props = {
                    k: v for k, v in row.items()
                    if k not in ("name", "timestamp") and v != ""
                }
                payloads.append(EventPayload(
                    name=row["name"].strip(),
                    timestamp=ts,
                    properties=props or None,
                ))
            except Exception as e:
                errors.append(f"Row {i}: {str(e)}")

        if not payloads:
            return {"ingested": 0, "errors": errors}

        events = await self.ingest_events(payloads, org_id, source="csv")
        return {
            "ingested": len(events),
            "errors": errors,
        }

    async def get_events(
        self,
        org_id: uuid.UUID,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        event_name: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ):
        return await self.event_repo.get_by_org(
            org_id,
            start=start,
            end=end,
            event_name=event_name,
            limit=limit,
            offset=offset,
        )