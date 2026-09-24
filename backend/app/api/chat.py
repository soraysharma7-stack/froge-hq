"""Chat — real two-way conversation with Maya + the team leads.

The user talks; Maya (and the relevant lead) reply IN THE CHAT, not just as events.
Model-backed when the gateway is configured; honest deterministic fallback otherwise
(never a fake model reply — it says so when the model is offline).
"""
from __future__ import annotations

import time

from app.employees import registry as employees
from app.events.bus import bus, EventType
from app.model_gateway.gateway import gateway, ModelRequest
from app.tools import open_tools
from app.voice import router as voice

# Which lead handles which intent (deterministic routing — the backend decides,
# the model only words the reply within that role).
_LEAD_FOR_INTENT = {
    "create": "alex",
    "research": "nova",
    "report": "nova",
    "stop": "maya",
    "status": "maya",
    "assign": "maya",
    "send": "maya",
}


def _lead_reply(lead_id: str, text: str, language: str) -> str:
    """Deterministic, honest reply when the model is offline or for simple commands."""
    emp = employees.get(lead_id)
    name = emp.name if emp else "Maya"
    low = text.lower()
    if lead_id == "maya":
        if "status" in low or "kya ho raha" in low:
            active = sum(1 for e in employees.all_employees() if e.state.value == "ACTIVE")
            return f"{name}: {active} agents active right now. Give me a mission and I'll route it to the smallest capable team."
        return f"{name}: Samjha. Isko mission bana deti hoon — main plan karke sahi employee ko dungi. START MISSION dabao ya yahi 'build …' likho."
    if lead_id == "alex":
        return f"{name}: Main build kar sakta hoon. File/sandbox ke andar kaam karunga, phir Sam verify karega. Bolo kya banana hai — script, page, ya tool?"
    if lead_id == "nova":
        return f"{name}: Main web pe dhoondh ke laata hoon. Query batao — latest news, research, ya fact-check?"
    return f"{name}: Ready."


async def chat_reply(text: str, *, mission_id: str | None = None) -> dict:
    """Route the user's message to the right lead and return a chat reply."""
    text = (text or "").strip()
    if not text:
        return {"reply": "Kuch toh bolo.", "from": "maya", "language": "hinglish"}

    routed = voice.route(text)
    language = routed.get("language", "en")
    intents = routed.get("intents", [])
    intent = intents[0] if intents else "assign"
    lead_id = _LEAD_FOR_INTENT.get(intent, "maya")

    await bus.publish(EventType.SYSTEM, f"[user] {text}", source="user",
                      mission_id=mission_id, metadata={"kind": "chat_user"})

    # Direct open command — "open youtube", "open vs code", "youtube kholo", etc.
    if intent in ("open", "assign") and any(k in text.lower() for k in ("open", "kholo", "khol do", "launch", "start", "chalao")):
        try:
            action = open_tools.resolve_open_command(text)
        except Exception as exc:
            action = {"type": "error", "error": str(exc)}
        who = "maya"
        if action.get("type") == "url":
            reply = f"Opening {action['url']} in your browser now."
        elif action.get("type") == "app":
            if action.get("action") == "opened":
                reply = f"Opened {action.get('label', 'the app')} on your device."
            else:
                reply = action.get("note", "I can't open that from here.")
        else:
            reply = action.get("error", "I don't know how to open that.")
        await bus.publish(EventType.SYSTEM, f"[{who}] {reply}", source=who,
                          mission_id=mission_id, employee_id=lead_id,
                          metadata={"kind": "chat_reply", "action": action})
        return {"reply": reply, "from": who, "action": action, "language": language,
                "model_used": False, "timestamp": time.time()}

    # Try the model for a natural reply within the lead's role; degrade honestly.
    reply: str
    resp = None
    if gateway.status.value == "ONLINE":
        emp = employees.get(lead_id)
        role = emp.role if emp else "Chief AI Orchestrator"
        prompt = (
            f"You are {emp.name if emp else 'Maya'}, the {role} of FROGÉ HQ, a virtual AI organization. "
            f"Reply to the user's message in 1-2 short sentences, in the same language they used "
            f"(English/Hindi/Hinglish), in character, direct and honest. No preamble.\n\n"
            f"User: {text}"
        )
        resp = await gateway.complete(ModelRequest(prompt=prompt, mission_id=mission_id,
                                                   employee_id=lead_id, max_tokens=200))
        if resp.error or not resp.text.strip():
            reply = _lead_reply(lead_id, text, language)
        else:
            reply = resp.text.strip()
    else:
        reply = _lead_reply(lead_id, text, language)

    who = (employees.get(lead_id).name if employees.get(lead_id) else "Maya").lower()
    await bus.publish(EventType.SYSTEM, f"[{who}] {reply}", source=who,
                      mission_id=mission_id, employee_id=lead_id,
                      metadata={"kind": "chat_reply", "lead": lead_id})

    return {"reply": reply, "from": who, "lead": lead_id, "language": language,
            "model_used": gateway.status.value == "ONLINE" and not (resp and resp.error),
            "timestamp": time.time()}
