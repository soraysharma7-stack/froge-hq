"""WebSocket foundation — streams live events to the HQ frontend."""
from __future__ import annotations

import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.events.bus import bus

router = APIRouter()


@router.websocket("/ws/events")
async def events_ws(websocket: WebSocket):
    await websocket.accept()
    q = bus.subscribe()
    try:
        # Send recent backlog first so a reconnecting client can reconcile state
        for event in bus.recent(limit=50):
            await websocket.send_json({"kind": "backlog", "event": event})
        while True:
            event = await q.get()
            await websocket.send_json({"kind": "live", "event": event})
    except WebSocketDisconnect:
        pass
    finally:
        bus.unsubscribe(q)
