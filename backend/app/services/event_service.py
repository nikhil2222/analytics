from __future__ import annotations

import csv
import hashlib
import io
import secrets
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException, UploadFile, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.websocket_manager import ws_manager
from app.models.api_key import APIKey
from app.models.event import Event
from app.repositories.api_key_repo import APIKeyRepository
from app.repositories.event_repo import EventRepository
from app.repositories.webhook_repo import WebhookRepository
from app.schemas.event import EventPayload, APIKeyCreate


class EventService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.event_repo = EventRepository(db)
        self.api_key_repo = APIKeyRepository(db)
        self.webhook_repo = WebhookRepository(db)

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
        return api_key, raw_key

    async def list_api_keys(self, org_id: uuid.UUID):
        return await self.api_key_repo.get_by_org(org_id)

    async def revoke_api_key(self, key_id: uuid.UUID, org_id: uuid.UUID):
        revoked = await self.api_key_repo.revoke(key_id, org_id)
        if not revoked:
            raise HTTPException(status_code=404, detail="API key not found")

    async def get_org_by_api_key(self, raw_key: str) -> Optional[APIKey]:
        key_hash = self._hash_key(raw_key)
        return await self.api_key_repo.get_by_hash(key_hash)

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

        try:
            from app.tasks.event_tasks import process_events_batch

            process_events_batch.delay(
                event_ids=[str(e.id) for e in saved],
                org_id=str(org_id),
            )
        except Exception:
            pass

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
            pass

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
                payloads.append(
                    EventPayload(
                        name=row["name"].strip(),
                        timestamp=ts,
                        properties=props or None,
                    )
                )
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

    async def create_webhook(self, name: str, org_id: uuid.UUID, user_id: uuid.UUID):
        return await self.webhook_repo.create(org_id, user_id, name)

    async def list_webhooks(self, org_id: uuid.UUID):
        return await self.webhook_repo.get_by_org(org_id)

    async def revoke_webhook(self, webhook_id: uuid.UUID, org_id: uuid.UUID):
        revoked = await self.webhook_repo.revoke(webhook_id, org_id)
        if not revoked:
            raise HTTPException(status_code=404, detail="Webhook not found")

    async def ingest_webhook(self, webhook_id: uuid.UUID, request: Request) -> dict:
        webhook = await self.webhook_repo.get_by_id(webhook_id)
        if not webhook:
            raise HTTPException(status_code=404, detail="Invalid or revoked webhook")

        try:
            body = await request.json()
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid JSON body")

        payloads: list[EventPayload] = []

        if isinstance(body, dict) and "events" in body:
            for item in body["events"]:
                payloads.append(self._parse_webhook_event(item))
        elif isinstance(body, dict) and "name" in body:
            payloads.append(self._parse_webhook_event(body))
        elif isinstance(body, dict) and "type" in body:
            payload = body.get("payload", body)
            event_name = body.get("type", "webhook_event")
            payloads.append(
                EventPayload(
                    name=event_name,
                    timestamp=None,
                    properties=payload if isinstance(payload, dict) else {"data": str(payload)},
                )
            )
        elif isinstance(body, list):
            for item in body:
                payloads.append(self._parse_webhook_event(item))
        else:
            raise HTTPException(status_code=400, detail="Unrecognized payload format")

        if not payloads:
            return {"ingested": 0}

        events = await self.ingest_events(payloads, webhook.org_id, source="webhook")
        return {"ingested": len(events)}

    @staticmethod
    def _parse_webhook_event(item: dict) -> EventPayload:
        name = item.get("name") or item.get("event") or item.get("type") or "webhook_event"
        ts_raw = item.get("timestamp") or item.get("time") or item.get("created_at")
        ts = None

        if ts_raw:
            try:
                ts = datetime.fromisoformat(str(ts_raw))
            except Exception:
                ts = None

        props = {
            k: v
            for k, v in item.items()
            if k not in ("name", "event", "type", "timestamp", "time", "created_at")
        }

        return EventPayload(
            name=str(name),
            timestamp=ts,
            properties=props or None,
        )