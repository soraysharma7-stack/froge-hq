"""REST API — all FROGÉ HQ subsystems."""
from __future__ import annotations

import time

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.approvals import engine as approvals
from app.artifacts import library as artifacts
from app.audit import log as audit
from app.boardroom import room as boardroom
from app.config.settings import settings
from app.cost import tracker as cost
from app.decisions import adr as decisions
from app.departments import registry as departments
from app.employees import registry as employees
from app.events.bus import bus, EventType
from app.healing import recovery as healing
from app.knowledge import graph as kgraph
from app.memory import vault
from app.missions import manager as missions
from app.model_gateway.gateway import gateway
from app.notifications import center as notifications
from app.prompts import compiler as prompts
from app.qa import center as qa
from app.reputation import tracker as reputation
from app.resources import governor
from app.search import global_search
from app.security import policy
from app.skills.registry import SKILLS
from app.voice import router as voice

router = APIRouter()
_STARTED = time.time()


# ---------- Core ----------
@router.get("/health")
def health():
    return {
        "status": "ok", "app": settings.app_name,
        "uptime_s": round(time.time() - _STARTED, 1),
        "mode": governor.mode(),
        "stop_all_engaged": governor.stop_all_engaged(),
        "model_gateway": gateway.info(),
    }


@router.get("/config")
def config():
    return {
        "max_active_agents": settings.max_active_agents,
        "max_browser_instances": settings.max_browser_instances,
        "max_queue_size": settings.max_queue_size,
        "workspace_root": settings.workspace_root,
        "prompt_version": prompts.version(),
        "model_gateway": gateway.info(),
    }


# ---------- Missions ----------
class MissionCreate(BaseModel):
    title: str
    objective: str
    simulate: bool = False


@router.get("/missions")
def list_missions():
    return missions.list_missions()


@router.get("/missions/{mission_id}")
def mission_detail(mission_id: str):
    m = missions.get_mission(mission_id)
    if not m:
        raise HTTPException(404, "Mission not found")
    return m.to_dict()


@router.get("/missions/{mission_id}/replay")
def mission_replay(mission_id: str):
    tl = missions.replay(mission_id)
    if tl is None:
        raise HTTPException(404, "Mission not found")
    return {"mission_id": mission_id, "read_only": True, "timeline": tl}


@router.post("/missions", status_code=202)
async def create_mission(payload: MissionCreate):
    m = await missions.run_mission(payload.title, payload.objective,
                                   simulate=payload.simulate)
    return m.to_dict()


@router.post("/missions/simulate")
def simulate(payload: MissionCreate):
    return missions.simulate_plan(payload.title, payload.objective)


@router.post("/missions/{mission_id}/pause")
async def pause(mission_id: str):
    m = await missions.pause_mission(mission_id)
    if not m:
        raise HTTPException(404, "Mission not found or not running")
    return m.to_dict()


@router.post("/missions/{mission_id}/cancel")
async def cancel(mission_id: str):
    m = await missions.cancel_mission(mission_id)
    if not m:
        raise HTTPException(404, "Mission not found or not cancellable")
    return m.to_dict()


# ---------- Simulation / cost preview ----------
@router.post("/cost-preview")
def cost_preview(payload: dict):
    return cost.preview(
        estimated_tokens=payload.get("estimated_tokens"),
        estimated_duration_s=payload.get("estimated_duration_s"),
        requires_approval=payload.get("requires_approval", False),
        risks=payload.get("risks", []))


@router.get("/cost")
def cost_overview():
    return {
        "by_mission": cost.usage_by("mission_id"),
        "by_employee": cost.usage_by("employee_id"),
        "by_provider": cost.usage_by("provider"),
        "records": cost.records(50),
    }


# ---------- Employees / departments / skills ----------
@router.get("/employees")
def employee_list():
    return [e.to_dict() for e in employees.all_employees()]


@router.get("/employees/{employee_id}")
def employee_detail(employee_id: str):
    e = employees.get(employee_id)
    if not e:
        raise HTTPException(404, "Employee not found")
    return e.to_dict()


@router.get("/departments")
def department_list():
    return departments.list_departments()


@router.get("/departments/{dept_id}")
def department_detail(dept_id: str):
    d = departments.get(dept_id)
    if not d:
        raise HTTPException(404, "Department not found")
    return d


@router.get("/skills")
def skill_list():
    return [
        {"id": s.id, "name": s.name, "description": s.description,
         "permissions": s.permissions, "input_schema": s.input_schema,
         "output_schema": s.output_schema}
        for s in SKILLS.values()
    ]


# ---------- Events / monitoring / time machine ----------
@router.get("/events")
def events(limit: int = 100, filter: str = "ALL"):
    return bus.recent(limit=limit, type_filter=filter)


@router.get("/monitoring")
def monitoring():
    active = sum(1 for e in employees.all_employees() if e.state.value == "ACTIVE")
    running = sum(1 for m in missions.list_missions() if m["status"] == "RUNNING")
    snap = governor.snapshot(active, running)
    snap["model_gateway"] = gateway.info()
    snap["event_log_size"] = len(bus.recent(limit=10000))
    return snap


@router.get("/time-machine")
def time_machine(limit: int = 50):
    return missions.time_machine(limit)


# ---------- Security ----------
@router.get("/security")
def security_overview():
    return {"rules": policy.rules(), "blocked": policy.blocked_actions(100)}


class PolicyCheck(BaseModel):
    action: str
    actor: str = "user"
    risk: str = "LOW"
    reason: str = ""


@router.post("/security/check")
async def security_check(payload: PolicyCheck):
    return await policy.enforce(payload.action, actor=payload.actor,
                                risk=policy.Risk(payload.risk), reason=payload.reason)


# ---------- Approvals ----------
@router.get("/approvals")
def list_approvals(state: str | None = None):
    return approvals.list_approvals(state)


class ApprovalRequest(BaseModel):
    action: str
    requester: str = "maya"
    reason: str = ""
    risk: str = "MEDIUM"
    mission_id: str | None = None


@router.post("/approvals", status_code=201)
async def request_approval(payload: ApprovalRequest):
    return await approvals.request(payload.action, requester=payload.requester,
                                   reason=payload.reason, risk=payload.risk,
                                   mission_id=payload.mission_id)


class ApprovalResolve(BaseModel):
    state: str  # APPROVED / DENIED / MODIFIED
    resolver: str = "user"
    modification: str | None = None


@router.post("/approvals/{approval_id}/resolve")
async def resolve_approval(approval_id: str, payload: ApprovalResolve):
    ap = await approvals.resolve(approval_id, approvals.ApprovalState(payload.state),
                                 resolver=payload.resolver,
                                 modification=payload.modification)
    if not ap:
        raise HTTPException(404, "Approval not found or already resolved")
    return ap


# ---------- Boardroom ----------
class BoardroomCall(BaseModel):
    topic: str
    participants: list[str] | None = None
    mission_id: str | None = None


@router.get("/boardroom")
def boardroom_sessions():
    return boardroom.list_sessions()


@router.post("/boardroom", status_code=201)
async def call_boardroom(payload: BoardroomCall):
    return await boardroom.call_boardroom(payload.topic, participants=payload.participants,
                                          mission_id=payload.mission_id)


# ---------- Memory ----------
@router.get("/memory")
def memory_list(q: str = "", category: str | None = None, limit: int = 50):
    return vault.retrieve(q, category=category, limit=limit)


@router.get("/memory/categories")
def memory_categories():
    return vault.categories()


class MemoryStore(BaseModel):
    content: str
    category: str
    source: str = "user"
    confidence: float = 0.7
    mission_id: str | None = None


@router.post("/memory", status_code=201)
def memory_store(payload: MemoryStore):
    return vault.store(payload.content, category=vault.Category(payload.category),
                       source=payload.source, confidence=payload.confidence,
                       mission_id=payload.mission_id)


# ---------- Knowledge graph ----------
@router.get("/knowledge")
def knowledge_graph():
    return kgraph.graph()


# ---------- Artifacts ----------
@router.get("/artifacts")
def artifact_list(type: str | None = None):
    return artifacts.list_artifacts(type)


@router.get("/artifacts/{artifact_id}")
def artifact_detail(artifact_id: str):
    a = artifacts.get(artifact_id)
    if not a:
        raise HTTPException(404, "Artifact not found")
    return a


# ---------- Decisions ----------
@router.get("/decisions")
def decision_list():
    return decisions.list_decisions()


class DecisionCreate(BaseModel):
    decision: str
    context: str
    alternatives: list[str] = []
    reasoning_summary: str = ""
    evidence: list[str] = []
    risks: list[str] = []
    owner: str = "maya"


@router.post("/decisions", status_code=201)
def decision_create(payload: DecisionCreate):
    return decisions.record_decision(**payload.model_dump())


# ---------- QA ----------
@router.get("/qa")
def qa_overview():
    return {"summary": qa.summary(), "checks": qa.list_checks(50),
            "unresolved_failures": qa.unresolved_failures()}


# ---------- Model gateway ----------
@router.get("/model-gateway")
def model_gateway_info():
    return gateway.info()


# ---------- Notifications ----------
@router.get("/notifications")
def notification_list(unread: bool = False):
    return notifications.list_notifications(unread)


@router.post("/notifications/{notification_id}/read")
def notification_read(notification_id: str):
    if not notifications.mark_read(notification_id):
        raise HTTPException(404, "Notification not found")
    return {"ok": True}


# ---------- Audit ----------
@router.get("/audit")
def audit_log(limit: int = 200, result: str | None = None):
    return audit.query(limit, result)


# ---------- Reputation ----------
@router.get("/reputation")
def reputation_scores():
    return reputation.all_scores()


# ---------- Healing ----------
@router.get("/healing/log")
def healing_log():
    return healing.log()


# ---------- Search ----------
@router.get("/search")
def search(q: str, limit: int = 50):
    collections = {
        "mission": missions.list_missions(),
        "employee": [e.to_dict() for e in employees.all_employees()],
        "department": departments.list_departments(),
        "artifact": artifacts.list_artifacts(),
        "decision": decisions.list_decisions(),
        "memory": vault.retrieve("", limit=500),
        "event": bus.recent(limit=500),
    }
    return global_search.search(q, collections=collections, limit=limit)


# ---------- STOP ALL ----------
@router.post("/stop-all")
async def stop_all(actor: str = "user"):
    return await governor.engage_stop_all(actor)


@router.post("/stop-all/release")
async def release_stop(actor: str = "user"):
    return await governor.release_stop_all(actor)


# ---------- Voice ----------
class VoiceCommand(BaseModel):
    utterance: str


@router.post("/voice/route")
def voice_route(payload: VoiceCommand):
    return voice.route(payload.utterance)


# ---------- Prompt compiler ----------
@router.get("/prompts/compile/{employee_id}")
def compile_prompt(employee_id: str):
    e = employees.get(employee_id)
    if not e:
        raise HTTPException(404, "Employee not found")
    return prompts.compile_prompt(employee=e.to_dict())
