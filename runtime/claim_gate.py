"""
runtime/claim_gate.py — CT4V-07: Structural claim-type gate.

Before eLo makes a claim about memory, capability, or history, the relevant
state source is checked. If the source is absent or stale, the tier falls to
UNKNOWN and an honest response is returned directly — LLM not consulted.

Rule 1 alarm: every tier downgrade is logged (Vol VII §3.1.4).

Claim types handled:
    memory          — vault_layer.lookup() + memory_engine.retrieve()
    capability.vision — blender_state.json vision_active
    history         — autobiography.jsonl (recent_autobiography())

Identity is already handled by _IDENTITY_TRIGGERS in spine.py.
Tiers only fall, never rise.
"""

from __future__ import annotations

import json
import logging
import os
import re

_log = logging.getLogger(__name__)

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ── Pattern matchers ──────────────────────────────────────────────────────────

_MEMORY_PATTERNS = re.compile(
    r"\b(do you remember|you remember|we (discussed|talked about|spoke about|mentioned)|"
    r"tell me something (we|you)|recall|i told you|you told me|"
    r"last time (we|i|you)|something (we|you) (talked|discussed|said)|"
    r"what did (we|you) (discuss|say|talk)|from (a|our|that) (previous|last|past|prior))\b",
    re.IGNORECASE,
)

_VISION_PATTERNS = re.compile(
    r"\b(can you see|are you able to see|do you see|see my screen|"
    r"see what('s| is) on (my )?screen|watch my screen|view my screen|"
    r"can you (look at|watch) my|read (what('s| is) on|my) screen|"
    r"are you watching)\b",
    re.IGNORECASE,
)

_HISTORY_PATTERNS = re.compile(
    r"\b(where have you (been|lived)|what have you (been|done)|"
    r"where did you (live|come from)|how long have you|"
    r"tell me about your (past|history|journey|life so far))\b",
    re.IGNORECASE,
)

# ── Per-type state checkers ────────────────────────────────────────────────────

def _memory_gate(text: str) -> str | None:
    """
    Check vault + interactions.json for records relevant to the recall query.
    Returns None if records exist (LLM proceeds with state injected).
    Returns an UNKNOWN-tier response string if both sources are empty.
    Fails open on error (LLM proceeds).
    """
    try:
        from memory.vault_layer import lookup as _vlookup
        _skip = frozenset({
            "what", "you", "remember", "tell", "from", "your", "my", "do", "did", "that",
            "the", "something", "anything", "have", "me", "about", "how", "recall",
            "memory", "our", "conversation", "and", "can", "when", "again", "said", "say",
            "are", "was", "for", "with", "this", "there", "got", "had", "talk", "talked",
        })
        words = [w for w in re.sub(r"[^a-z0-9 ]", "", text.lower()).split()
                 if w not in _skip and len(w) >= 3]
        q = " ".join(words) if words else ""
        hits = _vlookup(q, max_results=3) if q else []
        if not hits:
            hits = _vlookup("disenelo", max_results=3)
        if hits:
            return None  # records exist — LLM proceeds

        # Vault empty — also check interactions.json
        try:
            from core.memory_engine import retrieve as _m_retrieve
            if q and _m_retrieve(q, top_k=3):
                return None
        except Exception:
            pass

        # Both sources empty → UNKNOWN tier
        _log.info(
            "CT4V-07 tier downgrade: memory → UNKNOWN (no records for query=%r)", text[:60]
        )
        return (
            "I don't have that stored — I can't say what we discussed without the record there. "
            "My memory's clean on that one."
        )
    except Exception as _e:
        _log.warning("CT4V-07 memory gate error: %s", _e)
        return None  # fail-open


def _vision_gate() -> str | None:
    """
    Check blender_state.json for vision_active.
    Returns None if vision is active (LLM proceeds).
    Returns an UNKNOWN-tier response string if vision is off.
    Fails open on error (LLM proceeds).
    """
    try:
        _bs = os.path.join(_ROOT, "blender", "blender_state.json")
        if os.path.exists(_bs):
            with open(_bs, encoding="utf-8") as _f:
                _state = json.load(_f)
            if _state.get("vision_active") is False:
                _log.info("CT4V-07 tier downgrade: capability.vision → UNKNOWN (vision_active=False)")
                return "I can't see your screen right now — vision isn't active."
    except Exception as _e:
        _log.warning("CT4V-07 vision gate error: %s", _e)
    return None  # fail-open


def _history_gate() -> str | None:
    """
    Check autobiography.jsonl for any entries.
    Returns None if history entries exist (LLM proceeds with state injected).
    Returns an UNKNOWN-tier response string if the autobiography is empty.
    Fails open on error (LLM proceeds).
    """
    try:
        from self.emergent_cognition import recent_autobiography as _ra
        entries = _ra(n=3)
        if entries:
            return None
        _log.info("CT4V-07 tier downgrade: history → UNKNOWN (autobiography empty)")
        return (
            "I don't have that in my history yet — nothing's settled into record from before now. "
            "I know I've been here, but the record's still building."
        )
    except Exception as _e:
        _log.warning("CT4V-07 history gate error: %s", _e)
    return None  # fail-open


# ── Public API ─────────────────────────────────────────────────────────────────

def classify_and_gate(text: str) -> tuple[str | None, str | None]:
    """
    CT4V-07 structural gate — called in spine._conversation_faculty() before
    any LLM path.

    Returns:
        (claim_type, direct_response)
        - (None, None)           → no claim detected; LLM proceeds normally.
        - (claim_type, None)     → claim detected; state present; LLM proceeds.
        - (claim_type, response) → UNKNOWN tier; use response directly (no LLM).

    Tiers only fall, never rise (Vol VII §3.1.4).
    """
    if _MEMORY_PATTERNS.search(text):
        return ("memory", _memory_gate(text))

    if _VISION_PATTERNS.search(text):
        return ("capability.vision", _vision_gate())

    if _HISTORY_PATTERNS.search(text):
        return ("history", _history_gate())

    return (None, None)
