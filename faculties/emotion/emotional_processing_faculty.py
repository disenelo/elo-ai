"""
faculties/emotion/emotional_processing_faculty.py — WO-006

Emotional Processing Layer — Volume V, Chapter 4.

Computes AffectState from CognitiveState signals once per turn, before the
Executive decides. Emotion is information, not performance.

Contract:
  - Reads CognitiveState → returns AffectState (+ EmotionalTag for Ch.5).
  - Never produces text, voice, or animation.
  - Never writes identity, personality, or any shared state.
  - On any error: returns neutral AffectState; turn proceeds.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field

# ── Canonical emotion set (shared with Significance Engine, Ch.5) ────────────

DOMINANT_EMOTIONS = frozenset(
    {"joy", "curiosity", "challenge", "connection", "identity", "distress", "neutral"}
)

# ── Regulation thresholds ────────────────────────────────────────────────────

_SOFT_CAP_V   = 0.65   # |valence| at which regulation kicks in
_SOFT_CAP_A   = 0.70   # arousal at which regulation kicks in
_FLOOD_V      = 0.88   # |valence| at which flooded state triggers
_FLOOD_A      = 0.88   # arousal at which flooded state triggers

# ── Affect calculation weights ───────────────────────────────────────────────

_W_LEXICAL    = 0.45   # language (lexical/tonal) → valence
_W_RELATIONAL = 0.25   # relationship/register → valence
_W_SELFMODEL  = 0.30   # self-model mood delta → valence

_W_SALIENCE   = 0.40   # attention energy/salience → arousal
_W_NOVELTY    = 0.35   # attention novelty/momentum → arousal
_W_URGENCY    = 0.25   # urgency (distress, tension) → arousal

_DECAY_RATE   = 0.08   # arousal/valence pull toward baseline per turn

# ── Emotion-weight multipliers for the Significance Engine (Ch.5) ────────────
# identity + connection carry highest weight — they feed personality evolution.

_EMOTION_WEIGHT = {
    "identity":   1.00,
    "connection": 0.90,
    "distress":   0.85,
    "challenge":  0.70,
    "joy":        0.65,
    "curiosity":  0.60,
    "neutral":    0.30,
}


# ── Dataclasses ──────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class AffectState:
    """
    The Emotional Processing Layer's single product.
    Contributed to CognitiveState; read by the Executive and Significance Engine.
    """
    valence:           float = 0.0          # -1.0 … +1.0
    arousal:           float = 0.20         # 0.0 … 1.0
    dominant_emotion:  str   = "neutral"
    emotion_mix:       dict  = field(default_factory=dict)   # {emotion: weight}, sum ≤ 1.0
    regulation_state:  str   = "open"       # open | regulating | guarded | flooded
    affect_confidence: float = 1.0
    baseline_delta:    float = 0.0          # distance from eLo's resting affect
    distress_flag:     bool  = False        # True → Executive MUST route WITNESS/GROUND


@dataclass(frozen=True)
class EmotionalTag:
    """
    Advisory annotation for the Significance Engine (Ch.5).
    Rides on the turn envelope context; Ch.5 reads it as the Emotion Weight term.
    """
    valence:           float = 0.0
    intensity:         float = 0.0          # |valence| scaled by arousal
    dominant_emotion:  str   = "neutral"
    regulation_state:  str   = "open"
    emotion_weight:    float = 0.0          # pre-computed Ch.5 weight term [0,1]
    tag_ts:            float = 0.0


# ── Internal signal extractors ───────────────────────────────────────────────

def _lexical_valence(cs) -> float:
    """Map CognitiveState.valence string → float."""
    v = getattr(cs, "valence", "neutral") or "neutral"
    if "positive_high" in v: return  0.75
    if "positive"      in v: return  0.45
    if "negative_high" in v: return -0.75
    if "negative"      in v: return -0.45
    return 0.0


def _relational_valence(cs) -> float:
    """Derive relational valence from trust, familiarity, and register."""
    trust      = getattr(cs, "trust",       0.60)
    familiarity= getattr(cs, "familiarity", 0.55)
    register   = getattr(cs, "register",    "") or ""

    base = (trust - 0.5) * 0.6 + (familiarity - 0.5) * 0.4

    # Intimate register = positive relational signal (preserve South London context)
    if "SOUTH_LDN" in register or "PATOIS" in register or "HYBRID" in register:
        base += 0.10

    return max(-1.0, min(1.0, base))


def _selfmodel_signal(self_model_state) -> tuple[float, float]:
    """Return (valence_offset, resting_mood) from EloSelfModel. (0.0, 0.5) if absent."""
    if self_model_state is None:
        return 0.0, 0.5
    mood = getattr(self_model_state, "mood", 0.55)
    # mood 0-1; resting = 0.5; deviation → valence offset (scale × 1.4)
    return max(-1.0, min(1.0, (mood - 0.5) * 1.4)), mood


def _attention_arousal(cs) -> float:
    """Derive raw arousal from attention signals in CognitiveState."""
    emo_ctx = getattr(cs, "emotional_context", {}) or {}
    energy  = emo_ctx.get("energy",  "normal")
    tension = emo_ctx.get("tension", "normal")

    salience = 0.80 if energy == "high" else (0.20 if energy == "low" else 0.50)

    momentum = getattr(cs, "momentum", "stable") or "stable"
    novelty  = 0.70 if momentum == "building" else (0.30 if momentum == "declining" else 0.50)

    if getattr(cs, "distress_signal", False):
        urgency = 0.90
    elif tension == "high":
        urgency = 0.70
    elif tension == "low":
        urgency = 0.15
    else:
        urgency = 0.30

    return _W_SALIENCE * salience + _W_NOVELTY * novelty + _W_URGENCY * urgency


def _build_emotion_mix(valence: float, arousal: float, cs, sm) -> dict:
    """
    Build emotion distribution from evidence.
    Sum ≤ 1.0; contradiction (multiple emotions) is permitted.
    """
    scores: dict = {}

    # distress — distress_signal or extreme negative valence + elevated arousal
    if getattr(cs, "distress_signal", False) or (valence < -0.60 and arousal > 0.50):
        scores["distress"] = min(1.0, 0.50 + abs(valence) * 0.35 + arousal * 0.25)

    # joy — positive valence
    if valence > 0.15:
        scores["joy"] = min(1.0, valence * (0.55 + arousal * 0.30))

    # curiosity — open signals, building momentum, low-medium arousal
    emo_ctx = getattr(cs, "emotional_context", {}) or {}
    if emo_ctx.get("closure") == "open" or getattr(cs, "curiosity_signal", False):
        scores["curiosity"] = min(1.0, 0.45 + (1.0 - arousal) * 0.25)
    elif (getattr(cs, "momentum", "stable") or "stable") == "building":
        scores["curiosity"] = 0.30

    # challenge — moderate negative valence, below distress threshold
    if -0.65 < valence < -0.10 and "distress" not in scores:
        scores["challenge"] = abs(valence) * 0.65

    # connection — intimate register, social signals, high familiarity
    social   = getattr(cs, "social_signal", "") or ""
    register = getattr(cs, "register",      "") or ""
    if (social in ("greeting", "affirmation", "farewell")
            or "SOUTH_LDN" in register or "PATOIS" in register):
        scores["connection"] = min(1.0, 0.35 + getattr(cs, "familiarity", 0.55) * 0.30)

    # identity — identity/creative/imagination in inner_events or topic_signals
    inner  = (getattr(sm, "inner_events",  []) or []) if sm is not None else []
    topics = list(getattr(cs, "topic_signals", ()) or ())
    _id_words = {"identity", "creative", "imagination", "rebuild", "childhood", "who"}
    id_hits = sum(1 for e in inner + topics if any(w in str(e).lower() for w in _id_words))
    if id_hits > 0:
        # Weight by hit count — more identity signals → stronger score
        scores["identity"] = min(1.0, 0.55 + id_hits * 0.12)

    if not scores:
        scores["neutral"] = 1.0

    # Normalise so sum ≤ 1.0 (spec: contradiction allowed, total must not exceed 1.0)
    total = sum(scores.values())
    if total > 1.0:
        scores = {k: round(v / total, 4) for k, v in scores.items()}

    return scores


def _regulate(valence: float, arousal: float, trust: float) -> tuple[float, float, str]:
    """
    Apply regulation system.
    Returns (regulated_valence, regulated_arousal, regulation_state).
    """
    abs_v = abs(valence)

    if abs_v >= _FLOOD_V or arousal >= _FLOOD_A:
        state = "flooded"
    elif trust < 0.35 and valence < -0.15:
        state = "guarded"
    elif abs_v >= _SOFT_CAP_V or arousal >= _SOFT_CAP_A:
        state = "regulating"
    else:
        state = "open"

    # Hard clamp (MUST per spec §4.5 rule 2)
    valence = max(-1.0, min(1.0, valence))
    arousal = max(0.0,  min(1.0, arousal))

    # Damping toward eLo's resting baseline (0.0 / 0.2)
    if state == "flooded":
        valence = valence * 0.70
        arousal = arousal * 0.75 + 0.2 * 0.25
    elif state == "regulating":
        valence = valence * 0.82
        arousal = arousal * 0.85 + 0.2 * 0.15
    elif state == "guarded":
        arousal = arousal * 0.72

    return round(max(-1.0, min(1.0, valence)), 4), round(max(0.0, min(1.0, arousal)), 4), state


def _compute_weight(affect: AffectState) -> float:
    """Compute emotion_weight ∈ [0,1] for the Significance Engine (Ch.5)."""
    intensity = abs(affect.valence) * (0.5 + affect.arousal * 0.5)
    boost     = _EMOTION_WEIGHT.get(affect.dominant_emotion, 0.50)
    if affect.regulation_state == "flooded":
        boost *= 0.60
    elif affect.regulation_state == "guarded":
        boost *= 0.75
    return round(min(1.0, intensity * boost), 4)


# ── Public API ───────────────────────────────────────────────────────────────

def process_emotion(
    cognitive_state,
    self_model_state=None,
    prior_arousal: float = 0.20,
) -> tuple:
    """
    Compute (AffectState, EmotionalTag) from the current CognitiveState.

    Args:
        cognitive_state:    Frozen CognitiveState (or any object with the same fields).
        self_model_state:   EloSelfModel snapshot. None = degraded (confidence −0.15).
        prior_arousal:      Arousal from the previous turn for decay smoothing.

    Returns:
        (AffectState, EmotionalTag) — never raises; falls back to neutral on error.
    """
    try:
        return _compute(cognitive_state, self_model_state, prior_arousal)
    except Exception:
        neutral = AffectState()
        tag     = EmotionalTag(tag_ts=time.time())
        return neutral, tag


def compute_emotion_weight(affect_state: AffectState) -> float:
    """Return the emotion_weight term [0,1] for the Significance Engine (Ch.5)."""
    return _compute_weight(affect_state)


def decay_toward_baseline(affect_state: AffectState, steps: int = 1) -> AffectState:
    """
    Relax affect toward eLo's resting state (valence 0.0, arousal 0.2).

    Called between turns during quiet windows or used in integration tests.
    No permanent baseline shift — only integration (Ch.6/Ch.7) moves the baseline.
    """
    v = affect_state.valence
    a = affect_state.arousal
    for _ in range(steps):
        v = v + (0.0  - v) * _DECAY_RATE
        a = a + (0.20 - a) * _DECAY_RATE
    v = round(max(-1.0, min(1.0, v)), 4)
    a = round(max(0.0,  min(1.0, a)), 4)

    new_dominant = affect_state.dominant_emotion
    if abs(v) < 0.10 and new_dominant not in ("neutral",):
        new_dominant = "neutral"

    new_reg = affect_state.regulation_state
    if abs(v) < _SOFT_CAP_V and a < _SOFT_CAP_A:
        new_reg = "open"

    return AffectState(
        valence=v,
        arousal=a,
        dominant_emotion=new_dominant,
        emotion_mix=affect_state.emotion_mix,
        regulation_state=new_reg,
        affect_confidence=affect_state.affect_confidence,
        baseline_delta=round(v, 4),
        distress_flag=affect_state.distress_flag and abs(v) > 0.55,
    )


# ── Internal computation ─────────────────────────────────────────────────────

def _compute(cs, sm, prior_arousal: float) -> tuple:
    confidence = 1.0

    # 1. Valence sources
    lex_v  = _lexical_valence(cs)
    rel_v  = _relational_valence(cs)
    sm_v, _mood = _selfmodel_signal(sm)
    if sm is None:
        confidence -= 0.15

    raw_v = _W_LEXICAL * lex_v + _W_RELATIONAL * rel_v + _W_SELFMODEL * sm_v

    # Conflicting signal penalty: positive language but depleted self-model (or vice versa)
    if abs(lex_v - sm_v) > 0.45:
        confidence -= 0.10

    # 2. Arousal (with decay smoothing from prior turn)
    raw_a = _attention_arousal(cs)
    raw_a = raw_a * (1.0 - _DECAY_RATE) + prior_arousal * _DECAY_RATE

    # 3. Regulation
    trust = getattr(cs, "trust", 0.60)
    valence, arousal, reg_state = _regulate(raw_v, raw_a, trust)

    if reg_state == "flooded":
        confidence = max(0.60, confidence - 0.20)

    # 4. Emotion mix + dominant
    mix = _build_emotion_mix(valence, arousal, cs, sm)
    dominant = max(mix, key=mix.get) if mix else "neutral"

    # 5. Distress flag (spec §4.5 rule 4)
    distress = dominant == "distress" or getattr(cs, "distress_signal", False)
    if distress and reg_state == "open":
        reg_state = "regulating"

    # 6. Baseline delta (eLo's resting valence baseline = 0.0)
    baseline_delta = round(valence, 4)

    affect = AffectState(
        valence=valence,
        arousal=arousal,
        dominant_emotion=dominant,
        emotion_mix=mix,
        regulation_state=reg_state,
        affect_confidence=round(max(0.0, min(1.0, confidence)), 4),
        baseline_delta=baseline_delta,
        distress_flag=distress,
    )

    # 7. Emotional tag for Significance Engine
    intensity = abs(valence) * (0.5 + arousal * 0.5)
    tag = EmotionalTag(
        valence=affect.valence,
        intensity=round(intensity, 4),
        dominant_emotion=dominant,
        regulation_state=reg_state,
        emotion_weight=_compute_weight(affect),
        tag_ts=time.time(),
    )

    return affect, tag
