"""Confidence grading — HIGH / MEDIUM / LOW from evidence, never fake numbers."""
from __future__ import annotations


def grade(*, tool_ok: bool, verified: bool, has_errors: bool,
          memory_support: int = 0, simulated: bool = False) -> str:
    """Evidence-based confidence. No fabricated numeric scores."""
    if simulated:
        return "LOW"
    if verified and tool_ok and not has_errors:
        return "HIGH"
    if tool_ok and not has_errors:
        return "MEDIUM"
    if tool_ok and has_errors:
        return "MEDIUM" if memory_support > 0 else "LOW"
    return "LOW"
