"""Structured task understanding — stage 1 of the agent loop.

Deterministic keyword analysis. The backend owns the final shape and never
trusts model output blindly.
"""
from __future__ import annotations

from typing import Any

_WRITE_HINTS = ("write", "create", "build", "generate", "report", "file", "summarize", "summarise", "draft")
_VERIFY_HINTS = ("verify", "test", "check", "qa", "validate", "confirm")
_COMPLEX_HINTS = (" and ", " then ", " multiple", " several", "deploy", "refactor", "migrate")
_APPROVAL_HINTS = ("delete", "remove", "production", "deploy", "send", "email", "publish", "credential", "secret")


def understand(objective: str) -> dict[str, Any]:
    """Return the structured task representation for an objective."""
    text = objective.lower()

    requires_tools = any(h in text for h in _WRITE_HINTS + _VERIFY_HINTS)
    requires_verification = any(h in text for h in _VERIFY_HINTS) or requires_tools
    requires_approval = any(h in text for h in _APPROVAL_HINTS)
    complexity = "simple"
    if requires_tools and requires_verification:
        complexity = "medium"
    if any(h in text for h in _COMPLEX_HINTS) or len(objective.split()) > 25:
        complexity = "complex"

    capabilities: list[str] = []
    if requires_tools:
        capabilities.append("file_operations")
    if requires_verification:
        capabilities.append("verification")

    return {
        "objective": objective,
        "task_type": _classify(text),
        "complexity": complexity,
        "requires_tools": requires_tools,
        "requires_approval": requires_approval,
        "requires_verification": requires_verification,
        "required_capabilities": capabilities,
        "missing_information": _missing(objective),
    }


def _classify(text: str) -> str:
    if any(h in text for h in ("report", "summarize", "summarise", "research", "write")):
        return "content_generation"
    if any(h in text for h in ("test", "verify", "qa", "check")):
        return "verification"
    if any(h in text for h in ("build", "code", "implement", "fix")):
        return "engineering"
    return "general"


def _missing(objective: str) -> list[str]:
    missing = []
    if not objective.strip():
        missing.append("objective is empty")
    if len(objective.strip()) < 10:
        missing.append("objective is very short — desired outcome may be ambiguous")
    return missing
