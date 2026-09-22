"""Mission manager + Maya orchestration — full lifecycle.

USER → MAYA → MISSION → EMPLOYEE → SKILL → REAL TOOL → WS EVENTS → QA → RESULT → MEMORY/ARTIFACT/AUDIT
Simulation mode, mission replay, time-machine snapshots, STOP ALL, reputation, cost.
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
        # 1. MAYA PLANS
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

        mission.plan = [
            {"step": 1, "owner": "maya", "action": "plan", "status": "done"},
            {"step": 2, "owner": "alex", "action": "filesystem_write",
             "target": f"missions/{mission.id}/report.md", "status": "pending"},
            {"step": 3, "owner": "sam", "action": "filesystem_verify",
             "target": f"missions/{mission.id}/report.md", "status": "pending"},
        ]
        await bus.publish(EventType.PLAN_CREATED, f"Maya planned 3 steps for: {title}",
                          source="maya", mission_id=mission.id,
                          metadata={"model_status": "error" if model_resp.error else "ok"})
        mission.log("MAYA_PLANNED", "3 steps")

        if simulate:
            mission.status = MissionStatus.COMPLETED
            mission.completed_at = time.time()
            mission.final_summary = "SIMULATION COMPLETE — no execution performed."
            mission.outputs["simulation"] = simulate_plan(title, objective)
            mission.touch()
            if maya:
                maya.state = EmployeeState.AVAILABLE
            return mission

        # 2. ALEX EXECUTES (real tool, sandboxed) — resource-governed
        active_count = sum(1 for e in employees.all_employees() if e.state == EmployeeState.ACTIVE)
        if not governor.can_activate(active_count):
            await governor.enqueue({"mission_id": mission.id, "title": title})
            mission.status = MissionStatus.PAUSED
            mission.errors.append("Resource limit — queued")
            mission.log("QUEUED", "resource limit")
            mission.touch()
            if maya:
                maya.state = EmployeeState.AVAILABLE
            return mission

        mission.status = MissionStatus.RUNNING
        mission.current_step = 2
        mission.touch()
        if maya:
            maya.state = EmployeeState.WAITING
        if alex:
            alex.state = EmployeeState.ACTIVE
        mission.active_employees = ["alex"]
        _snapshot()
        await bus.publish(EventType.AGENT_ACTIVATED, "Alex activated (Software Engineer)",
                          source="maya", mission_id=mission.id, employee_id="alex")
        mission.log("EMPLOYEE_ACTIVATED", "alex")

        write_skill = SKILLS["filesystem_write"]
        report_content = (
            f"# Mission Report — {mission.title}\n\n"
            f"- Mission ID: {mission.id}\n- Objective: {mission.objective}\n"
            f"- Requester: {mission.requester}\n- Orchestrated by: Maya\n"
            f"- Executed by: Alex (filesystem_write skill)\n"
            f"- Status: EXECUTED (real tool execution, workspace sandbox)\n"
        )
        await bus.publish(EventType.SKILL_STARTED, "Skill started: filesystem_write",
                          source="alex", mission_id=mission.id, employee_id="alex")
        await bus.publish(EventType.TOOL_STARTED, "Tool started: workspace_file_write",
                          source="alex", mission_id=mission.id, employee_id="alex")
        mission.log("SKILL_STARTED", "filesystem_write")
        result = write_skill.execute(relative_path=f"missions/{mission.id}/report.md",
                                     content=report_content)
        audit.record("alex", "tool:workspace_file_write", mission_id=mission.id,
                     employee_id="alex", tool="workspace_file_write",
                     permission="workspace:write", result="ok", metadata=result)
        await bus.publish(EventType.TOOL_COMPLETED, f"File written: {result['bytes']} bytes",
                          source="alex", mission_id=mission.id, employee_id="alex",
                          metadata=result)
        await bus.publish(EventType.SKILL_COMPLETED, "Skill completed: filesystem_write",
                          source="alex", mission_id=mission.id, employee_id="alex")
        mission.log("TOOL_EXECUTED", result["path"])
        mission.outputs["artifact"] = result
        mission.plan[1]["status"] = "done"
        if alex:
            alex.state = EmployeeState.SUCCESS

        # 3. SAM VERIFIES (QA evidence)
        if sam:
            sam.state = EmployeeState.ACTIVE
        mission.active_employees = ["sam"]
        mission.current_step = 3
        await bus.publish(EventType.QA_STARTED, "QA verification started by Sam",
                          source="sam", mission_id=mission.id, employee_id="sam")
        verify_skill = SKILLS["filesystem_verify"]
        evidence = verify_skill.execute(relative_path=f"missions/{mission.id}/report.md")
        audit.record("sam", "qa:filesystem_verify", mission_id=mission.id,
                     employee_id="sam", tool="workspace_file_verify",
                     permission="workspace:read",
                     result="ok" if evidence["verified"] else "failed", metadata=evidence)
        mission.outputs["qa_evidence"] = evidence
        mission.plan[2]["status"] = "done" if evidence["verified"] else "failed"
        if sam:
            sam.state = EmployeeState.SUCCESS if evidence["verified"] else EmployeeState.FAILED

        if not evidence["verified"]:
            await bus.publish(EventType.QA_FAILURE, "QA could not verify artifact",
                              source="sam", severity="error", mission_id=mission.id,
                              employee_id="sam")
            raise RuntimeError("QA verification failed — artifact missing")
        mission.log("QA_VERIFIED", f"{evidence['bytes']} bytes")

        # 4. COMPLETE — artifact, memory, reputation, cost
        mission.status = MissionStatus.COMPLETED
        mission.completed_at = time.time()
        mission.confidence = 1.0
        mission.final_summary = (
            f"Mission completed. Artifact verified at {evidence['path']} "
            f"({evidence['bytes']} bytes). All steps executed for real."
        )
        mission.log("MISSION_COMPLETED", mission.final_summary)
        mission.touch()
        mission.active_employees = []
        if maya:
            maya.state = EmployeeState.AVAILABLE

        artifacts.create("REPORT", f"Mission Report — {title}", creator="alex",
                         location=result["path"], mission_id=mission.id)
        vault.store(f"Mission '{title}' completed successfully with verified artifact.",
                    category=vault.Category.SUCCESSES, source="maya",
                    mission_id=mission.id, confidence=0.9)
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
