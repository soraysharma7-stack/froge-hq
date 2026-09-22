"""Resource Governor + STOP ALL + degraded mode — independent of the AI model."""
from __future__ import annotations

import time

import psutil

from app.config.settings import settings
from app.events.bus import bus, EventType

_queued: list[dict] = []
_stop_all_engaged = False
_mode = "ONLINE"  # ONLINE / DEGRADED / OFFLINE
_overrides: dict[str, bool] = {}


def snapshot(active_employees: int, running_missions: int) -> dict:
    vm = psutil.virtual_memory()
    return {
        "cpu_percent": psutil.cpu_percent(interval=None),
        "ram_percent": vm.percent,
        "ram_used_mb": round(vm.used / 1024 / 1024),
        "ram_total_mb": round(vm.total / 1024 / 1024),
        "active_employees": active_employees,
        "max_active_agents": settings.max_active_agents,
        "browser_instances": 0,
        "max_browser_instances": settings.max_browser_instances,
        "queue_size": len(_queued),
        "max_queue_size": settings.max_queue_size,
        "running_missions": running_missions,
        "mode": _mode,
        "stop_all_engaged": _stop_all_engaged,
    }


def can_activate(active_employees: int) -> bool:
    """Bounded concurrency — queue instead of spawning unlimited agents."""
    return (not _stop_all_engaged) and active_employees < settings.max_active_agents


async def enqueue(item: dict) -> dict:
    if len(_queued) >= settings.max_queue_size:
        await bus.publish(EventType.RESOURCE_LIMIT, "Queue full — work rejected",
                          source="governor", severity="error")
        return {"queued": False, "reason": "queue_full"}
    item["queued_at"] = time.time()
    _queued.append(item)
    await bus.publish(EventType.RESOURCE_LIMIT, "Agent limit reached — work queued",
                      source="governor", severity="warning")
    return {"queued": True, "position": len(_queued)}


def dequeue() -> dict | None:
    return _queued.pop(0) if _queued else None


async def engage_stop_all(actor: str = "user") -> dict:
    """STOP ALL — deterministic, model-independent. Maya cannot override."""
    global _stop_all_engaged
    _stop_all_engaged = True
    await bus.publish("STOP_ALL", f"STOP ALL engaged by {actor}. New autonomous actions blocked.",
                      source="governor", severity="error")
    return {"stop_all": True, "actor": actor, "timestamp": time.time()}


async def release_stop_all(actor: str = "user") -> dict:
    global _stop_all_engaged
    _stop_all_engaged = False
    await bus.publish(EventType.SYSTEM, f"STOP ALL released by {actor}",
                      source="governor")
    return {"stop_all": False, "actor": actor, "timestamp": time.time()}


def stop_all_engaged() -> bool:
    return _stop_all_engaged


def set_degraded(component: str, degraded: bool) -> None:
    global _mode
    _overrides[component] = degraded
    _mode = "OFFLINE" if all(_overrides.values()) and _overrides else (
        "DEGRADED" if any(_overrides.values()) else "ONLINE")


def mode() -> str:
    return _mode
