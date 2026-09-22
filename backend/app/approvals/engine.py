"""Approval Engine — PENDING / APPROVED / DENIED / MODIFIED with full context."""
from __future__ import annotations

import time
import uuid
from enum import Enum

from app.audit import log as audit
from app.events.bus import bus, EventType


def restore(doc: dict) -> None:
    _APPROVALS[doc["id"]] = doc


class ApprovalState(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    DENIED = "DENIED"
    MODIFIED = "MODIFIED"


_APPROVALS: dict[str, dict] = {}


async def request(action: str, *, requester: str, reason: str, risk: str,
                  estimated_resources: dict | None = None,
                  mission_id: str | None = None) -> dict:
    ap = {
        "id": str(uuid.uuid4())[:8],
        "action": action,
        "requester": requester,
        "reason": reason,
        "risk": risk,
        "estimated_resources": estimated_resources or {},
        "mission_id": mission_id,
        "state": ApprovalState.PENDING.value,
        "created_at": time.time(),
        "resolved_at": None,
        "resolved_by": None,
        "modification": None,
    }
    _APPROVALS[ap["id"]] = ap
    from app.core import persistence
    persistence.save(persistence.TABLE_APPROVALS, ap["id"], ap)
    audit.record(requester, f"approval_requested:{action}", mission_id=mission_id,
                 approval_id=ap["id"], result="pending")
    await bus.publish(EventType.APPROVAL_REQUIRED,
                      f"{requester} requests approval: {action} ({risk} risk)",
                      source="approvals", severity="warning", mission_id=mission_id,
                      metadata={"approval_id": ap["id"]})
    return ap


async def resolve(approval_id: str, state: ApprovalState, *, resolver: str = "user",
                  modification: str | None = None) -> dict | None:
    ap = _APPROVALS.get(approval_id)
    if not ap or ap["state"] != ApprovalState.PENDING.value:
        return None
    ap["state"] = state.value
    from app.core import persistence
    persistence.save(persistence.TABLE_APPROVALS, ap["id"], ap)
    ap["resolved_at"] = time.time()
    ap["resolved_by"] = resolver
    ap["modification"] = modification
    audit.record(resolver, f"approval_{state.value.lower()}:{ap['action']}",
                 mission_id=ap["mission_id"], approval_id=approval_id,
                 result=state.value.lower())
    await bus.publish(EventType.SYSTEM, f"Approval {approval_id} {state.value} by {resolver}",
                      source="approvals", mission_id=ap["mission_id"])
    return ap


def list_approvals(state: str | None = None) -> list[dict]:
    items = list(_APPROVALS.values())
    if state:
        items = [a for a in items if a["state"] == state]
    return sorted(items, key=lambda a: a["created_at"], reverse=True)


def get(approval_id: str) -> dict | None:
    return _APPROVALS.get(approval_id)
