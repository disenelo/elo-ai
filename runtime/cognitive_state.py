"""
runtime/cognitive_state.py — Cognitive State Classification (WO-CAP-EMB-052)

§52 verbatim: "I would explicitly distinguish: ... That distinction could
become one of the most important foundations of eLo's cognition."

Thirteen states. Each one is a different claim about the world, and eLo must
never speak one of them in the voice of another. A dream is not a memory. A
simulation is not an action. A prediction is not an observation.

This module is the single vocabulary. The three that already existed each
carried a slice of the distinction and none of them carried all of it:

    MemoryOrigin (runtime/memory_origin.py)   — where a memory came from
    _EPISTEMIC_CLASSES (runtime/wkg_faculty)  — how well a fact is attested
    PROMOTION_LADDER (faculties/dream/…)      — how far an insight has climbed

Those axes are preserved, not replaced. §51's simulated-vs-physical
embodiment distinction in particular is ORTHOGONAL to this one: a simulated
body's experience is still a MEMORY of something that happened — what it may
not claim is PHYSICAL experience, and that guard stays in memory_origin.py.
Collapsing the two axes would lose one of them.
"""
from __future__ import annotations

from enum import Enum


class CognitiveState(str, Enum):
    """The thirteen states of §52, in source order."""
    MEMORY          = "memory"
    KNOWLEDGE       = "knowledge"
    INFERENCE       = "inference"
    PATTERN         = "pattern"
    HYPOTHESIS      = "hypothesis"
    IMAGINATION     = "imagination"
    DREAM           = "dream"
    SIMULATION      = "simulation"
    PREDICTION      = "prediction"
    OBSERVATION     = "observation"
    INSTINCT_REFLEX = "instinct_reflex"
    DECISION        = "decision"
    ACTION          = "action"


# Meanings verbatim from §52. Rule 4b — no paraphrase, no slash-collapsing.
# "Instinct/reflex" keeps both words; the member is INSTINCT_REFLEX for that
# reason, not INSTINCT.
MEANINGS: dict[CognitiveState, str] = {
    CognitiveState.MEMORY:          "This happened",
    CognitiveState.KNOWLEDGE:       "This is known",
    CognitiveState.INFERENCE:       "This follows from evidence",
    CognitiveState.PATTERN:         "This keeps recurring",
    CognitiveState.HYPOTHESIS:      "This might be true",
    CognitiveState.IMAGINATION:     "Let's explore this",
    CognitiveState.DREAM:           "Unconstrained/background association",
    CognitiveState.SIMULATION:      "Let's test this virtually",
    CognitiveState.PREDICTION:      "I expect this",
    CognitiveState.OBSERVATION:     "This is happening",
    CognitiveState.INSTINCT_REFLEX: "Respond quickly",
    CognitiveState.DECISION:        "Executive selected this",
    CognitiveState.ACTION:          "We actually did it",
}

# Source labels, verbatim, for anything that has to render the distinction
# back to David in his own words.
SOURCE_LABELS: dict[CognitiveState, str] = {
    CognitiveState.MEMORY:          "Memory",
    CognitiveState.KNOWLEDGE:       "Knowledge",
    CognitiveState.INFERENCE:       "Inference",
    CognitiveState.PATTERN:         "Pattern",
    CognitiveState.HYPOTHESIS:      "Hypothesis",
    CognitiveState.IMAGINATION:     "Imagination",
    CognitiveState.DREAM:           "Dream",
    CognitiveState.SIMULATION:      "Simulation",
    CognitiveState.PREDICTION:      "Prediction",
    CognitiveState.OBSERVATION:     "Observation",
    CognitiveState.INSTINCT_REFLEX: "Instinct/reflex",
    CognitiveState.DECISION:        "Decision",
    CognitiveState.ACTION:          "Action",
}


# ── What a state is allowed to claim ──────────────────────────────────────────
#
# Only three states assert that something occurred in the world. Everything
# else is internal: entertained, expected, associated, or selected. This is
# the practical edge of the distinction — it is what stops
#     "I already know how this works"
# meaning a dream, a simulation, or an expectation.

OCCURRED_STATES: frozenset[CognitiveState] = frozenset({
    CognitiveState.MEMORY,       # This happened
    CognitiveState.OBSERVATION,  # This is happening
    CognitiveState.ACTION,       # We actually did it
})

# States generated inside eLo with no external constraint. These may never
# be the sole basis for a factual claim.
INTERNALLY_GENERATED: frozenset[CognitiveState] = frozenset({
    CognitiveState.IMAGINATION,
    CognitiveState.DREAM,
    CognitiveState.SIMULATION,
    CognitiveState.HYPOTHESIS,
    CognitiveState.PREDICTION,
})

# An unrecognised input becomes HYPOTHESIS — "This might be true". It is the
# weakest honest position: it neither asserts the thing happened nor declares
# it fiction. Defaulting anywhere in OCCURRED_STATES would let an unlabelled
# record claim reality it has not earned, the same failure §51 forbids for
# embodiment.
UNKNOWN_STATE: CognitiveState = CognitiveState.HYPOTHESIS


def meaning(state: CognitiveState | str) -> str:
    """The §52 meaning of a state, verbatim. Unknown input returns ''."""
    try:
        return MEANINGS[CognitiveState(state)]
    except Exception:
        return ""


def describe(state: CognitiveState | str) -> str:
    """'Dream — Unconstrained/background association'. '' if unrecognised."""
    try:
        s = CognitiveState(state)
    except Exception:
        return ""
    return f"{SOURCE_LABELS[s]} — {MEANINGS[s]}"


def can_claim_occurred(state: CognitiveState | str) -> bool:
    """
    May eLo say this happened, on the strength of a record in this state?

    True only for MEMORY, OBSERVATION and ACTION. A DREAM, a SIMULATION, a
    PREDICTION and a HYPOTHESIS all answer False — none of them is evidence
    that anything took place.
    """
    try:
        return CognitiveState(state) in OCCURRED_STATES
    except Exception:
        return False


def may_assert_as(actual: CognitiveState | str, claimed: CognitiveState | str) -> bool:
    """
    May a record that is in `actual` be spoken as `claimed`?

    Only when they are the same state. §52 asks for the states to be
    EXPLICITLY DISTINGUISHED, so no state may borrow another's voice — not
    even a strong one borrowing a weak one, because "I dreamt this" said of a
    real memory is as wrong as the reverse.
    """
    try:
        return CognitiveState(actual) is CognitiveState(claimed)
    except Exception:
        return False


# ── Classification from the vocabularies that already exist ───────────────────

# MemoryOrigin → state. SIMULATED_EXPERIENCE and PHYSICAL_EXPERIENCE both map
# to MEMORY: both happened, and §51 already distinguishes WHICH BODY did them.
# That axis is not re-encoded here.
_ORIGIN_TO_STATE: dict[str, CognitiveState] = {
    "real_experience":      CognitiveState.MEMORY,
    "episodic_trace":       CognitiveState.MEMORY,
    "consolidated":         CognitiveState.MEMORY,
    "simulated_experience": CognitiveState.MEMORY,
    "physical_experience":  CognitiveState.MEMORY,
    "dream_simulation":     CognitiveState.DREAM,
    # EMB-031: a retained dream insight is a hypothesis, never knowledge.
    "dream_insight":        CognitiveState.HYPOTHESIS,
    "self_model":           CognitiveState.KNOWLEDGE,
    "semantic":             CognitiveState.KNOWLEDGE,
}

# runtime/wkg_faculty._EPISTEMIC_CLASSES → state.
_EPISTEMIC_TO_STATE: dict[str, CognitiveState] = {
    "VERIFIED":          CognitiveState.KNOWLEDGE,
    "HISTORICAL":        CognitiveState.MEMORY,
    "SOURCE_ATTRIBUTED": CognitiveState.KNOWLEDGE,
    "SYMBOLIC":          CognitiveState.DREAM,
    "HYPOTHESIS":        CognitiveState.HYPOTHESIS,
    "SPECULATIVE":       CognitiveState.IMAGINATION,
    "DISPUTED":          CognitiveState.HYPOTHESIS,
    "UNKNOWN":           UNKNOWN_STATE,
}

# faculties/dream/dream_review.PROMOTION_LADDER → state.
_LADDER_TO_STATE: dict[str, CognitiveState] = {
    "DREAM":      CognitiveState.DREAM,
    "IDEA":       CognitiveState.IMAGINATION,
    "EVALUATION": CognitiveState.HYPOTHESIS,
    "TEST":       CognitiveState.SIMULATION,
    "KNOWLEDGE":  CognitiveState.KNOWLEDGE,
}


def state_for_origin(origin) -> CognitiveState:
    """MemoryOrigin (or its string value) → CognitiveState."""
    key = getattr(origin, "value", origin)
    return _ORIGIN_TO_STATE.get(str(key).strip().lower(), UNKNOWN_STATE)


def state_for_epistemic_class(epistemic_class: str) -> CognitiveState:
    """A wkg epistemic class → CognitiveState."""
    return _EPISTEMIC_TO_STATE.get(str(epistemic_class).strip().upper(), UNKNOWN_STATE)


def state_for_ladder_stage(stage: str) -> CognitiveState:
    """An EMB-031 promotion-ladder stage → CognitiveState."""
    return _LADDER_TO_STATE.get(str(stage).strip().upper(), UNKNOWN_STATE)
