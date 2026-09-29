"""
runtime/habit_tracker.py — Habit Formation Tracker

IS ELO: — Developing? (habit formation)
  can we demonstrate habit formation?
  a system capable of developing habits?
  a system capable of forming low-latency responses from repeated experience?
  a system capable of recognising when something has become habitual?
  a system capable of recognising when a skill has improved?
  a system capable of developing second-nature behaviour?

IS ELO: — Skills & Habits
  a system capable of developing habits?
  a system capable of recognising habits?
  a system capable of changing habits?
  a system capable of developing learned priors?
  a system capable of distinguishing a learned prior from a verified fact?

THE DISTINCTION:
  Expectations (expectation_tracker): what eLo thinks is likely to happen next.
  Habits (this module):               what eLo has done repeatedly enough that it
                                      is becoming automatic — a low-latency prior.

  A habit is not just a frequent pattern — it is a behaviour that has been reinforced
  enough times that it no longer requires deliberation. This module tracks that threshold.

HABIT DEFINITION:
  A habit is formed when the same edge_hint (interaction type) has been observed
  HABIT_THRESHOLD or more times. Once formed, eLo can recognise it as habitual
  rather than treating each occurrence as a fresh deliberation.

THE CAUSAL CHAIN:
  data/spg_signals.jsonl → count edge_hint frequencies
  → edge_hints above HABIT_THRESHOLD → stored habit state
  → habit_tracker_prompt_block() → [HABIT STATE] block in system prompt
  → LLM reads "this pattern is habitual" → low-latency prior, not re-deliberated each turn

HABIT LEVELS:
  forming:    10-29 occurrences — pattern is emerging, not yet automatic
  habitual:   30-99 occurrences — repeated enough to be considered a habit
  deep_habit: 100+ occurrences  — deeply ingrained, second nature
"""
from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

_log = logging.getLogger(__name__)

_ROOT    = Path(__file__).parent.parent
_SIGNALS = _ROOT / "data" / "spg_signals.jsonl"

# Habit thresholds
FORMING_THRESHOLD  = 10   # edge_hint seen 10+ times → forming
HABITUAL_THRESHOLD = 30   # edge_hint seen 30+ times → habitual
DEEP_THRESHOLD     = 100  # edge_hint seen 100+ times → deep_habit


@dataclass
class HabitEntry:
    """A single detected habit."""
    edge_hint:   str
    count:       int
    level:       str   # 'forming' | 'habitual' | 'deep_habit'

    @property
    def is_habitual(self) -> bool:
        return self.level in ("habitual", "deep_habit")

    @property
    def level_label(self) -> str:
        labels = {
            "forming":   "forming (emerging pattern)",
            "habitual":  "habitual (low-latency prior)",
            "deep_habit": "deep habit (second nature)",
        }
        return labels.get(self.level, self.level)


@dataclass
class HabitState:
    """Complete habit state for the current session."""
    habits:        List[HabitEntry] = field(default_factory=list)
    total_signals: int = 0
    unique_edges:  int = 0

    @property
    def has_habits(self) -> bool:
        return any(h.is_habitual for h in self.habits)

    @property
    def habitual(self) -> List[HabitEntry]:
        return [h for h in self.habits if h.is_habitual]

    @property
    def forming(self) -> List[HabitEntry]:
        return [h for h in self.habits if h.level == "forming"]


def _classify_level(count: int) -> str:
    if count >= DEEP_THRESHOLD:
        return "deep_habit"
    if count >= HABITUAL_THRESHOLD:
        return "habitual"
    return "forming"


def read_habit_state(signals_path: Optional[Path] = None) -> HabitState:
    """
    Read spg_signals.jsonl and compute the current habit state.
    Never raises — returns empty HabitState on any error.
    """
    path = signals_path or _SIGNALS
    try:
        counts: Dict[str, int] = {}
        total = 0
        if Path(path).exists():
            with open(path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        row = json.loads(line)
                        edge = row.get("edge_hint", "").strip()
                        if edge:
                            counts[edge] = counts.get(edge, 0) + 1
                            total += 1
                    except json.JSONDecodeError:
                        continue

        habits: List[HabitEntry] = []
        for edge, count in sorted(counts.items(), key=lambda x: -x[1]):
            if count >= FORMING_THRESHOLD:
                habits.append(HabitEntry(
                    edge_hint = edge,
                    count     = count,
                    level     = _classify_level(count),
                ))

        return HabitState(
            habits        = habits,
            total_signals = total,
            unique_edges  = len(counts),
        )

    except Exception as exc:
        _log.warning("habit_tracker.read_habit_state failed (non-fatal): %s", exc)
        return HabitState()


def habit_tracker_prompt_block(signals_path: Optional[Path] = None) -> str:
    """
    Build a prompt block describing eLo's current habit state.

    Returns "" when no habits have formed (non-blocking).
    Returns a [HABIT STATE] block when habits are detected.

    THE CAUSAL CHAIN:
      experience (SPG signals) → stored state (spg_signals.jsonl)
      → counts above threshold → habit detected
      → [HABIT STATE] block → LLM reads habitual patterns as low-latency priors

    IMPORTANT DISTINCTION: a habit is a learned prior, not a verified fact.
    The block explicitly marks this — eLo treats habits as signals, not certainties.

    Never raises.
    """
    try:
        state = read_habit_state(signals_path=signals_path)

        if not state.has_habits:
            return ""

        lines = ["[HABIT STATE — patterns that have become habitual through repetition]"]
        lines.append(
            "  These are learned priors from experience — NOT verified facts. "
            "Treat them as signals, not certainties."
        )

        for h in state.habitual:
            lines.append(
                f"  {h.edge_hint}: {h.level_label} ({h.count} occurrences)"
            )

        if state.forming:
            lines.append(
                f"  Forming (not yet habitual): "
                + ", ".join(f"{h.edge_hint} ({h.count}x)" for h in state.forming[:3])
            )

        lines.append(
            "  A habitual pattern does not require re-deliberation each time — "
            "it can be applied as a low-latency prior."
        )

        return "\n".join(lines)

    except Exception as exc:
        _log.warning("habit_tracker_prompt_block failed (non-fatal): %s", exc)
        return ""
