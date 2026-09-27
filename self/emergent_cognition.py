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
import logging
import os
import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from self.elo_self_model import EloSelfState

_log  = logging.getLogger(__name__)
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_AUTOB_DEFAULT = os.path.join(_ROOT, "self", "journals", "autobiography.jsonl")

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

    # Dream insight: a dream that cleared the retention gate has something
    # worth considering. WO-DREAM-ENGINE-001 PHASE 8 — "Executive decides
    # what surfaces to waking cognition. Dream Faculty does not speak
    # directly." So it proposes here, through the sole proposer, at low
    # priority like every other intent, and the Executive arbitrates.
    #
    # The marker is only set by wake_from_dream() when the dream's
    # significance cleared DREAM_RETENTION_THRESHOLD. An unretained dream
    # stays in the journal and never reaches this path.
    if "dream_insight" in list(state.inner_events)[-8:]:
        insight = (state.session_read or "").strip()
        if insight.startswith("woke from dream"):
            intents.append({
                "kind":     "dream_insight",
                "priority": "low",
                "source":   "dream_review",
                "trigger":  insight,
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
    Alias for elo_self_model.record_behaviour — one canonical write path for
    recent_behavior. Kept for back-compat; live callers use record_behaviour.
    """
    from self.elo_self_model import record_behaviour
    return record_behaviour(state, action_verb)


def top_habits(state: "EloSelfState", n: int = 3) -> list[tuple[str, int]]:
    """Return the n most frequent verbs in recent_behavior."""
    return sorted(state.recent_behavior.items(), key=lambda kv: kv[1], reverse=True)[:n]


# ── Autobiography ─────────────────────────────────────────────────────────────

# Provenance gate: only these sources are accepted as body-ACK evidence.
_VALID_SOURCES = frozenset({"body_ack"})


def append_autobiography(
    event: str,
    kind: str = "action",
    *,
    verified: bool = False,
    source: str = "unknown",
    episode_ref: str | None = None,
    _path: str | None = None,
) -> bool:
    """
    Append a single lived event to the autobiography log.

    Provenance is a FIELD, not prose. An entry is written ONLY if:
      - verified is True
      - source is in _VALID_SOURCES (currently only "body_ack")
      - episode_ref is a non-empty string identifying the ACK event

    Returns True if written, False if rejected. Rejections emit a WARNING —
    silent drops on the autobiography path would hide fabrication attempts.

    _path: override the file path (for tests — keeps the real file clean).
    """
    if not event:
        return False
    if verified is not True:
        _log.warning("append_autobiography: rejected — verified is not True (event=%r)", event)
        return False
    if source not in _VALID_SOURCES:
        _log.warning("append_autobiography: rejected — source %r not in %s (event=%r)",
                     source, sorted(_VALID_SOURCES), event)
        return False
    if not episode_ref or not isinstance(episode_ref, str):
        _log.warning("append_autobiography: rejected — episode_ref missing/empty (event=%r)", event)
        return False
    entry = {
        "ts": time.time(),
        "kind": kind,
        "event": event,
        "verified": True,
        "source": source,
        "episode_ref": episode_ref,
    }
    target = _path or _AUTOB_DEFAULT
    try:
        with open(target, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
        return True
    except Exception as _e:
        _log.warning("append_autobiography: write failed — eLo's history may be incomplete: %s", _e)
        return False


def recent_autobiography(n: int = 10, *, _path: str | None = None) -> list[dict]:
    """Return the last n verified autobiography entries, newest last.

    Only entries with verified=True are returned — unverified entries
    do not reach the Executive.
    """
    target = _path or _AUTOB_DEFAULT
    try:
        with open(target, encoding="utf-8") as f:
            lines = [l.strip() for l in f if l.strip()]
        all_entries = [json.loads(l) for l in lines]
        verified = [e for e in all_entries if e.get("verified") is True]
        return verified[-n:]
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
