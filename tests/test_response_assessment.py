"""
tests/test_response_assessment.py — eLo can say a response of his was poor,
and why.

Builder 2 brief, two NO verdicts:

    recognising that a response was poor?                             NO
    distinguishing self-correction from merely generating another answer? NO
        "Output must be a structured signal, not free text."

The signals already existed. Measured 2026-10-06, five guards fire on a bad
turn and not one writes down the finding:

    identity_guard.scrub_ai_leakage       the reply broke character
    response_gate.last_was_repetition...  the reply repeated itself
    telemetry_guard.strip_internal_...    the reply carried machine records
    corrections_ledger                    the reply was corrected (47,238 rows)
    inner_thought_quality.reject_reason   the thought was filler

So eLo could have a reply scrubbed for breaking character, be corrected on it,
and still have no way to say the reply was poor — the information existed and
was discarded five times.
"""
from __future__ import annotations

import pytest

from faculties.metacognition import response_assessment as ra


# ── recognising ─────────────────────────────────────────────────────────────

def test_a_correction_is_a_recognition_that_a_response_was_poor():
    v = ra.assess_correction({"why": "identity drift: core value 'playful' absent"})
    assert v["verdict"] == ra.CORRECTED
    assert v["cause"] == ra.CAUSE_IDENTITY


@pytest.mark.parametrize("why,cause", [
    ("arithmetic", ra.CAUSE_FACTUAL),
    ("identity drift: core value 'calm' absent", ra.CAUSE_IDENTITY),
    ("character identity clarification", ra.CAUSE_TONE),
    ("tone: David corrected over-analytical response", ra.CAUSE_TONE),
])
def test_the_cause_is_named_not_guessed(why, cause):
    assert ra.cause_of(why) == cause


def test_being_wrong_outranks_sounding_wrong():
    assert ra.SEVERITY[ra.CAUSE_FACTUAL] > ra.SEVERITY[ra.CAUSE_TONE]
    assert ra.SEVERITY[ra.CAUSE_IDENTITY] > ra.SEVERITY[ra.CAUSE_REPETITION]


# ── distinguishing correction from another answer ──────────────────────────

def test_a_correction_and_an_answer_are_different_events():
    """
    The brief's second NO. "I said something wrong and this replaces it" and
    "I said another thing" cannot be told apart in free text by anything
    downstream.
    """
    corrected = ra.assess_correction({"why": "arithmetic"})
    answered = ra.assess_turn(response="fine", repeated=True)

    assert corrected["verdict"] == ra.CORRECTED
    assert answered["verdict"] == ra.ANSWERED
    assert corrected["verdict"] != answered["verdict"]


def test_a_silent_turn_is_its_own_verdict():
    v = ra.assess_turn(response="", scrubbed=True)
    assert v["verdict"] == ra.SUPPRESSED


# ── it reports only what was observed ───────────────────────────────────────

def test_no_guard_firing_is_not_an_endorsement():
    """
    None means nothing CAUGHT a problem, not that the response was good.
    Claiming quality it cannot see would be the same defect as a check that
    cannot fail.
    """
    assert ra.assess_turn(response="a perfectly fine reply") is None
    assert ra.was_poor(None) is False


def test_the_worst_cause_leads_when_several_fire():
    v = ra.assess_turn(response="x", scrubbed=True, repeated=True)
    assert v["cause"] == ra.CAUSE_IDENTITY
    assert set(v["causes"]) == {ra.CAUSE_IDENTITY, ra.CAUSE_REPETITION}


def test_every_verdict_names_what_observed_it():
    """A verdict that cannot be traced to a guard is an opinion."""
    assert ra.assess_correction({"why": "arithmetic"})["observed_by"] == "verify_layer"
    assert ra.assess_turn(response="x", repeated=True)["observed_by"] == "output_guards"


# ── it renders, it does not generate ───────────────────────────────────────

def test_the_sentence_is_rendered_from_the_record():
    """
    Not a sentence the model writes about itself — a model grading its own
    output is a second opinion from the same source.
    """
    assert ra.describe(ra.assess_correction({"why": "arithmetic"})) == "I got that wrong"
    assert "sounding like myself" in ra.describe(
        ra.assess_correction({"why": "identity drift: core value 'calm' absent"}))
    assert ra.describe(None) == ""


# ── it is wired ─────────────────────────────────────────────────────────────

def test_the_verdict_travels_with_the_correction_record():
    from faculties.metacognition.correction_capture import capture
    rec = capture({"id": "c", "why": "arithmetic", "input": "2+2",
                   "corrected_response": "4"}, apply=False)
    assert rec["verdict"] == ra.CORRECTED
    assert rec["cause"] == ra.CAUSE_FACTUAL
    assert rec["severity"] > 0.0


def test_the_taxonomies_do_not_drift_apart():
    """
    The ledger has its own vocabulary in spg_failure. Mapping onto it rather
    than inventing a parallel set is what stops two names for one failure.
    """
    from memory.spg_failure import KIND_ARITHMETIC, KIND_IDENTITY_DRIFT
    assert KIND_ARITHMETIC in ra._KIND_TO_CAUSE
    assert KIND_IDENTITY_DRIFT in ra._KIND_TO_CAUSE
