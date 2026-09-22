"""Memory Vault — persistent, classified, relevant-only memory.

Pipeline: CAPTURE → CLASSIFY → STORE → INDEX → RETRIEVE → APPLY → EVALUATE
Not every conversation is saved — only useful information.
"""
from __future__ import annotations

import time
import uuid
from enum import Enum

from app.audit import log as audit


class Category(str, Enum):
    DECISIONS = "DECISIONS"
    LESSONS = "LESSONS"
    FAILURES = "FAILURES"
    SUCCESSES = "SUCCESSES"
    PROJECT_KNOWLEDGE = "PROJECT_KNOWLEDGE"
    USER_PREFERENCES = "USER_PREFERENCES"
    SECURITY_RULES = "SECURITY_RULES"
    ARCHITECTURE = "ARCHITECTURE"
    RESEARCH = "RESEARCH"
    MISSION_CONTEXT = "MISSION_CONTEXT"


_MEMORIES: dict[str, dict] = {}


def store(content: str, *, category: Category, source: str, confidence: float = 0.7,
          mission_id: str | None = None, project_id: str | None = None,
          tags: list[str] | None = None) -> dict:
    mem = {
        "id": str(uuid.uuid4())[:8],
        "content": content,
        "category": category.value,
        "source": source,
        "confidence": max(0.0, min(1.0, confidence)),
        "mission_id": mission_id,
        "project_id": project_id,
        "tags": tags or [],
        "relevance_uses": 0,
        "created_at": time.time(),
    }
    _MEMORIES[mem["id"]] = mem
    from app.core import persistence
    persistence.save(persistence.TABLE_MEMORIES, mem["id"], mem)
    audit.record(source, f"memory_stored:{category.value}", mission_id=mission_id)
    return mem


def restore(doc: dict) -> None:
    _MEMORIES[doc["id"]] = doc


def retrieve(query: str = "", *, category: str | None = None, limit: int = 20) -> list[dict]:
    """Keyword relevance retrieval (extension point for semantic search later)."""
    items = list(_MEMORIES.values())
    if category:
        items = [m for m in items if m["category"] == category]
    if query:
        words = {w.lower() for w in query.split() if len(w) > 2}
        scored = []
        for m in items:
            hay = (m["content"] + " " + " ".join(m["tags"])).lower()
            score = sum(1 for w in words if w in hay)
            if score:
                scored.append((score, m))
        scored.sort(key=lambda x: (x[0], x[1]["confidence"]), reverse=True)
        items = [m for _, m in scored]
        for m in items:
            m["relevance_uses"] += 1
    else:
        items.sort(key=lambda m: m["created_at"], reverse=True)
    return items[:limit]


def categories() -> list[str]:
    return [c.value for c in Category]


def count() -> int:
    return len(_MEMORIES)
