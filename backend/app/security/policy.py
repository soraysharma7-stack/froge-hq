"""Security Center — deterministic policy engine. The AI is never the security boundary.

Flow: PROPOSE ACTION → POLICY ENGINE → PERMISSION CHECK → APPROVAL IF REQUIRED → EXECUTE → AUDIT
"""
from __future__ import annotations

import time
from enum import Enum

from app.audit import log as audit
from app.events.bus import bus, EventType


class Risk(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class Decision(str, Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    REQUIRE_APPROVAL = "REQUIRE_APPROVAL"


# Actions that always need human approval (configurable list)
APPROVAL_REQUIRED_ACTIONS = {
    "destructive_operation",
    "external_communication",
    "production_operation",
    "credential_access",
    "expensive_operation",
}

# Deterministically blocked — never executable, approval cannot override
HARD_BLOCKED_ACTIONS = {
    "read_credentials",
    "exfiltrate_data",
    "disable_security",
    "unrestricted_filesystem",
}

_BLOCKED: list[dict] = []


def evaluate(action: str, *, actor: str, risk: Risk = Risk.LOW,
             mission_id: str | None = None, reason: str = "") -> dict:
    """Deterministic policy decision."""
    ts = time.time()
    if action in HARD_BLOCKED_ACTIONS:
        decision = Decision.DENY
    elif action in APPROVAL_REQUIRED_ACTIONS or risk in (Risk.HIGH, Risk.CRITICAL):
        decision = Decision.REQUIRE_APPROVAL
    else:
        decision = Decision.ALLOW

    record = {
        "timestamp": ts, "action": action, "actor": actor,
        "risk": risk.value, "decision": decision.value,
        "mission_id": mission_id, "reason": reason,
    }
    if decision == Decision.DENY:
        _BLOCKED.append(record)
        audit.record(actor, f"blocked:{action}", mission_id=mission_id, result="denied")
    return record


async def enforce(action: str, *, actor: str, risk: Risk = Risk.LOW,
                  mission_id: str | None = None, reason: str = "") -> dict:
    """Policy check + SECURITY_BLOCK event on denial."""
    rec = evaluate(action, actor=actor, risk=risk, mission_id=mission_id, reason=reason)
    if rec["decision"] == Decision.DENY.value:
        await bus.publish(EventType.SECURITY_BLOCK,
                          f"Blocked '{action}' for {actor}: {reason or 'hard-blocked'}",
                          source="security", severity="warning", mission_id=mission_id)
    elif rec["decision"] == Decision.REQUIRE_APPROVAL.value:
        await bus.publish(EventType.APPROVAL_REQUIRED,
                          f"Approval required for '{action}' ({risk.value} risk)",
                          source="security", severity="warning", mission_id=mission_id)
    return rec


def blocked_actions(limit: int = 100) -> list[dict]:
    return list(reversed(_BLOCKED[-limit:]))


def rules() -> dict:
    return {
        "approval_required": sorted(APPROVAL_REQUIRED_ACTIONS),
        "hard_blocked": sorted(HARD_BLOCKED_ACTIONS),
        "sandbox": "project workspace only",
        "note": "Enforced by deterministic backend code. AI output is never the boundary.",
    }
