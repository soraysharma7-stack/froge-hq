"""Cost Intelligence — track usage when providers report it; never invent numbers."""
from __future__ import annotations

import time

_RECORDS: list[dict] = []


def record_usage(*, model: str | None, provider: str | None, mission_id: str | None,
                 employee_id: str | None, department: str | None,
                 duration_ms: float, tokens: dict | None = None,
                 estimated_cost: float | None = None,
                 actual_cost: float | None = None) -> dict:
    rec = {
        "timestamp": time.time(), "model": model, "provider": provider,
        "mission_id": mission_id, "employee_id": employee_id,
        "department": department, "duration_ms": duration_ms,
        "tokens": tokens,                      # only provider-reported
        "estimated_cost": estimated_cost,
        "actual_cost": actual_cost,            # None when inference is free/unknown
    }
    _RECORDS.append(rec)
    return rec


def usage_by(key: str) -> dict:
    totals: dict[str, dict] = {}
    for r in _RECORDS:
        k = r.get(key) or "unknown"
        t = totals.setdefault(k, {"count": 0, "duration_ms": 0.0,
                                  "actual_cost": 0.0, "cost_known": False})
        t["count"] += 1
        t["duration_ms"] += r["duration_ms"]
        if r["actual_cost"] is not None:
            t["actual_cost"] += r["actual_cost"]
            t["cost_known"] = True
    return totals


def preview(*, estimated_tokens: int | None = None, estimated_duration_s: float | None = None,
            requires_approval: bool = False, risks: list[str] | None = None) -> dict:
    """Cost preview before expensive work. Numbers are estimates, labeled as such."""
    return {
        "estimated_tokens": estimated_tokens,
        "estimated_duration_s": estimated_duration_s,
        "estimated_cost": None,  # unknown until a priced provider is configured
        "cost_note": "Current inference cost unknown/free — abstraction ready for paid providers.",
        "requires_approval": requires_approval,
        "potential_risks": risks or [],
    }


def records(limit: int = 100) -> list[dict]:
    return list(reversed(_RECORDS[-limit:]))
