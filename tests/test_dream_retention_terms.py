"""
tests/test_dream_retention_terms.py — no dream has ever been retained.

Measured across the live journal 2026-10-05:

    dreams                      166
    retention threshold        0.72
    highest significance       0.700
    retained == True               0
    surfaces_directly              0

Nothing has ever crossed, and the margin is 0.02. assess_significance has four
terms:

    0.40 * intensity + 0.30 * emotional + 0.20 * unresolved + 0.10 * recurrence

For the best dream (f3baa315) intensity and recurrence both fired at 1.0 and
emotional was 0.667. `unresolved` was 0 — as it is for all 856 seeds in the
journal, every one of them.

This file pins the term that was provably broken, and records the one that is
merely never triggered so it is not mistaken for working.
"""
from __future__ import annotations

from faculties.dream.dream_review import assess_significance


def _entry(seed_emotion=None, cycle_vector=None, intensity=0.0, unresolved=""):
    seed = {"source": "s", "emotional_weight": seed_emotion or {}, "unresolved": unresolved}
    return {
        "dream_intensity": intensity,
        "cycles": [{"emotion_vector": cycle_vector or {}, "seeds": [seed]}],
    }


# ── the dead read ───────────────────────────────────────────────────────────

def test_seed_emotion_counts_at_all():
    """
    Was seed.get("emotional_weight_max"), a key that appears exactly once in
    the codebase — on this read. No writer has ever produced it, so the term
    was a constant 0.0 for all 166 dreams.
    """
    without = assess_significance(_entry())
    with_seed = assess_significance(_entry(seed_emotion={"wonder": 1.0}))

    assert with_seed > without, (
        "a seed carrying emotion must raise significance; it was read from a "
        "key nothing writes, so it never could"
    )
    assert abs(with_seed - 0.30) < 0.001, "emotional carries weight 0.30"


def test_the_stronger_of_seed_and_cycle_emotion_wins():
    """Both are sources of the same quantity and must be treated identically."""
    seed_louder = assess_significance(
        _entry(seed_emotion={"grief": 0.9}, cycle_vector={"calm": 0.2}))
    cycle_louder = assess_significance(
        _entry(seed_emotion={"grief": 0.2}, cycle_vector={"calm": 0.9}))

    assert abs(seed_louder - cycle_louder) < 0.001


def test_a_malformed_seed_emotion_does_not_raise():
    assert assess_significance(_entry(seed_emotion={"x": "not a number"})) >= 0.0


# ── the term that has never fired, recorded rather than assumed working ─────

def test_unresolved_is_worth_a_fifth_of_the_score():
    """
    0 of 856 live seeds carry it. dream_work.py:242 sets it to the item
    content only when `unfinishedness > 0.0`, and that has never happened.

    Not fixed here: whether a memory reads as unfinished is dream_input's
    keyword judgement, and changing it changes what eLo finds significant —
    which is a decision, not a defect. Recorded so the 0.20 is known to be
    unavailable rather than assumed to be working.
    """
    without = assess_significance(_entry(intensity=1.0))
    with_unresolved = assess_significance(
        _entry(intensity=1.0, unresolved="the thing I did not finish"))

    assert abs(with_unresolved - without - 0.20) < 0.001


def test_the_best_real_dream_now_clears_the_bar():
    """
    f3baa315, the highest-scoring dream eLo has had: intensity 1.0,
    recurrence 1.0, emotional 0.667, unresolved 0 -> 0.700.

    This was `test_the_best_real_dream_still_falls_short` and asserted 0.700
    < 0.72, with the note "if this ever passes, retention has started
    working". David ruled the threshold down to 0.65 on 2026-10-09, so it has
    — the tripwire fired as designed and is turned over here rather than
    deleted.

    What it does NOT yet mean: 82 of 103 scored dreams sit at exactly 0.4000
    and nothing lives between 0.46 and 0.70, so this one dream is the only
    one the new bar admits. See the filing to Board, 2026-10-09.
    """
    from runtime.memory_origin import DREAM_RETENTION_THRESHOLD as T
    best = 0.40 * 1.0 + 0.30 * 0.667 + 0.20 * 0.0 + 0.10 * 1.0
    assert round(best, 3) >= T, (
        f"best real dream {round(best, 3)} no longer clears {T} — the "
        "threshold was raised past what any real dream has ever scored, "
        "which is the state David ruled out")
