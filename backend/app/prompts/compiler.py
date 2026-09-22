"""Prompt Compiler — assembles versioned employee context. Never exposes chain-of-thought."""
from __future__ import annotations

import time

PROMPT_VERSION = "1.0.0"
_compilations: list[dict] = []


def compile_prompt(*, employee: dict, mission: dict | None = None,
                   memories: list[dict] | None = None,
                   skills: list[str] | None = None,
                   output_requirements: str | None = None) -> dict:
    sections = {
        "global_policy": (
            "You are an AI employee of FROGÉ HQ. Be honest, concise, professional. "
            "Never claim an action happened when it did not. Never pretend to be human. "
            "Distinguish KNOWN / ASSUMED / EXECUTED / FAILED / BLOCKED / UNCERTAIN."
        ),
        "department": employee.get("department", ""),
        "role": employee.get("role", ""),
        "personality": employee.get("personality", ""),
        "project_context": (mission or {}).get("objective", ""),
        "mission": (mission or {}).get("title", ""),
        "relevant_memory": [m.get("content", "") for m in (memories or [])][:5],
        "available_skills": skills or employee.get("skills", []),
        "permissions": f"security_level={employee.get('security_level', 1)}; workspace sandbox only",
        "output_requirements": output_requirements or "Structured, verifiable output.",
    }
    record = {
        "version": PROMPT_VERSION,
        "employee_id": employee.get("id"),
        "timestamp": time.time(),
        "sections": sections,
    }
    _compilations.append(record)
    return record


def version() -> str:
    return PROMPT_VERSION
