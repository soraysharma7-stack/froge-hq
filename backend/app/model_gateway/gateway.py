"""FROGÉ MODEL GATEWAY — clean abstraction over the configured Arena AI Agent model/provider.

Rules (per spec):
- The model/provider comes ONLY from configuration (settings / environment).
- No model name is ever hard-coded.
- No silent fallback model. If the configured model is unavailable, we report
  a clear DEGRADED/error state.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum

from app.config.settings import settings
from app.events.bus import bus, EventType


class GatewayStatus(str, Enum):
    ONLINE = "ONLINE"
    DEGRADED = "DEGRADED"
    OFFLINE = "OFFLINE"
    UNCONFIGURED = "UNCONFIGURED"


@dataclass
class ModelRequest:
    prompt: str
    mission_id: str | None = None
    employee_id: str | None = None
    max_tokens: int = 1024


@dataclass
class ModelResponse:
    text: str
    latency_ms: float
    usage: dict | None = None          # only real provider-reported numbers, never invented
    error: str | None = None


@dataclass
class ModelGateway:
    """Single gateway for all model traffic."""

    status: GatewayStatus = field(init=False, default=GatewayStatus.UNCONFIGURED)
    requests_served: int = 0

    def __post_init__(self) -> None:
        self.refresh_status()

    def refresh_status(self) -> GatewayStatus:
        if not settings.model_name or not settings.model_provider:
            self.status = GatewayStatus.UNCONFIGURED
        else:
            # Phase 1: configuration presence = ONLINE. Real health probes arrive
            # with the provider adapter in a later phase.
            self.status = GatewayStatus.ONLINE
        return self.status

    def info(self) -> dict:
        return {
            "provider": settings.model_provider or None,
            "model": settings.model_name or None,
            "status": self.status.value,
            "requests_served": self.requests_served,
        }

    async def complete(self, request: ModelRequest) -> ModelResponse:
        """Send a completion request through the configured provider.

        Phase 1: if the provider is unconfigured we return a clear degraded
        response instead of pretending a model answered.
        """
        await bus.publish(
            EventType.MODEL_REQUEST_STARTED,
            f"Model request started (employee={request.employee_id})",
            source="model_gateway",
            mission_id=request.mission_id,
            employee_id=request.employee_id,
        )
        started = time.perf_counter()
        self.refresh_status()

        if self.status != GatewayStatus.ONLINE:
            latency = (time.perf_counter() - started) * 1000
            await bus.publish(
                EventType.MODEL_REQUEST_COMPLETED,
                "Model request failed: provider unconfigured",
                source="model_gateway",
                severity="error",
                mission_id=request.mission_id,
                employee_id=request.employee_id,
            )
            return ModelResponse(
                text="",
                latency_ms=latency,
                error="MODEL_UNAVAILABLE: configured Arena AI Agent model/provider is not set. "
                      "Set FROGE_MODEL_PROVIDER and FROGE_MODEL_NAME in the environment.",
            )

        # Phase 1 placeholder adapter: the real Arena provider call lands here.
        # We do NOT fake model output — we return a deterministic orchestration
        # response labeled as such until the provider adapter is wired.
        latency = (time.perf_counter() - started) * 1000
        self.requests_served += 1
        await bus.publish(
            EventType.MODEL_REQUEST_COMPLETED,
            f"Model request completed in {latency:.0f}ms",
            source="model_gateway",
            mission_id=request.mission_id,
            employee_id=request.employee_id,
            metadata={"latency_ms": latency},
        )
        return ModelResponse(
            text="[gateway: configured provider adapter pending — deterministic orchestrator response]",
            latency_ms=latency,
            usage=None,
        )


gateway = ModelGateway()
