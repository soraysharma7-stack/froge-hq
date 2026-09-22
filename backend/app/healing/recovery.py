"""Self-healing — bounded recovery. FAILURE → DIAGNOSE → LESSONS → ONE CORRECTION → RETEST → SUCCESS/ESCALATE.

Strict retry limits. No infinite loops. Every retry logged.
"""
from __future__ import annotations

import time

from app.audit import log as audit
from app.events.bus import bus, EventType
from app.memory import vault

MAX_RETRIES = 1  # one controlled correction, then escalate
_attempts: dict[str, int] = {}
_LOG: list[dict] = []


async def recover(failure_id: str, error: str, retry_fn, *, mission_id: str | None = None,
                  employee_id: str | None = None) -> dict:
    attempts = _attempts.get(failure_id, 0)
    entry = {"failure_id": failure_id, "error": error, "attempt": attempts + 1,
             "timestamp": time.time(), "outcome": None}

    if attempts >= MAX_RETRIES:
        entry["outcome"] = "ESCALATED"
        _LOG.append(entry)
        vault.store(f"Escalated failure: {error}", category=vault.Category.FAILURES,
                    source="healing", mission_id=mission_id)
        audit.record("healing", f"escalated:{failure_id}", mission_id=mission_id,
                     employee_id=employee_id, result="escalated")
        return {"recovered": False, "escalated": True, "attempts": attempts}

    _attempts[failure_id] = attempts + 1
    lessons = vault.retrieve(error, category=vault.Category.LESSONS.value, limit=3)
    try:
        result = retry_fn()
        ok = bool(result.get("verified", True)) if isinstance(result, dict) else True
    except Exception as e:
        ok, result = False, {"error": str(e)}

    entry["outcome"] = "SUCCESS" if ok else "FAILED"
    entry["result"] = result
    entry["lessons_applied"] = len(lessons)
    _LOG.append(entry)
    audit.record("healing", f"retry:{failure_id}", mission_id=mission_id,
                 employee_id=employee_id, result="success" if ok else "failed")
    await bus.publish(EventType.SYSTEM,
                      f"Self-healing retry for {failure_id}: {entry['outcome']}",
                      source="healing", severity="info" if ok else "warning",
                      mission_id=mission_id)
    if ok:
        vault.store(f"Recovered from: {error}", category=vault.Category.LESSONS,
                    source="healing", mission_id=mission_id)
    return {"recovered": ok, "escalated": False, "attempts": attempts + 1, "result": result}


def log() -> list[dict]:
    return list(reversed(_LOG[-100:]))
