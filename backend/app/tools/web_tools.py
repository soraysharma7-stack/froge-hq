"""Real web tools — sandboxed network access for research missions.

The AI proposes the query; the backend validates and executes the fetch.
Outbound HTTP only to allow-listed, read-only search endpoints. No arbitrary
URL fetching (that would be an SSRF hole); results are truncated and audited.
"""
from __future__ import annotations

import json
import urllib.parse
import urllib.request
import urllib.error

_UA = {"User-Agent": "FROGE-HQ/1.0 (+https://froge-hq.onrender.com)"}
_MAX_BODY = 4000  # never return unbounded payloads to the loop


class WebToolError(Exception):
    pass


def web_search(query: str, max_results: int = 5) -> dict:
    """DuckDuckGo Instant Answer API — free, no key, read-only.

    Returns a compact, bounded result set. This is a real network call;
    if the network is unreachable the error is reported, not faked.
    """
    q = (query or "").strip()
    if not q:
        raise WebToolError("web_search: empty query")
    if len(q) > 300:
        raise WebToolError("web_search: query too long")

    params = urllib.parse.urlencode({
        "q": q, "format": "json", "no_html": 1, "skip_disambig": 1,
    })
    url = f"https://api.duckduckgo.com/?{params}"
    req = urllib.request.Request(url, headers=_UA)
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="replace"))
    except urllib.error.URLError as exc:
        raise WebToolError(f"web_search unreachable: {exc.reason}") from exc
    except Exception as exc:  # malformed json etc.
        raise WebToolError(f"web_search failed: {exc}") from exc

    results: list[dict] = []
    if data.get("AbstractText"):
        results.append({
            "title": data.get("Heading", q),
            "snippet": data["AbstractText"][:400],
            "url": data.get("AbstractURL", ""),
        })
    for topic in (data.get("RelatedTopics") or []):
        if len(results) >= max_results:
            break
        if isinstance(topic, dict) and topic.get("Text"):
            results.append({
                "title": (topic.get("Text") or "")[:80],
                "snippet": topic["Text"][:400],
                "url": topic.get("FirstURL", ""),
            })

    return {
        "query": q,
        "count": len(results),
        "results": results[:max_results],
        "source": "duckduckgo_instant_answer",
        "note": "Bounded instant-answer results; not a full web crawl.",
    }
