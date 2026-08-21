"""
faculties/temporal/faculty.py — Temporal Cognition Faculty (WO-CANON-XXV)

One asked faculty. Three frozen per-turn slices:
  TemporalState  — present / circadian (Ch.1)
  FutureFrame    — deadlines / planning horizon (Ch.2)
  Retrospection  — memory ageing / retrospective framing (Ch.3)

Rules (MUST):
  - Reads LiveWorldState.time verbatim — NEVER calls time.time() mid-turn.
  - All derivations are pure/deterministic functions of now_ts + stored timestamps.
  - memory_instruction_store = False on every output — never writes LTM.
  - expires = now_ts + _TURN_TTL (a timestamp, not a bool) — perishable per turn.
  - Never fires autonomously; asked by Executive only.
  - Time-domain fault → TemporalState with defaults (circadian_phase=active, energy=0.5) — never blocks.
  - Cold start (no last_interaction_ts) → interaction_gap="unknown", no false reunion.
  - Baseless Anticipation → dropped, not softened.
  - Faded memory narrated as faded, never reconstructed.
  - autobiography.jsonl absent → retrospection from vault + IdentityState, path marked PENDING.

Vol XXV Canon ref: docs/architecture/Volume_XXV/
"""
from __future__ import annotations

import datetime
import math
import re
import time as _time_module
from dataclasses import dataclass, field

import logging
_log = logging.getLogger(__name__)
_log.addHandler(logging.NullHandler())
_log.propagate = False


# ── Perishability (Vol V CONTRACTS §2) ────────────────────────────────────────
_TURN_TTL = 30.0    # seconds; a frame from a prior turn is rejectable after this


# ── Faculty lifecycle states (Ch.1 §1.8 / Ch.2 §2.7 / Ch.3 §3.7) ─────────────
LC_INITIALISING   = "INITIALISING"
LC_ACTIVE         = "ACTIVE"
LC_PROCESSING     = "PROCESSING"
LC_ERROR_RECOVERY = "ERROR_RECOVERY"
LC_LEARNING       = "LEARNING_UPDATING"
LC_STABLE         = "STABLE"

_faculty_lifecycle: str = LC_ACTIVE   # transitions in compute()


# ── Cadence model (Ch.1 §1.8 scope amendment) ─────────────────────────────────
# Stated direction outranks learned. Nothing inferred from silence.
_stated_cadence: str = ""    # David's stated cadence direction — overrides learned
_learned_cadence: str = ""   # inferred from session history (fallback only)


# ── Current temporal state (module-level — updated by compute(), read by ambient) ──
_current_temporal_state: "TemporalState | None" = None


# ── Interaction-gap thresholds (Ch.1 §1.3) ────────────────────────────────────

_GAP_CONTINUOUS  =    90    # < 90 s
_GAP_BRIEF       =   900    # 90 s – 15 m
_GAP_HOURS       = 18_000   # 15 m – 5 h
_GAP_OVERNIGHT   = 64_800   # 5 h – 18 h  (+ night boundary)
_GAP_DAYS        = 432_000  # 18 h – 5 d
#                           > 5 d → long_absence


# ── Circadian curve (part_of_day → phase, energy) ─────────────────────────────

_CIRCADIAN: dict[str, tuple[str, float]] = {
    "early":     ("low",    0.30),
    "morning":   ("active", 0.75),
    "afternoon": ("active", 0.65),
    "evening":   ("alert",  0.50),
    "night":     ("low",    0.25),
    "late":      ("low",    0.20),
    "day":       ("active", 0.60),   # fallback for unclassified daytime
}

# Dream-faculty constants (Vol IX §1.3) — context only, NEVER fires the dream
_DREAM_IDLE_THRESHOLD = 600    # 10 min
_DREAM_COOLDOWN       = 3600   # 1 hour


# ── Deadline proximity thresholds (Ch.2 §2.3) ─────────────────────────────────

_PROX_IMMINENT    = 2 * 3600     # 0–2 h
_PROX_APPROACHING = 24 * 3600    # 2–24 h
# > 24 h → distant; < 0 → passed


# ── Data classes ──────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class TemporalState:
    """Present/circadian slice (Ch.1). Frozen, perishable, never writes memory."""
    # Objective anchor — verbatim from LiveWorldState.time
    now_iso:      str   = ""
    part_of_day:  str   = "active"
    weekday:      str   = ""
    # Derived subjective fields
    circadian_phase:     str   = "active"   # "active" | "alert" | "low"
    energy:              float = 0.5        # 0.0–1.0
    sleep_pressure:      float = 0.0        # monotone function of idle (context, not trigger)
    since_last_interaction_s: float = 0.0
    interaction_gap:     str   = "unknown"  # continuous/brief/hours/overnight/days/long_absence/unknown
    # Contract fields (Vol V CONTRACTS §2)
    expires:                  float = 0.0   # now_ts + _TURN_TTL; 0.0 = expired (fault)
    memory_instruction_store: bool  = False  # MUST always be False


@dataclass(frozen=True)
class Deadline:
    """A single anchored deadline (Ch.2). ref MUST be non-empty or this is not a deadline."""
    title:     str   = ""
    ref:       str   = ""        # calendar event id / goal id / stored user statement
    time_to_s: float = 0.0       # seconds until deadline (negative = passed)
    proximity: str   = "distant" # distant / approaching / imminent / passed
    priority:  str   = "normal"  # rises to "high" only when proximity == imminent


@dataclass(frozen=True)
class Anticipation:
    """
    A single cited anticipation (Ch.2 §2.5).

    MUST carry a basis — baseless Anticipation is DROPPED, not softened.
    Never triggers an action; surfaces to Agency/Executive as context only.
    """
    statement:  str   = ""
    basis:      str   = ""     # "learned_cadence" | "pattern_memory" | "calendar_gap"
    confidence: float = 0.0
    spoken:     bool  = False  # True only after Executive decides to surface it
    ref:        str   = ""     # source ref (same anchoring rule as Deadline)


@dataclass(frozen=True)
class PlanningHorizon:
    """
    A lens over Agency's existing goal tiers — NOT a second tier system (Ch.2 §2.3).

    No second tier enum. Priority rises to "high" only at imminent deadline.
    """
    tier:             str            = "short_term"  # maps to Agency: immediate/short_term/long_term/identity_goals
    priority:         str            = "normal"       # "high" only when nearest_deadline.proximity == "imminent"
    nearest_deadline: "Deadline | None" = None


@dataclass(frozen=True)
class FutureFrame:
    """Forward / planning slice (Ch.2). Frozen, perishable."""
    active_horizon: str   = "short"   # immediate / short / long / identity
    deadlines:      tuple = ()        # tuple[Deadline] — all carry refs
    anticipations:  tuple = ()        # tuple[Anticipation] — all carry basis
    horizon:        "PlanningHorizon | None" = None
    expires:                  float = 0.0   # now_ts + _TURN_TTL
    memory_instruction_store: bool  = False


@dataclass(frozen=True)
class FramedMemory:
    """A single retrospective memory frame (Ch.3). ref MUST be non-empty."""
    ref:         str  = ""       # ref to stored vault record
    content:     str  = ""
    fidelity:    str  = "clear"  # vivid / clear / faded — derived from strength, NOT age
    natural_age: str  = ""       # calendar-boundary framing ("yesterday", "last week")


@dataclass(frozen=True)
class Retrospection:
    """Backward / memory slice (Ch.3). Never writes or decays memory."""
    memories:            tuple = ()         # tuple[FramedMemory]
    gaps:                tuple = ()         # tuple[str] — honest gap statements
    thread_arc:          str   = ""         # Vol XXI thread: how far we've come (Ch.3 §3.5)
    window:              str   = ""         # what we've been doing lately
    autobiography_path:  str   = "PENDING" # "PENDING" if autobiography.jsonl not found
    expires:                  float = 0.0   # now_ts + _TURN_TTL
    memory_instruction_store: bool  = False


@dataclass(frozen=True)
class TemporalOutput:
    """
    Three frozen slices assembled per turn.  The public result of compute().

    Vol V CONTRACTS §2 envelope: sender, receiver, priority, payload_type,
    confidence, expires (timestamp), trace, context.memory_instruction.store.
    """
    temporal_state: TemporalState = field(default_factory=TemporalState)
    future_frame:   FutureFrame   = field(default_factory=FutureFrame)
    retrospection:  Retrospection = field(default_factory=Retrospection)
    # ── Vol V CONTRACTS §2 envelope ──
    sender:         str   = "TemporalCognitionFaculty"
    receiver:       str   = "*"
    priority:       str   = "normal"
    payload_type:   str   = "combined"   # temporal_state | future_frame | retrospection | combined
    confidence:     float = 0.0
    expires:        float = 0.0          # now_ts + _TURN_TTL (timestamp, not bool)
    trace:          tuple = ()           # ("TemporalCognitionFaculty@<ts>",)
    memory_instruction_store: bool = False   # MUST always be False


# ── Helpers ───────────────────────────────────────────────────────────────────

def _parse_now_ts(now_iso: str) -> float:
    """Parse ISO datetime string → unix timestamp. Returns 0.0 on any fault."""
    try:
        if now_iso:
            return datetime.datetime.fromisoformat(now_iso).timestamp()
    except Exception:
        pass
    return 0.0


def _interaction_gap(elapsed_s: float, part_of_day: str) -> str:
    """Classify elapsed seconds into an interaction gap category."""
    if elapsed_s <= 0:
        return "unknown"
    if elapsed_s < _GAP_CONTINUOUS:
        return "continuous"
    if elapsed_s < _GAP_BRIEF:
        return "brief"
    if elapsed_s < _GAP_HOURS:
        return "hours"
    if elapsed_s < _GAP_OVERNIGHT:
        # overnight requires a night boundary to have passed
        if part_of_day in ("night", "late", "early"):
            return "overnight"
        return "hours"      # long hours but night boundary not crossed
    if elapsed_s < _GAP_DAYS:
        return "days"
    return "long_absence"


def _sleep_pressure(idle_s: float) -> float:
    """Monotone sleep-pressure function scaled toward Dream thresholds (context only)."""
    if idle_s <= 0:
        return 0.0
    # 0.0 at 0s, 0.5 at DREAM_IDLE_THRESHOLD (600s), 1.0 at DREAM_COOLDOWN (3600s)
    return min(1.0, idle_s / _DREAM_COOLDOWN)


def _deadline_proximity(time_to_s: float) -> tuple[str, str]:
    """Return (proximity, priority) for a deadline time_to_s seconds away."""
    if time_to_s < 0:
        return "passed", "normal"
    if time_to_s <= _PROX_IMMINENT:
        return "imminent", "high"
    if time_to_s <= _PROX_APPROACHING:
        return "approaching", "normal"
    return "distant", "normal"


def _natural_age(elapsed_s: float, now_ts: float) -> str:
    """Calendar-boundary framing — 'yesterday', 'last week', etc."""
    if elapsed_s <= 0:
        return "recent"
    if elapsed_s < 3600:
        return "earlier today"
    if elapsed_s < 86400:
        return "earlier today"
    if elapsed_s < 172800:
        return "yesterday"
    if elapsed_s < 604800:
        return "this week"
    if elapsed_s < 2592000:
        return "last week"
    return "some time ago"


def _fidelity_from_strength(strength: float, identity_level: bool = False) -> str:
    """Fidelity from strength (not age). Identity/pinned always ≥ clear."""
    if identity_level:
        return "vivid" if strength >= 0.8 else "clear"
    if strength >= 0.75:
        return "vivid"
    if strength >= 0.45:
        return "clear"
    return "faded"


def _active_horizon(deadlines: list[Deadline]) -> str:
    """Choose active planning horizon from nearest binding deadline."""
    if any(d.proximity == "imminent" for d in deadlines):
        return "immediate"
    if any(d.proximity == "approaching" for d in deadlines):
        return "short"
    if deadlines:
        return "long"
    return "short"


# ── Ch.1: TemporalState ───────────────────────────────────────────────────────

_FAULT_TEMPORAL = TemporalState(
    circadian_phase="active",
    energy=0.5,
    expires=0.0,   # fault state: expired immediately — no TTL on a fault frame
    memory_instruction_store=False,
)


def _build_temporal_state(
    world_state: object | None,
    last_interaction_ts: float = 0.0,
    idle_seconds: float = 0.0,
) -> TemporalState:
    """Build the present/circadian slice from LiveWorldState.time. Fault-tolerant."""
    # Explicit fault: no world state at all
    if world_state is None:
        return _FAULT_TEMPORAL
    try:
        time_domain = getattr(world_state, "time", None)
        now_iso     = getattr(time_domain, "now_iso", "") or ""
        part_of_day = getattr(time_domain, "part_of_day", "day") or "day"
        weekday     = getattr(time_domain, "day_of_week", "") or ""

        # Derive unix ts from now_iso — never re-read the OS clock here
        now_ts = _parse_now_ts(now_iso)

        # Circadian phase and energy
        phase, energy = _CIRCADIAN.get(part_of_day, ("active", 0.5))

        # Sleep pressure — context only, never fires the dream
        pressure = _sleep_pressure(idle_seconds)

        # Subjective elapsed time
        since_s = (now_ts - last_interaction_ts) if (now_ts > 0 and last_interaction_ts > 0) else 0.0
        gap     = _interaction_gap(since_s, part_of_day) if since_s > 0 else "unknown"

        return TemporalState(
            now_iso=now_iso,
            part_of_day=part_of_day,
            weekday=weekday,
            circadian_phase=phase,
            energy=round(energy, 2),
            sleep_pressure=round(pressure, 3),
            since_last_interaction_s=round(since_s, 1),
            interaction_gap=gap,
            expires=now_ts + _TURN_TTL if now_ts > 0 else _time_module.time() + _TURN_TTL,
            memory_instruction_store=False,
        )
    except Exception as _e:
        _log.debug("temporal_state fault (%s) — default", _e)
        # Time-domain fault: ERROR_RECOVERY → neutral circadian, never blocks
        return TemporalState(
            circadian_phase="active",
            energy=0.5,
            expires=0.0,   # fault frame: expired
            memory_instruction_store=False,
        )


# ── Ch.2: FutureFrame ─────────────────────────────────────────────────────────

def _build_future_frame(world_state: object | None, now_ts: float = 0.0) -> FutureFrame:
    """Build the forward/planning slice from LiveWorldState.calendar."""
    deadlines: list[Deadline] = []
    anticipations: list[Anticipation] = []
    try:
        cal = getattr(world_state, "calendar", None) if world_state else None
        if cal:
            next_event = getattr(cal, "next_event", "") or ""
            if next_event:
                deadlines.append(Deadline(
                    title=next_event[:80],
                    ref=f"calendar:{next_event[:40]}",
                    time_to_s=_PROX_APPROACHING // 2,
                    proximity="approaching",
                    priority="normal",
                ))
            # Anticipation from calendar gap — only if basis is present
            free_until = getattr(cal, "free_until", "") or ""
            if free_until and not next_event:
                # Basis: calendar_gap (David has free time — cite the gap, not a claim)
                anticipations.append(Anticipation(
                    statement="open window coming up",
                    basis="calendar_gap",
                    confidence=0.6,
                    spoken=False,
                    ref=f"calendar:free_until:{free_until[:40]}",
                ))
    except Exception as _e:
        _log.debug("future_frame fault (%s)", _e)

    # Cadence-based anticipation (only if cadence is stated — never from silence)
    eff_cadence = effective_cadence()
    if eff_cadence:
        anticipations.append(Anticipation(
            statement=f"following {eff_cadence} cadence",
            basis="learned_cadence",
            confidence=0.5,
            spoken=False,
            ref=f"cadence:{eff_cadence[:40]}",
        ))

    # Baseless anticipations are DROPPED (not softened — Vol XXV §2.5)
    anticipations = [a for a in anticipations if a.basis]

    horizon_str = _active_horizon(deadlines)
    # Tier mapping (lens over Agency's existing tiers — no second enum)
    _tier_map = {
        "immediate": "immediate",
        "short":     "short_term",
        "long":      "long_term",
        "identity":  "identity_goals",
    }
    nearest = deadlines[0] if deadlines else None
    imm_priority = "high" if (nearest and nearest.proximity == "imminent") else "normal"
    horizon = PlanningHorizon(
        tier=_tier_map.get(horizon_str, "short_term"),
        priority=imm_priority,
        nearest_deadline=nearest,
    )

    ts = now_ts + _TURN_TTL if now_ts > 0 else _time_module.time() + _TURN_TTL
    return FutureFrame(
        active_horizon=horizon_str,
        deadlines=tuple(deadlines),
        anticipations=tuple(anticipations),
        horizon=horizon,
        expires=ts,
        memory_instruction_store=False,
    )


# ── Ch.3: Retrospection ───────────────────────────────────────────────────────

def _build_retrospection(world_state: object | None, now_ts: float) -> Retrospection:
    """Build the backward/memory slice. Never writes; never decays."""
    import os
    autobiography_path = "PENDING"
    memories: list[FramedMemory] = []
    gaps: list[str] = []

    # Check for autobiography journal (WO-078) — designed fallback if absent
    try:
        _ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        _AUTOBIO = os.path.join(_ROOT, "self", "journals", "autobiography.jsonl")
        if os.path.isfile(_AUTOBIO):
            autobiography_path = _AUTOBIO
    except Exception:
        pass

    # Read recent vault memories — never write, never decay
    try:
        from memory.vault_layer import lookup as _lookup
        hits = _lookup("", max_results=5)    # recent records
        if hits:
            for h in hits:
                content = h.get("content") or h.get("body") or ""
                ref     = h.get("spot") or h.get("id") or ""
                if not ref or not content:
                    gaps.append("one record missing ref — not reconstructed")
                    continue
                strength    = float(h.get("weight", 5)) / 9.0
                identity_lv = h.get("memory_type", "") in ("identity", "core")
                fid = _fidelity_from_strength(strength, identity_level=identity_lv)
                # Identity/pinned never reads faded
                if identity_lv and fid == "faded":
                    fid = "clear"
                ts_stored = float(h.get("ts", 0) or 0)
                elapsed   = (now_ts - ts_stored) if (now_ts > 0 and ts_stored > 0) else 0.0
                nat_age   = _natural_age(elapsed, now_ts)
                memories.append(FramedMemory(
                    ref=ref,
                    content=content[:200],
                    fidelity=fid,
                    natural_age=nat_age,
                ))
        else:
            gaps.append("no recent vault records available")
    except Exception as _e:
        _log.debug("retrospection vault fault (%s)", _e)
        gaps.append("vault unavailable — retrospection limited")

    # ── Vol XXI thread integration (Ch.3 §3.5) ───────────────────────────────
    # Reads IdentityState to frame thread_arc and window.
    # Does NOT own the thread, never writes memory, never adjusts strength.
    # autobiography.jsonl path: PENDING until WO-078 delivers it.
    thread_arc = ""
    window = ""
    try:
        from continuity.identity_state import IdentityState as _IS
        from continuity.continuity_engine import from_state as _from_state
        _identity = _from_state({})   # empty session → current identity state

        # thread_arc: "how far have we come?" — frames meaning in time
        if getattr(_identity, "what_changed", ""):
            thread_arc = _identity.what_changed[:200]
        elif getattr(_identity, "what_matters", ""):
            thread_arc = _identity.what_matters[:200]

        # window: "what have we been doing lately?"
        if getattr(_identity, "active_project", ""):
            window = _identity.active_project[:200]

        # Add identity memories (always available, never faded for pinned)
        if getattr(_identity, "what_matters", ""):
            memories.append(FramedMemory(
                ref="identity:what_matters",
                content=_identity.what_matters[:200],
                fidelity="clear",    # identity-level: always ≥ clear
                natural_age="ongoing",
            ))
    except Exception as _ie:
        _log.debug("retrospection thread fault (%s)", _ie)
        # Gaps are stated honestly — not filled
        if not memories:
            gaps.append("identity thread unavailable this turn")

    ts = now_ts + _TURN_TTL if now_ts > 0 else _time_module.time() + _TURN_TTL
    return Retrospection(
        memories=tuple(memories),
        gaps=tuple(gaps),
        thread_arc=thread_arc,
        window=window,
        autobiography_path=autobiography_path,
        expires=ts,
        memory_instruction_store=False,
    )


# ── Public API ────────────────────────────────────────────────────────────────

def compute(
    world_state: object | None = None,
    last_interaction_ts: float = 0.0,
    idle_seconds: float = 0.0,
) -> TemporalOutput:
    """
    Compute the three frozen temporal slices from read-only anchors.

    Called once per turn during assembly (spine.py). Pins output onto CognitiveState.

    Lifecycle: ACTIVE → PROCESSING → (ERROR_RECOVERY on fault) → STABLE.
    The only clock is LiveWorldState.time — NEVER re-senses mid-turn.
    """
    global _faculty_lifecycle, _current_temporal_state

    _faculty_lifecycle = LC_PROCESSING

    fault = False
    try:
        ts  = _build_temporal_state(world_state, last_interaction_ts, idle_seconds)
        now_ts = _parse_now_ts(ts.now_iso)
        ff  = _build_future_frame(world_state, now_ts=now_ts)
        ret = _build_retrospection(world_state, now_ts)
        if ts.expires == 0.0:
            fault = True
    except Exception as _e:
        _log.warning("TemporalCognitionFaculty.compute() fault (%s) — defaults", _e)
        fault = True
        ts  = _FAULT_TEMPORAL
        ff  = FutureFrame(expires=0.0, memory_instruction_store=False)
        ret = Retrospection(gaps=("temporal fault this turn",), expires=0.0,
                            memory_instruction_store=False)
        now_ts = 0.0

    _faculty_lifecycle = LC_ERROR_RECOVERY if fault else LC_STABLE

    # Update module-level current temporal state (read by ambient engine)
    _current_temporal_state = ts

    # ── Build envelope (Vol V CONTRACTS §2) ─────────────────────────────────
    expires_ts = now_ts + _TURN_TTL if now_ts > 0 else (_time_module.time() + _TURN_TTL)
    confidence = ts.energy if not fault else 0.0
    trace_str  = f"TemporalCognitionFaculty@{int(now_ts)}" if now_ts else "TemporalCognitionFaculty@fault"

    output = TemporalOutput(
        temporal_state=ts,
        future_frame=ff,
        retrospection=ret,
        sender="TemporalCognitionFaculty",
        receiver="*",
        priority="normal",
        payload_type="combined",
        confidence=round(confidence, 3),
        expires=expires_ts,
        trace=(trace_str,),
        memory_instruction_store=False,
    )

    _faculty_lifecycle = LC_ACTIVE   # return to ACTIVE between turns
    return output


# ── Cadence model public API ──────────────────────────────────────────────────

def set_stated_cadence(direction: str) -> None:
    """
    Record David's stated direction. This outranks anything learned (Ch.1 §1.8 rule).
    Nothing is inferred from silence — call this only when David explicitly states a cadence.
    """
    global _stated_cadence
    _stated_cadence = direction.strip()


def effective_cadence() -> str:
    """
    Return the active cadence: stated direction if set, else learned. Empty = no cadence.
    Stated outranks learned by rule — this function enforces that order.
    """
    return _stated_cadence if _stated_cadence else _learned_cadence


def get_lifecycle_state() -> str:
    """Return the current faculty lifecycle state."""
    return _faculty_lifecycle


def temporal_appropriateness(behaviour_kind: str, ts: "TemporalState | None" = None) -> dict:
    """
    Advise whether a timed behaviour is appropriate now.
    Returns {allow: bool, reason: str}. The owner (Ambient/Agency) makes the final call.

    ts=None → reads the module-level _current_temporal_state (set by compute() each turn).
    Quiet-hours rule: ambient/social behaviours suppressed during night/late phase.
    """
    if ts is None:
        ts = _current_temporal_state
    if ts is None:
        # Faculty hasn't run yet — allow, never block on missing state
        return {"allow": True, "reason": "temporal state unavailable"}

    quiet_behaviours = frozenset({
        "ambient_greeting", "idle_comment", "idle_utterance",
        "random_smile", "unsolicited_check_in",
    })
    if behaviour_kind in quiet_behaviours and ts.circadian_phase == "low":
        return {
            "allow":  False,
            "reason": f"quiet hours ({ts.part_of_day} phase — energy {ts.energy:.2f})",
        }
    return {"allow": True, "reason": ""}
