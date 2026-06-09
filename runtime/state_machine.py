"""
runtime/state_machine.py — eLo OS v2.1 Runtime State Machine.

Tracks the strict runtime state object per session.
Every cognitive cycle must call update(). No hidden states allowed outside this object.

State schema:
    mode:                   current response mode (5 options)
    loop_counter:           increments on any repetition/confusion signal
    stability:              0.0–1.0 — drops on distress, recovers on calm turns
    emotional_state:        current inferred emotional state string
    attention_snapshot_id:  millisecond timestamp of last attention computation

Rules:
    - State MUST update every turn
    - No hidden or persistent internal states outside this object
    - loop_counter > 3 → force stabilisation (checked by is_stabilisation_forced())
"""

from __future__ import annotations
import time

_MODES = frozenset({"DIRECT", "CONVERSATIONAL", "CREATIVE", "GENTLE_GROUNDED", "SIMPLIFY"})

_DEFAULT: dict = {
    "mode":                  "CONVERSATIONAL",
    "loop_counter":          0,
    "stability":             1.0,
    "emotional_state":       "present",
    "attention_snapshot_id": "",
}

# stability delta per emotional state per turn
_STABILITY_DELTA: dict[str, float] = {
    "overwhelmed": -0.30,
    "stressed":    -0.20,
    "low-energy":  -0.10,
    "present":     +0.05,
    "energised":   +0.10,
}

# response_goal → mode mapping
_GOAL_MODE: dict[str, str] = {
    "clarify":   "DIRECT",
    "stabilise": "GENTLE_GROUNDED",
    "explore":   "CREATIVE",
    "create":    "CREATIVE",
    "answer":    "CONVERSATIONAL",
    "reflect":   "CONVERSATIONAL",
}


def fresh() -> dict:
    """Return a fresh state dict for a new session."""
    return dict(_DEFAULT)


def update(
    current:       dict,
    attention:     dict,
    exec_decision: dict,
    loop_signal:   bool = False,
) -> dict:
    """
    Update runtime state after one cognitive cycle.

    Args:
        current:       Current state dict (not mutated).
        attention:     Output of core.attention.compute().
        exec_decision: Output of runtime.executive.decide().
        loop_signal:   True when hard loop detection or confusion fired.

    Returns:
        New state dict. current is never mutated.
    """
    state = dict(current)

    # emotional state
    emo_ctx   = attention.get("emotional_context", {})
    emo_state = emo_ctx.get("inferred_state", "present")
    state["emotional_state"] = emo_state

    # mode — derived from response_goal; stability override when distressed
    goal = exec_decision.get("response_goal", "answer")
    mode = _GOAL_MODE.get(goal, "CONVERSATIONAL")
    if exec_decision.get("stability", False):
        mode = "GENTLE_GROUNDED" if emo_state in ("overwhelmed", "stressed") else "DIRECT"
    if mode not in _MODES:
        mode = "CONVERSATIONAL"
    state["mode"] = mode

    # loop counter: increment on loop/confusion, decay on clean turns
    intent     = attention.get("intent", "conversation")
    is_loop    = loop_signal or intent in ("stabilise", "simplify")
    lc         = state.get("loop_counter", 0)
    state["loop_counter"] = (lc + 1) if is_loop else max(0, lc - 1)

    # stability: clamped [0.0, 1.0]
    delta = _STABILITY_DELTA.get(emo_state, 0.0)
    current_stability = state.get("stability", 1.0)
    state["stability"] = round(max(0.0, min(1.0, current_stability + delta)), 3)

    # attention snapshot id — ms timestamp
    state["attention_snapshot_id"] = str(int(time.time() * 1000))

    return state


def is_stabilisation_forced(state: dict) -> bool:
    """Return True when the loop_counter threshold mandates stabilisation."""
    return state.get("loop_counter", 0) > 3


def mode_from(state: dict) -> str:
    """Return the current mode string."""
    return state.get("mode", "CONVERSATIONAL")


def stability(state: dict) -> float:
    """Return the current stability score (0.0–1.0)."""
    return state.get("stability", 1.0)
