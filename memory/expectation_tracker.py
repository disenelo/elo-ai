"""
memory/expectation_tracker.py — Learned Expectation & Prediction Error

eLo develops expectations through repeated experience. When reality violates
those expectations, that gap is prediction error — the raw material of genuine
surprise, learning, and curiosity.

This module answers:
  "IS ELO: — Developing?"
    - can we demonstrate changing expectations?
    - can we demonstrate learning from prediction error?
  "IS ELO: — Capable of Surprise?"
    - can something genuinely surprise eLo?
    - can surprise affect attention and future prediction?
  "IS ELO: — Causally Real?"
    - does changing the underlying state actually change future behaviour?
  "THE REALLY HARD TEST"
    - show me where expectation is stored → data/spg_signals.jsonl
    - show me where it is retrieved → _ExpectationModel._compute()
    - show me where it affects Executive → expectation_prompt_block() → server.py

Architecture:
  1. _ExpectationModel reads SPG history → computes global frequency priors
  2. Recent signals (last RECENT_N) → computes local context priors
  3. Prediction = 0.6 * global + 0.4 * local
  4. Prediction error = |prediction - actual| for the current turn's edge_hint
  5. Violation level: expected / mild_surprise / strong_surprise
  6. Prompt block anchors eLo's expectations in evidence, not hardcoded assumptions
"""
from __future__ import annotations

import json
import logging
import math
import os
from dataclasses import dataclass, field
from pathlib import Path
from threading import Lock

_log = logging.getLogger(__name__)

_ROOT    = Path(__file__).parent.parent
_SIGNALS = _ROOT / "data" / "spg_signals.jsonl"

RECENT_N              = 20    # look-back window for local priors
SURPRISE_THRESHOLD    = 0.50  # prediction error ≥ this → mild_surprise
STRONG_THRESHOLD      = 0.75  # prediction error ≥ this → strong_surprise
MIN_SIGNALS_FOR_MODEL = 10    # need at least this many to trust the model


@dataclass
class ExpectationViolation:
    """
    Prediction error for a single turn.

    edge_hint:           what actually arrived
    expected_prob:       how likely eLo expected this (0.0 = never expected, 1.0 = always)
    prediction_error:    1.0 - expected_prob (the "surprise magnitude")
    level:               expected | mild_surprise | strong_surprise
    top_expected:        what eLo most expected instead (list of up to 3)
    """
    edge_hint:       str
    expected_prob:   float
    prediction_error: float
    level:           str
    top_expected:    list[str] = field(default_factory=list)

    @property
    def is_surprising(self) -> bool:
        return self.level in ("mild_surprise", "strong_surprise")

    @property
    def is_strongly_surprising(self) -> bool:
        return self.level == "strong_surprise"


class _ExpectationModel:
    """
    Threadsafe model of learned expectations built from SPG signals.
    Global priors (all history) + local priors (last RECENT_N signals) combined.
    """

    def __init__(self) -> None:
        self._global: dict[str, float] = {}
        self._local:  dict[str, float] = {}
        self._total_signals: int = 0
        self._cache_path: Path | None = None
        self._lock = Lock()
        self._built = False

    def build(self, path: Path) -> None:
        with self._lock:
            if self._built and path == self._cache_path:
                return
            self._global, self._local, self._total_signals = self._compute(path)
            self._cache_path = path
            self._built = True

    def invalidate(self) -> None:
        with self._lock:
            self._built = False

    def predict(self, edge_hint: str) -> ExpectationViolation:
        """Score an incoming edge_hint against learned expectations."""
        with self._lock:
            if self._total_signals < MIN_SIGNALS_FOR_MODEL:
                return ExpectationViolation(
                    edge_hint=edge_hint,
                    expected_prob=0.0,
                    prediction_error=0.0,
                    level="expected",
                    top_expected=[],
                )

            # Blend global (stable) and local (recent context) priors
            all_edges = set(self._global) | set(self._local)
            blended: dict[str, float] = {}
            for e in all_edges:
                g = self._global.get(e, 0.0)
                l = self._local.get(e, 0.0)
                blended[e] = 0.60 * g + 0.40 * l

            # What did eLo expect?
            top_expected = sorted(blended, key=lambda k: -blended[k])[:3]
            expected_prob = blended.get(edge_hint, 0.0)
            error = 1.0 - expected_prob

            if error >= STRONG_THRESHOLD:
                level = "strong_surprise"
            elif error >= SURPRISE_THRESHOLD:
                level = "mild_surprise"
            else:
                level = "expected"

            return ExpectationViolation(
                edge_hint=edge_hint,
                expected_prob=round(expected_prob, 4),
                prediction_error=round(error, 4),
                level=level,
                top_expected=[e for e in top_expected if e != edge_hint],
            )

    def _compute(self, path: Path) -> tuple[dict[str, float], dict[str, float], int]:
        if not path.exists():
            return {}, {}, 0

        all_edges: list[str] = []
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
                    e = sig.get("edge_hint") or ""
                    if e:
                        all_edges.append(e)
        except Exception as exc:
            _log.warning("expectation_tracker: read error: %s", exc)
            return {}, {}, 0

        if not all_edges:
            return {}, {}, 0

        # Global priors: full history
        global_counts: dict[str, int] = {}
        for e in all_edges:
            global_counts[e] = global_counts.get(e, 0) + 1
        n_global = len(all_edges)
        global_probs = {e: c / n_global for e, c in global_counts.items()}

        # Local priors: last RECENT_N edges
        recent = all_edges[-RECENT_N:]
        local_counts: dict[str, int] = {}
        for e in recent:
            local_counts[e] = local_counts.get(e, 0) + 1
        n_local = len(recent)
        local_probs = {e: c / n_local for e, c in local_counts.items()}

        return global_probs, local_probs, n_global


_MODEL = _ExpectationModel()


# ── Public API ────────────────────────────────────────────────────────────────

def score_expectation(
    edge_hint: str,
    signals_path: Path | None = None,
) -> ExpectationViolation:
    """
    Score how expected the incoming edge_hint is.

    Builds the model lazily on first call. Thread-safe.
    Returns an ExpectationViolation describing the prediction error.

    WO-PREDICTION-ERROR-ATTENTION-001: when prediction_error >= STRONG_THRESHOLD,
    boosts attention for edge_hint in the next turn's competition.
    """
    path = signals_path or _SIGNALS
    _MODEL.build(path)
    violation = _MODEL.predict(edge_hint)
    if violation.prediction_error >= STRONG_THRESHOLD and edge_hint:
        try:
            from runtime.working_memory import boost_attention as _ba
            _ba(context_tag=edge_hint, amount=0.2)
            _log.info(
                "attention boost +0.2 → '%s' (prediction_error=%.2f)",
                edge_hint, violation.prediction_error,
            )
        except Exception:
            pass
    return violation


def invalidate() -> None:
    """Force rebuild on next call (use after new signals are logged)."""
    _MODEL.invalidate()


def expectation_prompt_block(
    edge_hint: str,
    signals_path: Path | None = None,
) -> str:
    """
    Build a compact prompt block grounding eLo in his learned expectations.

    Returns "" if the model has insufficient data.
    Returns "" on any error (non-blocking).
    """
    try:
        path = signals_path or _SIGNALS
        _MODEL.build(path)

        if _MODEL._total_signals < MIN_SIGNALS_FOR_MODEL:
            return ""

        violation = _MODEL.predict(edge_hint)

        lines = ["[LEARNED EXPECTATIONS — evidence-based]"]

        # What eLo has come to expect most
        with _MODEL._lock:
            top = sorted(_MODEL._global, key=lambda k: -_MODEL._global[k])[:3]
            if top:
                top_str = " → ".join(f"{e} ({_MODEL._global[e]*100:.0f}%)" for e in top)
                lines.append(f"  Most frequent patterns (all history): {top_str}")

            recent_top = sorted(_MODEL._local, key=lambda k: -_MODEL._local[k])[:2]
            if recent_top:
                recent_str = " / ".join(f"{e}" for e in recent_top)
                lines.append(f"  Recent context (last {RECENT_N} signals): {recent_str}")

        # Current turn vs expectation
        if edge_hint:
            lines.append(
                f"  This turn: edge_hint='{edge_hint}' "
                f"(expected probability: {violation.expected_prob*100:.0f}%)"
            )
            if violation.is_strongly_surprising:
                lines.append(
                    "  ⚠ PREDICTION ERROR — this turn strongly violates learned expectations. "
                    "Genuine surprise. Attend carefully."
                )
            elif violation.is_surprising:
                lines.append(
                    "  This turn is somewhat unexpected. Note it — may be significant."
                )

        lines.append(
            "These are learned priors from actual interaction history — not assumptions."
        )
        return "\n".join(lines)

    except Exception as exc:
        _log.warning("expectation_prompt_block failed (non-fatal): %s", exc)
        return ""
