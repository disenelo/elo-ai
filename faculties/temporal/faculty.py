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
  - expires = True on every output — perishable per turn.
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
from dataclasses import dataclass, field

import logging
_log = logging.getLogger(__name__)
_log.addHandler(logging.NullHandler())
_log.propagate = False


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
    # Contract fields
    expires:                  bool = True
    memory_instruction_store: bool = False  # MUST always be False


@dataclass(frozen=True)
class Deadline:
    """A single anchored deadline (Ch.2). ref MUST be non-empty or this is not a deadline."""
    title:     str   = ""
    ref:       str   = ""        # calendar event id / goal id / stored user statement
    time_to_s: float = 0.0       # seconds until deadline (negative = passed)
    proximity: str   = "distant" # distant / approaching / imminent / passed
    priority:  str   = "normal"  # rises to "high" only when proximity == imminent


@dataclass(frozen=True)
class FutureFrame:
    """Forward / planning slice (Ch.2). Frozen, perishable."""
    active_horizon: str   = "short"   # immediate / short / long / identity
    deadlines:      tuple = ()        # tuple[Deadline] — all carry refs
    expires:                  bool = True
    memory_instruction_store: bool = False


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
    autobiography_path:  str   = "PENDING" # "PENDING" if autobiography.jsonl not found
    expires:                  bool = True
    memory_instruction_store: bool = False


@dataclass(frozen=True)
class TemporalOutput:
    """Three frozen slices assembled per turn. The public result of compute()."""
    temporal_state: TemporalState = field(default_factory=TemporalState)
    future_frame:   FutureFrame   = field(default_factory=FutureFrame)
    retrospection:  Retrospection = field(default_factory=Retrospection)
    expires:                  bool = True
    memory_instruction_store: bool = False  # MUST always be False


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
    expires=True,
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
            expires=True,
            memory_instruction_store=False,
        )
    except Exception as _e:
        _log.debug("temporal_state fault (%s) — default", _e)
        # Time-domain fault: defaults, never block
        return TemporalState(
            circadian_phase="active",
            energy=0.5,
            expires=True,
            memory_instruction_store=False,
        )


# ── Ch.2: FutureFrame ─────────────────────────────────────────────────────────

def _build_future_frame(world_state: object | None) -> FutureFrame:
    """Build the forward/planning slice from LiveWorldState.calendar."""
    deadlines: list[Deadline] = []
    try:
        cal = getattr(world_state, "calendar", None) if world_state else None
        if cal:
            next_event = getattr(cal, "next_event", "") or ""
            if next_event:
                # Build a deadline from next_event — ref is the event title
                # time_to_s unknown without full event metadata; mark as approaching
                deadlines.append(Deadline(
                    title=next_event[:80],      # surface without extra sensitive detail
                    ref=f"calendar:{next_event[:40]}",   # ref anchors it
                    time_to_s=_PROX_APPROACHING // 2,    # default to ~12h (approaching)
                    proximity="approaching",
                    priority="normal",
                ))
    except Exception as _e:
        _log.debug("future_frame fault (%s)", _e)

    horizon = _active_horizon(deadlines)
    return FutureFrame(
        active_horizon=horizon,
        deadlines=tuple(deadlines),
        expires=True,
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

    # IdentityState fallback (always available from continuity)
    if not memories:
        try:
            from continuity.identity_state import IdentityState
            from continuity.continuity_engine import from_state
            _state = from_state({})   # empty session → default identity
            if _state.what_matters:
                memories.append(FramedMemory(
                    ref="identity:what_matters",
                    content=_state.what_matters[:200],
                    fidelity="clear",
                    natural_age="ongoing",
                ))
        except Exception:
            pass

    return Retrospection(
        memories=tuple(memories),
        gaps=tuple(gaps),
        autobiography_path=autobiography_path,
        expires=True,
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

    Args:
        world_state:          LiveWorldState (from CognitiveState.world_state).
        last_interaction_ts:  Unix timestamp of last verified turn (from continuity).
        idle_seconds:         Seconds since last user interaction (for sleep pressure).

    Returns:
        TemporalOutput — frozen, perishable, never writes LTM.
    """
    ts  = _build_temporal_state(world_state, last_interaction_ts, idle_seconds)
    ff  = _build_future_frame(world_state)
    ret = _build_retrospection(world_state, _parse_now_ts(ts.now_iso))
    return TemporalOutput(
        temporal_state=ts,
        future_frame=ff,
        retrospection=ret,
        expires=True,
        memory_instruction_store=False,
    )


def temporal_appropriateness(behaviour_kind: str, ts: TemporalState) -> dict:
    """
    Advise whether a timed behaviour is appropriate now.
    Returns {allow: bool, reason: str}. The owner (Ambient/Agency) makes the final call.

    Quiet-hours rule: ambient/social behaviours suppressed during night/late phase.
    """
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
