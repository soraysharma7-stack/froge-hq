"""Skills — reusable capabilities shared by employees (no duplicated tool logic)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from app.tools import workspace_tools


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
