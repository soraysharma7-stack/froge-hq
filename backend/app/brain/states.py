"""Agent state machine — the full state set the Visual Office displays."""
from __future__ import annotations

from enum import Enum


class BrainState(str, Enum):
    DORMANT = "DORMANT"
    AVAILABLE = "AVAILABLE"
    PLANNING = "PLANNING"
    QUEUED = "QUEUED"
    ACTIVE = "ACTIVE"
    WAITING_TOOL = "WAITING_TOOL"
    WAITING_APPROVAL = "WAITING_APPROVAL"
    VERIFYING = "VERIFYING"
    BLOCKED = "BLOCKED"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
