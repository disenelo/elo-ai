"""
runtime/turn_result.py — S2 Phase 1: one shape for every turn.

STACK.md Phase 1: "Single string → {inner_thought, response, emotion,
intent}".

The main return already carries all four. Audited with ast over
_process_turn(): 43 of its 52 returns are turn-shaped, and 41 of those 43
carry only {"response", "mode", "backend"} — every fast path, every bypass,
the file agent, the identity answers, the animation commands. Only the main
return and one dream return are complete.

So a consumer reading result["intent"] gets a KeyError on a fast path, and
inner_thought is simply absent rather than empty — indistinguishable from a
turn where eLo thought nothing.

Normalised at the single call site (server.py:7777) rather than at 41
return statements. Same reasoning as putting the spoken-log write inside
speak() and the SPG link inside record_claim(): one chokepoint covers every
existing exit and the next one added.

NOTHING IS INVENTED. The defaults are honest:
  inner_thought  ""        — no second pass ran on a fast path, and ""
                             says that. A placeholder sentence would be
                             authored text passed off as eLo's thought,
                             which is the exact thing I was caught doing
                             on 2026-09-29.
  emotion        "neutral" — already the documented default on the error
                             return.
  intent         mode      — not a guess. On the main path intent and mode
                             are the SAME value (_action), so taking mode
                             follows the convention the turn already uses.
"""
from __future__ import annotations

import logging

_log = logging.getLogger("elo.turn_result")

REQUIRED_KEYS = ("inner_thought", "response", "emotion", "intent")


def normalise(result) -> dict:
    """
    Return a turn result carrying all four Phase 1 keys.

    Never raises, never overwrites a value the turn already set.
    """
    if result is None:
        _log.warning("turn produced no result at all — returning an empty turn")
        return {"inner_thought": "", "response": "", "emotion": "neutral",
                "intent": "error", "mode": "error", "backend": "error"}

    if isinstance(result, str):
        # Defensive: the pre-Phase-1 shape was a bare string.
        result = {"response": result}

    if not isinstance(result, dict):
        _log.warning("turn result was %s, not a dict", type(result).__name__)
        return {"inner_thought": "", "response": str(result), "emotion": "neutral",
                "intent": "unknown", "mode": "unknown", "backend": "unknown"}

    out = dict(result)
    out.setdefault("response", "")
    out.setdefault("inner_thought", "")
    out.setdefault("emotion", "neutral")
    # mode is what a fast path sets; on the main path intent == mode.
    out.setdefault("intent", out.get("mode") or "")
    out.setdefault("mode", out.get("intent") or "")
    return out


def is_complete(result) -> bool:
    """True when every Phase 1 key is present."""
    return isinstance(result, dict) and all(k in result for k in REQUIRED_KEYS)
