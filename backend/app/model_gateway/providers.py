"""Model provider adapters for the FROGÉ ModelGateway.

Every provider is configured ONLY via environment variables:
    FROGE_MODEL_PROVIDER   e.g. "openai", "openai-compatible", "arena"
    FROGE_MODEL_NAME       e.g. a model name supplied by config
    FROGE_MODEL_API_BASE   endpoint URL (for OpenAI-compatible / local endpoints)
    FROGE_MODEL_API_KEY    provider key, from env — never hard-coded
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request

from app.config.settings import settings


class ProviderError(Exception):
    """Raised when a configured provider call fails. Message is the real error."""


async def complete_openai_compatible(prompt: str, max_tokens: int = 1024,
                                     model: str | None = None) -> dict:
    """Call an OpenAI-compatible chat-completions endpoint."""
    chosen = model or settings.model_name
    if not chosen:
        raise ProviderError("MODEL_UNAVAILABLE: FROGE_MODEL_NAME is not set.")
    if not settings.model_api_base:
        raise ProviderError("MODEL_UNAVAILABLE: FROGE_MODEL_API_BASE is not set.")

    base = settings.model_api_base.rstrip("/")
    url = base if base.endswith("/chat/completions") else f"{base}/chat/completions"

    payload = {
        "model": chosen,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
    }
    body = json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if settings.model_api_key:
        headers["Authorization"] = f"Bearer {settings.model_api_key}"

    request = urllib.request.Request(url, data=body, headers=headers, method="POST")

    def _call() -> dict:
        try:
            with urllib.request.urlopen(request, timeout=120) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:300]
            raise ProviderError(f"PROVIDER_HTTP_{exc.code}: {detail}") from exc
        except urllib.error.URLError as exc:
            raise ProviderError(f"PROVIDER_UNREACHABLE: {exc.reason}") from exc
        choice = (data.get("choices") or [{}])[0]
        text = (choice.get("message") or {}).get("content", "")
        return {"text": text, "usage": data.get("usage")}

    import asyncio
    return await asyncio.to_thread(_call)


async def provider_complete(prompt: str, max_tokens: int = 1024,
                            model: str | None = None) -> dict:
    """Dispatch to the adapter for the configured provider."""
    provider = (settings.model_provider or "").lower()
    if provider in {"openai", "openai-compatible", "arena", "local", "ollama", "openrouter"}:
        return await complete_openai_compatible(prompt, max_tokens=max_tokens, model=model)
    raise ProviderError(
        f"PROVIDER_UNSUPPORTED: '{settings.model_provider}' has no adapter. "
        "Supported: openai, openai-compatible, arena, local, ollama, openrouter "
        "(all via an OpenAI-compatible chat-completions endpoint)."
    )
