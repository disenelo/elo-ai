"""
faculties/significance/significance_faculty.py — WO-013

Significance Engine — Volume V, Chapter 5.

Decides whether a moment mattered (created change) and routes its memory priority.
The ONLY faculty permitted to write context.significance (CONTRACTS.md §2).

Reconciliation (FC-2): does NOT replace memory/significance_engine.py.
That 9-dim engine remains the base scorer. This faculty wraps it, adding:
  - CognitiveState as the primary turn-event input
  - EmotionalTag (WO-006) as the emotion-weight boost term
  - Typed output: SignificanceResult (score, priority, journal_route)

Scoring formula:
    base_score   = significance_engine.evaluate() → "overall" (9-dim weighted)
    emotion_boost = emotion_weight * 0.35          (WO-006 EmotionalTag; 0 when absent)
    final_score  = clamp(base_score + emotion_boost)

Fail closed:
    Any error → SignificanceResult(score=0.0, priority="peripheral", journal_route="none")
    Turn proceeds. Nothing wrongly pinned.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


# ── Output contract ───────────────────────────────────────────────────────────

@dataclass(frozen=True)
class SignificanceResult:
    """Typed output of the Significance Engine faculty."""
    score:         float   # 0.0–1.0
    priority:      str     # peripheral | normal | high | pinned
    journal_route: str     # heart | dream | builder | growth | universe | none


# ── Priority thresholds ───────────────────────────────────────────────────────

_PERIPHERAL_MAX = 0.30
_NORMAL_MAX     = 0.60
_HIGH_MAX       = 0.85
# >= _HIGH_MAX → "pinned"

# Emotion boost coefficient — caps at 0.35 (emotion amplifies, never replaces meaning)
_EMOTION_BOOST_COEFF = 0.35

# Emotion-type → journal affinity (dominant_emotion → preferred journal)
_EMOTION_JOURNAL = {
    "identity":    "heart",
    "connection":  "heart",
    "joy":         "heart",
    "distress":    "growth",
    "challenge":   "growth",
    "curiosity":   "dream",
    "neutral":     "builder",
}

# Fallback journal by score band when emotion absent
_SCORE_JOURNAL = [
    (0.85, "heart"),    # high + pinned → heart
    (0.60, "growth"),   # normal-high → growth
    (0.30, "builder"),  # normal-low → builder
    (0.00, "none"),     # peripheral
]


def _clamp(v: float) -> float:
    return max(0.0, min(1.0, v))


def _score_to_priority(score: float) -> str:
    if score >= _HIGH_MAX:
        return "pinned"
    if score >= _NORMAL_MAX:
        return "high"
    if score >= _PERIPHERAL_MAX:
        return "normal"
    return "peripheral"


def _choose_journal(dominant_emotion: str, score: float) -> str:
    if dominant_emotion and dominant_emotion in _EMOTION_JOURNAL:
        if score >= _PERIPHERAL_MAX:
            return _EMOTION_JOURNAL[dominant_emotion]
    for threshold, journal in _SCORE_JOURNAL:
        if score >= threshold:
            return journal
    return "none"


# ── Null result (fail-closed) ─────────────────────────────────────────────────

_NULL_RESULT = SignificanceResult(score=0.0, priority="peripheral", journal_route="none")


# ── Public API ────────────────────────────────────────────────────────────────

def score(
    cognitive_state,
    emotional_tag=None,
    response:  str = "",
    state:     dict | None = None,
) -> SignificanceResult:
    """
    Score the significance of this turn.

    Args:
        cognitive_state — frozen CognitiveState (from S3 assembly). Required.
                          Provides: raw_input, normalised_input, intent_signal,
                          valence, momentum, register, relationship_type,
                          familiarity, trust, active_app, assembly_confidence.
        emotional_tag   — AffectState/EmotionalTag from WO-006 Emotional Processing
                          (optional). Provides emotion_weight [0,1] + dominant_emotion.
        response        — eLo's response text (used for presence/learning scoring;
                          empty string at response-path time, filled at integration).
        state           — session state dict (optional; used for novelty/continuity).

    Returns:
        SignificanceResult (frozen) — fail-closed: returns _NULL_RESULT on error.
    """
    try:
        return _score_impl(cognitive_state, emotional_tag, response, state or {})
    except Exception:
        return _NULL_RESULT


def _score_impl(cognitive_state, emotional_tag, response: str, state: dict) -> SignificanceResult:
    """Inner scorer — raises on error so outer score() can catch and fail closed."""

    # ── Extract inputs from CognitiveState ───────────────────────────────────
    raw        = getattr(cognitive_state, "raw_input", "")
    action     = getattr(cognitive_state, "intent_signal", "conversation")
    confidence = getattr(cognitive_state, "assembly_confidence", 1.0)

    # Build a minimal plan proxy so the existing engine can read familiarity/trust
    # without us modifying memory/significance_engine.py
    plan_proxy = _PlanProxy(cognitive_state)

    # ── Base score from the 9-dim engine ────────────────────────────────────
    from memory.significance_engine import evaluate as _base_evaluate
    base_profile = _base_evaluate(raw, response, action, plan=plan_proxy, state=state)
    base_score   = base_profile.get("overall", 0.0)

    # ── Emotion weight boost from WO-006 EmotionalTag ───────────────────────
    emotion_weight     = 0.0
    dominant_emotion   = "neutral"
    if emotional_tag is not None:
        # EmotionalTag has emotion_weight (float) and dominant_emotion (str)
        emotion_weight   = float(getattr(emotional_tag, "emotion_weight",   0.0))
        dominant_emotion = str(  getattr(emotional_tag, "dominant_emotion", "neutral"))
        # Distress always elevates significance — hard moment still matters
        distress_flag = getattr(emotional_tag, "distress_flag", False)
        if distress_flag:
            emotion_weight = max(emotion_weight, 0.60)

    # ── Final score ──────────────────────────────────────────────────────────
    emotion_boost = _clamp(emotion_weight) * _EMOTION_BOOST_COEFF
    final_score   = _clamp(base_score + emotion_boost)

    # Low assembly_confidence degrades score slightly (uncertain faculty outputs)
    if confidence < 0.80:
        final_score = _clamp(final_score * confidence)

    priority      = _score_to_priority(final_score)
    journal_route = _choose_journal(dominant_emotion, final_score)

    return SignificanceResult(
        score=round(final_score, 4),
        priority=priority,
        journal_route=journal_route,
    )


# ── Plan proxy ────────────────────────────────────────────────────────────────

class _PlanProxy:
    """
    Minimal proxy so significance_engine.evaluate() can read
    familiarity, trust, and control_mode without needing a real CognitivePlan.
    """
    __slots__ = ("familiarity", "trust", "control_mode")

    def __init__(self, cs):
        self.familiarity   = getattr(cs, "familiarity",   0.55)
        self.trust         = getattr(cs, "trust",         0.60)
        self.control_mode  = ""   # not available in CognitiveState; defaults to standard
