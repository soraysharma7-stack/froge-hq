import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        yield c


@pytest.mark.asyncio
async def test_health_full(client):
    r = await client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["mode"] in ("ONLINE", "DEGRADED", "OFFLINE")


@pytest.mark.asyncio
async def test_mission_full_lifecycle(client):
    r = await client.post("/api/missions", json={"title": "Full", "objective": "lifecycle"})
    m = r.json()
    assert m["status"] == "COMPLETED"
    assert m["outputs"]["qa_evidence"]["verified"] is True
    steps = [t["step"] for t in m["timeline"]]
    for s in ("MISSION_CREATED", "MAYA_PLANNED", "EMPLOYEE_ACTIVATED",
              "TOOL_EXECUTED", "QA_VERIFIED", "MISSION_COMPLETED"):
        assert s in steps

    rep = await client.get(f"/api/missions/{m['id']}/replay")
    assert rep.json()["read_only"] is True


@pytest.mark.asyncio
async def test_simulation_never_executes(client):
    r = await client.post("/api/missions", json={
        "title": "Sim", "objective": "simulate only", "simulate": True})
    m = r.json()
    assert m["status"] == "COMPLETED"
    assert "SIMULATION" in m["final_summary"]
    assert "artifact" not in m["outputs"]


@pytest.mark.asyncio
async def test_security_blocks_hard_denied(client):
    r = await client.post("/api/security/check", json={
        "action": "read_credentials", "actor": "maya", "reason": "test"})
    assert r.json()["decision"] == "DENY"

    r2 = await client.post("/api/security/check", json={
        "action": "workspace_file_write", "actor": "alex"})
    assert r2.json()["decision"] == "ALLOW"


@pytest.mark.asyncio
async def test_approval_lifecycle(client):
    r = await client.post("/api/approvals", json={
        "action": "destructive_operation", "requester": "maya", "risk": "HIGH"})
    ap = r.json()
    assert ap["state"] == "PENDING"
    r2 = await client.post(f"/api/approvals/{ap['id']}/resolve",
                           json={"state": "APPROVED", "resolver": "user"})
    assert r2.json()["state"] == "APPROVED"


@pytest.mark.asyncio
async def test_stop_all_blocks_missions(client):
    await client.post("/api/stop-all")
    r = await client.post("/api/missions", json={"title": "X", "objective": "stopped"})
    assert r.json()["status"] == "PAUSED"
    assert "STOP ALL" in r.json()["errors"][0]
    await client.post("/api/stop-all/release")
    r2 = await client.post("/api/missions", json={"title": "Y", "objective": "resumed"})
    assert r2.json()["status"] == "COMPLETED"


@pytest.mark.asyncio
async def test_boardroom_synthesis(client):
    r = await client.post("/api/boardroom", json={"topic": "Scale to prod?"})
    s = r.json()
    assert s["status"] == "SYNTHESIZED"
    assert len(s["positions"]) >= 3
    assert s["synthesis"].startswith("Maya synthesis")


@pytest.mark.asyncio
async def test_memory_store_retrieve(client):
    await client.post("/api/memory", json={
        "content": "User prefers concise updates", "category": "USER_PREFERENCES"})
    r = await client.get("/api/memory", params={"q": "concise"})
    assert any("concise" in m["content"] for m in r.json())


@pytest.mark.asyncio
async def test_artifacts_and_decisions(client):
    await client.post("/api/missions", json={"title": "Art", "objective": "artifact"})
    arts = await client.get("/api/artifacts")
    assert len(arts.json()) >= 1

    r = await client.post("/api/decisions", json={
        "decision": "Use modular monolith", "context": "low-spec machine",
        "alternatives": ["microservices"], "reasoning_summary": "lightweight",
        "owner": "maya"})
    assert r.status_code == 201
    decs = await client.get("/api/decisions")
    assert any(d["decision"] == "Use modular monolith" for d in decs.json())


@pytest.mark.asyncio
async def test_voice_router_hinglish(client):
    r = await client.post("/api/voice/route", json={"utterance": "website bana do"})
    assert "create" in r.json()["intents"]
    r2 = await client.post("/api/voice/route", json={"utterance": "research karke report banao"})
    assert set(r2.json()["intents"]) >= {"research", "report"}


@pytest.mark.asyncio
async def test_search(client):
    await client.post("/api/missions", json={"title": "Findme", "objective": "searchable"})
    r = await client.get("/api/search", params={"q": "Findme"})
    assert any(x["kind"] == "mission" for x in r.json())


@pytest.mark.asyncio
async def test_monitoring_and_audit_and_time_machine(client):
    mon = await client.get("/api/monitoring")
    assert "cpu_percent" in mon.json()
    aud = await client.get("/api/audit")
    assert len(aud.json()) >= 1
    tm = await client.get("/api/time-machine")
    assert isinstance(tm.json(), list)


@pytest.mark.asyncio
async def test_reputation_and_departments(client):
    rep = await client.get("/api/reputation")
    assert any(r["employee_id"] == "alex" for r in rep.json())
    deps = await client.get("/api/departments")
    names = {d["name"] for d in deps.json()}
    assert "Software Engineering" in names and "Memory Vault" in names


@pytest.mark.asyncio
async def test_notifications_generated(client):
    from app.notifications import center as notifications
    notifications.start()
    # Wait for listener subscription before publishing
    import asyncio
    for _ in range(20):
        await asyncio.sleep(0.05)
        if notifications._listener_task is not None:
            break
    await client.post("/api/approvals", json={
        "action": "external_communication", "requester": "maya", "risk": "HIGH"})
    for _ in range(30):
        await asyncio.sleep(0.1)
        r = await client.get("/api/notifications")
        if any(n["kind"] == "APPROVAL_REQUIRED" for n in r.json()):
            return
    raise AssertionError("notification not generated")
