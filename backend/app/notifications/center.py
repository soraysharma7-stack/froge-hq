"""Notifications — user-facing alerts driven by the event bus."""
from __future__ import annotations

import asyncio

from app.events.bus import bus

_NOTIFY_TYPES = {
    "APPROVAL_REQUIRED", "MISSION_COMPLETED", "MISSION_FAILED",
    "SECURITY_BLOCK", "QA_FAILURE", "BOARDROOM_STARTED",
    "RESOURCE_LIMIT", "STOP_ALL",
}

_NOTIFICATIONS: list[dict] = []
_listener_task: asyncio.Task | None = None


def restore(doc: dict) -> None:
    if not any(n["id"] == doc["id"] for n in _NOTIFICATIONS):
        _NOTIFICATIONS.append(doc)


async def _listen():
    q = bus.subscribe()
    try:
        while True:
            event = await q.get()
            if event["type"] in _NOTIFY_TYPES:
                _NOTIFICATIONS.append({
                    "id": event["id"],
                    "timestamp": event["timestamp"],
                    "kind": event["type"],
                    "message": event["message"],
                    "severity": event["severity"],
                    "mission_id": event["mission_id"],
                    "read": False,
                })
                from app.core import persistence
                persistence.save(persistence.TABLE_NOTIFICATIONS, event["id"], _NOTIFICATIONS[-1])
    except asyncio.CancelledError:
        bus.unsubscribe(q)


def start():
    global _listener_task
    if _listener_task is None:
        _listener_task = asyncio.create_task(_listen())


def list_notifications(unread_only: bool = False) -> list[dict]:
    items = list(reversed(_NOTIFICATIONS[-200:]))
    return [n for n in items if not n["read"]] if unread_only else items


def mark_read(notification_id: str) -> bool:
    for n in _NOTIFICATIONS:
        if n["id"] == notification_id:
            n["read"] = True
            return True
    return False
