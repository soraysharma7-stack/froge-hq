import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_health():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        r = await c.get("/api/health")
        assert r.status_code == 200
        body = r.json()
        assert body["status"] == "ok"
        assert "model_gateway" in body


@pytest.mark.asyncio
async def test_config_never_hardcodes_model():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        r = await c.get("/api/config")
        assert r.status_code == 200
        assert r.json()["max_active_agents"] == 5


@pytest.mark.asyncio
async def test_mission_vertical_slice_executes_real_tool():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        r = await c.post("/api/missions", json={"title": "Test", "objective": "write a file"})
        assert r.status_code == 202
        m = r.json()
        assert m["status"] == "COMPLETED"
        assert m["outputs"]["qa_evidence"]["verified"] is True
        assert m["outputs"]["artifact"]["bytes"] > 0


@pytest.mark.asyncio
async def test_events_recorded():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        await c.post("/api/missions", json={"title": "Ev", "objective": "check events"})
        r = await c.get("/api/events")
        types = {e["type"] for e in r.json()}
        assert "MISSION_CREATED" in types
        assert "MISSION_COMPLETED" in types
