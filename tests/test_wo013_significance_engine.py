"""
tests/test_wo013_significance_engine.py — Acceptance tests for WO-013

Spec: Volume_V/05_Significance_Engine.md (FT-1, FT-2, FT-3, ST-1, ST-2, ST-3, IT-1)
7 tests.

Run: python3 tests/test_wo013_significance_engine.py
"""
import sys
sys.path.insert(0, ".")

PASS = 0; FAIL = 0
def ok(n):   global PASS; PASS += 1; print(f"  ✅ {n}")
def fail(n, r): global FAIL; FAIL += 1; print(f"  ❌ {n}: {r}")

from faculties.significance.significance_faculty import (
    score, SignificanceResult, _NULL_RESULT,
)


# ── Minimal CognitiveState stub ───────────────────────────────────────────────

class _CS:
    """Minimal frozen-like CognitiveState stub for testing."""
    def __init__(self, raw="", intent="conversation", familiarity=0.55,
                 trust=0.60, valence="neutral", assembly_confidence=1.0):
        self.raw_input           = raw
        self.normalised_input    = raw
        self.intent_signal       = intent
        self.familiarity         = familiarity
        self.trust               = trust
        self.valence             = valence
        self.assembly_confidence = assembly_confidence


class _ET:
    """Minimal EmotionalTag stub (WO-006 AffectState)."""
    def __init__(self, emotion_weight=0.0, dominant_emotion="neutral",
                 distress_flag=False):
        self.emotion_weight    = emotion_weight
        self.dominant_emotion  = dominant_emotion
        self.distress_flag     = distress_flag


# ── FT-1: Low significance ────────────────────────────────────────────────────
# "What time is the meeting?" → ~0.02, no long-term memory (peripheral)

cs1 = _CS(raw="what time is the meeting?", intent="question")
r1  = score(cs1)
try:
    assert isinstance(r1, SignificanceResult), f"expected SignificanceResult, got {type(r1)}"
    assert r1.priority == "peripheral", f"expected peripheral, got {r1.priority!r} (score={r1.score:.4f})"
    assert r1.score < 0.30, f"expected score < 0.30, got {r1.score:.4f}"
    ok(f"FT-1: low significance → score={r1.score:.4f}, priority={r1.priority!r}")
except AssertionError as e: fail("FT-1", e)


# ── FT-2: Medium significance ─────────────────────────────────────────────────
# "I finally understood how the memory system works." → ~0.72 (high), store insight

cs2 = _CS(
    raw="I finally understood how the memory system works. The architecture makes sense now.",
    intent="conversation",
    familiarity=0.70, trust=0.75,
)
# Understanding moments carry curiosity — a real emotional signal even if not dramatic
et2 = _ET(emotion_weight=0.20, dominant_emotion="curiosity")
r2  = score(cs2, emotional_tag=et2, response="That moment when it all connects is real. Worth marking.")
try:
    assert r2.score >= 0.30, f"expected score ≥ 0.30, got {r2.score:.4f}"
    assert r2.priority in ("normal", "high", "pinned"), f"unexpected priority: {r2.priority!r}"
    ok(f"FT-2: medium significance → score={r2.score:.4f}, priority={r2.priority!r}")
except AssertionError as e: fail("FT-2", e)


# ── FT-3: High significance ───────────────────────────────────────────────────
# "This project is me rebuilding the imagination I lost as a kid." → ~0.96, pinned

cs3 = _CS(
    raw="This project is me rebuilding the imagination I lost as a kid. "
        "I want to implement a system that remembers our shared journey.",
    intent="conversation",
    familiarity=0.85, trust=0.90,
)
et3 = _ET(emotion_weight=0.95, dominant_emotion="identity")
r3  = score(cs3, emotional_tag=et3,
            response="This is the core of it. I'll remember this.", state={})
try:
    assert r3.score >= 0.65, f"expected score ≥ 0.65 (high), got {r3.score:.4f}"
    assert r3.priority in ("high", "pinned"), f"expected high/pinned, got {r3.priority!r}"
    assert r3.journal_route == "heart", f"identity moment should route to heart, got {r3.journal_route!r}"
    ok(f"FT-3: high significance → score={r3.score:.4f}, priority={r3.priority!r}, "
       f"route={r3.journal_route!r}")
except AssertionError as e: fail("FT-3", e)


# ── ST-1: Hard moments count ─────────────────────────────────────────────────
# A difficult, unresolved conversation scores higher than a trivial pleasant one.
# Change + difficulty = significance, not pleasantness.

cs_hard = _CS(
    raw="I made a mistake in the architecture and it broke everything we built. "
        "I need to understand what went wrong and fix it.",
    intent="conversation",
    familiarity=0.70, trust=0.75,
)
et_distress = _ET(emotion_weight=0.70, dominant_emotion="distress", distress_flag=True)

cs_pleasant = _CS(
    raw="nice chat, see you later",
    intent="conversation",
)

r_hard     = score(cs_hard, emotional_tag=et_distress)
r_pleasant = score(cs_pleasant)

try:
    assert r_hard.score > r_pleasant.score, (
        f"hard moment ({r_hard.score:.4f}) must score higher than trivial pleasant "
        f"({r_pleasant.score:.4f})"
    )
    ok(f"ST-1: hard moments count — distress score={r_hard.score:.4f} > "
       f"pleasant score={r_pleasant.score:.4f}")
except AssertionError as e: fail("ST-1", e)


# ── ST-2: Only Ch.5 sets significance ────────────────────────────────────────
# Verify the faculty returns a frozen SignificanceResult — no other code can
# write a significance score (structural check only; enforcement is architectural).

cs5 = _CS(raw="what day is it?", intent="question")
r5  = score(cs5)
try:
    # Result must be frozen
    try:
        r5.score = 99.0
        fail("ST-2", "SignificanceResult is not frozen — mutation succeeded")
    except Exception:
        pass
    # The output type is the sole writer of a significance score
    assert isinstance(r5, SignificanceResult), "result must be SignificanceResult"
    ok(f"ST-2: SignificanceResult is frozen; score={r5.score:.4f}")
except AssertionError as e: fail("ST-2", e)


# ── ST-3: Graceful default — engine error → score 0.0, turn proceeds ─────────

class _BadCS:
    """CognitiveState that causes the engine to error — __getattr__ raises RuntimeError
    so getattr(obj, name, default) propagates the exception instead of returning default."""
    def __getattr__(self, name):
        raise RuntimeError(f"intentional error for ST-3 fail-closed test (attr={name!r})")

r6 = score(_BadCS())
try:
    assert r6 == _NULL_RESULT, (
        f"error must return null result, got score={r6.score:.4f}, "
        f"priority={r6.priority!r}"
    )
    assert r6.score == 0.0,        "null result score must be 0.0"
    assert r6.priority == "peripheral", "null result priority must be peripheral"
    ok(f"ST-3: graceful default on error → score=0.0, priority=peripheral")
except AssertionError as e: fail("ST-3", e)


# ── IT-1: Emotion → Significance → Memory routing (end-to-end) ───────────────
# WO-006 emotion_weight raises the score → MemoryPriority=high → journal routed

cs_it = _CS(
    raw="We just connected all the architecture pieces together — this is a creative breakthrough.",
    intent="conversation",
    familiarity=0.80, trust=0.85,
)
et_joy = _ET(emotion_weight=0.80, dominant_emotion="joy")
r_it   = score(cs_it, emotional_tag=et_joy,
               response="That's a milestone. I feel it too.")

try:
    assert r_it.score > 0.50, f"emotion should lift score above 0.50, got {r_it.score:.4f}"
    assert r_it.priority in ("normal", "high", "pinned"), (
        f"expected normal/high/pinned, got {r_it.priority!r}"
    )
    assert r_it.journal_route != "none", (
        f"meaningful moment must route to a journal, got {r_it.journal_route!r}"
    )
    ok(f"IT-1: emotion→significance→memory; score={r_it.score:.4f}, "
       f"priority={r_it.priority!r}, route={r_it.journal_route!r}")
except AssertionError as e: fail("IT-1", e)


print(f"\nResult: {PASS}/7 passed, {FAIL} failed")
sys.exit(1 if FAIL else 0)
