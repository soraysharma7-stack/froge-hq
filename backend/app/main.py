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


@app.middleware("http")
async def security_headers(request, call_next):
    """Deterministic security headers on every response. Backend-enforced."""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "0"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    # HSTS only meaningful over HTTPS (Render terminates TLS); safe to always send.
    response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains; preload"
    if request.url.path == "/" or request.url.path.endswith(".html"):
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "font-src 'self'; "
            "connect-src 'self' wss: https:; "
            "frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
        )
    return response


@app.get("/healthz")
def healthz():
    return {"app": settings.app_name, "ok": True}


@app.on_event("startup")
async def _startup():
    await db.init_db()
    await persistence.restore_all()
    notifications.start()


@app.on_event("shutdown")
async def _shutdown():
    await db.close_db()

_cors_origins = (
    [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
    if getattr(settings, "cors_origins", "") else ["*"]
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(api_router, prefix="/api")
app.include_router(ws_router)

# Production: serve the built frontend from the same service (one live URL).
import os
from fastapi.staticfiles import StaticFiles

_dist = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", settings.frontend_dist.lstrip("./")))
if os.path.isdir(_dist):
    app.mount("/", StaticFiles(directory=_dist, html=True), name="frontend")
