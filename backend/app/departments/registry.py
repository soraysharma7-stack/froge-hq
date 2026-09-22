"""Departments — leads coordinate their areas; Maya remains overall orchestrator."""
from __future__ import annotations

from app.employees import registry as employees

_DEPARTMENTS: dict[str, dict] = {}


def _seed():
    defs = [
        ("orchestration", "Maya Office", "maya", ["orchestration", "planning"]),
        ("software_engineering", "Software Engineering", "alex", ["coding", "file_operations"]),
        ("qa", "QA", "sam", ["testing", "verification"]),
        ("security", "Security", "rex", ["policy_enforcement", "audit"]),
        ("ai_research", "AI Research", "casey", ["research", "analysis"]),
        ("business_ops", "Business / Product / Ops", "elena", ["cost_analysis", "planning"]),
        ("devops", "DevOps / Infrastructure", None, ["deployment", "monitoring"]),
        ("creative", "Creative / Media", None, ["content", "media"]),
        ("marketing", "Marketing / Growth", None, ["growth", "campaigns"]),
        ("science", "Science / Knowledge", None, ["research", "knowledge"]),
        ("space", "Space / Aerospace", None, ["aerospace"]),
        ("boardroom", "Boardroom", "maya", ["deliberation"]),
        ("monitoring", "Monitoring Room", None, ["telemetry"]),
        ("model_gateway", "Model Gateway", None, ["inference"]),
        ("memory_vault", "Memory Vault", None, ["memory"]),
        ("artifact_library", "Artifact Library", None, ["artifacts"]),
    ]
    for dept_id, name, lead, caps in defs:
        _DEPARTMENTS[dept_id] = {
            "id": dept_id,
            "name": name,
            "lead": lead,
            "capabilities": caps,
            "permissions": [],
            "mission_types": [],
        }


def list_departments() -> list[dict]:
    result = []
    for d in _DEPARTMENTS.values():
        members = [e.to_dict() for e in employees.all_employees() if e.department == d["id"]]
        result.append({**d, "employees": members,
                       "current_activity": [e["id"] for e in members if e["state"] == "ACTIVE"]})
    return result


def get(dept_id: str) -> dict | None:
    for d in list_departments():
        if d["id"] == dept_id:
            return d
    return None


_seed()
