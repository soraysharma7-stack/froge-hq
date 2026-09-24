"""Open tools — launch URLs and apps for the user.

Two kinds, honestly separated:
- open_url: returns the URL for the FRONTEND to open (window.open in the user's browser).
  The backend never fakes that it opened something.
- open_app: on the server device only. On Render (cloud) this is a no-op that says so —
  your laptop apps can't be opened from a cloud server. Real local opening only works
  when the backend runs ON your device (or via the browser bridge for web URLs).
"""
from __future__ import annotations

import re
import shutil
import subprocess
import sys

# Safe, allow-listed app names → how to open them (only on a local device).
_LOCAL_APPS: dict[str, dict] = {
    "vscode": {"cmd": ["code", "--new-window"], "label": "VS Code"},
    "notepad": {"cmd": ["notepad"], "label": "Notepad"},
    "calculator": {"cmd": ["calc"], "label": "Calculator"},
}

_URL_RE = re.compile(r"^(https?://)[\w.-]+(:\d+)?(/\S*)?$")


class OpenToolError(Exception):
    pass


def open_url(url: str) -> dict:
    """Validate a URL and return it for the frontend to open in the user's browser."""
    u = (url or "").strip()
    if not u:
        raise OpenToolError("open_url: empty url")
    if not u.startswith(("http://", "https://")):
        u = "https://" + u
    if not _URL_RE.match(u):
        raise OpenToolError(f"open_url: invalid or unsafe url: {u}")
    return {
        "action": "open_in_browser",
        "url": u,
        "opened_by": "frontend",
        "note": "Returned for the frontend to open in YOUR browser (window.open). "
                "The backend cannot open tabs on a cloud server.",
    }


def open_app(app: str) -> dict:
    """Open a local application — ONLY works when the backend runs on YOUR device."""
    name = (app or "").strip().lower()
    if not name:
        raise OpenToolError("open_app: empty app name")
    spec = _LOCAL_APPS.get(name)
    if not spec:
        raise OpenToolError(
            f"open_app: '{name}' is not allow-listed. Allowed: {', '.join(_LOCAL_APPS)}",
        )
    on_render = bool(__import__("os").environ.get("RENDER"))
    if on_render:
        return {
            "action": "cannot_open",
            "app": name,
            "reason": "cloud_server",
            "note": "I run on a cloud server, not your laptop — I can't open apps on your device. "
                    "To open apps, run FROGÉ HQ locally (bash start.sh) or use the browser bridge for web links.",
        }
    exe = shutil.which(spec["cmd"][0])
    if not exe:
        raise OpenToolError(f"open_app: '{spec['cmd'][0]}' not found on this device (install it or add to PATH)")
    try:
        subprocess.Popen(spec["cmd"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as exc:
        raise OpenToolError(f"open_app failed: {exc}") from exc
    return {"action": "opened", "app": name, "label": spec["label"], "note": f"{spec['label']} opened on your device."}


_ALIASES = {
    "youtube": "https://www.youtube.com",
    "yt": "https://www.youtube.com",
    "google": "https://www.google.com",
    "github": "https://github.com",
    "gmail": "https://mail.google.com",
    "maps": "https://maps.google.com",
    "vs code": "vscode",
    "vscode": "vscode",
    "code": "vscode",
    "notepad": "notepad",
    "calculator": "calculator",
    "calc": "calculator",
}


def resolve_open_command(text: str) -> dict:
    """Turn 'open youtube' / 'open vs code' into an open_url/open_app action."""
    low = (text or "").strip().lower()
    for word in ("open", "kholo", "khol do", "launch", "start", "chalao", "chalu karo"):
        low = low.replace(word, "", 1)
    target = low.strip()
    if not target:
        raise OpenToolError("resolve_open_command: nothing to open")

    if target in _LOCAL_APPS:
        return {"type": "app", **open_app(target)}
    if target in _ALIASES and not _ALIASES[target].startswith("http"):
        return {"type": "app", **open_app(_ALIASES[target])}
    url = _ALIASES.get(target, target if target.startswith(("http://", "https://")) or "." in target else None)
    if url:
        return {"type": "url", **open_url(url)}
    raise OpenToolError(
        f"Don't know how to open '{target}'. Try 'open youtube', 'open github', or a full URL.",
    )
