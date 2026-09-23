"""Context collection — stage 2. Relevance-filtered retrieval only.

Never dumps the entire memory database; pulls a small relevant slice.
"""
from __future__ import annotations

from typing import Any

from app.employees import registry as employees
from app.memory import vault
from app.skills.registry import SKILLS


def collect(objective: str, *, limit: int = 5) -> dict[str, Any]:
    """Gather only context relevant to this objective."""
    relevant_memories = vault.retrieve(objective, limit=limit)
    available_skills = sorted(SKILLS.keys())
    available_employees = [
        {"id": e.id, "role": e.role, "skills": e.skills, "state": e.state.value}
        for e in employees.all_employees()
        if e.enabled
    ]
    return {
        "relevant_memories": [
            {"content": m.get("content", "")[:200], "category": m.get("category"), "confidence": m.get("confidence")}
            for m in relevant_memories
        ],
        "available_skills": available_skills,
        "available_employees": available_employees,
    }
