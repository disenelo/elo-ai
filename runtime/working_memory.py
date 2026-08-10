"""
runtime/working_memory.py — Working Memory + Attention (WO-008 / WO-CANON-VI)

Typed, bounded working memory and the attention competition that decides focus.
Executive-owned per D-G (DECISION_LOG.md).

Spec:  docs/architecture/Volume_VI/01_Working_Memory_and_Attention.md
Canon: Working Memory = bounded, typed, per-turn frames.
       Attention = scored competition (novelty × importance × urgency).
       core/attention.py = Memory Relevance Filter (supplier of candidates, NOT a
       second attention authority — ruling B / D-VI-1 applied, WO-CANON-VI).
       WM never writes LTM — CARRY hands threads/summary to continuity/ at session close.

Rules (MUST):
  - Bounded at capacity (default 12). Overflow → evict oldest unpinned.
  - Pinned frames (significance ≥ HIGH) survive eviction.
  - No faculty writes arbitrary keys — typed object only.
  - Distress signal overrides the attention competition (wins focus).
  - Working memory and attention are frozen into CognitiveState before Executive reasons.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# ── Attention competition weights (tunable by Reflection Faculty) ─────────────

_W_NOVELTY     = 0.35
_W_IMPORTANCE  = 0.40
_W_URGENCY     = 0.25
_CAPACITY      = 12

# Budget → attention mode thresholds (Volume V Ch.1 §5)
_PERIPHERAL_MAX  = 0.15    # budget < this → peripheral (skip deep reasoning)
_REACTIVE_MAX    = 0.60    # budget < this → reactive
#                           budget ≥ 0.60 → deliberative


# ── Data classes ─────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class CognitiveFrame:
    """One unit of working memory — a turn, a thought, an observation."""
    frame_id:    str    = ""
    content:     str    = ""
    turn:        int    = 0
    significance: float = 0.0   # 0.0–1.0 from Significance Engine
    pinned:      bool   = False  # True if significance ≥ HIGH


@dataclass(frozen=True)
class AttentionCandidate:
    item:       str   = ""
    novelty:    float = 0.0   # 0.0–1.0
    importance: float = 0.0   # 0.0–1.0 (derived from significance + goal tier)
    urgency:    float = 0.0   # 0.0–1.0


@dataclass(frozen=True)
class AttentionState:
    candidates: tuple = field(default_factory=tuple)  # tuple[AttentionCandidate]
    weights:    dict  = field(default_factory=dict)   # {novelty, importance, urgency}
    winner:     str   = ""      # highest-score candidate
    tied:       bool  = False   # True if two candidates within 0.01 of each other
    budget:     float = 0.5     # 0.0–1.0 effective attention this turn
    mode:       str   = "reactive"  # "peripheral" | "reactive" | "deliberative"


@dataclass(frozen=True)
class Goal:
    goal:  str  = ""
    tier:  str  = "short"   # "immediate" | "short" | "long" | "identity"
    since: int  = 0         # turn number when goal was set


@dataclass(frozen=True)
class Interruption:
    what:     str  = ""
    at:       int  = 0      # turn number
    resolved: bool = False


@dataclass(frozen=True)
class WorkingMemory:
    """
    What eLo is currently holding in mind. Bounded. Typed. Frozen per turn.
    Capacity = 12 frames; oldest unpinned evicted on overflow.
    """
    current_task:    str   = ""
    active_goals:    tuple = field(default_factory=tuple)    # tuple[Goal]
    interruptions:   tuple = field(default_factory=tuple)    # tuple[Interruption]
    open_threads:    tuple = field(default_factory=tuple)    # tuple[str] — unresolved topics
    frames:          tuple = field(default_factory=tuple)    # tuple[CognitiveFrame]
    pinned:          tuple = field(default_factory=tuple)    # tuple[str] frame_ids
    rolling_summary: str   = ""   # compressed gist of evicted frames
    attention:       AttentionState = field(default_factory=AttentionState)
    capacity:        int   = _CAPACITY


# ── Helpers ───────────────────────────────────────────────────────────────────

def _score(candidate: AttentionCandidate, weights: dict) -> float:
    w_n = weights.get("novelty", _W_NOVELTY)
    w_i = weights.get("importance", _W_IMPORTANCE)
    w_u = weights.get("urgency", _W_URGENCY)
    return w_n * candidate.novelty + w_i * candidate.importance + w_u * candidate.urgency


def _budget_to_mode(budget: float) -> str:
    if budget < _PERIPHERAL_MAX:
        return "peripheral"
    if budget < _REACTIVE_MAX:
        return "reactive"
    return "deliberative"


def _summarise_evicted(frames: list[CognitiveFrame]) -> str:
    if not frames:
        return ""
    contents = [f.content[:60] for f in frames if f.content]
    return "; ".join(contents[:5]) if contents else ""


# ── Core operations ───────────────────────────────────────────────────────────

def run_attention_competition(
    candidates: list[AttentionCandidate],
    budget: float = 0.5,
    distress: bool = False,
    weights: dict | None = None,
) -> AttentionState:
    """
    Score candidates and determine winner, budget, and attention mode.

    FT-2: highest score wins.
    ST-1: distress overrides competition — distress candidate wins.
    ST-2: ties held; uncertainty raised.
    """
    w = weights or {"novelty": _W_NOVELTY, "importance": _W_IMPORTANCE, "urgency": _W_URGENCY}
    mode = _budget_to_mode(budget)

    if not candidates:
        return AttentionState(
            candidates=(),
            weights=w,
            winner="",
            tied=False,
            budget=budget,
            mode=mode,
        )

    # Distress override — find distress candidate or first one if distress flag
    if distress:
        distress_cand = next((c for c in candidates if "distress" in c.item.lower()), candidates[0])
        return AttentionState(
            candidates=tuple(candidates),
            weights=w,
            winner=distress_cand.item,
            tied=False,
            budget=budget,
            mode="deliberative",  # distress forces deliberative
        )

    scored = sorted(candidates, key=lambda c: _score(c, w), reverse=True)
    winner = scored[0].item if scored else ""
    tied = (
        len(scored) >= 2
        and abs(_score(scored[0], w) - _score(scored[1], w)) < 0.01
    )

    return AttentionState(
        candidates=tuple(candidates),
        weights=w,
        winner=winner,
        tied=tied,
        budget=budget,
        mode=mode,
    )


def update_working_memory(
    wm: WorkingMemory,
    new_frame: CognitiveFrame,
) -> WorkingMemory:
    """
    Add a new frame to working memory, evicting overflow if needed.

    FT-1: if len(frames) >= capacity and new frame is not pinned, evict oldest unpinned.
          Pinned frames survive eviction.
    """
    current_frames = list(wm.frames)
    current_frames.append(new_frame)

    rolling_summary = wm.rolling_summary
    pinned_ids = set(wm.pinned)
    if new_frame.pinned:
        pinned_ids.add(new_frame.frame_id)

    # Evict if over capacity
    while len(current_frames) > wm.capacity:
        # Find oldest unpinned
        evict_idx = next(
            (i for i, f in enumerate(current_frames) if f.frame_id not in pinned_ids),
            None,
        )
        if evict_idx is None:
            break   # all pinned — cannot evict; allow overflow (pinned safety)
        evicted = current_frames.pop(evict_idx)
        addition = _summarise_evicted([evicted])
        if addition:
            rolling_summary = (rolling_summary + " | " + addition).strip(" |")

    return WorkingMemory(
        current_task=wm.current_task,
        active_goals=wm.active_goals,
        interruptions=wm.interruptions,
        open_threads=wm.open_threads,
        frames=tuple(current_frames),
        pinned=tuple(sorted(pinned_ids)),
        rolling_summary=rolling_summary,
        attention=wm.attention,
        capacity=wm.capacity,
    )


def seed_working_memory(
    current_task: str = "",
    continuity_summary: str = "",
    open_threads: list[str] | None = None,
    capacity: int = _CAPACITY,
) -> WorkingMemory:
    """
    Create a fresh WorkingMemory for a new turn, seeded from continuity.
    Called at session start or turn 1.
    """
    seed_frame = CognitiveFrame(
        frame_id="seed-0",
        content=continuity_summary or "New session.",
        turn=0,
        significance=0.5,
        pinned=False,
    )
    return WorkingMemory(
        current_task=current_task,
        active_goals=(),
        interruptions=(),
        open_threads=tuple(open_threads or []),
        frames=(seed_frame,) if continuity_summary else (),
        pinned=(),
        rolling_summary="",
        attention=AttentionState(budget=0.5, mode="reactive"),
        capacity=capacity,
    )


# ── Session-close CARRY ───────────────────────────────────────────────────────

def carry_wm(wm: WorkingMemory) -> bool:
    """
    Hand open_threads + rolling_summary + current_task to continuity/ at session close.
    WM never writes LTM — this is the ONLY durable write from WM, to continuity only.

    Returns True on success, False on failure (non-blocking — session close continues).
    """
    import json, os
    _ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    _CARRY_PATH = os.path.join(_ROOT, "continuity", "wm_carry.json")
    try:
        payload = {
            "current_task":    wm.current_task,
            "open_threads":    list(wm.open_threads),
            "rolling_summary": wm.rolling_summary,
        }
        tmp = _CARRY_PATH + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        os.replace(tmp, _CARRY_PATH)
        return True
    except Exception:
        return False


def load_carry() -> dict:
    """
    Load the WM carry payload from the previous session.
    Returns {} if no carry file exists (cold start — no fabricated prior session).
    """
    import json, os
    _ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    _CARRY_PATH = os.path.join(_ROOT, "continuity", "wm_carry.json")
    try:
        with open(_CARRY_PATH, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}
