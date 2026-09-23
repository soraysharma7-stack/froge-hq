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
    "verification": [
        {"action": "filesystem_verify", "owner": "sam", "skill": "filesystem_verify",
         "tool": "workspace_file_verify", "permission": "workspace:read"},
    ],
    "engineering": [
        {"action": "filesystem_write", "owner": "alex", "skill": "filesystem_write",
         "tool": "workspace_file_write", "permission": "workspace:write"},
        {"action": "filesystem_verify", "owner": "sam", "skill": "filesystem_verify",
         "tool": "workspace_file_verify", "permission": "workspace:read"},
    ],
    "general": [
        {"action": "filesystem_write", "owner": "alex", "skill": "filesystem_write",
         "tool": "workspace_file_write", "permission": "workspace:write"},
        {"action": "filesystem_verify", "owner": "sam", "skill": "filesystem_verify",
         "tool": "workspace_file_verify", "permission": "workspace:read"},
    ],
}


def smallest_capable_team(task: dict[str, Any]) -> list[str]:
    """Pick the minimal set of employees for the task. Never activate unnecessary agents."""
    team = ["maya"]
    steps = _TASK_STEP_TEMPLATES.get(task["task_type"], _TASK_STEP_TEMPLATES["general"])
    for step in steps:
        if step["owner"] not in team:
            team.append(step["owner"])
    return team


def build_plan(task: dict[str, Any], mission_id: str, target_path: str) -> list[dict[str, Any]]:
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
        steps.append(
            {
                "step_id": i,
                "objective": f"{t['action']} on {target_path}",
                "action": t["action"],
                "employee": t["owner"],
                "skill": t["skill"],
                "tool": t["tool"],
                "target": target_path,
                "dependencies": [prev_id],
                "permission": t["permission"],
                "status": "pending",
            }
        )
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
