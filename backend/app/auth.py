"""FROGÉ HQ sign-in — single-owner auth with honest configuration.

Owner credentials come ONLY from environment variables:
    FROGE_OWNER_EMAIL      the owner login
    FROGE_OWNER_PASSWORD   the owner password
    FROGE_AUTH_SECRET      token signing secret (default is dev-only; set it in production)

No credentials are hard-coded. If owner email/password are not set, the app
runs in its normal open dev mode and /api/auth/config reports
auth_required=false. When they ARE set, every /api route requires a Bearer
token from /api/auth/login.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time

from app.config.settings import settings


def auth_required() -> bool:
    return bool(settings.owner_email and settings.owner_password)


def _sign(payload: dict) -> str:
    secret = (settings.auth_secret or "froge-dev-secret").encode()
    body = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
    sig = hmac.new(secret, body.encode(), hashlib.sha256).hexdigest()
    return f"{body}.{sig}"


def issue_token(email: str) -> dict:
    payload = {"sub": email, "iat": time.time(), "exp": time.time() + 60 * 60 * 24 * 7}
    return {"access_token": _sign(payload), "token_type": "bearer", "email": email}


def verify_credentials(email: str, password: str) -> bool:
    if not auth_required():
        return False
    return hmac.compare_digest(email, settings.owner_email) and hmac.compare_digest(
        password, settings.owner_password
    )


def verify_token(token: str) -> str | None:
    """Return the token subject (email) if valid, else None."""
    try:
        body, sig = token.rsplit(".", 1)
    except ValueError:
        return None
    secret = (settings.auth_secret or "froge-dev-secret").encode()
    expected = hmac.new(secret, body.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(sig, expected):
        return None
    try:
        padding = "=" * (-len(body) % 4)
        payload = json.loads(base64.urlsafe_b64decode(body + padding))
    except Exception:
        return None
    if payload.get("exp", 0) < time.time():
        return None
    return payload.get("sub")
