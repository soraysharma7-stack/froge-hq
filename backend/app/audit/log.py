"""Audit log — WHO / WHAT / WHEN / MISSION / EMPLOYEE / TOOL / PERMISSION / RESULT."""
from __future__ import annotations

import time
import uuid
from typing import Any

_LOG: list[dict[str, Any]] = []
_MAX = 5000


def record(
    who: str,
    what: str,
    *,
    mission_id: str | None = None,
    employee_id: str | None = None,
    tool: str | None = None,
    permission: str | None = None,
    approval_id: str | None = None,
    result: str = "ok",
    metadata: dict | None = None,
) -> dict:
    entry = {
        "id": str(uuid.uuid4())[:8],
        "timestamp": time.time(),
        "who": who,
        "what": what,
        "mission_id": mission_id,
        "employee_id": employee_id,
        "tool": tool,
        "permission": permission,
        "approval_id": approval_id,
        "result": result,
        "metadata": metadata or {},
    }
    _LOG.append(entry)
    if len(_LOG) > _MAX:
        del _LOG[: len(_LOG) - _MAX]
    return entry


def query(limit: int = 200, result: str | None = None) -> list[dict]:
    items = _LOG if not result else [e for e in _LOG if e["result"] == result]
    return list(reversed(items[-limit:]))
