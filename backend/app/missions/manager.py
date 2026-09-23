"""Mission manager + Maya orchestration — full lifecycle.

USER → MAYA → MISSION → EMPLOYEE → SKILL → REAL TOOL → WS EVENTS → QA → RESULT → MEMORY/ARTIFACT/AUDIT
Simulation mode, mission replay, time-machine snapshots, STOP ALL, reputation, cost.
Execution runs through the Agent Brain loop (app/brain/).
"""
from __future__ import annotations

import time
import uuid
from enum import Enum
from typing import Any

from app.artifacts import library as artifacts
from app.audit import log as audit
from app.cost import tracker as cost
from app.employees import registry as employees
from app.employees.registry import EmployeeState
from app.events.bus import bus, EventType
from app.knowledge import graph as kgraph
from app.memory import vault
from app.model_gateway.gateway import gateway, ModelRequest
from app.reputation import tracker as reputation
from app.resources import governor
from app.skills.registry import SKILLS
from app.tools.workspace_tools import ToolPermissionError, workspace_file_verify
from app.brain import loop as brain_loop


class MissionStatus(str, Enum):
    DRAFT = "DRAFT"
    PLANNING = "PLANNING"
    WAITING_APPROVAL = "WAITING_APPROVAL"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    BLOCKED = "BLOCKED"
    REVIEW = "REVIEW"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class Mission:
    def __init__(self, title: str, objective: str, requester: str = "user",
                 priority: str = "normal", simulate: bool = False):
        self.id = str(uuid.uuid4())[:8]
        self.title = title
        self.objective = objective
        self.requester = requester
        self.priority = priority
        self.simulate = simulate
        self.status = MissionStatus.DRAFT
        self.plan: list[dict] = []
        self.current_step: int = 0
        self.active_employees: list[str] = []
        self.dependencies: list[str] = []
        self.estimated_cost: float | None = None
        self.actual_cost: float | None = None
        self.confidence: float | None = None
        self.outputs: dict[str, Any] = {}
        self.approvals: list[str] = []
        self.errors: list[str] = []
        self.timeline: list[dict] = []   # mission replay — read-only record
        self.created_at = time.time()
        self.updated_at = self.created_at
        self.completed_at: float | None = None
        self.final_summary: str | None = None

    def touch(self):
        self.updated_at = time.time()
        if MISSIONS.get(self.id) is self:
            _persist(self)

    def log(self, step: str, detail: str = ""):
        self.timeline.append({"t": time.time(), "step": step, "detail": detail})

    def to_dict(self) -> dict:
        return {
            "id": self.id, "title": self.title, "objective": self.objective,
            "requester": self.requester, "priority": self.priority,
            "simulate": self.simulate,
            "status": self.status.value, "plan": self.plan,
            "current_step": self.current_step,
            "active_employees": self.active_employees,
            "dependencies": self.dependencies,
            "estimated_cost": self.estimated_cost, "actual_cost": self.actual_cost,
            "elapsed_time": round((self.completed_at or time.time()) - self.created_at, 2),
            "confidence": self.confidence, "outputs": self.outputs,
            "approvals": self.approvals, "errors": self.errors,
            "timeline": self.timeline,
            "created_at": self.created_at, "updated_at": self.updated_at,
            "completed_at": self.completed_at, "final_summary": self.final_summary,
        }


MISSIONS: dict[str, Mission] = {}
_SNAPSHOTS: list[dict] = []   # time machine


def _persist(mission: Mission) -> None:
    """Durable save of one mission (best-effort, never crashes the run)."""
    try:
        from app.core import persistence
        persistence.save(persistence.TABLE_MISSIONS, mission.id, mission.to_dict())
    except Exception:
        pass


def restore(doc: dict) -> None:
    """Rebuild a mission object from durable storage at startup."""
    m = Mission(doc["title"], doc["objective"], requester=doc.get("requester", "user"),
                priority=doc.get("priority", "normal"), simulate=doc.get("simulate", False))
    m.id = doc["id"]
    m.status = MissionStatus(doc["status"])
    m.plan = doc.get("plan", [])
    m.current_step = doc.get("current_step", 0)
    m.active_employees = doc.get("active_employees", [])
    m.dependencies = doc.get("dependencies", [])
    m.estimated_cost = doc.get("estimated_cost", 0.0)
    m.actual_cost = doc.get("actual_cost", 0.0)
    m.confidence = doc.get("confidence", 0.0)
    m.outputs = doc.get("outputs", {})
    m.approvals = doc.get("approvals", [])
    m.errors = doc.get("errors", [])
    m.timeline = doc.get("timeline", [])
    m.created_at = doc.get("created_at", time.time())
    m.updated_at = doc.get("updated_at", m.created_at)
    m.completed_at = doc.get("completed_at")
    m.final_summary = doc.get("final_summary")
    MISSIONS[m.id] = m


def list_missions() -> list[dict]:
    return [m.to_dict() for m in sorted(MISSIONS.values(), key=lambda m: m.created_at, reverse=True)]


def get_mission(mission_id: str) -> Mission | None:
    return MISSIONS.get(mission_id)


def replay(mission_id: str) -> list[dict] | None:
    """Read-only timeline replay. Never re-executes tools."""
    m = MISSIONS.get(mission_id)
    return m.timeline if m else None


def _snapshot():
    _SNAPSHOTS.append({
        "timestamp": time.time(),
        "missions": [{"id": m.id, "status": m.status.value} for m in MISSIONS.values()],
        "employees": [{"id": e.id, "state": e.state.value} for e in employees.all_employees()],
        "stop_all": governor.stop_all_engaged(),
        "mode": governor.mode(),
    })
    del _SNAPSHOTS[:-200]


def time_machine(limit: int = 50) -> list[dict]:
    return list(reversed(_SNAPSHOTS[-limit:]))


def simulate_plan(title: str, objective: str) -> dict:
    """Simulation mode — plan only, NO execution. Clearly labeled non-execution."""
    return {
        "simulation": True,
        "warning": "SIMULATION — nothing will be executed.",
        "title": title,
        "plan": [
            {"step": 1, "owner": "maya", "action": "plan"},
            {"step": 2, "owner": "alex", "action": "filesystem_write",
             "skill": "filesystem_write", "tool": "workspace_file_write",
             "permissions": ["workspace:write"]},
            {"step": 3, "owner": "sam", "action": "filesystem_verify",
             "skill": "filesystem_verify", "permissions": ["workspace:read"]},
        ],
        "risk": "LOW",
        "estimated_resources": {"agents": 2, "tool_calls": 2, "estimated_duration_s": 2},
        "cost_preview": cost.preview(estimated_tokens=None, estimated_duration_s=2,
                                     requires_approval=False, risks=["none identified"]),
        "actions": ["RUN", "EDIT PLAN", "CANCEL"],
    }


async def run_mission(title: str, objective: str, *, simulate: bool = False) -> Mission:
    mission = Mission(title=title, objective=objective, simulate=simulate)
    MISSIONS[mission.id] = mission
    _persist(mission)
    mission.log("MISSION_CREATED", title)
    kgraph.add_node("mission", mission.id, title)
    started = time.time()

    await bus.publish(EventType.MISSION_CREATED, f"Mission created: {title}",
                      source="maya", mission_id=mission.id)
    audit.record("user", f"mission_created:{title}", mission_id=mission.id)

    # STOP ALL gate — deterministic, Maya cannot override
    if governor.stop_all_engaged():
        mission.status = MissionStatus.PAUSED
        mission.errors.append("STOP ALL engaged — mission paused before start")
        mission.log("BLOCKED", "STOP ALL engaged")
        await bus.publish(EventType.MISSION_PAUSED, "STOP ALL engaged — mission paused",
                          source="governor", severity="warning", mission_id=mission.id)
        return mission

    maya = employees.get("maya")
    alex = employees.get("alex")
    sam = employees.get("sam")

    try:
        # 1. MAYA PLANS (brain loop: understand → context → plan)
        mission.status = MissionStatus.PLANNING
        mission.touch()
        mission.log("MAYA_PLANNED", "planning started")
        if maya:
            maya.state = EmployeeState.ACTIVE
        mission.active_employees = ["maya"]
        _snapshot()

        model_resp = await gateway.complete(ModelRequest(
            prompt=f"Plan mission: {objective}", mission_id=mission.id, employee_id="maya"))
        cost.record_usage(model=None, provider=None, mission_id=mission.id,
                          employee_id="maya", department="orchestration",
                          duration_ms=model_resp.latency_ms, tokens=model_resp.usage)

        def _content_builder(task: dict) -> tuple[str, str]:
            path = f"missions/{mission.id}/report.md"
            body = (
                f"# Mission Report — {mission.title}\n\n"
                f"- Mission ID: {mission.id}\n- Objective: {mission.objective}\n"
                f"- Task type: {task['task_type']} ({task['complexity']})\n"
                f"- Requester: {mission.requester}\n- Orchestrated by: Maya\n"
                f"- Executed via: Agent Brain loop (validated skills + tools)\n"
                f"- Status: EXECUTED (real tool execution, workspace sandbox)\n"
            )
            return path, body

        # 2–5. BRAIN LOOP executes: permission → skill/tool validate → execute →
        # observe → verify → bounded recovery → escalate. Backend owns every step.
        if simulate:
            mission.status = MissionStatus.COMPLETED
            mission.completed_at = time.time()
            mission.final_summary = "SIMULATION COMPLETE — no execution performed."
            mission.outputs["simulation"] = simulate_plan(title, objective)
            mission.touch()
            if maya:
                maya.state = EmployeeState.AVAILABLE
            return mission

        mission.status = MissionStatus.RUNNING
        mission.touch()
        result = await brain_loop.run_brain_loop(
            mission_id=mission.id, objective=objective, title=title,
            content_builder=_content_builder,
            stop_check=governor.stop_all_engaged)

        mission.plan = result.get("plan", [])
        mission.outputs["brain"] = {
            "task": result.get("task"), "team": result.get("team"),
            "confidence": result.get("confidence"),
            "observations": [
                {"status": o.get("status"), "summary": o.get("summary"),
                 "tool": o.get("record", {}).get("tool_id")}
                for o in result.get("observations", [])
            ],
            "supervision": result.get("supervision", []),
            "agent_message": result.get("agent_message"),
            "escalated": result.get("escalated", False),
        }

        if result.get("stage") == "queued":
            mission.status = MissionStatus.PAUSED
            mission.errors.append("Resource limit — queued")
            mission.log("QUEUED", "resource limit")
            mission.touch()
            if maya:
                maya.state = EmployeeState.AVAILABLE
            return mission
        if result.get("stage") == "plan_validation":
            raise RuntimeError("Plan failed validation: " + "; ".join(result.get("errors", [])))

        for obs in result.get("observations", []):
            rec = obs.get("record", {})
            emp = rec.get("employee_id")
            if emp and emp != "maya":
                mission.log("EMPLOYEE_ACTIVATED", emp)
            if rec.get("tool_id") and obs.get("status") == "SUCCESS":
                res = obs.get("result") or {}
                mission.log("TOOL_EXECUTED", res.get("path", rec["tool_id"]))

        artifact_obs = next(
            (o for o in result.get("observations", []) if o.get("result", {}) and "path" in (o.get("result") or {})),
            None)
        if artifact_obs:
            mission.outputs["artifact"] = artifact_obs["result"]
        mission.outputs["qa_evidence"] = {
            "verified": result.get("verified", False),
            "path": result.get("artifact_path"),
        }

        if not result.get("ok"):
            raise RuntimeError("; ".join(result.get("errors", ["mission incomplete"])))
        mission.log("QA_VERIFIED", result.get("artifact_path", ""))

        # 6. COMPLETE — artifact, memory, reputation, cost
        mission.status = MissionStatus.COMPLETED
        mission.completed_at = time.time()
        mission.confidence = {"HIGH": 1.0, "MEDIUM": 0.66, "LOW": 0.33}.get(
            result.get("confidence", "LOW"), 0.33)
        mission.final_summary = (
            f"Mission completed via Agent Brain. Artifact verified at "
            f"{result.get('artifact_path')}. Confidence: {result.get('confidence')}. "
            f"Team: {', '.join(result.get('team', []))}."
        )
        mission.log("MISSION_COMPLETED", mission.final_summary)
        mission.touch()
        mission.active_employees = []
        if maya:
            maya.state = EmployeeState.AVAILABLE

        artifacts.create("REPORT", f"Mission Report — {title}", creator="alex",
                         location=result.get("artifact_path", ""), mission_id=mission.id)
        duration = mission.completed_at - started
        reputation.record_outcome("alex", success=True, duration_s=duration)
        reputation.record_outcome("sam", success=True, duration_s=0.1)
        _snapshot()
        await bus.publish(EventType.MISSION_COMPLETED, mission.final_summary,
                          source="maya", mission_id=mission.id)

    except ToolPermissionError as e:
        mission.status = MissionStatus.BLOCKED
        mission.errors.append(str(e))
        mission.log("BLOCKED", str(e))
        mission.touch()
        vault.store(f"Security block: {e}", category=vault.Category.SECURITY_RULES,
                    source="security", mission_id=mission.id)
        reputation.record_outcome("alex", success=False, security_problem=True)
        await bus.publish(EventType.SECURITY_BLOCK, str(e), source="security",
                          severity="warning", mission_id=mission.id)
    except Exception as e:  # bounded failure — no infinite loops
        mission.status = MissionStatus.FAILED
        mission.errors.append(str(e))
        mission.completed_at = time.time()
        mission.log("MISSION_FAILED", str(e))
        mission.touch()
        mission.active_employees = []
        if maya:
            maya.state = EmployeeState.AVAILABLE
        vault.store(f"Mission failure: {e}", category=vault.Category.FAILURES,
                    source="maya", mission_id=mission.id)
        reputation.record_outcome("alex", success=False)
        _snapshot()
        await bus.publish(EventType.MISSION_FAILED, f"Mission failed: {e}",
                          source="maya", severity="error", mission_id=mission.id)

    return mission


async def pause_mission(mission_id: str) -> Mission | None:
    m = MISSIONS.get(mission_id)
    if m and m.status == MissionStatus.RUNNING:
        m.status = MissionStatus.PAUSED
        m.log("MISSION_PAUSED", "paused by user")
        m.touch()
        await bus.publish(EventType.MISSION_PAUSED, f"Mission paused: {m.title}",
                          source="user", mission_id=m.id)
    return m


async def cancel_mission(mission_id: str) -> Mission | None:
    m = MISSIONS.get(mission_id)
    if m and m.status in (MissionStatus.RUNNING, MissionStatus.PAUSED, MissionStatus.PLANNING):
        m.status = MissionStatus.CANCELLED
        m.completed_at = time.time()
        m.log("MISSION_CANCELLED", "cancelled by user")
        m.touch()
        await bus.publish(EventType.SYSTEM, f"Mission cancelled: {m.title}",
                          source="user", severity="warning", mission_id=m.id)
    return m
