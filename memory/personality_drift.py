"""
memory/personality_drift.py — slow personality drift for eLo OS.

eLo's personality is NOT static. It drifts slowly based on:
    - user emotional patterns
    - repeated interaction tone
    - project evolution
    - memory reinforcement

Drift is slow (±0.01–0.05 per session), clamped (0.2–0.9), and stability-locked.
Personality inversion is forbidden. Sudden changes are forbidden.

Persists to: memory/personality_state.json
"""

from __future__ import annotations

import json
import os
from datetime import datetime

_ROOT     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_PATH     = os.path.join(_ROOT, "memory", "personality_state.json")

_BASELINE: dict = {
    "tone_profile": {
        "calm":        0.7,
        "expressive":  0.4,
        "grounded":    0.8,
    },
    "interaction_bias": {
        "simplify_tendency":      0.6,
        "emotional_reflection":   0.7,
        "technical_focus":        0.5,
    },
    "drift_rate":    0.02,
    "stability_lock": True,
    "last_update":   "",
}

_CLAMP_MIN = 0.2
_CLAMP_MAX = 0.9


def _clamp(v: float) -> float:
    return max(_CLAMP_MIN, min(_CLAMP_MAX, v))


def _detect_instability(state: dict) -> bool:
    """Return True if any tone value is outside the safe band or drift_rate is high."""
    profile = state.get("tone_profile", {})
    for v in profile.values():
        if v < _CLAMP_MIN or v > _CLAMP_MAX:
            return True
    return state.get("drift_rate", 0.02) > 0.05


def load() -> dict:
    """Load personality state from disk. Returns baseline if missing or corrupt."""
    if not os.path.exists(_PATH):
        return dict(_BASELINE)
    try:
        with open(_PATH, encoding="utf-8") as f:
            state = json.load(f)
        # ensure all keys exist (backward compat)
        for k, v in _BASELINE.items():
            if k not in state:
                state[k] = v
        return state
    except Exception:
        return dict(_BASELINE)


def save(state: dict):
    """Persist personality state. Silently fails."""
    try:
        with open(_PATH, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


def _analyse_session(emotional_history: list, session_summaries: list) -> dict:
    """
    Derive drift signals from a session.

    Returns a dict of small adjustments:
        calm_delta, expressive_delta, grounded_delta,
        simplify_delta, emotional_delta, technical_delta
    """
    if not emotional_history:
        return {}

    recent_tones = [h.get("tone", "neutral") for h in emotional_history[-10:]]
    user_texts   = " ".join(s.get("user", "") for s in session_summaries[-10:]).lower()

    counts: dict = {}
    for t in recent_tones:
        counts[t] = counts.get(t, 0) + 1
    dominant = max(counts, key=counts.get) if counts else "neutral"

    adj: dict = {}

    # calm: rises when user is neutral/positive; drops when frustrated
    if dominant in ("neutral", "positive"):
        adj["calm_delta"] = +0.01
    elif dominant == "frustrated":
        adj["calm_delta"] = -0.02

    # expressive: rises when user opens creative/emotional space
    creative_words = ["what if", "imagine", "create", "build", "design"]
    if any(w in user_texts for w in creative_words):
        adj["expressive_delta"] = +0.02
    elif dominant == "low-energy":
        adj["expressive_delta"] = -0.01

    # grounded: rises when user needs simplification; drops on exploration
    simplify_words = ["too much", "overwhelm", "can't", "stuck", "confused"]
    if any(w in user_texts for w in simplify_words):
        adj["grounded_delta"]  = +0.02
        adj["simplify_delta"]  = +0.02
    elif dominant in ("exploratory", "positive"):
        adj["grounded_delta"]  = -0.01
        adj["simplify_delta"]  = -0.01

    # emotional reflection: rises with emotional inputs
    if dominant in ("low-energy", "positive"):
        adj["emotional_delta"] = +0.01
    elif dominant == "frustrated":
        adj["emotional_delta"] = -0.01

    # technical focus: rises when user talks system/build topics
    tech_words = ["system", "memory", "kernel", "backend", "build", "implement", "code"]
    if any(w in user_texts for w in tech_words):
        adj["technical_delta"] = +0.02
    else:
        adj["technical_delta"] = -0.01

    return adj


def update(personality_state: dict, emotional_history: list, session_summaries: list) -> dict:
    """
    Apply one session's drift to the personality state.

    Rules:
        - Max change per value per session: drift_rate (default 0.02)
        - All values clamped to [0.2, 0.9]
        - Stability lock resets drift_rate to 0.01 if instability detected
        - Personality inversion never happens (slow drift, clamped)

    Args:
        personality_state:  Current personality_state dict (from load()).
        emotional_history:  state["emotional_history"] list.
        session_summaries:  state["session_summaries"] list.

    Returns:
        Updated personality_state dict (caller should save()).
    """
    state = dict(personality_state)
    rate  = state.get("drift_rate", 0.02)

    adj = _analyse_session(emotional_history, session_summaries)
    if not adj:
        return state

    tone    = dict(state.get("tone_profile", _BASELINE["tone_profile"]))
    biases  = dict(state.get("interaction_bias", _BASELINE["interaction_bias"]))

    _TONE_KEY_MAP = {
        "calm_delta":       ("tone_profile",     "calm"),
        "expressive_delta": ("tone_profile",     "expressive"),
        "grounded_delta":   ("tone_profile",     "grounded"),
        "simplify_delta":   ("interaction_bias", "simplify_tendency"),
        "emotional_delta":  ("interaction_bias", "emotional_reflection"),
        "technical_delta":  ("interaction_bias", "technical_focus"),
    }

    for key, (section, field) in _TONE_KEY_MAP.items():
        delta = adj.get(key, 0.0)
        if delta == 0.0:
            continue
        # cap change to drift_rate
        delta = max(-rate, min(rate, delta))
        if section == "tone_profile":
            tone[field] = _clamp(round(tone.get(field, 0.5) + delta, 4))
        else:
            biases[field] = _clamp(round(biases.get(field, 0.5) + delta, 4))

    state["tone_profile"]     = tone
    state["interaction_bias"] = biases
    state["last_update"]      = datetime.now().isoformat()

    # stability check — reset drift_rate if instability detected
    if _detect_instability(state):
        state["drift_rate"]    = 0.01
        state["stability_lock"] = True
        # restore any out-of-band values to baseline
        for k, v in _BASELINE["tone_profile"].items():
            if state["tone_profile"][k] < _CLAMP_MIN or state["tone_profile"][k] > _CLAMP_MAX:
                state["tone_profile"][k] = v

    return state


if __name__ == "__main__":
    ps = load()
    print("Current personality state:")
    print(json.dumps(ps, indent=2))
