"""QA Center — verify actual results. Never declare success without evidence."""
from __future__ import annotations

import time
import uuid

from app.events.bus import bus, EventType

_CHECKS: list[dict] = []


async def verify(kind: str, target: str, verify_fn, *, mission_id: str | None = None,
                 verifier: str = "sam") -> dict:
    """Run a real verification function and record pass/fail evidence."""
    await bus.publish(EventType.QA_STARTED, f"QA verifying {kind}: {target}",
                      source=verifier, mission_id=mission_id)
    check = {
        "id": str(uuid.uuid4())[:8],
        "kind": kind,
        "target": target,
        "mission_id": mission_id,
        "verifier": verifier,
        "timestamp": time.time(),
        "status": "FAILED",
        "evidence": {},
    }
    try:
        evidence = verify_fn()
        check["evidence"] = evidence
        check["status"] = "PASSED" if evidence.get("verified") else "FAILED"
    except Exception as e:  # evidence of failure, not a crash
        check["evidence"] = {"error": str(e)}
        check["status"] = "FAILED"
    _CHECKS.append(check)
    if check["status"] == "FAILED":
        await bus.publish(EventType.QA_FAILURE, f"QA failed for {kind}: {target}",
                          source=verifier, severity="error", mission_id=mission_id)
    return check


def list_checks(limit: int = 100) -> list[dict]:
    return list(reversed(_CHECKS[-limit:]))


def unresolved_failures() -> list[dict]:
    return [c for c in reversed(_CHECKS) if c["status"] == "FAILED"]


def summary() -> dict:
    total = len(_CHECKS)
    passed = sum(1 for c in _CHECKS if c["status"] == "PASSED")
    return {"total": total, "passed": passed, "failed": total - passed,
            "pass_rate": (passed / total) if total else None}
