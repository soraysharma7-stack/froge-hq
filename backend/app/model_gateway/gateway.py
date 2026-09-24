"""FROGÉ MODEL GATEWAY — clean abstraction over the configured Arena AI Agent model/provider.

Rules (per spec):
- The model/provider comes ONLY from configuration (settings / environment).
- No model name is ever hard-coded.
- No silent fallback model. If the configured model is unavailable, we walk the
  configured fallback list and report which model actually answered, or degrade
  honestly if every configured model fails.
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
            "active_model": getattr(self, "active_model", None),
            "candidate_models": self.candidate_models(),
            "requests_served": self.requests_served,
            "last_error": self.last_error,
        }

    def candidate_models(self) -> list[str]:
        """Models to try, in order. The configured model is always tried first;
        optional FROGE_MODEL_FALLBACKS (comma-separated) provides alternates.
        Only models you configured are ever used — nothing is invented."""
        ordered: list[str] = []
        if settings.model_name:
            ordered.append(settings.model_name)
        extra = getattr(settings, "model_fallbacks", "") or ""
        for name in (n.strip() for n in extra.split(",")):
            if name and name not in ordered:
                ordered.append(name)
        return ordered

    async def complete(self, request: ModelRequest) -> ModelResponse:
        """Send a completion request through the configured provider.

        Tries the configured model first; on a clear failure it walks the
        configured fallback list and reports which model actually answered.
        If the provider is unconfigured or every call fails we return a clear
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

        result = None
        last_exc: Exception | None = None
        used_model: str | None = None
        tried: list[str] = []
        for model in self.candidate_models() or [None]:
            tried.append(model or "<none>")
            try:
                result = await provider_complete(request.prompt, max_tokens=request.max_tokens,
                                                 model=model)
                used_model = model
                break
            except ProviderError as exc:
                last_exc = exc
                continue
        if result is None:
            self.status = GatewayStatus.DEGRADED
            self.last_error = str(last_exc)
            return await self._fail(request, started,
                                    f"all configured models failed ({', '.join(tried)}): {last_exc}")

        latency = (time.perf_counter() - started) * 1000
        self.requests_served += 1
        self.status = GatewayStatus.ONLINE
        self.last_error = None
        self.active_model = used_model
        await bus.publish(
            EventType.MODEL_REQUEST_COMPLETED,
            f"Model request completed in {latency:.0f}ms (model={used_model})",
            source="model_gateway",
            mission_id=request.mission_id,
            employee_id=request.employee_id,
            metadata={"latency_ms": latency, "model": used_model},
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
