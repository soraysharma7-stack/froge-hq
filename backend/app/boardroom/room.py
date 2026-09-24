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
from app.model_gateway.gateway import gateway, ModelRequest

_SESSIONS: dict[str, dict] = {}


def _position_for(emp_id: str, topic: str) -> dict:
    """Deterministic structured stance per role (no fake model output)."""
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


async def call_meeting(topic: str, *, participants: list[str] | None = None,
                       mission_id: str | None = None, called_by: str = "user") -> dict:
    """Meeting Room — all team leads speak on the topic with real model output.

    Each lead replies in their own voice via the configured model. If the model
    is unavailable, leads fall back to their deterministic role stance and the
    session is marked degraded — nothing is faked.
    """
    ids = participants or ["maya", "alex", "sam", "nova", "rex"]
    ids = [i for i in ids if employees.get(i)]
    turns: list[dict] = []
    degraded = False
    for emp_id in ids:
        emp = employees.get(emp_id)
        role = emp.role if emp else emp_id
        prompt = (
            f"You are {emp.name if emp else emp_id}, {role} at FROGÉ HQ. "
            f"The team is in a meeting about: {topic!r}. "
            f"Speak in 2 short sentences, in your own role voice, directly to the user. "
            f"Be concrete and honest."
        )
        resp = await gateway.complete(ModelRequest(prompt=prompt, mission_id=mission_id,
                                                   employee_id=emp_id, max_tokens=180))
        if resp.error:
            degraded = True
            stance = _position_for(emp_id, topic)
            text = stance["position"]
        else:
            text = resp.text.strip()
        turns.append({
            "participant": emp_id,
            "name": emp.name if emp else emp_id,
            "role": role,
            "text": text,
            "from_model": not bool(resp.error),
        })
        await bus.publish("MEETING_TURN",
                          f"{emp.name if emp else emp_id}: {text[:80]}",
                          source=emp_id, mission_id=mission_id,
                          metadata={"participant": emp_id, "role": role,
                                    "from_model": not bool(resp.error)})

    session = {
        "id": str(uuid.uuid4())[:8],
        "kind": "MEETING",
        "topic": topic,
        "called_by": called_by,
        "mission_id": mission_id,
        "participants": ids,
        "turns": turns,
        "degraded": degraded,
        "status": "DONE",
        "created_at": time.time(),
    }
    _SESSIONS[session["id"]] = session
    await bus.publish(EventType.BOARDROOM_STARTED,
                      f"Meeting started by {called_by}: {topic} ({len(ids)} leads)",
                      source="boardroom", mission_id=mission_id,
                      metadata={"session_id": session["id"], "degraded": degraded})
    return session


def list_sessions() -> list[dict]:
    return sorted(_SESSIONS.values(), key=lambda s: s["created_at"], reverse=True)


def get(session_id: str) -> dict | None:
    return _SESSIONS.get(session_id)
