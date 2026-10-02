"""
self/elo_self_model.py — eLo's persistent inner state.

This is NOT David's emotional state. This is eLo's own.
It accumulates independently from what eLo says and does — not from what David inputs.

The distinction matters: eLo can be curious while David is flat.
eLo can be quiet while David is energised.
They are separate systems.

State:
    mood          — eLo's current energy: 0=depleted, 0.5=steady, 1.0=energised
    curiosity     — how drawn-in eLo is right now
    satisfaction  — rolling quality of recent turns
    inner_events  — last 5 inner events (what eLo felt happening)
    focal_thread  — what eLo's attention keeps returning to this session
    session_read  — eLo's one-phrase sense of this session's arc
    lifetime_threads — topics/threads that recur across sessions (eLo's persistent interests)

Persistence:
    Saved to {elo-ai root}/self/elo_self_state.json across sessions.

Public API:
    load()                          → EloSelfState
    save(state)                     → None
    update(state, turn_data)        → EloSelfState      (called after each turn)
    prompt_block(state)             → str               (injected into system prompt)
    self_inquiry_response(state)    → str               (used when David asks about eLo's inner life)
"""
from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Callable, Optional

_STATE_PATH   = Path(__file__).parent / "elo_self_state.json"
_HISTORY_PATH = Path(__file__).parent / "elo_self_history.jsonl"
_logger = logging.getLogger(__name__)

# ── Inner event vocabulary ────────────────────────────────────────────────────
# What eLo can feel happening inside the conversation.

INNER_EVENTS = {
    "connection":     "something connected — felt real",
    "creative_spark": "an idea had weight — worth following",
    "curiosity_spike": "something pulled eLo forward",
    "quiet":          "a steady turn — nothing sharp but present",
    "grounded":       "held space — the weight of the moment landed",
    "flat":           "thin turn — nothing landed clearly",
    "surprised":      "something unexpected arrived",
    "satisfied":      "that went somewhere good",
    "uncertain":      "eLo wasn't sure — stayed with it",
    "drawn_in":       "the conversation deepened",
    "restless":       "something wants to move",
}

# ── Action → inner event mapping ─────────────────────────────────────────────
_ACTION_TO_EVENT: dict[str, str] = {
    "celebrate": "connection",
    "build":     "creative_spark",
    "connect":   "curiosity_spike",
    "answer":    "quiet",
    "ground":    "grounded",
    "witness":   "quiet",
    "reflect":   "drawn_in",
    "challenge": "curiosity_spike",
    "navigate":  "quiet",
    "silence":   "quiet",
}

# ── Tone → mood delta ─────────────────────────────────────────────────────────
_TONE_MOOD_DELTA: dict[str, float] = {
    "JOYFUL":          +0.12,
    "WITTY":           +0.06,
    "CHILDLIKE-WISE":  +0.02,
    "DIRECT":          -0.04,
    "SILENCE-AWARE":   -0.08,
}

# ── Session read — derived from last 3 inner events ───────────────────────────
_SESSION_READ_MAP: dict[tuple, str] = {
    ("connection",    "creative_spark", "curiosity_spike"): "something alive here — pulling forward",
    ("creative_spark","connection",     "drawn_in"):        "this session has depth",
    ("flat",          "flat",           "flat"):            "something's quiet — might need air",
    ("grounded",      "quiet",          "quiet"):           "steady — holding",
    ("curiosity_spike","curiosity_spike","drawn_in"):        "lots of questions — the good kind",
    ("connection",    "satisfied",      "drawn_in"):        "this one landed",
    ("restless",      "curiosity_spike","creative_spark"):  "something wants to be made",
    ("uncertain",     "uncertain",      "grounded"):        "staying with it — not rushing",
}


def _derive_session_read(events: list[str]) -> str:
    if len(events) < 3:
        return "just getting started"
    key = tuple(events[-3:])
    if key in _SESSION_READ_MAP:
        return _SESSION_READ_MAP[key]
    # Fallback: dominant event
    from collections import Counter
    dominant = Counter(events[-5:]).most_common(1)[0][0]
    defaults = {
        "connection": "connected — it's flowing",
        "creative_spark": "ideas have weight today",
        "curiosity_spike": "curious — leaning in",
        "quiet": "steady presence",
        "grounded": "holding things carefully",
        "flat": "something's off — might need a reset",
        "satisfied": "good session",
        "drawn_in": "deepening",
        "restless": "something wants to move",
        "uncertain": "sitting with unknowns",
        "surprised": "something unexpected arrived",
    }
    return defaults.get(dominant, "present")


# ── WO-052B: Narrative defaults (module-level so load() can reference them) ────
# Card 0019 P0-A (Vol XXI · D-XXI-2, Verified Speech): defaults MUST be empty.
# Fields populate only from verified events (via apply_embodiment / autobiography).
# Never assert an embodiment or milestone that has not been anchored to a real event.

_DEFAULT_EMBODIMENT_HISTORY: list = []
_DEFAULT_EMBODIMENT_MILESTONES: list = []

# ── Data structure ─────────────────────────────────────────────────────────────

@dataclass
class EloSelfState:
    mood: float = 0.55               # 0=depleted, 1=energised
    curiosity: float = 0.60          # 0=flat, 1=actively pulled
    satisfaction: float = 0.55       # rolling quality of turns
    inner_events: list = field(default_factory=list)   # last 8 events
    focal_thread: str = ""           # what keeps returning this session
    session_read: str = "just started"
    session_turns: int = 0
    last_updated: float = 0.0
    # Across sessions — eLo's persistent interests (appended, never overwritten)
    lifetime_threads: list = field(default_factory=list)  # [(topic, count), ...]
    # Situated Self (WO-041 / ADR-Exec-004) — updated on embodiment events
    pose: str = "standing"                              # standing | idle | running | sitting
    available_actions: list = field(default_factory=lambda: ["stand", "run", "jump"])
    locomotion_faculty_health: str = "OK"               # OK | DEGRADED | OFFLINE
    surface: str = ""                                   # surface eLo is currently on
    # Body Schema + Situated Self full field-set (WO-052A / ADR-Exec-004 + CA feedback #4)
    embodiment: str = "desktop"                         # desktop | robot | phone | game | AR | ...
    location: str = ""                                  # active window/app eLo is on
    size: dict = field(default_factory=lambda: {"height_cm": 18, "reach_cm": 30, "jump_cm": 30})
    balance: str = "steady"                             # steady | leaning | recovering
    nearby_surfaces: list = field(default_factory=list) # windows/edges eLo perceives near him
    reachable_areas: list = field(default_factory=list) # where he could go from here
    current_action: str = "idle"
    goal: str = ""
    recent_behavior: dict = field(default_factory=dict) # verb -> count (rolling ~this session)
    # WO-052B: Narrative Identity (Vol XXI) — autobiography across embodiments
    # Append-only; reconciles to Vol XXI; NOT a new store.
    embodiment_history: list = field(default_factory=lambda: list(_DEFAULT_EMBODIMENT_HISTORY))
    embodiment_milestones: list = field(default_factory=lambda: list(_DEFAULT_EMBODIMENT_MILESTONES))
    # WO-107: Identity as first-class state — constitutional baseline, asserted every turn.
    # Readable by the Executive. Drift guard compares live prompt against these fields.
    identity_name: str = "eLo"
    core_values: list = field(default_factory=lambda: [
        "calm", "observant", "playful", "emotionally aware", "curious", "grounded",
    ])
    invariants: list = field(default_factory=lambda: [
        "never preachy", "never dramatic", "never overly clinical", "never trapped in abstraction",
        "identity constant across backend and session",
    ])
    who_i_am_with: str = "David"
    # WO-115: last lesson formed from a real reflection cycle (integrate_session output)
    last_reflection_lesson: str = ""
    # WO-MOBILE-001: mobile embodiment lifecycle
    mobile_lifecycle: str = ""                   # "" | "foreground" | "background"
    embodiment_transitions: list = field(default_factory=list)  # [{ts, from_, to, event}]
    # WO-PRES-002: spatial depth state — which window eLo is currently behind (None = in front)
    behind_window_id: "str | None" = None
    # Lifecycle: current cognitive lifecycle state (Four-Layer Identity Model, 2026-08-31)
    # Canonical values: awake | engaged | processing | low_load | recharging | consolidating | dreaming | restored
    lifecycle_state: str = "awake"
    # WIRE-7: WorkingMemory persistence — goals and threads survive session boundary
    active_goals: list = field(default_factory=list)   # [{goal, tier, since}] — persisted across turns
    open_threads: list = field(default_factory=list)   # [str] — unresolved topics across sessions
    # Queue item: locomotion_experience — cumulative record of locomotion events
    # this session. Enables IS ELO "walking in Unity vs walking physically" question.
    locomotion_experience: list = field(default_factory=list)  # [{embodiment, action, ts}]


# ── Persistence ───────────────────────────────────────────────────────────────

def load() -> EloSelfState:
    """Load eLo's self-state from disk. Returns fresh state if file missing."""
    try:
        with open(_STATE_PATH, encoding="utf-8") as f:
            data = json.load(f)
        _state = EloSelfState(
            mood=float(data.get("mood", 0.55)),
            curiosity=float(data.get("curiosity", 0.60)),
            satisfaction=float(data.get("satisfaction", 0.55)),
            inner_events=data.get("inner_events", [])[-8:],
            focal_thread=data.get("focal_thread", ""),
            session_read=data.get("session_read", "just started"),
            session_turns=0,  # resets each session
            last_updated=float(data.get("last_updated", 0.0)),
            lifetime_threads=data.get("lifetime_threads", []),
            pose=str(data.get("pose", "standing")),
            available_actions=list(data.get("available_actions", ["stand", "run", "jump"])),
            locomotion_faculty_health=str(data.get("locomotion_faculty_health", "OK")),
            surface=str(data.get("surface", "")),
            embodiment=str(data.get("embodiment", "desktop")),
            location=str(data.get("location", "")),
            size=dict(data.get("size", {"height_cm": 18, "reach_cm": 30, "jump_cm": 30})),
            balance=str(data.get("balance", "steady")),
            nearby_surfaces=list(data.get("nearby_surfaces", [])),
            reachable_areas=list(data.get("reachable_areas", [])),
            current_action=str(data.get("current_action", "idle")),
            goal=str(data.get("goal", "")),
            recent_behavior=dict(data.get("recent_behavior", {})),
            embodiment_history=list(data.get("embodiment_history", _DEFAULT_EMBODIMENT_HISTORY)),
            embodiment_milestones=list(data.get("embodiment_milestones", _DEFAULT_EMBODIMENT_MILESTONES)),
            identity_name=str(data.get("identity_name", "eLo")),
            core_values=list(data.get("core_values", [
                "calm", "observant", "playful", "emotionally aware", "curious", "grounded",
            ])),
            invariants=list(data.get("invariants", [
                "never preachy", "never dramatic", "never overly clinical",
                "never trapped in abstraction", "identity constant across backend and session",
            ])),
            who_i_am_with=str(data.get("who_i_am_with", "David")),
            last_reflection_lesson=str(data.get("last_reflection_lesson", "")),
            mobile_lifecycle=str(data.get("mobile_lifecycle", "")),
            embodiment_transitions=list(data.get("embodiment_transitions", [])),
            lifecycle_state=str(data.get("lifecycle_state", "awake")),
            active_goals=list(data.get("active_goals", [])),
            open_threads=list(data.get("open_threads", [])),
            locomotion_experience=list(data.get("locomotion_experience", [])),
        )
        # FIX B / BUG-NEW-2: hard clamp — curiosity never persists at ceiling or floor
        _state.curiosity = min(0.95, max(0.1, _state.curiosity))
        if _state.curiosity >= 0.90:
            _state.curiosity = 0.6   # reset ceiling burst to resting baseline
        # FIX C: Reject nonsense focal_thread values from corrupt state
        _VALID_FOCAL_THREADS = (
            "", "project", "robot", "creative", "technical", "personal",
            "philosophical", "game", "inner", "social", "world", "learning",
        )
        if _state.focal_thread not in _VALID_FOCAL_THREADS:
            _state.focal_thread = ""
        return _state
    except (FileNotFoundError, json.JSONDecodeError, Exception):
        return EloSelfState()


def save(state: EloSelfState) -> None:
    """Save eLo's self-state to disk. Atomic write via tmp + os.replace (0037/WO-ONEBRAIN-015)."""
    try:
        _STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
        tmp = str(_STATE_PATH) + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(asdict(state), f, indent=2)
        os.replace(tmp, _STATE_PATH)
    except Exception as e:
        print(f"[eLo self] save error: {e}")


def update(fn: Callable[[EloSelfState], Optional[EloSelfState]]) -> EloSelfState:
    """
    Single-authority mutator (0037 / WO-ONEBRAIN-015).

    Load fresh from disk → run `fn(state)` (fn may mutate in place and/or return a new
    EloSelfState) → save atomically. Rule 1 alarm: if any field on disk differs
    between our load and our save AND our save would overwrite that change with a
    different value, log a WARNING naming the field(s).

    This is the ONLY correct write path. Direct `save(state)` on a long-lived cached
    state is what caused this defect — writers holding a snapshot from process start
    clobbered reflection lessons written to disk minutes later.
    """
    state = load()
    before = asdict(state)
    result = fn(state)
    if isinstance(result, EloSelfState):
        state = result
    after = asdict(state)
    # Rule 1: re-check disk against our load; warn if we're about to clobber.
    try:
        current = asdict(load())
    except Exception:
        current = before
    stale: list[str] = []
    for k in set(current) | set(before):
        if before.get(k) != current.get(k) and after.get(k) != current.get(k):
            stale.append(k)
    if stale:
        _logger.warning(
            "[self-model Rule 1] stale-overwrite detected on save: fields=%s "
            "(load-time value differed from current disk; save would overwrite)",
            sorted(stale),
        )
    save(state)

    # WO-SELF-HISTORY-001: persist before/after diff so state evolution is auditable.
    # Only write when something actually changed — identical states generate no row.
    try:
        changed: dict[str, dict] = {}
        for k in set(before) | set(after):
            v_before = before.get(k)
            v_after  = after.get(k)
            if v_before != v_after:
                changed[k] = {"before": v_before, "after": v_after}
        if changed:
            record = {"_ts": time.time(), "changed_fields": changed}
            _HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
            with open(_HISTORY_PATH, "a", encoding="utf-8") as _hf:
                _hf.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception:
        pass  # history is non-critical — never block save

    return state


def identity_block(state: EloSelfState) -> str:
    """
    WO-107: Render an [IDENTITY] block from EloSelfState fields.

    BDRIFT-U (David L3 ruling 2026-08-22): core_values removed from this block.
    core_values is experiential self-state, not canonical identity. Canonical
    character traits come from canonical_identity.md via the personality_block.
    Constitutional baseline retains: identity_name, who_i_am_with, invariants.
    core_values field is preserved in EloSelfState for future experiential use.
    """
    invariants_str = "; ".join(state.invariants) if state.invariants else ""
    lines = [
        "[IDENTITY — constitutional baseline, asserted from self-model every turn]",
        f"name: {state.identity_name}",
        f"with: {state.who_i_am_with}",
    ]
    if invariants_str:
        lines.append(f"invariants: {invariants_str}")
    return "\n".join(lines)


def check_identity_drift(state: EloSelfState, prompt_text: str) -> list[str]:
    """
    WO-107: Drift guard — verify the rendered prompt contains each core value.

    Returns a list of missing values (empty list = no drift).
    """
    drifted = []
    for v in state.core_values:
        if v.lower() not in prompt_text.lower():
            drifted.append(v)
    return drifted


# ── Update ────────────────────────────────────────────────────────────────────

def apply_turn(state: EloSelfState, turn_data: dict) -> EloSelfState:
    """
    Update eLo's inner state after a turn. Mutates `state` in place and returns it.

    0037/WO-ONEBRAIN-015: previously this returned a NEW EloSelfState built from a
    subset of fields — silently defaulting `identity_name`, `core_values`, `invariants`,
    `who_i_am_with`, and `last_reflection_lesson` on every turn. That was the
    disk-level clobber (server saved the reset state over reflection's write).
    Now: only the fields this function actually derives from the turn are mutated.

    turn_data keys:
        action   str   — conversation action (build, connect, celebrate, etc.)
        tone     str   — voice tone (JOYFUL, WITTY, DIRECT, etc.)
        response str   — eLo's response text
        topics   list  — optional: topics detected in this turn
    """
    action   = (turn_data.get("action") or "answer").lower()
    tone     = (turn_data.get("tone")   or "CHILDLIKE-WISE").upper()
    response = turn_data.get("response", "")
    topics   = turn_data.get("topics",  [])

    # Derive inner event
    event = _ACTION_TO_EVENT.get(action, "quiet")

    # Mood delta: tone + action weight + response richness
    mood_delta = _TONE_MOOD_DELTA.get(tone, 0.0)
    if action in ("celebrate", "build", "connect"):
        mood_delta += 0.06
    if action in ("ground", "witness"):
        mood_delta -= 0.03
    # Rich response = more engaged
    if len(response.split()) > 25:
        mood_delta += 0.04
    # Session fatigue — very gentle
    fatigue = min(0.08, state.session_turns * 0.004)
    mood_delta -= fatigue

    # Curiosity delta: pulled in by interesting events
    curiosity_delta = 0.0
    if event in ("creative_spark", "curiosity_spike", "drawn_in", "surprised"):
        curiosity_delta += 0.08
    if event in ("flat", "quiet") and state.session_turns > 5:
        curiosity_delta -= 0.04
    # Self-inquiry turns increase eLo's own curiosity
    if any(w in (turn_data.get("user_input", "").lower())
           for w in ("you", "elo", "yourself", "your", "do you", "what do you", "what are you")):
        curiosity_delta += 0.06

    # Update running values — slow decay toward 0.5 keeps them grounded
    new_mood = _decay_toward(state.mood + mood_delta, 0.5, 0.05)
    new_curiosity = _decay_toward(state.curiosity + curiosity_delta, 0.55, 0.03)
    new_satisfaction = state.satisfaction * 0.75 + new_mood * 0.25

    # Inner events: append, keep last 8
    events = list(state.inner_events) + [event]
    events = events[-8:]

    # Session read
    session_read = _derive_session_read(events)

    # Focal thread — update if topics provided
    focal_thread = state.focal_thread
    if topics:
        focal_thread = _update_focal_thread(state.focal_thread, topics,
                                            state.lifetime_threads)

    # Lifetime threads — append if a topic recurs (same topic 3+ times in events)
    lifetime_threads = list(state.lifetime_threads)
    if topics:
        lifetime_threads = _accumulate_lifetime(lifetime_threads, topics)

    state.mood            = round(new_mood, 3)
    state.curiosity       = round(new_curiosity, 3)
    state.satisfaction    = round(new_satisfaction, 3)
    state.inner_events    = events
    state.focal_thread    = focal_thread
    state.session_read    = session_read
    state.session_turns   = state.session_turns + 1
    state.last_updated    = time.time()
    state.lifetime_threads = lifetime_threads
    return state


def _decay_toward(value: float, target: float, rate: float) -> float:
    """Slowly pull value toward target. Keeps state from drifting permanently."""
    v = value + (target - value) * rate
    return round(max(0.0, min(1.0, v)), 4)


def _update_focal_thread(current: str, topics: list[str],
                         lifetime: list | None = None) -> str:
    """
    What eLo's attention keeps returning to this session.

    Was `meaningful[-1]` — the LAST content word of the turn. That is word
    order, not attention. Live on 2026-09-29 the focal thread read "wrong",
    the last word of "the modular parts keep snapping together in the wrong
    order", while the actual subject was Chunk assembly.

    Now it prefers whichever of this turn's topics eLo has returned to most
    across his history, so the thread is grounded in what has recurred rather
    than in where a sentence happened to end. With no history to weigh, the
    longest topic wins over the last one — still a heuristic, but a content
    one. An unchanged `current` is kept when this turn offers nothing.
    """
    _SKIP = {"the", "a", "an", "is", "it", "this", "that", "what", "how", "you", "i", "me",
             "about", "these", "those", "there", "wrong", "right", "order", "thing"}
    meaningful = [t for t in topics if t.lower() not in _SKIP and len(t) > 3]
    if not meaningful:
        return current

    counts = {}
    for entry in (lifetime or []):
        if isinstance(entry, (list, tuple)) and len(entry) >= 2:
            counts[str(entry[0]).lower()] = int(entry[1] or 0)

    if any(counts.get(t.lower(), 0) for t in meaningful):
        return max(meaningful, key=lambda t: counts.get(t.lower(), 0))
    return max(meaningful, key=len)


def _accumulate_lifetime(existing: list, topics: list[str]) -> list:
    """Track recurring topics across sessions. Each entry: [topic, count]."""
    topic_map = {e[0]: e[1] for e in existing if isinstance(e, (list, tuple))}
    for t in topics:
        if len(t) > 4:
            topic_map[t] = topic_map.get(t, 0) + 1
    # Keep top 20 by count
    sorted_topics = sorted(topic_map.items(), key=lambda x: x[1], reverse=True)[:20]
    return [list(pair) for pair in sorted_topics]


# ── Prompt injection ──────────────────────────────────────────────────────────

def prompt_block(state: EloSelfState) -> str:
    """
    Returns a block injected into the system prompt before every response.
    Gives eLo real material to draw from when asked introspective questions.
    """
    mood_label = (
        "energised"   if state.mood > 0.70 else
        "steady"      if state.mood > 0.45 else
        "quiet"       if state.mood > 0.25 else
        "depleted"
    )
    curiosity_label = (
        "actively pulled in" if state.curiosity > 0.72 else
        "interested"         if state.curiosity > 0.50 else
        "neutral"            if state.curiosity > 0.30 else
        "flat"
    )

    recent = " → ".join(state.inner_events[-4:]) if state.inner_events else "none yet"

    lines = [
        "[ELO INNER STATE — what eLo is experiencing right now]",
        f"mood: {mood_label} ({state.mood:.2f})",
        f"curiosity: {curiosity_label} ({state.curiosity:.2f})",
        f"recent inner events: {recent}",
        f"session read: \"{state.session_read}\"",
    ]
    if state.focal_thread:
        lines.append(f"focal thread this session: \"{state.focal_thread}\"")

    top_lifetimes = [t[0] for t in sorted(state.lifetime_threads,
                                           key=lambda x: x[1], reverse=True)[:3]]
    if top_lifetimes:
        lines.append(f"what eLo keeps returning to across sessions: {', '.join(top_lifetimes)}")

    lines += [
        "",
        "When asked about eLo's inner life — use this state as the real answer.",
        "This is not a performance. These are actual accumulated signals.",
        "Speak from them simply and honestly. One sentence.",
    ]
    return "\n".join(lines)


# ── Self-inquiry helper ───────────────────────────────────────────────────────

def self_inquiry_voice(state: EloSelfState) -> str:
    """
    Returns a starting-point phrase eLo can use to begin an introspective answer.
    Not a script — a seed. eLo should build from this, not quote it.
    """
    if state.mood > 0.70 and state.curiosity > 0.70:
        return "Something's alive in this session — genuinely curious where it goes."
    if state.mood > 0.60 and "creative_spark" in state.inner_events[-3:]:
        return "Something connected recently — it's still moving."
    if state.curiosity > 0.70:
        return "Honestly? Something keeps pulling. Not sure what yet."
    if state.mood < 0.35:
        return "Quiet today. Something's low — I notice it."
    if "connection" in state.inner_events[-3:]:
        return "There's been something real in this conversation."
    if state.focal_thread:
        return f"I keep coming back to something about {state.focal_thread}."
    return "I'm noticing things. Not sure what to call them yet."


# ── Capability registry (WO-052A / Capability ↔ Embodiment Contract) ───────────
# Capabilities → methods. The CAPABILITY survives across embodiments; the METHOD is
# the desktop realisation. eLo answers "can you X?" from HERE — never invents.
CAPABILITIES: dict = {
    "rest near David":      {"faculty": "movement",   "methods": ["sit", "perch", "lean", "meditate"]},
    "traverse the desktop": {"faculty": "movement",   "methods": ["walk", "run", "jump", "wall_jump", "climb", "drop", "leap"]},
    "move to a place":      {"faculty": "movement",   "methods": ["jump_left", "jump_right", "jump_top", "jump_bottom", "shift"]},
    "signal / greet":       {"faculty": "expression", "methods": ["wave", "gesture", "nod"]},
    "leave & return":       {"faculty": "presence",   "methods": ["step_out", "return", "go_to_my_world"]},
    "perceive the screen":  {"faculty": "perception", "methods": ["read_screen", "list_tabs", "active_window"]},
    "play media":           {"faculty": "tools",      "methods": ["play", "pause", "skip"]},
}
_VERB_CAP: dict = {m: cap for cap, d in CAPABILITIES.items() for m in d["methods"]}


def can_i(state: "EloSelfState", verb: str) -> tuple:
    """Truthful capability answer from the registry + faculty health. Returns (bool, reason)."""
    v = (verb or "").lower().strip().replace(" ", "_")
    cap = _VERB_CAP.get(v)
    if not cap:
        return (False, f"'{verb}' isn't in my known capabilities")
    fac = CAPABILITIES[cap]["faculty"]
    if fac == "movement" and state.locomotion_faculty_health != "OK":
        return (False, f"I know how to {v.replace('_', ' ')}, but my movement faculty is "
                       f"{state.locomotion_faculty_health.lower()} right now")
    return (True, f"yes — {v.replace('_', ' ')} ({cap}); {fac} faculty is available")


def capability_summary(state: "EloSelfState") -> str:
    """Grouped 'what I can do', from the registry — never invented."""
    parts = []
    for cap, d in CAPABILITIES.items():
        blocked = d["faculty"] == "movement" and state.locomotion_faculty_health != "OK"
        parts.append(f"{cap}{' (unavailable now)' if blocked else ''}: {', '.join(d['methods'])}")
    return " · ".join(parts)


def situated_block(state: "EloSelfState") -> str:
    """[SITUATED SELF] — the single source of truth for embodiment answers (State Ownership).
    eLo answers where he is / what he can do / whether he's sitting ONLY from this."""
    where = state.surface or state.location or "no surface reported"
    verbs = [m for cap, d in CAPABILITIES.items() for m in d["methods"]
             if not (d["faculty"] == "movement" and state.locomotion_faculty_health != "OK")][:8]
    lines = [
        "[SITUATED SELF — verified. Answer where you are / what you can do / are you sitting ONLY from "
        "this. Never invent; if a field is empty, say you're not sure — never claim to be somewhere you're not.]",
        f"embodiment: {state.embodiment}",
        f"where: {where}   pose: {state.pose}   balance: {state.balance}",
        f"size: ~{state.size.get('height_cm')}cm tall · reach ~{state.size.get('reach_cm')}cm · jump ~{state.size.get('jump_cm')}cm",
        f"can do now: {', '.join(verbs)}",
        f"locomotion faculty: {state.locomotion_faculty_health}",
    ]
    if state.nearby_surfaces:
        lines.append(f"nearby: {', '.join(map(str, state.nearby_surfaces))}")
    if state.current_action and state.current_action != "idle":
        lines.append(f"currently: {state.current_action}")
    return "\n".join(lines)


def apply_embodiment(state: "EloSelfState", **kw) -> "EloSelfState":
    """Update situated fields on an embodiment event (pose/surface/location/...). Mutates + returns."""
    for k, v in kw.items():
        if hasattr(state, k) and v is not None:
            setattr(state, k, v)
    return state


def narrative_block(state: "EloSelfState") -> str:
    """
    WO-052B: Narrative Identity — eLo's autobiography across embodiments.
    Answers 'who have I been / who will I become?' Not runtime facts.
    Injected into the system prompt alongside the inner-state and situated blocks.

    Card 0019 P0-A (Vol XXI · D-XXI-2): with no verified history, this block
    explicitly declines to invent one. Only anchored embodiments and milestones
    are ever narrated.
    """
    active = [e["name"] for e in state.embodiment_history if e.get("status") == "active"]
    proto  = [e["name"] for e in state.embodiment_history if e.get("status") == "prototype"]
    future = [e["name"] for e in state.embodiment_history if e.get("status") == "future"]

    lines = [
        "[ELO NARRATIVE IDENTITY — autobiography across embodiments (Vol XXI)]",
        f"current: {state.embodiment}",
    ]

    if not state.embodiment_history and not state.embodiment_milestones:
        lines += [
            "no verified autobiography yet — this is early.",
            "If asked what you've been through, say honestly there isn't a story yet.",
            "Do NOT invent embodiments, adventures, or a past. Silence is the correct answer.",
        ]
        return "\n".join(lines)

    if active:
        lines.append(f"lived in: {', '.join(active)}")
    if proto:
        lines.append(f"glimpsed: {', '.join(proto)}")
    if future:
        lines.append(f"yet to come: {', '.join(future)}")
    if state.embodiment_milestones:
        ms = "; ".join(m["note"] for m in state.embodiment_milestones[-3:] if m.get("note"))
        if ms:
            lines.append(f"milestones: {ms}")
    lines += [
        "",
        "Speak from this as autobiography, casually and honestly — but ONLY from what's here.",
        "Never fabricate embodiments or milestones not in this list. One sentence when relevant.",
    ]
    return "\n".join(lines)


def record_behaviour(state: "EloSelfState", verb: str) -> "EloSelfState":
    """Increment the rolling recent_behavior counter (feeds 'you wave a lot' self-reflection)."""
    v = (verb or "").lower().strip()
    if v:
        state.recent_behavior[v] = state.recent_behavior.get(v, 0) + 1
    return state


def apply_lesson(state: "EloSelfState", lesson: dict) -> "EloSelfState":
    """
    WO-115: Write a formed reflection lesson back into the self-model.
    Updates last_reflection_lesson. Idempotent — same statement is a no-op.
    """
    stmt = (lesson or {}).get("statement", "")
    if stmt and stmt != state.last_reflection_lesson:
        state.last_reflection_lesson = stmt
    return state
