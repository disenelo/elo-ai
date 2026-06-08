"""
dashboard/event_bus.py — Thread-safe event queue for kernel decision cycles.

Events are pushed here by the observer and consumed by the SSE server.
Does NOT modify any kernel or engine source file.
"""

import queue
import json
from datetime import datetime


# ── event schema ───────────────────────────────────────────────────────────────

def build_event(
    user_input:     str,
    classification: dict,
    assembled:      dict,
    mode:           str,
    routing_reason: str,
) -> dict:
    """
    Build a structured dashboard event from the raw kernel decision data.
    This is the canonical event schema exposed on the /stream endpoint.
    """
    # memory snapshot — safe reads with defaults
    mem = assembled.get("memory", {})
    st  = assembled.get("state",  {})
    em  = assembled.get("emotion",{})
    id_ = assembled.get("identity",{})

    return {
        "timestamp":  datetime.utcnow().isoformat() + "Z",
        "input":      user_input,
        "mode":       mode,
        "reason":     routing_reason,
        "loop":       assembled.get("loop_detected", False),
        "loop_reason":assembled.get("loop_reason",   ""),

        "memory_snapshot": {
            "tone":            mem.get("tone",            "neutral"),
            "project":         mem.get("project",         "elo_core"),
            "returning_theme": mem.get("returning_theme", ""),
            "symbolic_echo":   mem.get("symbolic_echo",   ""),
            "confidence":      assembled.get("tone_confidence", None),
            "drift":           assembled.get("tone_drift",      None),
        },

        "emotion_snapshot": {
            "emotion": em.get("label",  em.get("emotion", "neutral")),
            "tone":    em.get("tone",   "warm"),
            "pacing":  em.get("pacing", "moderate"),
            "warmth":  em.get("warmth", 0.7),
        },

        "state_snapshot": {
            "name":        st.get("name",        "exploring"),
            "tone_bias":   st.get("tone_bias",   "open"),
            "weight":      st.get("weight",      0.5),
            "pacing_bias": st.get("pacing_bias", "moderate"),
        },

        "identity_snapshot": {
            "perspective": id_.get("perspective", ""),
            "intent":      id_.get("intent",      ""),
            "bias":        id_.get("bias",         ""),
        },

        "classification": {
            "type":       classification.get("type") or _resolve_type(classification),
            "factual":    classification.get("is_factual",   False),
            "creative":   classification.get("is_creative",  False),
            "emotional":  classification.get("is_emotional", False),
            "distorted":  classification.get("is_distorted", False),
            "entities":   classification.get("entities",     []),
        },
    }


def _resolve_type(flags: dict) -> str:
    """Local copy — avoids importing kernel (no coupling)."""
    if flags.get("is_factual"):   return "INFORMATION_REQUEST"
    if flags.get("is_project"):   return "PROJECT_QUERY"
    if flags.get("is_emotional") or flags.get("is_distorted"): return "EMOTIONAL"
    if flags.get("is_creative"):  return "CREATIVE"
    if flags.get("is_uncertainty"): return "UNCERTAINTY"
    return "CONVERSATION"


# ── thread-safe queue ─────────────────────────────────────────────────────────

_bus: queue.Queue = queue.Queue(maxsize=500)
_history: list    = []
_MAX_HISTORY      = 100


def push(event: dict):
    """Push an event onto the bus. Drops oldest if full."""
    _history.append(event)
    if len(_history) > _MAX_HISTORY:
        _history.pop(0)
    try:
        _bus.put_nowait(event)
    except queue.Full:
        try:
            _bus.get_nowait()   # drop oldest
        except queue.Empty:
            pass
        _bus.put_nowait(event)


def subscribe(timeout: float = 1.0):
    """
    Generator — yields events as they arrive.
    Blocks up to timeout seconds between events.
    Use in SSE handlers.
    """
    while True:
        try:
            yield _bus.get(timeout=timeout)
        except queue.Empty:
            yield None   # heartbeat tick — caller decides what to do


def recent(n: int = 50) -> list:
    """Return the last N events from history (newest last)."""
    return _history[-n:]


def to_sse(event: dict) -> str:
    """Format an event dict as an SSE data line."""
    return f"data: {json.dumps(event)}\n\n"
