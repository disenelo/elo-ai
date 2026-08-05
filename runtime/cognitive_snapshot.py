"""
runtime/cognitive_snapshot.py — CognitiveSnapshot (WO-052)

ONE frozen read of eLo's full state, assembled at the TOP of each turn,
pushed to the Executive BEFORE any decision is made.

Rule: assemble once per turn, at the top. Never pull from faculties mid-turn.

Components:
    self_model      — eLo's own inner state (mood, curiosity, focal thread)
    faculty_health  — per-faculty CONNECTED/DEGRADED/OFFLINE
    attention       — intent, valence, momentum (from server.py pre-computed)
    body_schema     — eLo's current presence state (pending sit, movement intent)
    intentions      — pending intentions that must survive the decision cycle

Usage:
    from runtime.cognitive_snapshot import build_snapshot
    snapshot = build_snapshot(attention=att, pending_sit=_PENDING_SIT)
    # pass snapshot to spine.run() → Executive reads it before deciding
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field


# ── Body schema ───────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class BodySchema:
    """What eLo knows about his own body/presence state right now."""
    pending_sit: bool = False           # sit command in-flight, avatar not yet confirmed
    sit_pending_since: float = 0.0     # epoch when sit was commanded
    queued_intent: str = ""            # movement intent queued while sit is pending
    last_known_movement: str = ""      # last movement intent (contextual)


# ── CognitiveSnapshot ─────────────────────────────────────────────────────────

@dataclass(frozen=True)
class CognitiveSnapshot:
    """
    The complete assembled state BEFORE any Executive decision.

    Assembled once per turn at the top of spine.run().
    Frozen immediately. The Executive reads this; no faculty mutates it.
    Push (assembled and delivered) not pull (queried mid-turn).
    """

    # ── eLo's inner state (self/elo_self_model.py) ────────────────────────────
    self_mood: float = 0.55
    self_curiosity: float = 0.60
    self_satisfaction: float = 0.55
    self_session_read: str = "just started"
    self_focal_thread: str = ""
    self_model_block: str = ""         # pre-formatted [ELO INNER STATE] prompt block

    # ── Faculty health (runtime/faculty_health.py) ─────────────────────────────
    faculty_health: dict = field(default_factory=dict)   # {faculty: CONNECTED/DEGRADED/OFFLINE}
    health_summary: str = ""

    # ── Attention (pre-computed by server.py, passed in via attention dict) ────
    intent: str = "conversation"
    valence: str = "neutral"
    momentum: str = "stable"
    tone: str = ""
    action: str = ""

    # ── Body / presence schema ─────────────────────────────────────────────────
    body: BodySchema = field(default_factory=BodySchema)

    # ── Pending intentions ─────────────────────────────────────────────────────
    pending_intentions: tuple = field(default_factory=tuple)   # ((name, target), ...)

    # ── Assembly metadata ──────────────────────────────────────────────────────
    assembled_ts: float = 0.0
    turn_id: str = ""
    confidence: float = 1.0          # degrades when components fail; never blocks the turn


# ── Assembly ──────────────────────────────────────────────────────────────────

def build_snapshot(
    attention: dict | None = None,
    pending_sit: dict | None = None,
    turn_id: str = "",
) -> CognitiveSnapshot:
    """
    Assemble one CognitiveSnapshot from all available sources.

    Called ONCE at the top of spine.run(), BEFORE the Executive decides.
    Each component fails independently — a failed component returns a safe
    default, never blocking the turn.

    Args:
        attention   — pre-computed attention dict from server.py
                      (intent, valence, momentum, tone, action, …)
        pending_sit — _PENDING_SIT dict from server.py
                      {"active": bool, "since": float, "queued": str|None}
        turn_id     — optional identifier for this turn
    """
    confidence = 1.0
    assembled_ts = time.time()
    att = attention or {}

    # ── eLo self-model ─────────────────────────────────────────────────────────
    self_mood = 0.55
    self_curiosity = 0.60
    self_satisfaction = 0.55
    self_session_read = "just started"
    self_focal_thread = ""
    self_model_block = ""
    try:
        from self.elo_self_model import load as _self_load, prompt_block as _self_block
        _self_state = _self_load()
        self_mood = _self_state.mood
        self_curiosity = _self_state.curiosity
        self_satisfaction = _self_state.satisfaction
        self_session_read = _self_state.session_read
        self_focal_thread = _self_state.focal_thread
        self_model_block = _self_block(_self_state)
    except Exception:
        confidence -= 0.05

    # ── Faculty health ─────────────────────────────────────────────────────────
    fac_health: dict = {}
    fac_summary = ""
    try:
        from runtime.faculty_health import all_statuses, health_summary as _fac_summary
        fac_health = all_statuses()
        fac_summary = _fac_summary()
    except Exception:
        confidence -= 0.05

    # ── Body schema (from server.py _PENDING_SIT, passed in) ──────────────────
    body = BodySchema()
    pending_intentions: list = []
    if pending_sit and pending_sit.get("active"):
        body = BodySchema(
            pending_sit=True,
            sit_pending_since=float(pending_sit.get("since", 0.0)),
            queued_intent=str(pending_sit.get("queued") or ""),
        )
        pending_intentions.append(("sit", "cursor"))

    return CognitiveSnapshot(
        self_mood=round(self_mood, 3),
        self_curiosity=round(self_curiosity, 3),
        self_satisfaction=round(self_satisfaction, 3),
        self_session_read=self_session_read,
        self_focal_thread=self_focal_thread,
        self_model_block=self_model_block,
        faculty_health=fac_health,
        health_summary=fac_summary,
        intent=att.get("intent", "conversation"),
        valence=att.get("valence", "neutral"),
        momentum=att.get("momentum", "stable"),
        tone=att.get("tone", ""),
        action=att.get("action", ""),
        body=body,
        pending_intentions=tuple(pending_intentions),
        assembled_ts=assembled_ts,
        turn_id=turn_id,
        confidence=max(0.0, min(1.0, confidence)),
    )
