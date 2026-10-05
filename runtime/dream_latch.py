"""
runtime/dream_latch.py — hold a dream request that a turn would otherwise erase.

David, 2026-10-05: "How would it work if it isn't triggered and eLo is active?"

It would not. Measured: intent="dream" was injected at 16:51:12, and 25 turns
were spoken before the ambient callback next ran. By then `intent` read
"conversation". The request was gone.

THE DEFECT. The drain-to-sleep chain carries the request in
blender_state.json's `intent` field, and every turn writes that field. The
gate that reads it lives in ambient_thought(), which fires every 8-20
minutes. So the request survives only if eLo stays completely idle for up to
twenty minutes — and a single message destroys it. Builder 1's trigger fires
on "battery low + calm", and calm does not stop David speaking.

THE FIX. Latch fast, consume slow. ambient_engine's poll loop runs every
0.5s and already reads blender_state every tick; when it sees a dream
request it copies it here, where a turn cannot reach it. The 8-20 minute
callback then consumes the latch instead of racing the conversation.

`intent` stays the signalling channel, so Builder 1's trigger side needs no
change and Unity keeps reading `intent` for the lay-down pose.
"""
from __future__ import annotations

import json
import logging
import os
import time

_log = logging.getLogger("elo.dream_latch")

_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data", "dream_request.json",
)

# A request older than this is stale — eLo's battery or calm state has very
# likely moved on, and waking him for a request from an hour ago is worse
# than missing it.
_MAX_AGE_S = 1800.0


def latch(reason: str = "intent") -> bool:
    """Record that a dream was requested. Idempotent while one is pending."""
    if pending():
        return False
    try:
        os.makedirs(os.path.dirname(_PATH), exist_ok=True)
        with open(_PATH, "w", encoding="utf-8") as f:
            json.dump({"_ts": time.time(), "reason": reason}, f)
        _log.info("dream request latched (%s) — safe from the next turn", reason)
        return True
    except Exception:
        return False


def pending() -> bool:
    """True if a fresh request is waiting. Stale ones are dropped."""
    try:
        with open(_PATH, encoding="utf-8") as f:
            ts = float((json.load(f) or {}).get("_ts", 0) or 0)
    except Exception:
        return False
    if ts <= 0:
        return False
    if time.time() - ts > _MAX_AGE_S:
        clear()
        _log.info("dream request expired unused after %.0fs", _MAX_AGE_S)
        return False
    return True


def take() -> bool:
    """Consume a pending request. True if one was waiting."""
    if not pending():
        return False
    clear()
    return True


def clear() -> None:
    try:
        if os.path.exists(_PATH):
            os.remove(_PATH)
    except Exception:
        pass
