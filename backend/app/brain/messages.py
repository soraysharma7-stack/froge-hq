"""Structured agent-to-agent messages — no uncontrolled free-form hidden state."""
from __future__ import annotations

import time
import uuid
from typing import Any


def message(*, frm: str, to: str, mission_id: str, type: str, status: str,
            summary: str, evidence: list[str] | None = None,
            confidence: str | None = None,
            extra: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "id": str(uuid.uuid4())[:8],
        "from": frm,
        "to": to,
        "mission_id": mission_id,
        "type": type,          # RESULT / ESCALATION / STATUS / REQUEST
        "status": status,      # SUCCESS / PARTIAL_SUCCESS / FAILED / BLOCKED / TIMEOUT
        "summary": summary,
        "evidence": evidence or [],
        "confidence": confidence,
        "timestamp": time.time(),
        **(extra or {}),
    }
