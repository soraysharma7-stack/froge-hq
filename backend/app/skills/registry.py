"""Skills — reusable capabilities shared by employees (no duplicated tool logic)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from app.tools import open_tools, web_tools, workspace_tools


@dataclass
class Skill:
    id: str
    name: str
    description: str
    permissions: list[str]
    input_schema: dict
    execute: Callable[..., Any]
    output_schema: dict


SKILLS: dict[str, Skill] = {}


def register(skill: Skill) -> None:
    SKILLS[skill.id] = skill


register(Skill(
    id="filesystem_write",
    name="Workspace File Write",
    description="Create a file inside the project workspace sandbox.",
    permissions=["workspace:write"],
    input_schema={"relative_path": "string", "content": "string"},
    execute=workspace_tools.workspace_file_write,
    output_schema={"path": "string", "bytes": "number", "status": "string"},
))

register(Skill(
    id="filesystem_verify",
    name="Workspace File Verify",
    description="Verify a file exists in the workspace with real content (QA evidence).",
    permissions=["workspace:read"],
    input_schema={"relative_path": "string"},
    execute=workspace_tools.workspace_file_verify,
    output_schema={"exists": "boolean", "bytes": "number", "verified": "boolean"},
))

register(Skill(
    id="web_search",
    name="Web Search",
    description="Search the public web for research. Read-only, allow-listed endpoint.",
    permissions=["web:search"],
    input_schema={"query": "string", "max_results": "number (optional)"},
    execute=web_tools.web_search,
    output_schema={"query": "string", "count": "number", "results": "list"},
))

register(Skill(
    id="filesystem_read",
    name="Workspace File Read",
    description="Read a file inside the workspace sandbox (bounded content).",
    permissions=["workspace:read"],
    input_schema={"relative_path": "string", "max_bytes": "number (optional)"},
    execute=workspace_tools.workspace_file_read,
    output_schema={"path": "string", "bytes": "number", "content": "string"},
))

register(Skill(
    id="filesystem_list",
    name="Workspace List Directory",
    description="List a directory inside the workspace sandbox.",
    permissions=["workspace:read"],
    input_schema={"relative_path": "string (optional)"},
    execute=workspace_tools.workspace_list_dir,
    output_schema={"path": "string", "count": "number", "entries": "list"},
))

register(Skill(
    id="filesystem_append",
    name="Workspace File Append",
    description="Append text to a file inside the workspace sandbox.",
    permissions=["workspace:write"],
    input_schema={"relative_path": "string", "content": "string"},
    execute=workspace_tools.workspace_file_append,
    output_schema={"path": "string", "bytes": "number", "status": "string"},
))

register(Skill(
    id="filesystem_delete",
    name="Workspace File Delete",
    description="Delete a file inside the workspace sandbox (requires approval).",
    permissions=["workspace:write", "destructive"],
    input_schema={"relative_path": "string"},
    execute=workspace_tools.workspace_file_delete,
    output_schema={"path": "string", "deleted": "boolean"},
))

register(Skill(
    id="open_url",
    name="Open URL",
    description="Open a website in the user's browser (frontend opens it).",
    permissions=["open:url"],
    input_schema={"url": "string"},
    execute=open_tools.open_url,
    output_schema={"action": "string", "url": "string"},
))

register(Skill(
    id="open_app",
    name="Open App",
    description="Open a local app (VS Code, Notepad, Calculator) — only on your device.",
    permissions=["open:app"],
    input_schema={"app": "string"},
    execute=open_tools.open_app,
    output_schema={"action": "string", "app": "string"},
))
