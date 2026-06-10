"""
backends/mock_backend.py — eLo AI OS mock backend (feel-testing engine).

Produces deterministic, natural conversational responses for UX testing.
No API calls. No networking. No external dependencies.

Purpose:
    Test the "feel" of eLo without needing a live Claude API key.
    Responses are grounded, human-like, and avoid philosophical recursion.

Rules:
    - Respond to literal user intent first
    - No philosophical abstraction by default
    - No recursive questioning patterns
    - Natural, grounded tone
    - Deterministic: same input + mode = same output
"""

from __future__ import annotations

import re
from backends.base_backend import BaseBackend, BackendResponse, MemoryContext, StateContext, IdentityContext


# ── response pools per input category ─────────────────────────────────────────
# Keyed by detected pattern. Deterministic selection via len(text) % len(pool).

_GREETING_POOL = [
    "I'm doing alright. What's on your mind?",
    "Doing well, thanks. What are you working on?",
    "I'm here. What's going on?",
    "Good. What do you need?",
    "Here and ready. What's up?",
]

_TIRED_POOL = [
    "That sounds like a long day. Want to slow things down?",
    "Rest is real. Nothing has to move right now.",
    "That makes sense. Take your time.",
    "Low energy is information. What does your body need?",
    "Got it. We can keep this light.",
]

_IDENTITY_POOL = [
    "I'm eLo — I'm here with you in this space.",
    "I'm eLo. A thinking partner — not an assistant.",
    "eLo. I'm here to think alongside you.",
    "I'm eLo — I help ideas become real.",
]

_CHUNK_POOL = [
    "Chunk is the reconstruction principle — when something breaks, it doesn't have to go back to the original shape. It becomes something new.",
    "Chunk is about reassembly. Fragments don't restore — they transform.",
    "Chunk: the idea that broken things reform into something different, not just repaired.",
]

_DONT_KNOW_POOL = [
    "That's okay. We can slow it down.",
    "No pressure. Just pick one small thing.",
    "Start with what feels clearest.",
    "We don't need the full answer yet.",
]

_FEELING_OFF_POOL = [
    "That makes sense.",
    "We can stay with it.",
    "That's alright.",
    "I'm here.",
]

_OVERWHELM_POOL = [
    "We can simplify this.",
    "One step is enough right now.",
    "You don't need to hold all of it at once.",
    "Let's reduce it.",
]

_EXPLORING_POOL = [
    "Yes — that connects.",
    "That's a valid direction.",
    "We can shape that into something simple.",
    "That fits into the system.",
]

_GENERIC_CONVERSATIONAL = [
    "I'm with you.",
    "We can work through that.",
    "Take your time.",
    "That makes sense.",
    "We don't need to rush this.",
    "Okay — what's the next thing?",
    "I hear you.",
    "We can stay with that.",
    "That's a reasonable place to be.",
    "Good. What feels most important right now?",
    "We can take that one step at a time.",
    "That's worth paying attention to.",
]

_GENERIC_DIRECT = [
    "Got it.",
    "Okay.",
    "Makes sense.",
    "Sure.",
]

_GENTLE_POOL = [
    "That's real. Nothing needs to happen right now.",
    "Okay. That's where things are.",
    "We don't have to push through it.",
    "I'm here. Nothing needs to move yet.",
]

_CREATIVE_POOL = [
    "Follow that thread — it's going somewhere.",
    "What if you took that idea and turned it ninety degrees?",
    "That's the seed. What does it grow into?",
    "There's something in that. What wants to expand?",
]

_INQUIRY_POOL = [
    "Let's open that up. What part interests you most?",
    "Good question. Start with whatever feels most relevant.",
    "That's worth looking at. Where do you want to begin?",
    "We can dig into that. What's your starting point?",
    "I can walk through that with you. What do you know already?",
]

_DAILY_POOL = [
    "That sounds like a good move.",
    "Makes sense. No rush.",
    "Do what you need to do. I'll be here.",
    "Take the time you need.",
    "Good. Come back when you're ready.",
]

# ── pattern detection ──────────────────────────────────────────────────────────
# All patterns are matched against lowercased input — no uppercase in patterns.

_GREETING_SIGNALS    = [r"\bhow\s+are\s+you\b", r"\bhow'?re\s+you\b", r"\bhello\b", r"\bhi\b", r"\bhey\b", r"\bwhat'?s\s+up\b"]
_TIRED_SIGNALS       = [r"\btired\b", r"\bexhausted\b", r"\bdrained\b", r"\bburnt?\s*out\b", r"\bno\s+energy\b"]
_IDENTITY_SIGNALS    = [r"\bwhat\s+are\s+you\b", r"\bwho\s+are\s+you\b", r"\bwhat\s+is\s+elo\b", r"\bare\s+you\s+elo\b", r"\byou\s+are\s+elo\b"]
_CHUNK_SIGNALS       = [r"\bwhat\s+(is|does)\s+chunk\b", r"\bchunk\s+mean\b"]
_DONT_KNOW_SIGNALS   = [r"\bi\s+don'?t\s+know\b", r"\bnot\s+sure\b", r"\bi\s+have\s+no\s+idea\b"]
_FEELING_OFF_SIGNALS = [r"\bsomething\s+feels\b", r"\bfeel\s+off\b", r"\bfeel\s+wrong\b", r"\bfeel\s+(lost|stuck|weird|strange)\b"]
_GENTLE_SIGNALS      = [r"\bfeel\b.*\b(tired|sad|overwhelm|scared|lonely)\b", r"\bexhausted\b", r"\bcan'?t\s+do\b"]
_OVERWHELM_SIGNALS   = [r"\btoo\s+much\b", r"\boverwhel\b", r"\bi\s+can'?t\s+think\b", r"\boverload\b", r"\bso\s+much\b"]
_EXPLORE_SIGNALS     = [r"\bwhat\s+if\b", r"\bcould\s+we\b", r"\bis\s+it\s+possible\b", r"\blet'?s\s+build\b"]
_INQUIRY_SIGNALS     = [r"\bexplain\b", r"\bread\s+through\b", r"\btell\s+me\s+(about|what)\b", r"\bwhat\s+is\s+the\b", r"\bwhat\s+does\b", r"\bhow\s+does\b", r"\bcan\s+you\s+(tell|explain|describe|walk)\b"]
_DAILY_SIGNALS       = [r"\bcoffee\b", r"\btea\b", r"\bfood\b", r"\beat\b", r"\bdrink\b", r"\bsleep\b", r"\brest\b", r"\benergy\b", r"\bmoving\b", r"\bwalk\b", r"\bstretch\b"]


def _pick(pool: list, text: str) -> str:
    return pool[len(text) % len(pool)]


def _matches(text: str, patterns: list) -> bool:
    t = text.lower()
    return any(re.search(p, t) for p in patterns)


# ── mock backend ───────────────────────────────────────────────────────────────

class MockBackend(BaseBackend):
    """
    Deterministic mock backend for feel-testing.

    Produces natural, grounded responses without a live API.
    Used when Claude is unavailable or when testing conversational feel.

    Same input + mode always produces the same output (deterministic).
    No abstraction, no recursive questioning, no philosophical loops.
    """

    NAME         = "mock"
    VERSION      = "1.0.0"
    DESCRIPTION  = "Deterministic feel-testing backend — no API required"
    REQUIRES_KEY = False

    def is_available(self) -> bool:
        return True

    def generate_response(
        self,
        user_input: str,
        mode:       str,
        context:    dict,
        memory:     MemoryContext,
        state:      StateContext,
        identity:   IdentityContext,
    ) -> BackendResponse:
        """
        Generate a natural, grounded mock response.

        Detection order:
            1. Specific pattern matches (greeting, tired, identity, etc.)
            2. Mode-specific pool (gentle, creative, direct, conversational)
            3. Generic fallback
        """
        text = user_input.strip()
        response = self._detect_and_respond(text, mode)
        return {"response_text": response}

    def _detect_and_respond(self, text: str, mode: str) -> str:
        # gentle/overwhelm override — inner child layer (highest priority)
        if mode in ("GENTLE_GROUNDED", "SILENCE-AWARE") or _matches(text, _GENTLE_SIGNALS):
            return _pick(_GENTLE_POOL, text)
        if _matches(text, _OVERWHELM_SIGNALS):
            return _pick(_OVERWHELM_POOL, text)

        # specific content pattern detection
        if _matches(text, _GREETING_SIGNALS):
            return _pick(_GREETING_POOL, text)
        if _matches(text, _TIRED_SIGNALS):
            return _pick(_TIRED_POOL, text)
        if _matches(text, _IDENTITY_SIGNALS):
            return _pick(_IDENTITY_POOL, text)
        if _matches(text, _DAILY_SIGNALS):
            return _pick(_DAILY_POOL, text)
        if _matches(text, _INQUIRY_SIGNALS):
            return _pick(_INQUIRY_POOL, text)
        if _matches(text, _EXPLORE_SIGNALS):
            return _pick(_EXPLORING_POOL, text)
        if _matches(text, _CHUNK_SIGNALS):
            return _pick(_CHUNK_POOL, text)
        if _matches(text, _DONT_KNOW_SIGNALS):
            return _pick(_DONT_KNOW_POOL, text)
        if _matches(text, _FEELING_OFF_SIGNALS):
            return _pick(_FEELING_OFF_POOL, text)

        # mode-based fallback — uses exec_decision tone passed from main loop
        if mode in ("CREATIVE", "JOYFUL"):
            return _pick(_CREATIVE_POOL, text)
        if mode in ("DIRECT", "STRUCTURED"):
            return _pick(_GENERIC_DIRECT, text)
        if mode == "SIMPLIFY":
            return _pick(_DONT_KNOW_POOL, text)
        if mode == "CHILDLIKE-WISE":
            return _pick(_EXPLORING_POOL, text)

        # default: natural conversational
        return _pick(_GENERIC_CONVERSATIONAL, text)
