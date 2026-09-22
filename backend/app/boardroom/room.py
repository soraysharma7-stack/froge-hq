"""Boardroom — structured multi-perspective deliberation.

Called when: departments disagree, architecture uncertain, multiple strategies,
high security risk, low confidence, expensive/production decisions.
Participants may disagree. Maya synthesizes. Human is final authority.
"""
from __future__ import annotations

import time
import uuid

from app.events.bus import bus, EventType
from app.employees import registry as employees

_SESSIONS: dict[str, dict] = {}


def _position_for(emp_id: str, topic: str) -> dict:
    """Deterministic structured stance per role (Phase: rule-based, no fake model output)."""
    stances = {
        "maya": ("Proceed with smallest viable step; verify before scaling.", 0.7),
        "alex": ("Implement behind clear interfaces; keep blast radius small.", 0.65),
        "sam": ("No sign-off without executable evidence and regression checks.", 0.8),
        "rex": ("Treat unknowns as hostile; require approvals for elevated risk.", 0.75),
        "elena": ("Bound cost first; queue work when limits are near.", 0.6),
        "casey": ("Gather one more source of evidence before committing.", 0.55),
    }
    text, conf = stances.get(emp_id, ("No strong position; defer to evidence.", 0.4))
    return {
        "participant": emp_id,
        "position": text,
        "evidence": f"Role-based analysis of: {topic}",
        "risk": "medium" if conf < 0.7 else "low",
        "confidence": conf,
        "recommendation": text,
    }


async def call_boardroom(topic: str, *, participants: list[str] | None = None,
                         mission_id: str | None = None, called_by: str = "user") -> dict:
    ids = participants or ["maya", "alex", "sam", "rex"]
    ids = [i for i in ids if employees.get(i)]
    session = {
        "id": str(uuid.uuid4())[:8],
        "topic": topic,
        "called_by": called_by,
        "mission_id": mission_id,
        "participants": ids,
        "positions": [_position_for(i, topic) for i in ids],
        "synthesis": None,
        "status": "OPEN",
        "created_at": time.time(),
    }
    # Maya synthesizes: highest-confidence recommendation, noting disagreement
    best = max(session["positions"], key=lambda p: p["confidence"])
    disagree = len({p["position"] for p in session["positions"]}) > 1
    session["synthesis"] = (
        f"Maya synthesis: {best['recommendation']} "
        f"(strongest position: {best['participant']}, confidence {best['confidence']}). "
        + ("Positions diverged — human review advised." if disagree else "Consensus reached.")
    )
    session["status"] = "SYNTHESIZED"
    _SESSIONS[session["id"]] = session
    await bus.publish(EventType.BOARDROOM_STARTED,
                      f"Boardroom called by {called_by}: {topic}",
                      source="boardroom", mission_id=mission_id,
                      metadata={"session_id": session["id"]})
    return session


def list_sessions() -> list[dict]:
    return sorted(_SESSIONS.values(), key=lambda s: s["created_at"], reverse=True)


def get(session_id: str) -> dict | None:
    return _SESSIONS.get(session_id)
