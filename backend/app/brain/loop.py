"""Master agent loop — UNDERSTAND → CONTEXT → PLAN → PERMISSION → SKILL → TOOL →
EXECUTE → OBSERVE → VERIFY → CONTINUE/CORRECT/ESCALATE → FINAL RESULT.

Maya supervises: who/what/why/current step/tool/status/result/next action.
Emits structured decision summaries (no chain-of-thought) for every phase.
"""
from __future__ import annotations

import time
from typing import Any

from app.brain import confidence as confidence_mod
from app.brain import context as context_mod
from app.brain import planner, understand
from app.brain.executor import execute_step_with_recovery
from app.brain.messages import message as agent_message
from app.employees import registry as employees
from app.employees.registry import EmployeeState
from app.events.bus import bus, EventType
from app.memory import vault
from app.resources import governor


def _set_state(emp_id: str, state: EmployeeState) -> None:
    emp = employees.get(emp_id)
    if emp:
        emp.state = state


class BrainResult(dict):
    """What the loop returns to the mission manager."""


async def run_brain_loop(*, mission_id: str, objective: str, title: str,
                         content_builder, stop_check) -> BrainResult:
    """Run the full controlled agent loop for one mission."""
    supervision: list[dict[str, Any]] = []

    def supervise(who: str, what: str, why: str, step: str, tool: str | None,
                  status: str, result: str, next_action: str) -> None:
        supervision.append({
            "who": who, "what": what, "why": why, "current_step": step,
            "tool": tool, "status": status, "result": result, "next_action": next_action,
            "at": time.time(),
        })

    # Decision summary — structured, observable, no chain-of-thought.
    decision_log: list[dict[str, Any]] = []

    async def decide(stage: str, decision: str, reason: str,
                     confidence: str = "HIGH") -> None:
        entry = {"stage": stage, "decision": decision, "reason": reason,
                 "confidence": confidence, "at": time.time()}
        decision_log.append(entry)
        await bus.publish("DECISION_SUMMARY",
                          f"[{stage}] {decision}",
                          source="maya", mission_id=mission_id,
                          metadata={"stage": stage, "decision": decision,
                                    "reason": reason, "confidence": confidence})

    # 1. UNDERSTAND
    task = understand.understand(objective)
    await bus.publish(EventType.SYSTEM,
                      f"Maya understood task: {task['task_type']} ({task['complexity']})",
                      source="maya", mission_id=mission_id,
                      metadata={"task": task})
    supervise("maya", "understand objective", "structured task model", "UNDERSTAND",
              None, "done", task["task_type"], "collect context")
    await decide("UNDERSTAND",
                 f"Task is {task['task_type']} ({task['complexity']})",
                 f"requires_tools={task['requires_tools']}, verification={task['requires_verification']}")

    # 2. CONTEXT — relevance-filtered
    ctx = context_mod.collect(objective)
    supervise("maya", "collect context", "relevance-filtered retrieval", "CONTEXT",
              None, "done", f"{len(ctx['relevant_memories'])} memories", "plan")

    # Research upgrade: if the objective needs the live web, use the research plan.
    research = planner.is_research(objective)
    if research:
        task["task_type"] = "research"

    # 3. PLAN — smallest capable team, validated
    team = planner.smallest_capable_team(task)
    relative_path, content = content_builder(task)
    plan = planner.build_plan(task, mission_id, relative_path,
                              research_query=objective if research else None)
    problems = planner.validate_plan(plan)
    if problems:
        return BrainResult(ok=False, stage="plan_validation", errors=problems,
                           plan=plan, task=task, supervision=supervision)
    await bus.publish(EventType.PLAN_CREATED,
                      f"Maya planned {len(plan)} steps for: {title} (team: {', '.join(team)})",
                      source="maya", mission_id=mission_id,
                      metadata={"plan_steps": len(plan), "team": team})
    supervise("maya", "plan mission", f"{len(plan)} validated steps", "PLAN",
              None, "done", "plan valid", "check resources")
    await decide("PLAN",
                 f"{len(plan)} steps, team={', '.join(team)}",
                 "smallest capable team; every step validated against registries")

    # 4. RESOURCE CHECK — backend-enforced 5-agent hard limit
    active_count = sum(1 for e in employees.all_employees() if e.state == EmployeeState.ACTIVE)
    if not governor.can_activate(active_count):
        await governor.enqueue({"mission_id": mission_id, "title": title})
        supervise("maya", "resource check", "agent hard limit", "RESOURCE_CHECK",
                  None, "queued", "limit reached", "wait for slot")
        return BrainResult(ok=False, stage="queued", errors=["Resource limit — queued"],
                           plan=plan, task=task, supervision=supervision)

    # 5. EXECUTE steps in dependency order
    observations: list[dict] = []
    executed_ok = True
    verified = False
    errors: list[str] = []
    escalation = False

    for step in plan:
        if step["action"] == "plan":
            continue
        if stop_check():
            errors.append("STOP ALL engaged")
            executed_ok = False
            break

        emp_id = step["employee"]
        _set_state(emp_id, EmployeeState.ACTIVE)
        supervise(emp_id, step["objective"], f"plan step {step['step_id']}", "EXECUTE",
                  step.get("tool"), "running", "-", "execute tool")
        await bus.publish(EventType.AGENT_ACTIVATED,
                          f"{emp_id.capitalize()} activated for: {step['action']}",
                          source="maya", mission_id=mission_id, employee_id=emp_id)

        args: dict[str, Any] = {}
        if step["skill"] == "filesystem_write":
            args = {"relative_path": relative_path, "content": content}
        elif step["skill"] == "filesystem_append":
            args = {"relative_path": relative_path, "content": content}
        elif step["skill"] in ("filesystem_verify", "filesystem_read", "filesystem_delete"):
            args = {"relative_path": relative_path}
            if step["skill"] == "filesystem_verify":
                _set_state(emp_id, EmployeeState.WAITING)
        elif step["skill"] == "filesystem_list":
            args = {"relative_path": "."}
        elif step["skill"] == "web_search":
            args = {"query": step.get("query", objective), "max_results": 5}

        obs = await execute_step_with_recovery(step, mission_id=mission_id, args=args,
                                               stop_check=stop_check)
        observations.append(dict(obs))

        if obs["status"] == "SUCCESS":
            result = obs.get("result") or {}
            if step["skill"] == "filesystem_verify":
                verified = bool(result.get("verified"))
                supervise(emp_id, step["objective"], "QA evidence", "VERIFY",
                          step.get("tool"), "done",
                          f"verified={verified}", "report to maya")
                _set_state(emp_id, EmployeeState.SUCCESS if verified else EmployeeState.FAILED)
                await decide("VERIFY",
                             f"Artifact {'verified' if verified else 'NOT verified'}",
                             f"{result.get('bytes', '?')} bytes present in sandbox")
            elif step["skill"] == "web_search":
                supervise(emp_id, step["objective"], "live web data", "EXECUTE",
                          step.get("tool"), "done", f"{result.get('count', 0)} results",
                          "synthesize")
                _set_state(emp_id, EmployeeState.SUCCESS)
                await decide("RESEARCH",
                             f"Web search returned {result.get('count', 0)} results",
                             f"query='{step.get('query', '')[:60]}'")
            else:
                supervise(emp_id, step["objective"], "real artifact", "EXECUTE",
                          step.get("tool"), "done", f"{result.get('bytes', '?')} bytes",
                          "next step")
                _set_state(emp_id, EmployeeState.SUCCESS)
            step["status"] = "done"
        else:
            executed_ok = False
            step["status"] = "failed" if obs["status"] == "FAILED" else "blocked"
            errors.append(obs.get("error") or obs.get("summary") or "step failed")
            escalation = escalation or bool(obs.get("escalated"))
            supervise(emp_id, step["objective"], "step failure", "EXECUTE",
                      step.get("tool"), obs["status"], obs.get("error") or "failed",
                      "escalate to maya")
            _set_state(emp_id, EmployeeState.FAILED if obs["status"] == "FAILED" else EmployeeState.BLOCKED)
            break

    # 6. CONFIDENCE — evidence-based, never fabricated numbers
    grade = confidence_mod.grade(
        tool_ok=executed_ok, verified=verified, has_errors=bool(errors),
        memory_support=len(ctx["relevant_memories"]))
    await decide("COMPLETE" if executed_ok else "BLOCKED",
                 f"Mission {'completed' if executed_ok else 'incomplete'} — confidence {grade}",
                 "; ".join(errors) if errors else "all steps executed and verified",
                 confidence=grade)

    # 7. AGENT COMMUNICATION — structured result message back to Maya
    msg = agent_message(
        frm=team[-1] if len(team) > 1 else "maya", to="maya", mission_id=mission_id,
        type="RESULT", status="SUCCESS" if (executed_ok and verified) else (
            "PARTIAL_SUCCESS" if executed_ok else "FAILED"),
        summary=(f"Mission '{title}' executed; artifact verified."
                 if executed_ok and verified else
                 f"Mission '{title}' incomplete: {'; '.join(errors) or 'verification pending'}"),
        evidence=[f"{o['record']['tool_id']}: {o['status']}" for o in observations],
        confidence=grade)

    # 8. MEMORY — only if useful for future missions
    if executed_ok and verified:
        vault.store(f"Mission '{title}' completed with verified artifact (confidence {grade}).",
                    category=vault.Category.SUCCESSES, source="maya",
                    mission_id=mission_id, confidence=0.9)
    elif errors:
        vault.store(f"Mission '{title}' failure: {'; '.join(errors)[:200]}",
                    category=vault.Category.FAILURES, source="maya", mission_id=mission_id)

    return BrainResult(
        ok=executed_ok and verified, stage="completed" if executed_ok else "failed",
        plan=plan, task=task, team=team, observations=observations,
        verified=verified, errors=errors, escalated=escalation,
        confidence=grade, agent_message=msg, supervision=supervision,
        artifact_path=relative_path, decision_log=decision_log, research=research,
    )
