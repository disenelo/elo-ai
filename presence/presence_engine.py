"""
presence/presence_engine.py — derives PresenceState from conversation context.

Input:  CAL action, attention model, response text, continuity state
Output: PresenceState

Does not store state. Stateless derivation only.
"""
from __future__ import annotations

from presence.presence_state import PresenceMode, PresenceState, MODE_FEEL


# ── action → mode mapping ─────────────────────────────────────────────────────

_ACTION_MODE: dict[str, PresenceMode] = {
    "ANSWER":    PresenceMode.BUILDING,
    "BUILD":     PresenceMode.BUILDING,
    "CONNECT":   PresenceMode.OBSERVING,
    "CELEBRATE": PresenceMode.CELEBRATING,
    "REFLECT":   PresenceMode.THINKING,
    "GROUND":    PresenceMode.RESTING,
    "CHALLENGE": PresenceMode.EXPLORING,
    "WITNESS":   PresenceMode.OBSERVING,
    "SILENCE":   PresenceMode.IDLE,
}

# ── tone → energy ─────────────────────────────────────────────────────────────

_TONE_ENERGY: dict[str, float] = {
    "energised":   0.85,
    "present":     0.65,
    "low-energy":  0.3,
    "overwhelmed": 0.4,
    "stressed":    0.45,
}

# ── response length → duration ────────────────────────────────────────────────

def _duration_from_response(text: str) -> float:
    words = len(text.split())
    if words < 15:
        return 2.5
    if words < 40:
        return 4.0
    return 6.0


# ── mood from mode + energy ───────────────────────────────────────────────────

def _mood(mode: PresenceMode, energy: float) -> str:
    default = MODE_FEEL[mode]["default_mood"]
    if mode == PresenceMode.THINKING and energy < 0.45:
        return "quiet"
    if mode == PresenceMode.BUILDING and energy > 0.75:
        return "focused"
    return default


# ── intensity from action confidence ─────────────────────────────────────────

def _intensity(action: str, attention_signals: dict) -> float:
    """Higher intensity = more committed to this mode."""
    base = 0.6
    score = attention_signals.get("top_score", 0.0)
    if score > 0.7:
        base += 0.2
    if action == "CELEBRATE":
        base = max(base, 0.8)
    if action in ("SILENCE", "GROUND"):
        base = min(base, 0.4)
    return round(min(1.0, base), 2)


# ── main derive function ──────────────────────────────────────────────────────

def derive(
    action:           str,
    attention_model:  dict,
    response_text:    str,
    tone:             str = "present",
) -> PresenceState:
    """
    Derive a PresenceState from current conversation context.

    Args:
        action:          CAL decision (e.g. "BUILD")
        attention_model: dict from attention engine (may include top_score)
        response_text:   eLo's response this turn
        tone:            current emotional tone from session state
    """
    mode      = _ACTION_MODE.get(action, PresenceMode.IDLE)
    energy    = _TONE_ENERGY.get(tone, 0.55)
    intensity = _intensity(action, attention_model or {})
    duration  = _duration_from_response(response_text)
    mood      = _mood(mode, energy)

    return PresenceState(
        mode      = mode,
        intensity = intensity,
        energy    = energy,
        duration  = duration,
        mood      = mood,
    )
