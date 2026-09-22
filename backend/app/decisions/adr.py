"""Decision System — versioned Architecture Decision Records (no hidden chain-of-thought)."""
from __future__ import annotations

import time
import uuid

_DECISIONS: dict[str, dict] = {}


def record_decision(decision: str, *, context: str, alternatives: list[str],
                    reasoning_summary: str, evidence: list[str], risks: list[str],
                    owner: str, status: str = "ACCEPTED",
                    mission_id: str | None = None) -> dict:
    adr = {
        "id": str(uuid.uuid4())[:8],
        "decision": decision,
        "context": context,
        "alternatives": alternatives,
        "reasoning_summary": reasoning_summary,  # concise, no private CoT
        "evidence": evidence,
        "risks": risks,
        "owner": owner,
        "status": status,
        "mission_id": mission_id,
        "version": 1,
        "created_at": time.time(),
        "history": [],
    }
    _DECISIONS[adr["id"]] = adr
    return adr


def supersede(adr_id: str, *, new_decision: str, reasoning_summary: str, owner: str) -> dict | None:
    old = _DECISIONS.get(adr_id)
    if not old:
        return None
    old["status"] = "SUPERSEDED"
    old["history"].append({"version": old["version"], "superseded_at": time.time()})
    new = record_decision(
        new_decision, context=old["context"], alternatives=old["alternatives"],
        reasoning_summary=reasoning_summary, evidence=old["evidence"],
        risks=old["risks"], owner=owner)
    new["version"] = old["version"] + 1
    return new


def list_decisions() -> list[dict]:
    return sorted(_DECISIONS.values(), key=lambda d: d["created_at"], reverse=True)


def get(adr_id: str) -> dict | None:
    return _DECISIONS.get(adr_id)
