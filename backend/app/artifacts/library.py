"""Artifact Library — versioned outputs with provenance."""
from __future__ import annotations

import time
import uuid

_ARTIFACTS: dict[str, dict] = {}


def create(type: str, title: str, *, creator: str, location: str,
           mission_id: str | None = None, project_id: str | None = None,
           status: str = "FINAL") -> dict:
    now = time.time()
    art = {
        "id": str(uuid.uuid4())[:8],
        "type": type,
        "title": title,
        "mission_id": mission_id,
        "project_id": project_id,
        "creator": creator,
        "version": 1,
        "location": location,
        "status": status,
        "created_at": now,
        "updated_at": now,
        "history": [{"version": 1, "timestamp": now, "note": "created"}],
    }
    _ARTIFACTS[art["id"]] = art
    from app.core import persistence
    persistence.save(persistence.TABLE_ARTIFACTS, art["id"], art)
    return art


def new_version(artifact_id: str, *, note: str = "", location: str | None = None) -> dict | None:
    art = _ARTIFACTS.get(artifact_id)
    if not art:
        return None
    art["version"] += 1
    if location:
        art["location"] = location
    art["updated_at"] = time.time()
    art["history"].append({"version": art["version"], "timestamp": art["updated_at"],
                           "note": note or "updated"})
    return art


def list_artifacts(type: str | None = None) -> list[dict]:
    items = list(_ARTIFACTS.values())
    if type:
        items = [a for a in items if a["type"] == type]
    return sorted(items, key=lambda a: a["created_at"], reverse=True)


def get(artifact_id: str) -> dict | None:
    return _ARTIFACTS.get(artifact_id)
