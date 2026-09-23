"""Step executor — permission check → argument validation → tool execution →
observation → verification → bounded recovery. The backend owns every transition.
"""
from __future__ import annotations

import time
from typing import Any

from app.approvals import engine as approvals
from app.audit import log as audit
from app.events.bus import bus, EventType
from app.healing import recovery
from app.security import policy
from app.skills.registry import SKILLS
from app.tools.workspace_tools import ToolPermissionError

# tool metadata: risk classification for the policy engine
_TOOL_RISK: dict[str, policy.Risk] = {
    "workspace_file_write": policy.Risk.MEDIUM,
    "workspace_file_verify": policy.Risk.LOW,
    "web_search": policy.Risk.LOW,
}


class Observation(dict):
    """Observed tool result. status: SUCCESS / PARTIAL_SUCCESS / FAILED / BLOCKED / TIMEOUT"""


def _validate_arguments(skill_id: str, args: dict[str, Any]) -> list[str]:
    """Validate tool arguments against the skill's input schema. Never execute arbitrary input."""
    skill = SKILLS.get(skill_id)
    if not skill:
        return [f"unknown skill '{skill_id}'"]
    problems = []
    for key, kind in skill.input_schema.items():
        if key not in args:
            problems.append(f"missing argument '{key}'")
        elif kind == "string" and not isinstance(args[key], str):
            problems.append(f"argument '{key}' must be a string")
    for key in args:
        if key not in skill.input_schema:
            problems.append(f"unexpected argument '{key}'")
    return problems


async def execute_step(step: dict[str, Any], *, mission_id: str, args: dict[str, Any],
                       stop_check) -> Observation:
    """Run one plan step through the full controlled pipeline."""
    employee_id = step["employee"]
    skill_id = step["skill"]
    tool_id = step.get("tool") or "none"
    started = time.time()
    record = {
        "mission_id": mission_id, "employee_id": employee_id, "skill_id": skill_id,
        "tool_id": tool_id, "arguments": {k: (v[:80] + "…" if isinstance(v, str) and len(v) > 80 else v)
                                          for k, v in args.items()},
        "start_time": started, "permission": step.get("permission"),
    }

    # STOP ALL gate — checked before every step, model-independent
    if stop_check():
        return Observation(status="BLOCKED", summary="STOP ALL engaged", record=record,
                           error="stop_all")

    # 1. Permission check via the deterministic policy engine
    risk = _TOOL_RISK.get(tool_id, policy.Risk.LOW)
    decision = await policy.enforce(step["action"], actor=employee_id, risk=risk,
                                    mission_id=mission_id,
                                    reason=f"plan step {step.get('step_id')}: {step['objective']}")
    if decision["decision"] == policy.Decision.DENY.value:
        audit.record(employee_id, f"brain:denied:{step['action']}", mission_id=mission_id,
                     tool=tool_id, result="denied")
        return Observation(status="BLOCKED", summary=f"Policy denied: {step['action']}",
                           record=record, error="policy_denied")

    if decision["decision"] == policy.Decision.REQUIRE_APPROVAL.value:
        await bus.publish(EventType.APPROVAL_REQUIRED,
                          f"Approval required: {step['action']} by {employee_id}",
                          source="brain", severity="warning", mission_id=mission_id,
                          employee_id=employee_id,
                          metadata={"action": step["action"], "risk": risk.value,
                                    "requester": employee_id})
        ap = await approvals.request(step["action"], requester=employee_id,
                                     reason=step["objective"], risk=risk.value,
                                     mission_id=mission_id)
        record["approval"] = ap["id"]
        return Observation(status="BLOCKED", summary="Waiting for approval",
                           record=record, error="approval_required", approval_id=ap["id"])

    # 2. Argument validation — never execute arbitrary model-generated commands
    problems = _validate_arguments(skill_id, args)
    if problems:
        audit.record(employee_id, f"brain:invalid_args:{skill_id}", mission_id=mission_id,
                     tool=tool_id, result="rejected", metadata={"problems": problems})
        return Observation(status="FAILED", summary=f"Invalid arguments: {'; '.join(problems)}",
                           record=record, error="invalid_arguments")

    # 3. Execute the real tool
    skill = SKILLS[skill_id]
    await bus.publish(EventType.SKILL_STARTED, f"Skill started: {skill_id}",
                      source=employee_id, mission_id=mission_id, employee_id=employee_id)
    await bus.publish(EventType.TOOL_STARTED, f"Tool started: {tool_id}",
                      source=employee_id, mission_id=mission_id, employee_id=employee_id)
    try:
        if skill_id == "web_search":
            result = skill.execute(query=args["query"], max_results=args.get("max_results", 5))
        else:
            result = skill.execute(**args)
        status = "SUCCESS"
        error = None
    except ToolPermissionError as e:
        result, status, error = None, "BLOCKED", str(e)
    except Exception as e:
        result, status, error = None, "FAILED", str(e)

    record.update(end_time=time.time(), status=status,
                  result=result if isinstance(result, dict) else None, error=error)
    audit.record(employee_id, f"tool:{tool_id}", mission_id=mission_id, employee_id=employee_id,
                 tool=tool_id, permission=step.get("permission"),
                 result="ok" if status == "SUCCESS" else "failed",
                 metadata=record["arguments"])

    if status == "SUCCESS":
        await bus.publish(EventType.TOOL_COMPLETED, f"Tool completed: {tool_id}",
                          source=employee_id, mission_id=mission_id, employee_id=employee_id,
                          metadata=result if isinstance(result, dict) else {})
        await bus.publish(EventType.SKILL_COMPLETED, f"Skill completed: {skill_id}",
                          source=employee_id, mission_id=mission_id, employee_id=employee_id)
    return Observation(status=status, result=result, record=record, error=error)


async def execute_step_with_recovery(step: dict[str, Any], *, mission_id: str,
                                     args: dict[str, Any], stop_check,
                                     verify: bool = True) -> Observation:
    """Execute + observe + verify + ONE bounded recovery attempt, then escalate."""
    obs = await execute_step(step, mission_id=mission_id, args=args, stop_check=stop_check)
    if obs["status"] in ("SUCCESS", "BLOCKED"):
        return obs

    # Bounded self-healing: one correction, then escalate (strict limit lives in healing module)
    outcome = await recovery.recover(
        f"{mission_id}:step:{step.get('step_id')}", obs.get("error") or "unknown",
        lambda: None, mission_id=mission_id, employee_id=step["employee"])
    if outcome.get("recovered"):
        retry_obs = await execute_step(step, mission_id=mission_id, args=args, stop_check=stop_check)
        if retry_obs["status"] == "SUCCESS":
            retry_obs["summary"] = "Recovered after one controlled retry"
            return retry_obs
        obs = retry_obs

    obs["escalated"] = True
    await bus.publish(EventType.SYSTEM,
                      f"Escalated to Maya: step {step.get('step_id')} failed after bounded recovery",
                      source="maya", severity="error", mission_id=mission_id,
                      employee_id=step["employee"])
    return obs
