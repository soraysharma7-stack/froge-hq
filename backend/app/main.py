"""FROGÉ HQ — FastAPI entrypoint (Phase 1: modular monolith)."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router as api_router
from app.websocket.ws import router as ws_router
from app.config.settings import settings
from app.notifications import center as notifications

app = FastAPI(title=settings.app_name, version="1.0.0")


@app.on_event("startup")
async def _startup():
    notifications.start()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Phase 1 dev; tighten later
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")
app.include_router(ws_router)


@app.get("/")
def root():
    return {"app": settings.app_name, "docs": "/docs", "api": "/api", "ws": "/ws/events"}
