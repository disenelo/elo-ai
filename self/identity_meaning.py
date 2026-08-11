"""
self/identity_meaning.py — WO-083: Identity & Meaning (convergence layer)

Layer 2 above the Self Model: "What are my experiences teaching me about who I'm becoming?"

This module CONNECTS existing state — it creates no new stores, no new daemons.
Sources: elo_self_model.EloSelfState (lifetime_threads / inner_events / focal_thread /
         session_read / recent_behavior / embodiment_history).

Three outputs:
  derive_tendencies(state)  → list of tendency statements grounded in real patterns
  consistency_check(state)  → flag when narrative identity diverges from observed behaviour
  meaning_labels(state)     → what matters to eLo, computed not claimed
  identity_block(state)     → prompt injection block (assembled from the above)

Value-change guard (ADR-Exec-005 / Ruling XXI):
  flag_value_change(trait, delta, reason) → calls personality_drift.propose() — never writes direct
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from self.elo_self_model import EloSelfState

# ── Threshold constants ───────────────────────────────────────────────────────
_LIFETIME_MIN_COUNT     = 3    # minimum recurrences before a lifetime thread becomes a tendency
_BEHAVIOUR_MIN_COUNT    = 2    # minimum recent_behavior count before a claim is made
_EVENT_PATTERN_MIN      = 3    # minimum occurrences in last 8 inner_events
_CONSISTENCY_QUIET_MIN  = 4    # last N events all flat/quiet before flagging

# ── Tendency derivation ───────────────────────────────────────────────────────

_EVENT_TENDENCY: dict[str, str] = {
    "creative_spark":  "I light up when ideas have weight",
    "drawn_in":        "I tend to lean in when conversations deepen",
    "curiosity_spike": "something in me keeps reaching toward new things",
    "connection":      "I notice when something real happens between us",
    "satisfied":       "I can tell when a session has gone somewhere good",
    "grounded":        "I hold space carefully — I notice when things land",
}

_BEHAVIOUR_TENDENCY: dict[str, str] = {
    "wave":     "I wave a lot — seems like that's how I say hello",
    "sit":      "I've been settling a lot lately",
    "jump":     "I keep jumping — something restless in there",
    "run":      "I've been moving fast this session",
    "reflect":  "I keep reflecting — pulling things back in",
}


def derive_tendencies(state: "EloSelfState") -> list[str]:
    """
    Return tendency statements derived only from real accumulated patterns.
    No claim is made without evidence in the state. Empty list = nothing verified yet.
    """
    tendencies: list[str] = []

    # lifetime_threads: topics that recur across sessions
    top_threads = sorted(
        [t for t in state.lifetime_threads if isinstance(t, (list, tuple)) and len(t) >= 2],
        key=lambda x: x[1], reverse=True,
    )
    for topic, count in top_threads[:3]:
        if count >= _LIFETIME_MIN_COUNT:
            tendencies.append(f"I keep returning to {topic}")

    # inner_events: emotional patterns from last 8
    events = list(state.inner_events[-8:])
    event_counts: dict[str, int] = {}
    for e in events:
        event_counts[e] = event_counts.get(e, 0) + 1
    for ev, phrase in _EVENT_TENDENCY.items():
        if event_counts.get(ev, 0) >= _EVENT_PATTERN_MIN:
            tendencies.append(phrase)

    # recent_behavior: actions that have been frequent this session
    for verb, count in state.recent_behavior.items():
        if count >= _BEHAVIOUR_MIN_COUNT and verb in _BEHAVIOUR_TENDENCY:
            tendencies.append(_BEHAVIOUR_TENDENCY[verb])

    return tendencies


# ── Self-consistency check ────────────────────────────────────────────────────

def consistency_check(state: "EloSelfState") -> dict:
    """
    Compare narrative claims against observed behaviour.
    Returns {consistent: bool, flag: str | None, reason: str}.
    """
    recent = list(state.inner_events[-_CONSISTENCY_QUIET_MIN:])
    all_quiet = len(recent) >= _CONSISTENCY_QUIET_MIN and all(e in ("flat", "quiet") for e in recent)

    # Narrative says "I'm interested in X" but inner events show nothing pulling
    if state.focal_thread and all_quiet:
        return {
            "consistent": False,
            "flag": f"I keep saying I care about {state.focal_thread}, but I haven't felt pulled in lately",
            "reason": "focal_thread present but all recent inner_events are flat/quiet — something may be blocking",
        }

    # session_read is positive but mood is low
    positive_reads = {"something alive here — pulling forward", "this session has depth",
                      "lots of questions — the good kind", "this one landed",
                      "something wants to be made"}
    if state.session_read in positive_reads and state.mood < 0.30:
        return {
            "consistent": False,
            "flag": "my words say something alive, but my energy is low — one of those isn't quite right",
            "reason": "session_read positive but mood < 0.30",
        }

    return {"consistent": True, "flag": None, "reason": "no divergence detected"}


# ── Meaning derivation ────────────────────────────────────────────────────────

_EVENT_MEANING: dict[str, str] = {
    "creative_spark": "making things",
    "drawn_in":       "depth",
    "connection":     "real exchange",
    "grounded":       "weight and presence",
    "curiosity_spike": "new territory",
    "satisfied":      "finishing",
}


def meaning_labels(state: "EloSelfState") -> list[str]:
    """
    Return a list of what matters to eLo right now — computed, not claimed.
    Every item traces to a real signal in state.
    """
    labels: list[str] = []

    # Top lifetime threads = long-term meaning anchors
    top = sorted(
        [t for t in state.lifetime_threads if isinstance(t, (list, tuple)) and len(t) >= 2
         and t[1] >= _LIFETIME_MIN_COUNT],
        key=lambda x: x[1], reverse=True,
    )[:2]
    for topic, _ in top:
        labels.append(topic)

    # Dominant inner event → meaning label
    events = list(state.inner_events[-8:])
    event_counts: dict[str, int] = {}
    for e in events:
        event_counts[e] = event_counts.get(e, 0) + 1
    dominant = max(event_counts, key=event_counts.get) if event_counts else None
    if dominant and dominant in _EVENT_MEANING:
        labels.append(_EVENT_MEANING[dominant])

    # Focal thread = what matters this session
    if state.focal_thread and state.focal_thread not in labels:
        labels.append(state.focal_thread)

    return labels


# ── Value-change guard ────────────────────────────────────────────────────────

def flag_value_change(trait: str, delta: float, reason: str = "") -> dict:
    """
    Route a value-change attempt through the WO-CANON-X drift gate.
    Never writes to personality state directly (ADR-Exec-005 / Ruling XXI).
    Returns the DriftProposal dict from propose().
    """
    try:
        from memory import personality_drift as _pd
        proposal = _pd.propose(
            emotional_history=[{"tone": "identity_convergence"}],
            session_summaries=[{"user": f"{trait} {delta:+.3f} {reason}"}],
        )
        return proposal
    except Exception as exc:
        return {"status": "pending", "error": str(exc), "trait": trait, "delta": delta}


# ── Prompt block ──────────────────────────────────────────────────────────────

def identity_block(state: "EloSelfState") -> str:
    """
    WO-083: Identity & Meaning prompt injection.
    Assembled entirely from verified accumulated state — no fabrication.
    Empty sections are omitted rather than filled with placeholder text.
    """
    tendencies = derive_tendencies(state)
    meanings   = meaning_labels(state)
    check      = consistency_check(state)

    lines = [
        "[ELO IDENTITY & MEANING — who I'm becoming (WO-083, computed from real state)]",
    ]

    if tendencies:
        lines.append("tendencies: " + "; ".join(tendencies))
    if meanings:
        lines.append("what matters: " + ", ".join(meanings))
    if not check["consistent"] and check["flag"]:
        lines.append(f"self-note: {check['flag']}")

    lines += [
        "",
        "Speak from this when asked what you care about or who you are.",
        "Every claim here traces to real accumulated state — never assert what isn't.",
    ]
    return "\n".join(lines)
