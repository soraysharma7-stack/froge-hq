"""FROGÉ HQ sign-in — owner auth + member accounts, with honest configuration.

Owner credentials come ONLY from environment variables:
    FROGE_OWNER_EMAIL      the owner login
    FROGE_OWNER_PASSWORD   the owner password
    FROGE_AUTH_SECRET      token signing secret (default is dev-only; set it in production)

Member accounts are created through /api/auth/signup and stored durably
(passwords salted + PBKDF2-hashed, never plaintext, never logged).

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
import os
import re
import time

from app.config.settings import settings
from app.core import persistence

TABLE_ACCOUNTS = "accounts"

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_PBKDF2_ROUNDS = 120_000

# email -> {email, name, password_hash, salt, role, created_at}
_ACCOUNTS: dict[str, dict] = {}


def auth_required() -> bool:
    return bool(settings.owner_email and settings.owner_password)


# ---------- Member accounts ----------
def _hash_password(password: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac(
        "sha256", password.encode(), bytes.fromhex(salt), _PBKDF2_ROUNDS
    ).hex()


def restore_account(doc: dict) -> None:
    """Restore one account document from persistence at startup."""
    email = (doc.get("email") or "").strip().lower()
    if email:
        _ACCOUNTS[email] = doc


def list_accounts() -> list[dict]:
    """Account metadata only — password hashes are never exposed."""
    return [
        {"email": a["email"], "name": a.get("name", ""), "role": a.get("role", "member"),
         "created_at": a.get("created_at")}
        for a in _ACCOUNTS.values()
    ]


def create_account(email: str, password: str, name: str = "") -> dict:
    """Create a member account. Raises ValueError with a user-safe message on bad input."""
    email = (email or "").strip().lower()
    if not _EMAIL_RE.match(email):
        raise ValueError("invalid email address")
    if len(password or "") < 8:
        raise ValueError("password must be at least 8 characters")
    if email in _ACCOUNTS or (auth_required() and email == settings.owner_email.lower()):
        raise ValueError("an account with this email already exists")
    salt = os.urandom(16).hex()
    doc = {
        "email": email,
        "name": (name or "").strip(),
        "password_hash": _hash_password(password, salt),
        "salt": salt,
        "role": "member",
        "created_at": time.time(),
    }
    _ACCOUNTS[email] = doc
    persistence.save(TABLE_ACCOUNTS, email, doc)
    return {"email": email, "name": doc["name"], "role": "member"}


def verify_account(email: str, password: str) -> bool:
    a = _ACCOUNTS.get((email or "").strip().lower())
    if not a:
        return False
    return hmac.compare_digest(a["password_hash"], _hash_password(password, a["salt"]))


def _sign(payload: dict) -> str:
    secret = (settings.auth_secret or "froge-dev-secret").encode()
    body = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
    sig = hmac.new(secret, body.encode(), hashlib.sha256).hexdigest()
    return f"{body}.{sig}"


def issue_token(email: str) -> dict:
    payload = {"sub": email, "iat": time.time(), "exp": time.time() + 60 * 60 * 24 * 7}
    return {"access_token": _sign(payload), "token_type": "bearer", "email": email}


def verify_credentials(email: str, password: str) -> bool:
    """True for the owner (env credentials) or any stored member account."""
    if auth_required() and hmac.compare_digest(
        (email or "").lower(), settings.owner_email.lower()
    ) and hmac.compare_digest(password, settings.owner_password):
        return True
    return verify_account(email, password)


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
