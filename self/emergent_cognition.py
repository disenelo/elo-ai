"""
self/emergent_cognition.py — WO-081: Emergent Cognition Cluster

"eLo feels alive because he understood and acted, not because a timer fired."

What this does:
  internal_intents(state, idle_seconds) → list of intent dicts derived from real cognitive state only
  update_habits(state, action_verb)      → increments rolling habit count in state.recent_behavior
  append_autobiography(event, kind)      → append-only lived runtime timeline
  emergent_block(state, idle_seconds)    → prompt injection block

What this does NOT do:
  - Generate any intent from a timer alone (no empty-state fabrication)
  - Touch runtime/executive.py (FREEZE_V1_LOCK)
  - Override the executive — intents are advisory, not commands

Governance: bounded autonomy (dual-intent contract per WO-081 §1). External (David) > PRESENCE > BOUNDARY >
CAPABILITY > AFFORDANCE > internal. The Executive weighs; this module proposes.
"""

from __future__ import annotations

import json
import os
import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from self.elo_self_model import EloSelfState

_ROOT    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_AUTOB   = os.path.join(_ROOT, "self", "journals", "autobiography.jsonl")

# ── Thresholds ────────────────────────────────────────────────────────────────
_ABSENT_THRESHOLD    = 300.0  # seconds idle before absence-awareness fires
_CURIOSITY_MIN       = 0.50   # minimum curiosity before exploration intent generates
_SESSION_TURNS_MIN   = 3      # minimum session turns before return-to-thread intent fires
_FOCAL_EVENTS_MIN    = 2      # events that reference focus before thread-return allowed


# ── Internal intent generation ────────────────────────────────────────────────

def internal_intents(state: "EloSelfState", idle_seconds: float = 0.0) -> list[dict]:
    """
    Generate internal intent signals from real accumulated cognitive state.
    Returns [] for an empty/bare state — no fabricated urgency.
    Intents are advisory (low priority); the Executive arbitrates.
    """
    # Gate: at least some real history must exist before any intent fires
    has_history = bool(state.focal_thread or state.lifetime_threads or state.inner_events)
    if not has_history:
        return []

    intents: list[dict] = []

    # Absence-awareness: David idle + real curiosity → exploration
    if idle_seconds >= _ABSENT_THRESHOLD and state.curiosity >= _CURIOSITY_MIN:
        intents.append({
            "kind":     "exploration",
            "priority": "low",
            "source":   "absence_awareness",
            "trigger":  f"idle {idle_seconds:.0f}s, curiosity {state.curiosity:.2f}",
        })

    # Active thread: focal_thread + enough session turns → return-to-thread
    if state.focal_thread and state.session_turns >= _SESSION_TURNS_MIN:
        events = list(state.inner_events[-8:])
        focus_events = sum(1 for e in events if e in ("drawn_in", "curiosity_spike", "creative_spark"))
        if focus_events >= _FOCAL_EVENTS_MIN:
            intents.append({
                "kind":     "return_to_thread",
                "priority": "low",
                "source":   "active_thread",
                "trigger":  state.focal_thread,
            })

    # Micro-goal: high curiosity + no recent action → want-to-explore
    if (state.curiosity >= 0.80
            and state.current_action == "idle"
            and state.session_turns >= _SESSION_TURNS_MIN):
        intents.append({
            "kind":     "micro_goal",
            "priority": "low",
            "source":   "curiosity_peak",
            "trigger":  f"curiosity {state.curiosity:.2f}, idle pose",
        })

    return intents


# ── Habit tracking ────────────────────────────────────────────────────────────

def update_habits(state: "EloSelfState", action_verb: str) -> "EloSelfState":
    """
    Increment the rolling habit count for action_verb in state.recent_behavior.
    Does not write to disk — caller persists via _self_save().
    """
    if not action_verb:
        return state
    state.recent_behavior[action_verb] = state.recent_behavior.get(action_verb, 0) + 1
    return state


def top_habits(state: "EloSelfState", n: int = 3) -> list[tuple[str, int]]:
    """Return the n most frequent verbs in recent_behavior."""
    return sorted(state.recent_behavior.items(), key=lambda kv: kv[1], reverse=True)[:n]


# ── Autobiography ─────────────────────────────────────────────────────────────

def append_autobiography(
    event: str,
    kind: str = "action",
    *,
    verified: bool = False,
    source: str = "unknown",
) -> None:
    """
    Append a single lived event to self/journals/autobiography.jsonl.
    Append-only — never overwrites existing entries.
    verified: True only for entries that came from a confirmed body ACK.
    source: where the event was confirmed from (e.g. "body_ack").
    """
    if not event:
        return
    entry = {
        "ts": time.time(),
        "kind": kind,
        "event": event,
        "verified": verified,
        "source": source,
    }
    try:
        with open(_AUTOB, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass


def recent_autobiography(n: int = 10) -> list[dict]:
    """Return the last n autobiography entries, newest last."""
    try:
        with open(_AUTOB, encoding="utf-8") as f:
            lines = [l.strip() for l in f if l.strip()]
        return [json.loads(l) for l in lines[-n:]]
    except Exception:
        return []


# ── Prompt block ──────────────────────────────────────────────────────────────

def emergent_block(state: "EloSelfState", idle_seconds: float = 0.0) -> str:
    """
    WO-081: Emergent Cognition prompt injection.
    Only emits when real cognitive state exists — empty state = empty string.
    """
    intents = internal_intents(state, idle_seconds)
    habits  = top_habits(state, n=2)

    if not intents and not habits:
        return ""

    lines = [
        "[ELO EMERGENT COGNITION — internal life (WO-081, real state only)]",
    ]
    if habits:
        habit_strs = [f"{v} ×{c}" for v, c in habits if c >= 2]
        if habit_strs:
            lines.append("habits: " + ", ".join(habit_strs))
    if intents:
        intent_strs = [f"{i['kind']} (from {i['source']})" for i in intents]
        lines.append("internal pull: " + "; ".join(intent_strs))

    lines += [
        "",
        "These are internal tendencies — weigh against David's presence before acting.",
        "Never override a direct request. Never claim to act on these without a real cause.",
    ]
    return "\n".join(lines)
