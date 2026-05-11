from __future__ import annotations

import json
import uuid
from typing import Optional
from fastapi import WebSocket


class ConnectionManager:
    """
    Manages all active WebSocket connections.
    Connections are grouped by org_id so we only
    broadcast to the right organization.
    """

    def __init__(self):
        # { org_id: { connection_id: WebSocket } }
        self._connections: dict[str, dict[str, WebSocket]] = {}

    async def connect(self, websocket: WebSocket, org_id: str) -> str:
        await websocket.accept()
        connection_id = str(uuid.uuid4())
        if org_id not in self._connections:
            self._connections[org_id] = {}
        self._connections[org_id][connection_id] = websocket
        print(f"✅ WS connected: org={org_id} conn={connection_id}")
        return connection_id

    def disconnect(self, org_id: str, connection_id: str) -> None:
        if org_id in self._connections:
            self._connections[org_id].pop(connection_id, None)
            if not self._connections[org_id]:
                del self._connections[org_id]
        print(f"❌ WS disconnected: org={org_id} conn={connection_id}")

    async def send_to_connection(self, websocket: WebSocket, data: dict) -> None:
        try:
            await websocket.send_text(json.dumps(data))
        except Exception:
            pass

    async def broadcast_to_org(self, org_id: str, data: dict) -> None:
        """Send a message to ALL connections in an org"""
        if org_id not in self._connections:
            return
        dead = []
        for conn_id, ws in self._connections[org_id].items():
            try:
                await ws.send_text(json.dumps(data))
            except Exception:
                dead.append(conn_id)
        # clean up dead connections
        for conn_id in dead:
            self.disconnect(org_id, conn_id)

    def get_connection_count(self, org_id: str) -> int:
        return len(self._connections.get(org_id, {}))


# Global singleton — imported everywhere
ws_manager = ConnectionManager()