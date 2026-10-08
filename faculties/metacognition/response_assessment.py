"""
faculties/metacognition/response_assessment.py — eLo can say a response of his
was poor, and why.

Builder 2 brief, two NO verdicts:

    capable of recognising that a response was poor?                   NO
        "inner_thought generates post-hoc rationalisation. Cannot flag the
         response it followed as poor."
    capable of distinguishing self-correction from merely generating
    another answer?                                                    NO
        "inner_thought is generating, not correcting. Output must be a
         structured signal, not free text."

THE SIGNALS ALREADY EXIST. Measured 2026-10-06, five separate guards fire on a
bad turn and not one of them is written down as a judgement:

    identity_guard.scrub_ai_leakage      the reply broke character
    response_gate.last_was_repetition... the reply repeated itself
    telemetry_guard.strip_internal_...   the reply contained machine records
    corrections_ledger                   the reply was corrected (47,238 rows)
    inner_thought_quality.reject_reason  the thought was filler

Each one fixes its own symptom and discards the finding. So eLo could have a
reply scrubbed for breaking character, be corrected on it, and have no way to
say afterwards that the reply was poor — the information existed and was
thrown away five times.

STRUCTURED, which is the other half of the brief. A verdict is a typed record
with a named cause, not a sentence. That is what makes CORRECTED
distinguishable from ANSWERED: "I said something wrong and this replaces it"
and "I said another thing" are different events, and free text cannot carry
the difference in a way anything downstream can read.

Deliberately judges what ALREADY HAPPENED. It does not re-run the model or
ask an LLM whether a reply was good — a model grading its own output is a
second opinion from the same source. These are events that were observed by
guards that had to fire.
"""
from __future__ import annotations

import logging
import time
from typing import Any, Mapping

_log = logging.getLogger("elo.response_assessment")

# What kind of event this was. CORRECTED is the one the brief asks for: a
# prior response was wrong and this replaces it, as opposed to simply saying
# another thing.
ANSWERED = "ANSWERED"
CORRECTED = "CORRECTED"
SUPPRESSED = "SUPPRESSED"

# Named causes. Each maps to a guard that actually fired, so a verdict can
# always be traced to the thing that observed it.
CAUSE_IDENTITY = "identity_break"
CAUSE_REPETITION = "repetition"
CAUSE_TELEMETRY = "internal_record_leaked"
CAUSE_FACTUAL = "factual_error"
CAUSE_TONE = "tone"
CAUSE_UNSPECIFIED = "unspecified"

# [BUILDER CHOICE] How much each cause should weigh on later behaviour.
# Identity and factual errors outrank tone: sounding wrong is a smaller
# failure than being wrong or not being himself.
SEVERITY: dict[str, float] = {
    CAUSE_FACTUAL: 0.90,
    CAUSE_IDENTITY: 0.85,
    CAUSE_TELEMETRY: 0.70,
    CAUSE_TONE: 0.55,
    CAUSE_REPETITION: 0.45,
    CAUSE_UNSPECIFIED: 0.40,
}

# Maps the correction ledger's own vocabulary onto these causes, so the two
# systems do not drift into separate taxonomies of the same thing.
_KIND_TO_CAUSE: dict[str, str] = {
    "arithmetic": CAUSE_FACTUAL,
    "identity_drift": CAUSE_IDENTITY,
    "character_clarification": CAUSE_TONE,
    "other": CAUSE_UNSPECIFIED,
}


def cause_of(why: str) -> str:
    """Which named cause this correction reason belongs to."""
    text = str(why or "").lower()
    if "tone" in text or "over-analytical" in text or "presence, not explanation" in text:
        return CAUSE_TONE
    try:
        from memory.spg_failure import classify
        return _KIND_TO_CAUSE.get(classify(why), CAUSE_UNSPECIFIED)
    except Exception:
        return CAUSE_UNSPECIFIED


def assess_correction(row: Mapping[str, Any]) -> dict:
    """
    Turn one correction into a verdict about the response it corrected.

    This is the recognition the brief says is missing: a correction IS eLo
    finding out that a response of his was poor, and until now that finding
    went into an append-only ledger nobody reads.
    """
    why = str((row or {}).get("why", "") or "")
    cause = cause_of(why)
    return {
        "verdict": CORRECTED,
        "cause": cause,
        "severity": SEVERITY.get(cause, SEVERITY[CAUSE_UNSPECIFIED]),
        "why": why[:300],
        "observed_by": "verify_layer",
        "ts": time.time(),
    }


def assess_turn(
    *,
    response: str,
    scrubbed: bool = False,
    repeated: bool = False,
    telemetry_stripped: bool = False,
) -> dict | None:
    """
    A verdict from the guards that fired on this turn, or None if none did.

    None means nothing OBSERVED a problem — not that the response was good.
    The difference matters: this faculty reports what was caught, and claiming
    quality it cannot see would be the same defect as a check that cannot fail.
    """
    causes: list[str] = []
    if scrubbed:
        causes.append(CAUSE_IDENTITY)
    if telemetry_stripped:
        causes.append(CAUSE_TELEMETRY)
    if repeated:
        causes.append(CAUSE_REPETITION)

    if not causes:
        return None

    worst = max(causes, key=lambda c: SEVERITY.get(c, 0.0))
    return {
        # Recorded, not acted on — see CONFIDENCE_IS_CALIBRATED above.
        "confidence": _confidence(response),
        "verdict": SUPPRESSED if not str(response or "").strip() else ANSWERED,
        "cause": worst,
        "causes": causes,
        "severity": SEVERITY.get(worst, SEVERITY[CAUSE_UNSPECIFIED]),
        "observed_by": "output_guards",
        "ts": time.time(),
    }


# WO-METACOGNITION-001 (85cc8bf) built assess_confidence / flag_uncertainty /
# detect_reasoning_error and nothing has ever called them — zero production
# callers, tests only. Card 0005 went looking for the entry point; there is
# none.
#
# It is NOT wired as a cause, and that is deliberate. Measured 2026-10-08:
#
#   conf 0.25  uncertain=True  "The eLo robot uses a Raspberry Pi 5 and TPU shell."
#   conf 0.50  uncertain=True  "I think maybe it could possibly be around 1972..."
#   conf 0.00  uncertain=True  "Yes."
#
# A well-grounded factual statement scores BELOW a hedged uncertain one, and
# flag_uncertainty (threshold 0.6) fires on all three. The score is really
# measuring WKG coverage, which is low across the board, so wiring it as a
# verdict cause would mark every response eLo gives as uncertain — noise
# dressed as self-knowledge.
#
# So it is READ and recorded, never acted on. That makes it reachable and its
# calibration measurable instead of invisible, which is the same shape as the
# observe-only Vol XI envelope check: a gate that cannot be trusted yet should
# announce itself rather than either sit dead or fire wrongly.
CONFIDENCE_IS_CALIBRATED: bool = False


def _confidence(response: str) -> float | None:
    """metacognition's own score, recorded for calibration. Never a cause."""
    try:
        from faculties.metacognition.metacognition import assess_confidence
        return round(float(assess_confidence(str(response or ""), {})), 4)
    except Exception:
        return None


def was_poor(verdict: Mapping[str, Any] | None) -> bool:
    """
    Did anything actually observe a problem?

    None is not an endorsement — it means no guard fired, which is different
    from the response being good. The first version of this was a tangle of
    `and`/`or` that happened to be right for the cases I had in mind and
    unreadable for the rest.
    """
    if not verdict:
        return False
    return bool(verdict.get("cause") or verdict.get("causes"))


def describe(verdict: Mapping[str, Any] | None) -> str:
    """
    One line eLo could actually say about it.

    Not a sentence the model generates about itself — a rendering of a
    typed record, so it cannot claim more than was observed.
    """
    if not verdict:
        return ""
    cause = str(verdict.get("cause", CAUSE_UNSPECIFIED))
    phrasing = {
        CAUSE_IDENTITY: "I stopped sounding like myself there",
        CAUSE_FACTUAL: "I got that wrong",
        CAUSE_TELEMETRY: "I let something internal slip into what I said",
        CAUSE_TONE: "I explained where I should have been present",
        CAUSE_REPETITION: "I said that again",
        CAUSE_UNSPECIFIED: "that one needed correcting",
    }
    return phrasing.get(cause, phrasing[CAUSE_UNSPECIFIED])
