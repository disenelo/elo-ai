"""
faculties/dream/sleep_cycle.py — Multi-cycle sleep schedule engine.

WO-DREAM-ENGINE-001 PHASE 1.

Replaces the single-cycle NREM/REM binary in dream_faculty.py with a
controllable generative schedule:

    CYCLE 1: NREM -> DEEP  -> REM
    CYCLE 2: NREM -> DEEP  -> REM
    CYCLE 3: NREM -> DEEP  -> REM
    CYCLE 4: NREM -> LIGHT -> REM
    CYCLE 5: NREM -> LIGHT -> LONG REM

REM lengthens with each cycle (~10 min at cycle 1 -> ~40 min at cycle 5).
Dream intensity is derived from cycle position and phase, and drives
prompt abstraction, concept merge count, visual distortion, layer opacity,
blend modes, randomness and colour transformation downstream.

This module owns schedule + state only. It does not dream, does not call
an LLM, and does not import server.py. Phase transitions can be published
to blender_state.json via publish() — Unity reads dream_cycle / dream_phase /
dream_intensity for the visual state.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Iterator

# ── Intensity scale (canonical, WO PHASE 1) ────────────────────────────────────
#   0.00 — waking residue
#   0.25 — fragmented memory
#   0.50 — associative dream
#   0.75 — strong symbolic dream
#   1.00 — maximum surreal / emotional synthesis
INTENSITY_SCALE: dict[float, str] = {
    0.00: "waking residue",
    0.25: "fragmented memory",
    0.50: "associative dream",
    0.75: "strong symbolic dream",
    1.00: "maximum surreal / emotional synthesis",
}

TOTAL_CYCLES = 5

# Per-cycle middle phase. Cycles 1-3 go deep; 4-5 stay light (REM-dominant).
_MIDDLE_PHASE: dict[int, str] = {1: "deep", 2: "deep", 3: "deep", 4: "light", 5: "light"}

# REM duration per cycle, seconds. Spec: cycle 1 ~10 min, cycle 5 ~40 min.
_REM_DURATION_S: dict[int, int] = {1: 600, 2: 1050, 3: 1500, 4: 1950, 5: 2400}

# Non-REM phase durations, seconds. [ESTIMATE] — not specified in the WO.
# David/Board to confirm against observed runtime before these are treated as canon.
_NREM_DURATION_S = 900
_DEEP_DURATION_S = 1200
_LIGHT_DURATION_S = 600

# Phase weighting applied to the cycle-position base intensity.
# Deep sleep dreams least; REM is the peak.
_PHASE_INTENSITY_FACTOR: dict[str, float] = {
    "nrem": 0.40,
    "deep": 0.20,
    "light": 0.55,
    "rem": 1.00,
}

# Cycle content weighting (WO PHASE 1 "Cycle content weighting").
# Bands name which Dream Input Field sources dream_input.py should pull from.
CONTENT_BANDS: dict[str, tuple[int, ...]] = {
    "early": (1, 2),
    "middle": (3,),
    "late": (4, 5),
}

CONTENT_DESCRIPTION: dict[str, str] = {
    "early": "recent experiences, concrete memories, recent conversations, "
             "current projects, grounded imagery",
    "middle": "memory recombination, WKG relationships, older experiences, "
              "recurring SPG patterns, unresolved ideas",
    "late": "abstraction, unusual associations, distant memories, emotional "
            "transformation, surreal imagery, creative recombination",
}


def content_band(cycle_number: int) -> str:
    """Return 'early' | 'middle' | 'late' for a cycle number."""
    for band, cycles in CONTENT_BANDS.items():
        if cycle_number in cycles:
            return band
    return "late"


def intensity_for(cycle_number: int, phase: str) -> float:
    """
    Dream intensity (0.0–1.0) for a given cycle position and phase.

    Base rises linearly with cycle position (1/5 .. 5/5), then is weighted by
    phase: REM carries the cycle's full intensity, deep sleep the least.
    """
    base = max(1, min(TOTAL_CYCLES, int(cycle_number))) / TOTAL_CYCLES
    factor = _PHASE_INTENSITY_FACTOR.get(phase, 0.5)
    return round(base * factor, 2)


def intensity_label(intensity: float) -> str:
    """Nearest label on the canonical intensity scale."""
    nearest = min(INTENSITY_SCALE, key=lambda k: abs(k - intensity))
    return INTENSITY_SCALE[nearest]


# ── Phase record ───────────────────────────────────────────────────────────────

@dataclass
class CyclePhase:
    """One phase inside one sleep cycle."""
    cycle_number: int
    phase: str            # "nrem" | "deep" | "light" | "rem"
    duration_s: int
    dream_intensity: float
    content_band: str     # "early" | "middle" | "late"
    long_rem: bool = False
    index: int = 0        # position in the flattened schedule

    @property
    def is_rem(self) -> bool:
        return self.phase == "rem"

    @property
    def rem_duration_s(self) -> int:
        """REM length for this phase's cycle (0 outside REM)."""
        return _REM_DURATION_S[self.cycle_number] if self.is_rem else 0

    def state_fields(self) -> dict:
        """The three fields Unity reads from blender_state.json."""
        return {
            "dream_cycle": self.cycle_number,
            "dream_phase": self.phase,
            "dream_intensity": self.dream_intensity,
        }

    def as_dict(self) -> dict:
        d = asdict(self)
        d["rem_duration_s"] = self.rem_duration_s
        d["intensity_label"] = intensity_label(self.dream_intensity)
        return d


# ── Schedule ───────────────────────────────────────────────────────────────────

def build_schedule(cycles: int = TOTAL_CYCLES) -> list[CyclePhase]:
    """
    Build the flattened phase schedule for a full sleep session.

    cycles — 1..5. Fewer cycles = a short sleep that never reaches the late
    abstraction band; the schedule truncates rather than compressing.
    """
    cycles = max(1, min(TOTAL_CYCLES, int(cycles)))
    schedule: list[CyclePhase] = []
    idx = 0

    for n in range(1, cycles + 1):
        middle = _MIDDLE_PHASE[n]
        band = content_band(n)
        ordered = (
            ("nrem", _NREM_DURATION_S),
            (middle, _DEEP_DURATION_S if middle == "deep" else _LIGHT_DURATION_S),
            ("rem", _REM_DURATION_S[n]),
        )
        for phase, duration in ordered:
            schedule.append(
                CyclePhase(
                    cycle_number=n,
                    phase=phase,
                    duration_s=duration,
                    dream_intensity=intensity_for(n, phase),
                    content_band=band,
                    long_rem=(phase == "rem" and n == TOTAL_CYCLES),
                    index=idx,
                )
            )
            idx += 1

    return schedule


def total_duration_s(cycles: int = TOTAL_CYCLES) -> int:
    """Total wall-clock seconds for a full schedule."""
    return sum(p.duration_s for p in build_schedule(cycles))


def rem_phases(cycles: int = TOTAL_CYCLES) -> list[CyclePhase]:
    """Just the REM phases — one dream per REM peak."""
    return [p for p in build_schedule(cycles) if p.is_rem]


# ── State machine ──────────────────────────────────────────────────────────────

class SleepCycle:
    """
    Phase state machine for one sleep session.

    Usage:
        sc = SleepCycle(cycles=5)
        while not sc.is_complete:
            phase = sc.advance()
            publish(phase)          # -> blender_state.json
            ... run the phase ...
    """

    def __init__(self, cycles: int = TOTAL_CYCLES) -> None:
        self._schedule = build_schedule(cycles)
        self._pos = -1

    # -- introspection --
    @property
    def schedule(self) -> list[CyclePhase]:
        return list(self._schedule)

    @property
    def is_complete(self) -> bool:
        return self._pos >= len(self._schedule) - 1

    @property
    def started(self) -> bool:
        return self._pos >= 0

    def current(self) -> CyclePhase | None:
        if 0 <= self._pos < len(self._schedule):
            return self._schedule[self._pos]
        return None

    def peek(self) -> CyclePhase | None:
        nxt = self._pos + 1
        return self._schedule[nxt] if nxt < len(self._schedule) else None

    # -- movement --
    def advance(self) -> CyclePhase | None:
        """Step to the next phase. Returns None when the schedule is spent."""
        if self.is_complete and self.started:
            return None
        self._pos += 1
        return self.current()

    def reset(self) -> None:
        self._pos = -1

    def __iter__(self) -> Iterator[CyclePhase]:
        while True:
            phase = self.advance()
            if phase is None:
                return
            yield phase

    # -- output --
    def state_fields(self) -> dict:
        phase = self.current()
        if phase is None:
            return {"dream_cycle": 0, "dream_phase": None, "dream_intensity": 0.0}
        return phase.state_fields()


# ── blender_state.json publishing ──────────────────────────────────────────────

def publish(phase: CyclePhase | None) -> bool:
    """
    Write this phase's dream fields to blender_state.json.

    Best-effort: returns False and stays silent if the bridge is unavailable.
    Called on each phase transition. Unity reads for the dream visual state.
    """
    fields = phase.state_fields() if phase is not None else {
        "dream_cycle": 0, "dream_phase": None, "dream_intensity": 0.0,
    }
    try:
        from blender_bridge.state_writer import patch as _patch
        _patch(fields)
        return True
    except Exception:
        return False
