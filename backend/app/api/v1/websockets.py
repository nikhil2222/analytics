from __future__ import annotations

import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.websocket_manager import ws_manager
from app.core.security import decode_token
from app.db.session import AsyncSessionLocal
from app.repositories.user_repo import UserRepository

router = APIRouter(tags=["WebSockets"])


async def get_user_from_token(token: str) -> tuple[str, str] | None:
    """Validate JWT and return (user_id, org_id) or None"""
    user_id = decode_token(token)
    if not user_id:
        return None
    async with AsyncSessionLocal() as db:
        user = await UserRepository(db).get_by_id(user_id)
        if not user or not user.is_active:
            return None
        return str(user.id), str(user.org_id)


# ── Dashboard Live Updates ─────────────────────────────────────────────────

@router.websocket("/ws/dashboard/{dashboard_id}")
async def dashboard_websocket(
    websocket: WebSocket,
    dashboard_id: str,
    token: str = Query(..., description="JWT access token"),
):
    """
    Connect to receive live updates for a specific dashboard.
    Client receives a message whenever new events are ingested.

    Usage:
        ws://localhost:8000/ws/dashboard/{id}?token=<access_token>
    """
    result = await get_user_from_token(token)
    if not result:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    user_id, org_id = result
    connection_id = await ws_manager.connect(websocket, org_id)

    # Send welcome message
    await ws_manager.send_to_connection(websocket, {
        "type": "connected",
        "dashboard_id": dashboard_id,
        "message": "Connected to live dashboard updates",
    })

    try:
        while True:
            # Keep connection alive — listen for ping from client
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                if msg.get("type") == "ping":
                    await ws_manager.send_to_connection(websocket, {"type": "pong"})
            except json.JSONDecodeError:
                pass

    except WebSocketDisconnect:
        ws_manager.disconnect(org_id, connection_id)


# ── Alert Notifications ────────────────────────────────────────────────────

@router.websocket("/ws/alerts")
async def alerts_websocket(
    websocket: WebSocket,
    token: str = Query(..., description="JWT access token"),
):
    """
    Connect to receive real-time alert trigger notifications.

    Usage:
        ws://localhost:8000/ws/alerts?token=<access_token>
    """
    result = await get_user_from_token(token)
    if not result:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    user_id, org_id = result
    connection_id = await ws_manager.connect(websocket, f"alerts:{org_id}")

    await ws_manager.send_to_connection(websocket, {
        "type": "connected",
        "message": "Connected to alert notifications",
    })

    try:
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                if msg.get("type") == "ping":
                    await ws_manager.send_to_connection(websocket, {"type": "pong"})
            except json.JSONDecodeError:
                pass

    except WebSocketDisconnect:
        ws_manager.disconnect(f"alerts:{org_id}", connection_id)


# ── Live Event Stream ──────────────────────────────────────────────────────

@router.websocket("/ws/events/stream")
async def event_stream_websocket(
    websocket: WebSocket,
    token: str = Query(..., description="JWT access token"),
):
    """
    Live tail of incoming events — like `tail -f` but for your event stream.

    Usage:
        ws://localhost:8000/ws/events/stream?token=<access_token>
    """
    result = await get_user_from_token(token)
    if not result:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    user_id, org_id = result
    connection_id = await ws_manager.connect(websocket, f"stream:{org_id}")

    await ws_manager.send_to_connection(websocket, {
        "type": "connected",
        "message": "Connected to live event stream",
    })

    try:
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                if msg.get("type") == "ping":
                    await ws_manager.send_to_connection(websocket, {"type": "pong"})
            except json.JSONDecodeError:
                pass

    except WebSocketDisconnect:
        ws_manager.disconnect(f"stream:{org_id}", connection_id)