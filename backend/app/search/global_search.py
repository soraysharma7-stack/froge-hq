"""Global search across missions, employees, departments, artifacts, decisions, memories, events.
DB-style keyword search now; clean extension point for semantic search later.
"""
from __future__ import annotations


def search(query: str, *, collections: dict[str, list[dict]], limit: int = 50) -> list[dict]:
    q = query.lower().strip()
    if not q:
        return []
    results = []
    for kind, items in collections.items():
        for item in items:
            hay = " ".join(str(v) for v in item.values()
                           if isinstance(v, (str, int, float))).lower()
            if q in hay:
                results.append({"kind": kind, "item": item,
                                "label": item.get("title") or item.get("name")
                                         or item.get("decision") or item.get("id")})
    return results[:limit]
