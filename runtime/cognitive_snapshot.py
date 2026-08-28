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
import uuid
from dataclasses import dataclass, field


# ── Intent (WO-CANON-VII §C) ──────────────────────────────────────────────────

@dataclass(frozen=True)
class Intent:
    """One proposed or committed intention in eLo's intent queue."""
    id: str                     # uuid4 short hex, unique per construction
    lane: str                   # "external" (user/world) | "internal" (faculty-proposed)
    kind: str                   # e.g. "sit", "move", "speak"
    content: str                # target / payload (e.g. "cursor", "window_corner")
    origin: str                 # "user_command" | "faculty_propose" | "ambient"
    pressure: float             # 0.0..1.0 urgency
    feasible: bool              # can this be satisfied right now?
    boundary_ok: bool           # respects action-boundary rules?
    status: str                 # "proposed" | "committed" | "abandoned" | "satisfied"
    created_ts: float
    expires: float              # 0.0 = never; else epoch deadline


@dataclass(frozen=True)
class IntentQueue:
    """
    Two-lane intent queue: external (world/user) and internal (faculty-proposed).

    Faculty-propose, Executive-admits flow:
      - Faculties write proposed Intents into external/internal lanes.
      - The Executive reads the queue and admits exactly one per turn → committed.
      - Losing intents are journalled (see self/decision_journal.py).
    """
    external: tuple = field(default_factory=tuple)   # tuple[Intent]
    internal: tuple = field(default_factory=tuple)   # tuple[Intent]
    committed: object = None                          # Intent | None


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

    # ── WO-CANON-VII §C: Intent queue (replaces hard-coded sit tuple) ──────────
    intent_queue: IntentQueue = field(default_factory=IntentQueue)

    # ── WO-CANON-VII §B: Speech licence (tier gate — Written Not Connected → Connected)
    speech_licence: object = None   # SpeechLicence | None; built from the_moment tiers

    # ── WO-056: Affordances — surface → possible actions ──────────────────────
    surface_type: str = "unknown"
    surface_affordances: tuple = field(default_factory=tuple)  # ("stand","run",…)

    # ── WO-057: Perception scope — Chrome + capability gate ───────────────────
    chrome_open: bool = False
    chrome_tab_count: int = 0
    chrome_active_url: str = ""
    chrome_recent_domains: tuple = field(default_factory=tuple)  # top 5 domains
    gated_capabilities: tuple = field(default_factory=tuple)     # enabled cap IDs

    # ── WO-095: Recalled lessons (confirmed only, ≤3, ≤240 chars total) ────────
    lessons: tuple = field(default_factory=tuple)  # each: str (the lesson statement)

    # ── WO-CREATIVE-001: Creative imagination candidates ─────────────────────
    creative_candidates: tuple = field(default_factory=tuple)  # ({"candidate":…,"score":…},…) epistemic_status="imagined", ≤3

    # ── Assembly metadata ──────────────────────────────────────────────────────
    assembled_ts: float = 0.0
    turn_id: str = ""
    confidence: float = 1.0          # degrades when components fail; never blocks the turn


# WO-CANON-XVI / Ruling C: canonical name. CognitiveSnapshot is the implementation class;
# UnifiedCognitiveState is the name the architecture uses (ADR-Exec-006).
UnifiedCognitiveState = CognitiveSnapshot


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
        from runtime.faculty_health import (
            all_statuses,
            health_summary as _fac_summary,
            genome_health_summary as _genome_summary,
            genome_health_status as _genome_status,
        )
        fac_health = all_statuses()
        # WO-CANON-XXII: overlay genome-aware per-faculty health onto coarse buckets.
        # Coarse (reasoning|memory|tools|embodiment) stays authoritative for the
        # summary line; genome_health_summary() adds Faculty-name granularity
        # so the Snapshot exposes both.
        try:
            _genomes = _genome_summary()
            if _genomes:
                fac_health = {**fac_health, **_genomes}
            # Explicit single-faculty read for the Executive's speech-licensing
            # code (Vol VII Ch.3) — an Emotion or Perception genome that has
            # gone OFFLINE forces the "verified only" epistemic tier this turn.
            _perc = _genome_status("PerceptionFaculty")
            _emo  = _genome_status("EmotionFaculty")
            if _perc == "OFFLINE" or _emo == "OFFLINE":
                fac_health["_critical_offline"] = True
        except Exception:
            confidence -= 0.02
        fac_summary = _fac_summary()
    except Exception:
        confidence -= 0.05

    # ── Body schema (from server.py _PENDING_SIT, passed in) ──────────────────
    body = BodySchema()
    pending_intentions: list = []
    _intent_queue = IntentQueue()
    if pending_sit and pending_sit.get("active"):
        body = BodySchema(
            pending_sit=True,
            sit_pending_since=float(pending_sit.get("since", 0.0)),
            queued_intent=str(pending_sit.get("queued") or ""),
        )
        # §C: Build a real Intent instead of the hard-coded ("sit", "cursor") tuple.
        # Parity: pending_intentions still carries the legacy tuple for existing readers.
        _sit_intent = Intent(
            id=uuid.uuid4().hex[:12],
            lane="external",
            kind="sit",
            content="cursor",
            origin="user_command",
            pressure=1.0,
            feasible=True,
            boundary_ok=True,
            status="committed",
            created_ts=float(pending_sit.get("since", assembled_ts)),
            expires=0.0,   # persists until ACK'd
        )
        pending_intentions.append(("sit", "cursor"))   # legacy readers
        _intent_queue = IntentQueue(
            external=(_sit_intent,),
            internal=(),
            committed=_sit_intent,
        )

    # ── WO-056: Affordances ────────────────────────────────────────────────────
    surface_type = "unknown"
    surface_affordances: tuple = ()
    try:
        from blender_bridge.state_writer import read as _bbs_read
        _bbs = _bbs_read()
        surface_type = str(_bbs.get("surface_type", "unknown"))
    except Exception:
        pass
    try:
        from runtime.affordances import affordances_for as _aff_for, gap_state as _gap_state
        surface_affordances = _aff_for(surface_type)
        # WO-113: annotate surface_affordances with a GapAssessment for jumps
        # so the Executive can read the reliable range without re-deriving it.
        try:
            for _verb in ("jump", "wall-jump", "wall-run"):
                if _verb in surface_affordances:
                    _g = _gap_state(_verb, gap_distance=None, surface_type=surface_type)
                    # attach only when we have a signal to add (BLOCKED/UNKNOWN inclusive)
                    if _g and getattr(_g, "detail", ""):
                        break
        except Exception:
            pass
    except Exception:
        confidence -= 0.02

    # ── WO-057: Perception scope — Chrome + capability gate ───────────────────
    chrome_open = False
    chrome_tab_count = 0
    chrome_active_url = ""
    chrome_recent_domains: tuple = ()
    try:
        from desktop.chrome_reader import all_tabs as _chrome_tabs, recent_history as _chrome_hist
        _tabs = _chrome_tabs()
        if _tabs:
            chrome_open = True
            chrome_tab_count = len(_tabs)
            chrome_active_url = _tabs[0].url if _tabs else ""
        _hist = _chrome_hist(limit=20)
        _domains: list = []
        _seen: set = set()
        for _h in _hist:
            import re as _re
            _m = _re.search(r"https?://(?:www\.)?([^/]+)", _h.url)
            if _m:
                _d = _m.group(1)
                if _d not in _seen:
                    _seen.add(_d)
                    _domains.append(_d)
                    if len(_domains) >= 5:
                        break
        chrome_recent_domains = tuple(_domains)
    except Exception:
        pass

    gated_capabilities: tuple = ()
    try:
        from runtime.capabilities.registry import ALL_CAPABILITIES
        from runtime.capabilities.capability import Capability
        _enabled = []
        for _cap in ALL_CAPABILITIES:
            if not hasattr(_cap, "future") or not _cap.future:
                _fac = getattr(_cap, "requires_faculty", None)
                if _fac is None or fac_health.get(_fac) not in ("OFFLINE", "DEGRADED"):
                    _enabled.append(_cap.id)
        gated_capabilities = tuple(_enabled)
    except Exception:
        pass

    # ── WO-CANON-VII §B: Speech licence — wire tier markers to runtime gate ────
    _speech_licence = None
    try:
        from runtime.the_moment import verify_response_tiers as _vrt
        _tier_snap = {
            "self_mood":    "observed" if self_model_block else "last-known",
            "pose":         "last-known",    # conservative; pose_acked not available here
            "surface":      "last-known",    # conservative; perch_fresh not available here
            "locomotion":   "live"  if fac_health else "last-known",
            "capabilities": "live"  if gated_capabilities else "unknown",
            "nearby":       "unknown",
            "recent_behaviour": "observed" if surface_type != "unknown" else "last-known",
        }
        _speech_licence = _vrt(_tier_snap)
    except Exception:
        confidence -= 0.01

    # ── WO-095: Recalled confirmed lessons (≤3, ≤240 chars) ──────────────────
    recalled_lessons: tuple = ()
    try:
        from self.lesson_store import recall as _ls_recall
        _ls_rows = _ls_recall(
            context={"focal_thread": self_focal_thread, "topic": att.get("intent", "")},
            k=3,
        )
        recalled_lessons = tuple(r.get("statement", "") for r in _ls_rows if r.get("statement"))
    except Exception:
        confidence -= 0.01

    # ── WO-CREATIVE-001: Creative imagination (≤3 candidates, epistemic_status="imagined") ─
    _ci_snap_candidates: tuple = ()
    try:
        from faculties.creative.creative_imagination import (
            diverge as _ci_diverge,
            evaluate as _ci_evaluate,
        )
        _ci_intent = att.get("intent", "")
        if _ci_intent:
            _ci_seeds = [_ci_intent, self_focal_thread] if self_focal_thread else [_ci_intent]
            _ci_raw = _ci_diverge(goal=_ci_intent, seeds=_ci_seeds, breadth_budget=3)
            _ci_snap_candidates = tuple(
                {"candidate": c.to_dict(), "score": _ci_evaluate(c, goal=_ci_intent).to_dict()}
                for c in _ci_raw
            )
    except Exception:
        confidence -= 0.01

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
        intent_queue=_intent_queue,
        speech_licence=_speech_licence,
        surface_type=surface_type,
        surface_affordances=surface_affordances,
        chrome_open=chrome_open,
        chrome_tab_count=chrome_tab_count,
        chrome_active_url=chrome_active_url,
        chrome_recent_domains=chrome_recent_domains,
        gated_capabilities=gated_capabilities,
        lessons=recalled_lessons,
        creative_candidates=_ci_snap_candidates,
        assembled_ts=assembled_ts,
        turn_id=turn_id,
        confidence=max(0.0, min(1.0, confidence)),
    )
