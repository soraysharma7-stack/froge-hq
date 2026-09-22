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
from app.model_gateway.providers import provider_complete, ProviderError


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
    last_error: str | None = None

    def __post_init__(self) -> None:
        self.refresh_status()

    def refresh_status(self) -> GatewayStatus:
        if not settings.model_name or not settings.model_api_base:
            self.status = GatewayStatus.UNCONFIGURED
        else:
            # Configuration present. A failed provider call flips us to DEGRADED
            # with the real error; a successful one flips back to ONLINE.
            if self.status == GatewayStatus.UNCONFIGURED:
                self.status = GatewayStatus.ONLINE
        return self.status

    def info(self) -> dict:
        return {
            "provider": settings.model_provider or None,
            "model": settings.model_name or None,
            "api_base": settings.model_api_base or None,
            "api_key_set": bool(settings.model_api_key),
            "status": self.status.value,
            "requests_served": self.requests_served,
            "last_error": self.last_error,
        }

    async def complete(self, request: ModelRequest) -> ModelResponse:
        """Send a completion request through the configured provider.

        If the provider is unconfigured or its call fails we return a clear
        degraded response with the real error instead of pretending a model
        answered.
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

        if self.status == GatewayStatus.UNCONFIGURED:
            return await self._fail(
                request,
                started,
                "MODEL_UNAVAILABLE: model/provider not configured. Set FROGE_MODEL_NAME, "
                "FROGE_MODEL_API_BASE (and FROGE_MODEL_API_KEY if needed) in the environment.",
            )

        try:
            result = await provider_complete(request.prompt, max_tokens=request.max_tokens)
        except ProviderError as exc:
            self.status = GatewayStatus.DEGRADED
            self.last_error = str(exc)
            return await self._fail(request, started, str(exc))

        latency = (time.perf_counter() - started) * 1000
        self.requests_served += 1
        self.status = GatewayStatus.ONLINE
        self.last_error = None
        await bus.publish(
            EventType.MODEL_REQUEST_COMPLETED,
            f"Model request completed in {latency:.0f}ms",
            source="model_gateway",
            mission_id=request.mission_id,
            employee_id=request.employee_id,
            metadata={"latency_ms": latency},
        )
        return ModelResponse(text=result["text"], latency_ms=latency, usage=result.get("usage"))

    async def _fail(self, request: ModelRequest, started: float, error: str) -> ModelResponse:
        latency = (time.perf_counter() - started) * 1000
        await bus.publish(
            EventType.MODEL_REQUEST_COMPLETED,
            f"Model request failed: {error[:120]}",
            source="model_gateway",
            severity="error",
            mission_id=request.mission_id,
            employee_id=request.employee_id,
            metadata={"latency_ms": latency},
        )
        return ModelResponse(text="", latency_ms=latency, error=error)


gateway = ModelGateway()
