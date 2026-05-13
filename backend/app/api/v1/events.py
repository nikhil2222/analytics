# NO "from __future__ import annotations" here — breaks Pydantic v2 on Python 3.9

import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.webhook import WebhookCreate, WebhookResponse  
from app.db.session import get_db
from app.core.dependencies import get_current_user, require_role
from app.core.rate_limit import limiter
from app.models.user import User, UserRole
from app.schemas.event import (
    EventPayload, BatchEventRequest, EventResponse,
    APIKeyCreate, APIKeyResponse, APIKeyCreatedResponse
)
from app.services.event_service import EventService

router = APIRouter(prefix="/events", tags=["Events"])


# ── Helper: get org_id from API key header ─────────────────────────────────
async def get_org_from_api_key(
    x_api_key: str = Header(..., description="Your API key"),
    db: AsyncSession = Depends(get_db),
) -> uuid.UUID:
    service = EventService(db)
    api_key = await service.get_org_by_api_key(x_api_key)
    if not api_key:
        raise HTTPException(status_code=401, detail="Invalid or revoked API key")
    return api_key.org_id


# ── Event Ingestion ────────────────────────────────────────────────────────

@router.post("/ingest", summary="Ingest single event")
@limiter.limit("1000/minute")
async def ingest_single(
    request: Request,
    payload: EventPayload,
    org_id: uuid.UUID = Depends(get_org_from_api_key),
    db: AsyncSession = Depends(get_db),
):
    events = await EventService(db).ingest_events([payload], org_id, source="api")
    return {"ingested": len(events), "event_id": str(events[0].id)}


@router.post("/ingest/batch", summary="Ingest batch of events")
@limiter.limit("100/minute")
async def ingest_batch(
    request: Request,
    body: BatchEventRequest,
    org_id: uuid.UUID = Depends(get_org_from_api_key),
    db: AsyncSession = Depends(get_db),
):
    events = await EventService(db).ingest_events(body.events, org_id, source="api")
    return {"ingested": len(events)}


@router.post("/ingest/csv", summary="Ingest events from CSV file")
@limiter.limit("20/minute")
async def ingest_csv(
    request: Request,
    file: UploadFile = File(...),
    org_id: uuid.UUID = Depends(get_org_from_api_key),
    db: AsyncSession = Depends(get_db),
):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are accepted")
    result = await EventService(db).ingest_csv(file, org_id)
    return result


@router.get("/", response_model=list[EventResponse], summary="List events")
async def list_events(
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    event_name: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    events = await EventService(db).get_events(
        org_id=current_user.org_id,
        start=start, end=end,
        event_name=event_name,
        limit=min(limit, 1000),
        offset=offset,
    )
    return events


# ── API Key Management ─────────────────────────────────────────────────────

@router.post("/api-keys", response_model=APIKeyCreatedResponse, summary="Create API key")
async def create_api_key(
    data: APIKeyCreate,
    current_user: User = Depends(require_role(UserRole.OWNER, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    api_key, raw_key = await EventService(db).create_api_key(
        data, current_user.org_id, current_user.id
    )
    return APIKeyCreatedResponse(
        id=api_key.id,
        name=api_key.name,
        prefix=api_key.prefix,
        is_active=api_key.is_active,
        created_at=api_key.created_at,
        raw_key=raw_key,
    )


@router.get("/api-keys", response_model=list[APIKeyResponse], summary="List API keys")
async def list_api_keys(
    current_user: User = Depends(require_role(UserRole.OWNER, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    return await EventService(db).list_api_keys(current_user.org_id)


@router.delete("/api-keys/{key_id}", summary="Revoke API key")
async def revoke_api_key(
    key_id: uuid.UUID,
    current_user: User = Depends(require_role(UserRole.OWNER, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    await EventService(db).revoke_api_key(key_id, current_user.org_id)
    return {"message": "API key revoked"}

@router.post("/ingest/webhook/{webhook_id}", summary="Receive webhook events")
async def ingest_webhook(
    request: Request,
    webhook_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Slack-compatible webhook receiver.
    Payload can be:
    - Single event: {"name": "...", "timestamp": "...", "properties": {...}}
    - Batch:        {"events": [...]}
    - Slack-style:  {"type": "...", "payload": {...}}
    """
    return await EventService(db).ingest_webhook(webhook_id, request)

@router.post("/webhooks", summary="Create webhook source")
async def create_webhook(
    data: WebhookCreate,
    current_user: User = Depends(require_role(UserRole.OWNER, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    wh = await EventService(db).create_webhook(data.name, current_user.org_id, current_user.id)
    webhook_url = f"/api/v1/events/ingest/webhook/{wh.id}"
    return {"id": str(wh.id), "name": wh.name, "webhook_url": webhook_url}


@router.get("/webhooks", summary="List webhook sources")
async def list_webhooks(
    current_user: User = Depends(require_role(UserRole.OWNER, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    return await EventService(db).list_webhooks(current_user.org_id)


@router.delete("/webhooks/{webhook_id}", summary="Revoke webhook")
async def revoke_webhook(
    webhook_id: uuid.UUID,
    current_user: User = Depends(require_role(UserRole.OWNER, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    await EventService(db).revoke_webhook(webhook_id, current_user.org_id)
    return {"message": "Webhook revoked"}