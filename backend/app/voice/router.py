"""Voice architecture — STT → COMMAND ROUTER → MAYA → AGENT SYSTEM → TTS.

English, Hindi, Roman Hindi, and Hinglish commands. Voice never bypasses permissions.
"""
from __future__ import annotations

import re

# Roman Hindi / Hinglish intent markers
_PATTERNS = [
    (r"(bana\s?do|banao|build|create|make)", "create"),
    (r"(research|khojo|dhundo|search)", "research"),
    (r"(report|ripot)", "report"),
    (r"(roko|band\s?karo|stop)", "stop"),
    (r"(bhejo|send)", "send"),
    (r"(task\s?do|assign|ko\s?ye\s?task)", "assign"),
    (r"(status|kya\s?ho\s?raha)", "status"),
]

_LANG_HINTS = {
    "hi": ["kar", "karo", "banao", "do", "hai", "raha", "chahiye", "mujhe", "ye", "ko"],
}


def detect_language(text: str) -> str:
    if re.search(r"[\u0900-\u097F]", text):
        return "hi"
    words = set(re.findall(r"[a-z]+", text.lower()))
    if len(words & set(_LANG_HINTS["hi"])) >= 2:
        return "hinglish"
    return "en"


def route(utterance: str) -> dict:
    """Parse a voice/text command into an intent. Permissions enforced downstream."""
    lang = detect_language(utterance)
    intents = [intent for pattern, intent in _PATTERNS if re.search(pattern, utterance.lower())]
    return {
        "utterance": utterance,
        "language": lang,
        "intents": intents or ["status"],
        "note": "Voice commands pass through the same policy engine as any action.",
    }
