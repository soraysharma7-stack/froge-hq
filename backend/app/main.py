"""FROGÉ HQ — FastAPI entrypoint (Phase 1: modular monolith)."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router as api_router
from app.websocket.ws import router as ws_router
from app.config.settings import settings
from app.notifications import center as notifications
from app.core import db
from app.core import persistence

app = FastAPI(title=settings.app_name, version="1.0.0")


@app.get("/")
def root():
    return {"app": settings.app_name, "docs": "/docs", "api": "/api", "ws": "/ws/events"}


@app.on_event("startup")
async def _startup():
    await db.init_db()
    await persistence.restore_all()
    notifications.start()


@app.on_event("shutdown")
async def _shutdown():
    await db.close_db()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Phase 1 dev; tighten later
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")
app.include_router(ws_router)

# Production: serve the built frontend from the same service (one live URL).
import os
from fastapi.staticfiles import StaticFiles

_dist = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", settings.frontend_dist))
if os.path.isdir(_dist):
    app.mount("/", StaticFiles(directory=_dist, html=True), name="frontend")


@app.get("/healthz")
def healthz():
    return {"app": settings.app_name, "ok": True}
