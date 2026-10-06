"""
tests/test_spg_failure.py — ROOT-4 item 6: failures must score.

Brief: "a system capable of changing strategy after repeated failure? NO —
Failures not stored. SPG not scoring."

Half wrong, and the correction is the design. Failures ARE stored:
self/corrections_ledger.jsonl holds 47,006 rows. They were never scored.

Measured 2026-10-06, and it is why a flat weight would be useless:

    45,934  scrub: raw generation differed from final output     97.7%
       774  identity drift: core value '<trait>' absent
       157  character identity clarification
       137  arithmetic

A scrub is the verify layer WORKING. Scoring those as failures buries the
thousand that matter under forty-six thousand that do not.
"""
from __future__ import annotations

import pytest

from memory import spg_failure as sf


def _c(why):
    return {"why": why, "input": "x", "corrected_response": "y"}


SCRUB = "scrub: raw generation differed from final output (verify layer caught a slip)"
DRIFT = "identity drift: core value 'playful' absent from response"


# ── the taxonomy ────────────────────────────────────────────────────────────

@pytest.mark.parametrize("why,kind", [
    (SCRUB, sf.KIND_SCRUB),
    (DRIFT, sf.KIND_IDENTITY_DRIFT),
    ("character identity clarification", sf.KIND_CHARACTER),
    ("arithmetic", sf.KIND_ARITHMETIC),
    ("something nobody has seen before", sf.KIND_OTHER),
])
def test_corrections_are_classified(why, kind):
    assert sf.classify(why) == kind


def test_a_working_guard_is_not_a_failure():
    """
    97.7% of the ledger is scrubs. If those score like failures, the whole
    signal is 'eLo generated text again'.
    """
    assert sf.score_correction(_c(SCRUB)) < 0.1
    assert sf.FAILURE_WEIGHT[sf.KIND_SCRUB] < sf.FAILURE_WEIGHT[sf.KIND_CHARACTER]


def test_being_objectively_wrong_outranks_being_unclear():
    assert (sf.FAILURE_WEIGHT[sf.KIND_ARITHMETIC]
            > sf.FAILURE_WEIGHT[sf.KIND_CHARACTER])


# ── repetition is the point ─────────────────────────────────────────────────

def test_a_repeated_failure_scores_above_a_single_one():
    rows = [_c(DRIFT)] * 40 + [_c("arithmetic")]
    counts = sf.failure_counts(rows)
    assert sf.score_correction(_c(DRIFT), counts) > sf.score_correction(_c(DRIFT))


def test_repetition_never_promotes_a_scrub():
    rows = [_c(SCRUB)] * 5000
    counts = sf.failure_counts(rows)
    assert sf.score_correction(_c(SCRUB), counts) < 0.1, (
        "frequency does not turn a working guard into a failure"
    )


def test_different_traits_are_different_failures():
    """
    774 drift rows share one sentence. Without the trait in the signature they
    read as a single failure repeated 774 times, and 'which value does he lose'
    becomes unanswerable.
    """
    playful = sf.signature("identity drift: core value 'playful' absent from response")
    calm = sf.signature("identity drift: core value 'calm' absent from response")
    assert playful != calm
    assert "playful" in playful


def test_a_score_never_exceeds_one():
    rows = [_c(DRIFT)] * 100000
    assert sf.score_correction(_c(DRIFT), sf.failure_counts(rows)) <= 1.0


# ── the answer the brief needs ──────────────────────────────────────────────

def test_recurring_failures_excludes_the_noise():
    rows = [_c(SCRUB)] * 900 + [_c(DRIFT)] * 12 + [_c("arithmetic")] * 5
    top = dict(sf.recurring_failures(rows, 10))
    assert not any(k.startswith(sf.KIND_SCRUB) for k in top)
    assert top[sf.signature(DRIFT)] == 12


def test_a_malformed_row_does_not_abort_the_pass():
    assert sf.classify(None) == sf.KIND_OTHER
    assert sf.score_correction({}) > 0.0


def test_the_signal_type_exists_so_failures_can_be_logged():
    """Without this a correction had no way into SPG at all."""
    from memory.spg_capture import _VALID_SIGNAL_TYPES
    assert "failure_event" in _VALID_SIGNAL_TYPES


# ── against the real ledger ─────────────────────────────────────────────────

def test_the_real_ledger_ranks_identity_drift_at_the_top():
    rows = sf.load_corrections()
    if len(rows) < 1000:
        pytest.skip("corrections_ledger not present at full size")

    top = sf.recurring_failures(rows, 6)
    assert top, "no repeated failures found in 47k corrections"
    assert top[0][0].startswith(sf.KIND_IDENTITY_DRIFT), (
        f"expected identity drift to lead, got {top[0]}"
    )
    assert not any(k.startswith(sf.KIND_SCRUB) for k, _ in top)
