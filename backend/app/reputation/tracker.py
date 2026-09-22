"""Reputation — employee performance as one input into future assignment. Never irreversible."""
from __future__ import annotations

_SCORES: dict[str, dict] = {}


def restore(doc: dict) -> None:
    _SCORES[doc["employee_id"]] = doc


def _persist(r: dict) -> None:
    from app.core import persistence
    persistence.save(persistence.TABLE_REPUTATION, r["employee_id"], r)


def _get(employee_id: str) -> dict:
    return _SCORES.setdefault(employee_id, {
        "employee_id": employee_id, "missions_success": 0, "missions_failed": 0,
        "qa_corrections": 0, "security_problems": 0, "total_time_s": 0.0,
        "feedback": [], "score": 0.5,
    })


def _recompute(r: dict) -> None:
    success, failed = r["missions_success"], r["missions_failed"]
    base = success / (success + failed) if (success + failed) else 0.5
    penalty = 0.05 * r["security_problems"] + 0.02 * r["qa_corrections"]
    fb = r["feedback"]
    fb_boost = (sum(fb) / len(fb)) * 0.1 if fb else 0.0
    r["score"] = round(max(0.0, min(1.0, base - penalty + fb_boost)), 3)


def record_outcome(employee_id: str, *, success: bool, duration_s: float = 0.0,
                   qa_correction: bool = False, security_problem: bool = False) -> dict:
    r = _get(employee_id)
    if success:
        r["missions_success"] += 1
    else:
        r["missions_failed"] += 1
    r["total_time_s"] += duration_s
    if qa_correction:
        r["qa_corrections"] += 1
    if security_problem:
        r["security_problems"] += 1
    _recompute(r)
    _persist(r)
    return r


def add_feedback(employee_id: str, rating: float) -> dict:
    r = _get(employee_id)
    r["feedback"].append(max(-1.0, min(1.0, rating)))
    _recompute(r)
    _persist(r)
    return r


def all_scores() -> list[dict]:
    return list(_SCORES.values())
