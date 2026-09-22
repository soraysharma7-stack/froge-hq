"""Real, sandboxed tools. The AI is never the security boundary:
every tool call passes the policy engine BEFORE execution and is audited after.
"""
from __future__ import annotations

from pathlib import Path

from app.config.settings import settings


class ToolPermissionError(Exception):
    pass


def _sandbox_root() -> Path:
    root = Path(settings.workspace_root).resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


def _resolve_in_sandbox(relative_path: str) -> Path:
    """Resolve a path strictly inside the workspace sandbox. Escape = blocked."""
    root = _sandbox_root()
    target = (root / relative_path).resolve()
    if root not in target.parents and target != root:
        raise ToolPermissionError(f"SECURITY_BLOCK: path escapes workspace sandbox: {relative_path}")
    # Block credential-ish targets deterministically
    lowered = target.name.lower()
    for marker in (".env", "secret", "credential", "password", "id_rsa", ".pem"):
        if marker in lowered:
            raise ToolPermissionError(f"SECURITY_BLOCK: credential-sensitive file denied: {relative_path}")
    return target


def workspace_file_write(relative_path: str, content: str) -> dict:
    """Write a file inside the project workspace sandbox. Real execution."""
    target = _resolve_in_sandbox(relative_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return {"path": str(target), "bytes": len(content.encode("utf-8")), "status": "written"}


def workspace_file_verify(relative_path: str) -> dict:
    """QA verification: prove the artifact actually exists with real content."""
    target = _resolve_in_sandbox(relative_path)
    exists = target.is_file()
    size = target.stat().st_size if exists else 0
    return {"path": str(target), "exists": exists, "bytes": size, "verified": exists and size > 0}
