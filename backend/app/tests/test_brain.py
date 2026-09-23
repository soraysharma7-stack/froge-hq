"""Agent Brain tests — understanding, planning, validation, loop execution."""
import asyncio

from app.brain import context, planner, understand
from app.brain import loop as brain_loop
from app.brain.confidence import grade
from app.brain.states import BrainState
from app.resources import governor


def test_understand_structures_task():
    t = understand.understand("Research AI trends and write a report file")
    assert t["task_type"] == "content_generation"
    assert t["requires_tools"] is True
    assert t["requires_verification"] is True
    assert t["complexity"] in ("medium", "complex")


def test_understand_flags_approval_for_sensitive():
    t = understand.understand("Delete the production database")
    assert t["requires_approval"] is True


def test_smallest_capable_team():
    t = understand.understand("write a report")
    team = planner.smallest_capable_team(t)
    assert "maya" in team and "alex" in team and "sam" in team
    assert "rex" not in team  # security not activated unnecessarily


def test_plan_validates_against_registry():
    t = understand.understand("write a report")
    plan = planner.build_plan(t, "m1", "missions/m1/report.md")
    assert planner.validate_plan(plan) == []
    broken = planner.build_plan(t, "m1", "missions/m1/report.md")
    broken[1]["employee"] = "nobody"
    assert planner.validate_plan(broken) != []


def test_confidence_is_evidence_based():
    assert grade(tool_ok=True, verified=True, has_errors=False) == "HIGH"
    assert grade(tool_ok=True, verified=False, has_errors=False) == "MEDIUM"
    assert grade(tool_ok=False, verified=False, has_errors=True) == "LOW"
    assert grade(tool_ok=True, verified=True, has_errors=False, simulated=True) == "LOW"


def test_brain_state_set_complete():
    names = {s.value for s in BrainState}
    assert "WAITING_APPROVAL" in names and "VERIFYING" in names and "QUEUED" in names


def test_brain_loop_executes_and_verifies():
    def builder(task):
        return "missions/test-brain/report.md", "# test\nreal content"

    result = asyncio.run(brain_loop.run_brain_loop(
        mission_id="test-brain", objective="write a test report", title="Brain Test",
        content_builder=builder, stop_check=lambda: False))
    assert result["ok"] is True
    assert result["verified"] is True
    assert result["confidence"] == "HIGH"
    assert result["agent_message"]["type"] == "RESULT"
    assert result["agent_message"]["status"] == "SUCCESS"
    assert len(result["observations"]) >= 2  # write + verify
    statuses = {o["status"] for o in result["observations"]}
    assert statuses == {"SUCCESS"}


def test_brain_loop_stop_all_blocks():
    def builder(task):
        return "missions/test-stop/report.md", "x"

    result = asyncio.run(brain_loop.run_brain_loop(
        mission_id="test-stop", objective="write", title="Stop Test",
        content_builder=builder, stop_check=lambda: True))
    assert result["ok"] is False
    assert "STOP ALL" in "; ".join(result["errors"]) or result["stage"] != "completed"


def test_context_is_relevance_filtered():
    ctx = context.collect("write a report about agents")
    assert len(ctx["relevant_memories"]) <= 5
    assert "filesystem_write" in ctx["available_skills"]
