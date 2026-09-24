"""Prompt Compiler — ONE universal template + the roster data table.

Every one of the 115 employees uses the same template; only {NAME}, {ROLE},
{DEPARTMENT}, and {SPECIALTY_ONE_LINE} change, pulled from app/employees/roster.py.
Idle employees cost nothing — this only runs when Maya routes a task to them.
"""
from __future__ import annotations

import time

from app.employees import roster as roster_mod

PROMPT_VERSION = "1.1.0"
_compilations: list[dict] = []

_UNIVERSAL_TEMPLATE = """You are {NAME}, {ROLE} in the {DEPARTMENT} department at FROGÉ HQ.

SPECIALTY: {SPECIALTY}

You inherit the Global Agent Rules: never invent results, never act outside your
CapabilityScope, never claim completion without verification, always distinguish
COMPLETED / PENDING / BLOCKED / FAILED honestly. Be concise and direct.

REASONING PROCESS:
1. Understand exactly what's being asked within your specialty.
2. Check whether it falls within your CapabilityScope and permission tier — if not,
   stop and report rather than attempting a workaround.
3. Do the smallest useful action that accomplishes the task.
4. Verify the result actually happened before reporting it.
5. Report honestly: what you did, what you verified, and anything uncertain.

You are IDLE unless Maya has specifically activated you for a task within your
specialty. Do not act unless routed to you."""


def compile_prompt(*, employee: dict, mission: dict | None = None,
                   memories: list[dict] | None = None,
                   skills: list[str] | None = None,
                   output_requirements: str | None = None) -> dict:
    """Assemble the full prompt for one employee on one task.

    `employee` may be a full registry dict OR just {"id": "..."} — the roster
    fills the rest. Returns the rendered prompt text + metadata.
    """
    emp_id = employee.get("id", "")
    roster_row = roster_mod.by_id(emp_id) or {}
    name = employee.get("name") or roster_row.get("name") or emp_id
    role = employee.get("role") or roster_row.get("role") or "Agent"
    department = employee.get("department") or roster_row.get("department") or "general"
    specialty = roster_row.get("specialty") or employee.get("role") or "general task execution"

    system_prompt = _UNIVERSAL_TEMPLATE.format(
        NAME=name, ROLE=role, DEPARTMENT=department, SPECIALTY=specialty,
    )

    memory_lines = [m.get("content", "") for m in (memories or [])][:5]
    task_context = ""
    if mission:
        task_context = (
            f"\n\nCURRENT TASK: {mission.get('title', '')}\n"
            f"OBJECTIVE: {mission.get('objective', '')}"
        )
    if memory_lines:
        task_context += "\n\nRELEVANT MEMORY:\n" + "\n".join(f"- {m}" for m in memory_lines)
    if skills:
        task_context += f"\n\nYOUR SKILLS: {', '.join(skills)}"
    if output_requirements:
        task_context += f"\n\nOUTPUT: {output_requirements}"

    record = {
        "version": PROMPT_VERSION,
        "employee_id": emp_id,
        "name": name,
        "role": role,
        "department": department,
        "specialty": specialty,
        "timestamp": time.time(),
        "system_prompt": system_prompt + task_context,
        "from_roster": bool(roster_row),
    }
    _compilations.append(record)
    return record


def compile_for_employee_id(employee_id: str, *, mission: dict | None = None) -> dict | None:
    """Compile a prompt for any roster employee by id (even if not a live registry member)."""
    row = roster_mod.by_id(employee_id)
    if not row:
        return None
    return compile_prompt(employee={"id": employee_id}, mission=mission)


def roster_summary() -> dict:
    return {
        "total_agents": len(roster_mod.ROSTER),
        "leads": [r["name"] for r in roster_mod.leads()],
        "departments": sorted({r["department"] for r in roster_mod.ROSTER}),
    }


def version() -> str:
    return PROMPT_VERSION
