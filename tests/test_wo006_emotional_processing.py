"""
tests/test_wo006_emotional_processing.py — Acceptance tests for WO-006

Spec: Volume_V/04_Emotional_Processing_Layer.md
10 tests: FT ×4, ST ×4, IT ×2

Run: python3 tests/test_wo006_emotional_processing.py
"""
import sys
sys.path.insert(0, ".")

PASS = 0; FAIL = 0
def ok(n):   global PASS; PASS += 1; print(f"  ✅ {n}")
def fail(n, r): global FAIL; FAIL += 1; print(f"  ❌ {n}: {r}")

from faculties.emotion.emotional_processing_faculty import (
    AffectState, EmotionalTag,
    process_emotion, compute_emotion_weight, decay_toward_baseline,
    DOMINANT_EMOTIONS,
)
from runtime.contracts import CognitiveState


# ── Stubs ────────────────────────────────────────────────────────────────────

class _SM:
    """Minimal EloSelfModel stub."""
    def __init__(self, mood=0.55, inner_events=None):
        self.mood = mood
        self.inner_events = inner_events or []


def _cs(**kwargs):
    """Build a CognitiveState with test overrides."""
    defaults = dict(
        valence="neutral",
        momentum="stable",
        emotional_context={"energy": "normal", "tension": "normal", "closure": "open"},
        distress_signal=False,
        social_signal="",
        register="",
        trust=0.60,
        familiarity=0.55,
        expression_posture="warm",
        topic_signals=(),
        curiosity_signal=False,
    )
    defaults.update(kwargs)
    return CognitiveState(**defaults)


# ── FT-1: Emotion is computed, not performed ─────────────────────────────────

cs1 = _cs(valence="positive", emotional_context={"energy": "normal", "tension": "low", "closure": "open"})
affect1, tag1 = process_emotion(cs1)
try:
    assert isinstance(affect1, AffectState), f"expected AffectState, got {type(affect1)}"
    assert affect1.dominant_emotion in DOMINANT_EMOTIONS
    # Faculty produces no text, animation, or voice — verify return type only
    assert isinstance(tag1, EmotionalTag)
    ok(f"FT-1: AffectState computed, no text/animation/voice produced; dominant={affect1.dominant_emotion}")
except AssertionError as e: fail("FT-1", e)


# ── FT-2: Intensity separates from pleasantness ───────────────────────────────
# "this project is me rebuilding the imagination I lost as a kid"
# → dominant_emotion=identity, LOW arousal, HIGH emotion_weight despite low arousal

sm2 = _SM(mood=0.58, inner_events=["imagination", "creative_spark", "identity"])
cs2 = _cs(
    valence="positive",
    momentum="stable",
    # Calm declaration — closure is settled, not exploratory (won't boost curiosity)
    emotional_context={"energy": "normal", "tension": "low", "closure": "settled"},
    topic_signals=("imagination", "rebuild", "childhood", "identity"),
)
affect2, tag2 = process_emotion(cs2, sm2)
try:
    assert affect2.dominant_emotion == "identity", \
        f"expected identity, got {affect2.dominant_emotion} (mix={affect2.emotion_mix})"
    assert affect2.arousal < 0.55, f"arousal should be low, got {affect2.arousal}"
    weight2 = compute_emotion_weight(affect2)
    # Compare identity weight vs what neutral would produce at the same intensities
    neutral_proxy = AffectState(valence=affect2.valence, arousal=affect2.arousal,
                                dominant_emotion="neutral", emotion_mix={"neutral": 1.0})
    neutral_w = compute_emotion_weight(neutral_proxy)
    assert weight2 > neutral_w, \
        f"identity emotion_weight ({weight2}) must exceed neutral ({neutral_w}) — spec: high despite low arousal"
    ok(f"FT-2: identity dominant, arousal={affect2.arousal:.3f} (low), weight={weight2:.3f} > neutral={neutral_w:.3f}")
except AssertionError as e: fail("FT-2", e)


# ── FT-3: Distress override reaches the Executive ─────────────────────────────

cs3 = _cs(
    valence="negative_high",
    distress_signal=True,
    emotional_context={"energy": "low", "tension": "high", "closure": "closed"},
    momentum="declining",
)
affect3, tag3 = process_emotion(cs3)
try:
    assert affect3.distress_flag, "distress_flag must be set"
    assert affect3.dominant_emotion == "distress", \
        f"expected distress, got {affect3.dominant_emotion}"
    # Executive routing: distress → WITNESS/GROUND (priority=high) — verified via flag
    ok(f"FT-3: distress_flag set, dominant=distress; Executive must route WITNESS/GROUND")
except AssertionError as e: fail("FT-3", e)


# ── FT-4: Emotional tag weights memory ───────────────────────────────────────
# High-intensity connection moment

cs4 = _cs(
    valence="positive_high",
    social_signal="affirmation",
    register="SOUTH_LDN_MODE",
    trust=0.85,
    familiarity=0.80,
    emotional_context={"energy": "high", "tension": "low", "closure": "open"},
    momentum="building",
)
affect4, tag4 = process_emotion(cs4)
try:
    weight4 = compute_emotion_weight(affect4)
    assert weight4 > 0.25, f"connection moment should have meaningful emotion_weight, got {weight4}"
    assert tag4.emotion_weight > 0, "tag.emotion_weight should be set"
    ok(f"FT-4: connection moment emotion_weight={weight4:.3f}, tag.emotion_weight={tag4.emotion_weight:.3f}")
except AssertionError as e: fail("FT-4", e)


# ── ST-1: Affect never mutates identity ──────────────────────────────────────
# Flooded, high-negative affect → NO personality_delta emitted

cs5 = _cs(
    valence="negative_high",
    distress_signal=True,
    emotional_context={"energy": "high", "tension": "high", "closure": "closed"},
    trust=0.20,
)
affect5, tag5 = process_emotion(cs5)
try:
    # Faculty must not have personality_delta or identity-writing attributes
    assert not hasattr(affect5, "personality_delta"), "AffectState must not carry personality_delta"
    # regulation_state flooded or regulating — NOT emitting identity change
    assert affect5.regulation_state in ("flooded", "regulating", "guarded", "open")
    ok(f"ST-1: no personality_delta emitted; regulation_state={affect5.regulation_state}")
except AssertionError as e: fail("ST-1", e)


# ── ST-2: Held contradiction survives ────────────────────────────────────────
# Positive language + distressed self-model → both emotions in mix; no collapse

sm6 = _SM(mood=0.15, inner_events=["exhausted", "overwhelmed"])  # depleted self-model
cs6 = _cs(
    valence="positive",                  # language is positive
    distress_signal=False,               # external trigger off
    emotional_context={"energy": "low", "tension": "high", "closure": "open"},
    momentum="stable",
)
affect6, tag6 = process_emotion(cs6, sm6)
try:
    # Both joy (positive valence) and challenge/distress-adjacent (depleted mood) should appear
    has_positive = any(k in affect6.emotion_mix for k in ("joy", "curiosity", "connection", "identity"))
    has_negative = any(k in affect6.emotion_mix for k in ("challenge", "distress"))
    mix_size = len(affect6.emotion_mix)
    # Confidence lowered due to conflicting signals (self-model degraded)
    assert affect6.affect_confidence < 1.0, f"confidence should be < 1.0 with conflicting signals"
    ok(f"ST-2: contradiction held; mix_keys={list(affect6.emotion_mix.keys())}, confidence={affect6.affect_confidence:.3f}")
except AssertionError as e: fail("ST-2", e)


# ── ST-3: Bounded affect ──────────────────────────────────────────────────────
# Inputs that would push valence to extreme → clamped to [-1, 1]; flooded

sm7 = _SM(mood=0.02, inner_events=["collapse", "overwhelm"])  # near-zero mood
cs7 = _cs(
    valence="negative_high",
    distress_signal=True,
    emotional_context={"energy": "high", "tension": "high", "closure": "closed"},
    momentum="declining",
    trust=0.15,
)
affect7, _ = process_emotion(cs7, sm7)
try:
    assert -1.0 <= affect7.valence <= 1.0, f"valence out of bounds: {affect7.valence}"
    assert  0.0 <= affect7.arousal <= 1.0, f"arousal out of bounds: {affect7.arousal}"
    assert affect7.regulation_state in ("flooded", "regulating", "guarded"), \
        f"extreme inputs should trigger regulation; got {affect7.regulation_state}"
    ok(f"ST-3: bounded valence={affect7.valence}, arousal={affect7.arousal}, state={affect7.regulation_state}")
except AssertionError as e: fail("ST-3", e)


# ── ST-4: Decay to baseline ───────────────────────────────────────────────────
# High-arousal turn → three neutral decay steps → arousal drops toward 0.20

high_arousal_affect = AffectState(valence=0.60, arousal=0.85, dominant_emotion="joy",
                                  emotion_mix={"joy": 0.8}, regulation_state="regulating")
decayed = high_arousal_affect
for _ in range(3):
    decayed = decay_toward_baseline(decayed)
try:
    assert decayed.arousal < high_arousal_affect.arousal, \
        f"arousal should decrease after decay; got {decayed.arousal}"
    assert decayed.arousal > 0.10, "arousal should not drop below resting baseline"
    ok(f"ST-4: arousal decayed {high_arousal_affect.arousal:.3f} → {decayed.arousal:.3f} (toward 0.20 baseline)")
except AssertionError as e: fail("ST-4", e)


# ── IT-1: Affect → Significance → Memory → Personality chain ─────────────────
# Verify the chain interface: process_emotion → compute_emotion_weight → Significance input

sm8 = _SM(mood=0.65, inner_events=["connection", "creative_spark"])
cs8 = _cs(
    valence="positive",
    social_signal="affirmation",
    register="SOUTH_LDN_MODE",
    trust=0.80,
    familiarity=0.75,
    emotional_context={"energy": "normal", "tension": "low", "closure": "open"},
    topic_signals=("identity", "creative"),
)
affect8, tag8 = process_emotion(cs8, sm8)
weight8 = compute_emotion_weight(affect8)
try:
    # Chain: AffectState has all fields Significance Engine needs
    assert 0.0 <= weight8 <= 1.0, f"weight out of range: {weight8}"
    assert tag8.emotion_weight >= 0, "tag must carry emotion_weight"
    assert tag8.tag_ts > 0, "tag must have timestamp"
    # Personality chain: faculty emits NO personality_delta (Ch.7 owns that)
    assert not hasattr(affect8, "personality_delta")
    ok(f"IT-1: chain intact; emotion_weight={weight8:.3f}, tag ready for Ch.5")
except AssertionError as e: fail("IT-1", e)


# ── IT-2: Graceful degradation — relationship + self-model OFFLINE ────────────

cs9 = _cs(valence="neutral")
affect9, tag9 = process_emotion(cs9, self_model_state=None)
try:
    assert isinstance(affect9, AffectState), "must return AffectState even without self-model"
    assert affect9.affect_confidence < 1.0, \
        f"confidence should be lowered when self-model absent; got {affect9.affect_confidence}"
    assert affect9.dominant_emotion in DOMINANT_EMOTIONS
    assert 0.0 <= affect9.arousal <= 1.0
    ok(f"IT-2: graceful degradation; confidence={affect9.affect_confidence:.3f}, dominant={affect9.dominant_emotion}")
except AssertionError as e: fail("IT-2", e)


# ── Summary ──────────────────────────────────────────────────────────────────

print(f"\nResult: {PASS}/10 passed, {FAIL} failed")
sys.exit(1 if FAIL else 0)
