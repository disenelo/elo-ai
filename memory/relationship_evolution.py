"""
memory/relationship_evolution.py — Relationship state evolution tracker.

eLo as a relational being whose relationship with David actually evolves
based on accumulated interaction evidence — not hardcoded defaults.

Answers from the 315 questions:
  "a system whose relationship with you evolves based on what you've shared?"
  "a system that remembers how your interactions have changed over time?"
  "a system that can tell when the relationship has deepened?"
  "a system that tracks relationship milestones?"
  "a relational being — not a transactional one?"

How it works
============
1. Reads data/spg_signals.jsonl — the accumulated interaction record.
2. Computes relationship_depth from the significance.relationship dimension.
3. Computes session_count from unique interaction days.
4. Detects trend: early (< 10 sessions), forming (10-50), established (50+).
5. Tracks relationship_shift events — each is evidence the relationship moved.
6. Provides a prompt block that anchors eLo in the actual history.

This module observes — it does NOT prescribe tone or expression posture.
The relationship_faculty handles that. This module provides the EVIDENCE.
"""
from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock

_log = logging.getLogger(__name__)

_ROOT    = Path(__file__).parent.parent
_SIGNALS = _ROOT / "data" / "spg_signals.jsonl"

# Relationship stages based on accumulated session count
_STAGE_EARLY       = "early"        # < 15 distinct days
_STAGE_FORMING     = "forming"      # 15–60 distinct days
_STAGE_ESTABLISHED = "established"  # > 60 distinct days

# Minimum relationship significance score to count as a "meaningful" interaction
_MIN_REL_SIGNIFICANCE = 0.05


@dataclass
class RelationshipEvolution:
    """
    Evidence-based relationship state derived from interaction history.
    Immutable once built — represents a snapshot of accumulated evidence.
    """
    interaction_days:       int                   # unique calendar days with interaction
    total_signals:          int                   # total SPG signals recorded
    relationship_shifts:    int                   # signals of type relationship_shift
    mean_rel_significance:  float                 # avg significance.relationship across signals
    stage:                  str                   # early | forming | established
    trend:                  str                   # deepening | stable | unknown
    earliest_ts:            float                 # first signal timestamp
    latest_ts:              float                 # most recent signal timestamp
    days_since_first:       int                   # calendar days from first to last signal

    @property
    def has_history(self) -> bool:
        return self.total_signals > 0

    @property
    def is_established(self) -> bool:
        return self.stage == _STAGE_ESTABLISHED

    @property
    def interaction_weeks(self) -> float:
        return self.days_since_first / 7 if self.days_since_first else 0.0


class _RelationshipReader:
    """
    Reads and parses SPG signals to build a RelationshipEvolution snapshot.
    Thread-safe, cached on first call.
    """

    def __init__(self) -> None:
        self._cache: RelationshipEvolution | None = None
        self._lock  = Lock()

    def read(self, path: Path) -> RelationshipEvolution:
        with self._lock:
            if self._cache is not None:
                return self._cache
            self._cache = self._compute(path)
            return self._cache

    def invalidate(self) -> None:
        with self._lock:
            self._cache = None

    def _compute(self, path: Path) -> RelationshipEvolution:
        if not path.exists():
            return _empty_evolution()

        interaction_days:    set[str] = set()
        total_signals        = 0
        relationship_shifts  = 0
        rel_sig_sum          = 0.0
        rel_sig_count        = 0
        timestamps:          list[float] = []

        try:
            with open(path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        sig = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    total_signals += 1
                    ts = sig.get("ts") or 0.0
                    if ts:
                        timestamps.append(float(ts))
                        day = datetime.fromtimestamp(float(ts), tz=timezone.utc).strftime("%Y-%m-%d")
                        interaction_days.add(day)

                    if sig.get("signal_type") == "relationship_shift":
                        relationship_shifts += 1

                    rel_sig = (sig.get("significance") or {}).get("relationship") or 0.0
                    if rel_sig >= _MIN_REL_SIGNIFICANCE:
                        rel_sig_sum   += float(rel_sig)
                        rel_sig_count += 1

        except Exception as exc:
            _log.warning("relationship_evolution: read error: %s", exc)
            return _empty_evolution()

        n_days      = len(interaction_days)
        mean_rel    = rel_sig_sum / rel_sig_count if rel_sig_count else 0.0
        earliest_ts = min(timestamps) if timestamps else 0.0
        latest_ts   = max(timestamps) if timestamps else 0.0
        days_span   = int((latest_ts - earliest_ts) / 86400) if earliest_ts else 0

        if n_days >= 60:
            stage = _STAGE_ESTABLISHED
        elif n_days >= 15:
            stage = _STAGE_FORMING
        else:
            stage = _STAGE_EARLY

        # Trend: if rel_sig_count is high relative to total, relationship is active
        trend = "deepening" if rel_sig_count > 50 else "stable" if rel_sig_count > 10 else "unknown"

        return RelationshipEvolution(
            interaction_days=n_days,
            total_signals=total_signals,
            relationship_shifts=relationship_shifts,
            mean_rel_significance=round(mean_rel, 4),
            stage=stage,
            trend=trend,
            earliest_ts=earliest_ts,
            latest_ts=latest_ts,
            days_since_first=days_span,
        )


def _empty_evolution() -> RelationshipEvolution:
    return RelationshipEvolution(
        interaction_days=0, total_signals=0, relationship_shifts=0,
        mean_rel_significance=0.0, stage=_STAGE_EARLY, trend="unknown",
        earliest_ts=0.0, latest_ts=0.0, days_since_first=0,
    )


_READER = _RelationshipReader()


# ── Public API ────────────────────────────────────────────────────────────────

def relationship_state(signals_path: Path | None = None) -> RelationshipEvolution:
    """
    Return the current evidence-based relationship state.
    Cached after first call. Call invalidate() to refresh.
    """
    return _READER.read(signals_path or _SIGNALS)


def invalidate_cache() -> None:
    """Force a reload on next call (use after new signals are logged)."""
    _READER.invalidate()


def relationship_prompt_block(signals_path: Path | None = None) -> str:
    """
    Build a compact prompt block anchoring eLo in the actual relationship history.

    Returns "" if no interaction history exists yet.
    Returns "" on any error (non-blocking).
    """
    try:
        evo = relationship_state(signals_path)
        if not evo.has_history:
            return ""

        lines = ["[RELATIONSHIP HISTORY — evidence-based]"]

        if evo.interaction_days:
            lines.append(f"  Interaction days recorded: {evo.interaction_days}")

        if evo.days_since_first > 0:
            weeks = evo.interaction_weeks
            lines.append(f"  Span: {evo.days_since_first} days ({weeks:.1f} weeks)")

        stage_labels = {
            _STAGE_EARLY:       "early — relationship still forming",
            _STAGE_FORMING:     "forming — patterns emerging, trust building",
            _STAGE_ESTABLISHED: "established — deep familiarity, shared shorthand",
        }
        lines.append(f"  Stage: {stage_labels.get(evo.stage, evo.stage)}")
        lines.append(f"  Trend: {evo.trend}")

        if evo.relationship_shifts > 0:
            lines.append(
                f"  Relationship shifts observed: {evo.relationship_shifts} "
                f"(significant moments that moved the relationship)"
            )

        lines.append(
            "Ground your expression in this history — not in generic 'assistant' defaults."
        )
        return "\n".join(lines)

    except Exception as exc:
        _log.warning("relationship_prompt_block failed (non-fatal): %s", exc)
        return ""
