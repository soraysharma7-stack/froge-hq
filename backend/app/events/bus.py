"""Live event system — the backbone of observability in FROGÉ HQ."""
from __future__ import annotations

import asyncio
import time
import uuid
from typing import Any, Callable


class EventType:
    MISSION_CREATED = "MISSION_CREATED"
    PLAN_CREATED = "PLAN_CREATED"
    AGENT_ACTIVATED = "AGENT_ACTIVATED"
    SKILL_STARTED = "SKILL_STARTED"
    SKILL_COMPLETED = "SKILL_COMPLETED"
    TOOL_STARTED = "TOOL_STARTED"
    TOOL_COMPLETED = "TOOL_COMPLETED"
    APPROVAL_REQUIRED = "APPROVAL_REQUIRED"
    MODEL_REQUEST_STARTED = "MODEL_REQUEST_STARTED"
    MODEL_REQUEST_COMPLETED = "MODEL_REQUEST_COMPLETED"
    SECURITY_BLOCK = "SECURITY_BLOCK"
    QA_STARTED = "QA_STARTED"
    QA_FAILURE = "QA_FAILURE"
    MISSION_PAUSED = "MISSION_PAUSED"
    MISSION_COMPLETED = "MISSION_COMPLETED"
    MISSION_FAILED = "MISSION_FAILED"
    RESOURCE_LIMIT = "RESOURCE_LIMIT"
    BOARDROOM_STARTED = "BOARDROOM_STARTED"
    SYSTEM = "SYSTEM"


class EventBus:
    """In-process async event bus. Broadcasts to WebSocket subscribers and keeps a bounded log."""

    def __init__(self, max_log: int = 1000):
        self._subscribers: list[asyncio.Queue] = []
        self._log: list[dict[str, Any]] = []
        self._max_log = max_log

    def subscribe(self) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue(maxsize=500)
        self._subscribers.append(q)
        return q

    def unsubscribe(self, q: asyncio.Queue) -> None:
        if q in self._subscribers:
            self._subscribers.remove(q)

    async def publish(
        self,
        type: str,
        message: str,
        *,
        source: str = "system",
        severity: str = "info",
        mission_id: str | None = None,
        employee_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        event = {
            "id": str(uuid.uuid4()),
            "timestamp": time.time(),
            "type": type,
            "source": source,
            "severity": severity,
            "message": message,
            "mission_id": mission_id,
            "employee_id": employee_id,
            "metadata": metadata or {},
        }
        self._log.append(event)
        if len(self._log) > self._max_log:
            self._log = self._log[-self._max_log:]
        for q in list(self._subscribers):
            try:
                q.put_nowait(event)
            except asyncio.QueueFull:
                pass
        return event

    def recent(self, limit: int = 100, type_filter: str | None = None) -> list[dict[str, Any]]:
        events = self._log
        if type_filter and type_filter != "ALL":
            events = [e for e in events if e["type"].startswith(type_filter) or e["source"] == type_filter.lower()]
        return events[-limit:]


bus = EventBus()
