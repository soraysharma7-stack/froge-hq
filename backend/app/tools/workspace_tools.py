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


def workspace_file_read(relative_path: str, max_bytes: int = 8000) -> dict:
    """Read a file inside the sandbox. Returns bounded content."""
    target = _resolve_in_sandbox(relative_path)
    if not target.is_file():
        raise ToolPermissionError(f"NOT_FOUND: no such file in workspace: {relative_path}")
    data = target.read_bytes()[:max_bytes]
    return {"path": str(target), "bytes": target.stat().st_size,
            "content": data.decode("utf-8", errors="replace")}


def workspace_list_dir(relative_path: str = ".", max_entries: int = 200) -> dict:
    """List a directory inside the sandbox (one level). Missing dir = empty list."""
    target = _resolve_in_sandbox(relative_path)
    if not target.exists():
        return {"path": str(target), "count": 0, "entries": [], "note": "directory does not exist yet"}
    if not target.is_dir():
        raise ToolPermissionError(f"NOT_A_DIRECTORY: {relative_path}")
    entries = []
    for child in sorted(target.iterdir())[:max_entries]:
        entries.append({"name": child.name, "type": "dir" if child.is_dir() else "file",
                        "bytes": child.stat().st_size if child.is_file() else None})
    return {"path": str(target), "count": len(entries), "entries": entries}


def workspace_file_append(relative_path: str, content: str) -> dict:
    """Append text to a file inside the sandbox (creates if missing)."""
    target = _resolve_in_sandbox(relative_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8") as fh:
        fh.write(content)
    return {"path": str(target), "bytes": target.stat().st_size, "status": "appended"}


def workspace_file_delete(relative_path: str) -> dict:
    """Delete a file inside the sandbox. Destructive — the policy engine
    requires approval for this via the brain's permission step."""
    target = _resolve_in_sandbox(relative_path)
    if not target.exists():
        raise ToolPermissionError(f"NOT_FOUND: no such file in workspace: {relative_path}")
    if target.is_dir():
        raise ToolPermissionError(f"SECURITY_BLOCK: refusing to delete a directory: {relative_path}")
    target.unlink()
    return {"path": str(target), "deleted": True}
