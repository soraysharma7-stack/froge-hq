"""Planner — stage 3. Maya's structured plan: steps with employee, skill, tool,
dependencies, permission and status. The planner picks the SMALLEST capable team.
"""
from __future__ import annotations

from typing import Any

from app.employees import registry as employees

# Deterministic capability → step templates. The model may propose a plan through
# the gateway, but the backend validates every step against the registries.
_TASK_STEP_TEMPLATES: dict[str, list[dict[str, Any]]] = {
    "content_generation": [
        {"action": "filesystem_write", "owner": "alex", "skill": "filesystem_write",
         "tool": "workspace_file_write", "permission": "workspace:write"},
        {"action": "filesystem_verify", "owner": "sam", "skill": "filesystem_verify",
         "tool": "workspace_file_verify", "permission": "workspace:read"},
    ],
    "research": [
        {"action": "web_search", "owner": "nova", "skill": "web_search",
         "tool": "web_search", "permission": "web:search"},
        {"action": "filesystem_write", "owner": "alex", "skill": "filesystem_write",
         "tool": "workspace_file_write", "permission": "workspace:write"},
        {"action": "filesystem_verify", "owner": "sam", "skill": "filesystem_verify",
         "tool": "workspace_file_verify", "permission": "workspace:read"},
    ],
    "verification": [
        {"action": "filesystem_verify", "owner": "sam", "skill": "filesystem_verify",
         "tool": "workspace_file_verify", "permission": "workspace:read"},
    ],
    "engineering": [
        {"action": "filesystem_list", "owner": "alex", "skill": "filesystem_list",
         "tool": "workspace_list_dir", "permission": "workspace:read"},
        {"action": "filesystem_write", "owner": "alex", "skill": "filesystem_write",
         "tool": "workspace_file_write", "permission": "workspace:write"},
        {"action": "filesystem_verify", "owner": "sam", "skill": "filesystem_verify",
         "tool": "workspace_file_verify", "permission": "workspace:read"},
    ],
    "file_read": [
        {"action": "filesystem_read", "owner": "alex", "skill": "filesystem_read",
         "tool": "workspace_file_read", "permission": "workspace:read"},
    ],
    "general": [
        {"action": "filesystem_write", "owner": "alex", "skill": "filesystem_write",
         "tool": "workspace_file_write", "permission": "workspace:write"},
        {"action": "filesystem_verify", "owner": "sam", "skill": "filesystem_verify",
         "tool": "workspace_file_verify", "permission": "workspace:read"},
    ],
}


_RESEARCH_HINTS = ("research", "search", "look up", "find out", "latest", "news",
                    "current", "who is", "what is", "web")


def is_research(objective: str) -> bool:
    text = objective.lower()
    return any(h in text for h in _RESEARCH_HINTS)


def smallest_capable_team(task: dict[str, Any]) -> list[str]:
    """Pick the minimal set of employees for the task. Never activate unnecessary agents."""
    team = ["maya"]
    steps = _TASK_STEP_TEMPLATES.get(task["task_type"], _TASK_STEP_TEMPLATES["general"])
    for step in steps:
        if step["owner"] not in team:
            team.append(step["owner"])
    return team


def build_plan(task: dict[str, Any], mission_id: str, target_path: str,
               research_query: str | None = None) -> list[dict[str, Any]]:
    """Structured plan with validated steps. Each step: id/objective/employee/skill/tool/
    dependencies/permission/status."""
    steps: list[dict[str, Any]] = [
        {
            "step_id": 1,
            "objective": "Understand objective and plan execution",
            "action": "plan",
            "employee": "maya",
            "skill": "mission_planning",
            "tool": None,
            "dependencies": [],
            "permission": None,
            "status": "done",
        }
    ]
    template = _TASK_STEP_TEMPLATES.get(task["task_type"], _TASK_STEP_TEMPLATES["general"])
    prev_id = 1
    for i, t in enumerate(template, start=2):
        step: dict[str, Any] = {
            "step_id": i,
            "objective": (f"web search: {research_query}" if t["skill"] == "web_search"
                          else f"{t['action']} on {target_path}"),
            "action": t["action"],
            "employee": t["owner"],
            "skill": t["skill"],
            "tool": t["tool"],
            "target": target_path,
            "dependencies": [prev_id],
            "permission": t["permission"],
            "status": "pending",
        }
        if t["skill"] == "web_search" and research_query:
            step["query"] = research_query
        steps.append(step)
        prev_id = i
    return steps


def validate_plan(plan: list[dict[str, Any]]) -> list[str]:
    """Backend validation of a plan — every employee and skill must exist and be permitted."""
    problems: list[str] = []
    from app.skills.registry import SKILLS

    for step in plan:
        emp = employees.get(step.get("employee", ""))
        if not emp:
            problems.append(f"step {step.get('step_id')}: unknown employee '{step.get('employee')}'")
            continue
        skill = step.get("skill")
        if skill and skill != "mission_planning":
            if skill not in SKILLS:
                problems.append(f"step {step.get('step_id')}: unknown skill '{skill}'")
            elif skill not in emp.skills:
                problems.append(f"step {step.get('step_id')}: employee '{emp.id}' lacks skill '{skill}'")
    return problems
