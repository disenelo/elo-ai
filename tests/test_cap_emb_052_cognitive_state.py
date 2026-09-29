"""
WO-CAP-EMB-052 — dreams, simulations and memories as different states.

The Board cross-check rule for this WO is mechanical: "Board reads source §52
verbatim. ... For each line of the source spec, Board asks: is there evidence
this behaviour exists in the built system? Unmatched source lines = FAIL."

So test_every_source_line_is_represented parses the VERBATIM SOURCE block out
of the work order itself. If the source changes and the build does not, or the
build drifts from the source, it goes red. It is the cross-check, executable.
"""
import os
import re

import pytest

from runtime.cognitive_state import (
    CognitiveState,
    MEANINGS,
    SOURCE_LABELS,
    OCCURRED_STATES,
    INTERNALLY_GENERATED,
    UNKNOWN_STATE,
    meaning,
    describe,
    can_claim_occurred,
    may_assert_as,
    state_for_origin,
    state_for_epistemic_class,
    state_for_ladder_stage,
)

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_WO = os.path.join(
    _ROOT, "engineering", "work_orders",
    "WO-CAP-EMB-052_elo_should_understand_dreams_simulations_and_memories_as_different_states.md",
)

# The doc conversion turned the source table into alternating label/meaning
# lines separated by "WidthNNNNWidthN" cell artefacts. Everything that is not
# an artefact and not the header is a real State or Meaning line.
_ARTEFACT = re.compile(r"^Width\d+Width\d+$")


def _source_pairs() -> list[tuple[str, str]]:
    with open(_WO, encoding="utf-8") as f:
        body = f.read()
    block = body.split("**VERBATIM SOURCE — §52:**", 1)[1].split("**Acceptance test:**", 1)[0]
    lines = []
    for raw in block.splitlines():
        line = raw.strip()
        if not line.startswith(">"):
            continue
        line = line[1:].strip()
        if not line or _ARTEFACT.match(line):
            continue
        lines.append(line)
    # Drop the lead-in, the table header, and the closing sentence.
    assert lines[0].startswith("I would explicitly distinguish"), lines[0]
    assert lines[1] == "State" and lines[2] == "Meaning", lines[1:3]
    assert lines[-1].startswith("That distinction could become"), lines[-1]
    rows = lines[3:-1]
    assert len(rows) % 2 == 0, f"odd number of table cells: {rows}"
    return [(rows[i], rows[i + 1]) for i in range(0, len(rows), 2)]


def test_source_block_parses_to_thirteen_rows():
    pairs = _source_pairs()
    assert len(pairs) == 13, pairs


def test_every_source_line_is_represented():
    """The Board cross-check, executable. Unmatched source line = FAIL."""
    built = {SOURCE_LABELS[s]: MEANINGS[s] for s in CognitiveState}
    unmatched = []
    for label, sense in _source_pairs():
        if built.get(label) != sense:
            unmatched.append((label, sense, built.get(label)))
    assert not unmatched, f"source lines with no matching built state: {unmatched}"


def test_no_state_invented_beyond_the_source():
    """The build may not carry a state §52 does not name."""
    source_labels = {label for label, _ in _source_pairs()}
    extra = {SOURCE_LABELS[s] for s in CognitiveState} - source_labels
    assert not extra, f"states not in §52: {extra}"


def test_instinct_reflex_is_not_slash_collapsed():
    """Rule 4b — 'Instinct/reflex' keeps both words."""
    assert SOURCE_LABELS[CognitiveState.INSTINCT_REFLEX] == "Instinct/reflex"


def test_meanings_are_distinct():
    """Thirteen states, thirteen distinct meanings — nothing collapses."""
    senses = [MEANINGS[s] for s in CognitiveState]
    assert len(set(senses)) == len(senses)


# ── the distinction has teeth ─────────────────────────────────────────────────

def test_only_three_states_may_claim_something_occurred():
    assert OCCURRED_STATES == {
        CognitiveState.MEMORY, CognitiveState.OBSERVATION, CognitiveState.ACTION,
    }


@pytest.mark.parametrize("state", [
    CognitiveState.DREAM,
    CognitiveState.SIMULATION,
    CognitiveState.IMAGINATION,
    CognitiveState.PREDICTION,
    CognitiveState.HYPOTHESIS,
])
def test_internal_states_cannot_claim_it_happened(state):
    """A dream is not evidence that anything took place. Neither is a sim."""
    assert state in INTERNALLY_GENERATED
    assert can_claim_occurred(state) is False


def test_memory_observation_action_can():
    for s in (CognitiveState.MEMORY, CognitiveState.OBSERVATION, CognitiveState.ACTION):
        assert can_claim_occurred(s) is True


def test_no_state_may_be_spoken_as_another():
    for a in CognitiveState:
        for b in CognitiveState:
            assert may_assert_as(a, b) is (a is b), (a, b)


def test_dream_may_not_be_asserted_as_memory():
    """The headline conflation §52 exists to prevent."""
    assert may_assert_as(CognitiveState.DREAM, CognitiveState.MEMORY) is False
    assert may_assert_as(CognitiveState.SIMULATION, CognitiveState.ACTION) is False
    assert may_assert_as(CognitiveState.PREDICTION, CognitiveState.OBSERVATION) is False
    assert may_assert_as(CognitiveState.HYPOTHESIS, CognitiveState.KNOWLEDGE) is False


# ── classification from the vocabularies that already existed ─────────────────

def test_memory_origins_classify():
    from runtime.memory_origin import MemoryOrigin
    assert state_for_origin(MemoryOrigin.REAL_EXPERIENCE) is CognitiveState.MEMORY
    assert state_for_origin(MemoryOrigin.DREAM_SIMULATION) is CognitiveState.DREAM
    assert state_for_origin(MemoryOrigin.DREAM_INSIGHT) is CognitiveState.HYPOTHESIS
    assert state_for_origin(MemoryOrigin.SEMANTIC) is CognitiveState.KNOWLEDGE
    assert state_for_origin(MemoryOrigin.SELF_MODEL) is CognitiveState.KNOWLEDGE


def test_every_memory_origin_is_explicitly_mapped():
    """
    Coverage, not value: DREAM_INSIGHT legitimately maps to HYPOTHESIS, which
    is also the fall-through, so comparing against UNKNOWN_STATE cannot tell a
    real mapping from an accident. Membership can. A new MemoryOrigin added
    without a state fails here instead of silently becoming a hypothesis.
    """
    from runtime.memory_origin import MemoryOrigin
    from runtime.cognitive_state import _ORIGIN_TO_STATE
    missing = [o.value for o in MemoryOrigin if o.value not in _ORIGIN_TO_STATE]
    assert not missing, f"MemoryOrigin values with no CognitiveState: {missing}"


def test_embodiment_axis_is_orthogonal_and_preserved():
    """
    §51's simulated-vs-physical distinction must NOT be re-encoded here.
    Both are MEMORY — both happened. Which BODY did it stays in memory_origin,
    and only the physical one may claim physical experience.
    """
    from runtime.memory_origin import (
        MemoryOrigin, can_claim_physical_experience,
    )
    assert state_for_origin(MemoryOrigin.SIMULATED_EXPERIENCE) is CognitiveState.MEMORY
    assert state_for_origin(MemoryOrigin.PHYSICAL_EXPERIENCE) is CognitiveState.MEMORY
    assert can_claim_physical_experience(MemoryOrigin.SIMULATED_EXPERIENCE) is False
    assert can_claim_physical_experience(MemoryOrigin.PHYSICAL_EXPERIENCE) is True


def test_every_epistemic_class_classifies():
    from runtime.wkg_faculty import _EPISTEMIC_CLASSES
    for cls in _EPISTEMIC_CLASSES:
        assert isinstance(state_for_epistemic_class(cls), CognitiveState), cls
    assert state_for_epistemic_class("VERIFIED") is CognitiveState.KNOWLEDGE
    assert state_for_epistemic_class("SYMBOLIC") is CognitiveState.DREAM
    assert state_for_epistemic_class("SPECULATIVE") is CognitiveState.IMAGINATION


def test_every_ladder_stage_classifies():
    from faculties.dream.dream_review import PROMOTION_LADDER
    for stage in PROMOTION_LADDER:
        assert isinstance(state_for_ladder_stage(stage), CognitiveState), stage
    assert state_for_ladder_stage("DREAM") is CognitiveState.DREAM
    assert state_for_ladder_stage("KNOWLEDGE") is CognitiveState.KNOWLEDGE


# ── fail-safe ─────────────────────────────────────────────────────────────────

def test_unknown_input_never_lands_in_an_occurred_state():
    """
    An unlabelled record must not be able to claim reality. Same discipline as
    §51, where an unknown body fails safe to simulated.
    """
    for probe in ("", "  ", "nonsense", "made_up_origin", None):
        assert state_for_origin(probe) is UNKNOWN_STATE
        assert can_claim_occurred(state_for_origin(probe)) is False
    assert state_for_epistemic_class("NOT_A_CLASS") is UNKNOWN_STATE
    assert state_for_ladder_stage("NOT_A_STAGE") is UNKNOWN_STATE
    assert UNKNOWN_STATE not in OCCURRED_STATES


def test_lookups_never_raise():
    for probe in (None, "", "zzz", 7, object()):
        assert meaning(probe) == ""
        assert describe(probe) == ""
        assert can_claim_occurred(probe) is False
        assert may_assert_as(probe, CognitiveState.MEMORY) is False


# ── wired: the dream journal carries the state ────────────────────────────────

def test_insight_carries_its_cognitive_state():
    from faculties.dream.dream_review import (
        CandidateInsight, STAGE_DREAM, STAGE_IDEA, STAGE_EVALUATION,
        STAGE_TEST, STAGE_KNOWLEDGE,
    )
    expected = {
        STAGE_DREAM:      CognitiveState.DREAM,
        STAGE_IDEA:       CognitiveState.IMAGINATION,
        STAGE_EVALUATION: CognitiveState.HYPOTHESIS,
        STAGE_TEST:       CognitiveState.SIMULATION,
        STAGE_KNOWLEDGE:  CognitiveState.KNOWLEDGE,
    }
    for stage, state in expected.items():
        ins = CandidateInsight(content="c", significance=0.8, stage=stage)
        assert ins.cognitive_state == state.value, stage
        assert ins.as_dict()["cognitive_state"] == state.value


def test_no_rung_of_the_ladder_can_claim_something_happened():
    """
    A dream is never evidence that anything occurred, however far its insight
    has climbed. Not even at KNOWLEDGE.
    """
    from faculties.dream.dream_review import CandidateInsight, PROMOTION_LADDER
    for stage in PROMOTION_LADDER:
        ins = CandidateInsight(content="c", significance=1.0, stage=stage)
        assert can_claim_occurred(ins.cognitive_state) is False, stage


def test_state_is_derived_not_stored():
    """It tracks `stage`, so the ladder and the vocabulary cannot disagree."""
    from faculties.dream.dream_review import CandidateInsight, STAGE_DREAM, STAGE_KNOWLEDGE
    ins = CandidateInsight(content="c", significance=0.9, stage=STAGE_DREAM)
    assert ins.cognitive_state == CognitiveState.DREAM.value
    ins.stage = STAGE_KNOWLEDGE
    assert ins.cognitive_state == CognitiveState.KNOWLEDGE.value


# ── cross-seat: Check 16 in response_gate.py ─────────────────────────────────
#
# WO-CHECK16-FIX (2026-09-29): Builder 1 switched check-16 from deny-list
# (_INTERNALLY_GENERATED_STATE_NAMES, 5 entries) to allow-list (can_claim_occurred,
# 3 entries: MEMORY/OBSERVATION/ACTION). All six xfail tests below now PASS.
# Markers removed — tests are clean green.

_OCCURRENCE_CLAIM = "I remember that happened to me."


@pytest.mark.parametrize("state", [
    CognitiveState.KNOWLEDGE,
    CognitiveState.INFERENCE,
    CognitiveState.PATTERN,
    CognitiveState.INSTINCT_REFLEX,
    CognitiveState.DECISION,
])
def test_check16_should_flag_every_non_occurred_state(state):
    from runtime.response_gate import _check_cognitive_claim_origin as check16
    assert can_claim_occurred(state) is False
    ok, _, _ = check16(_OCCURRENCE_CLAIM, {"state": state.value})
    assert ok is False, (
        f"{state.value} may claim occurrence at the response layer although "
        "can_claim_occurred() is False"
    )


def test_a_promoted_dream_insight_may_not_say_it_happened():
    """
    The conflation EMB-052 exists to prevent, at the layer that speaks.

    EMB-031's ladder can promote a dream insight to KNOWLEDGE. KNOWLEDGE is
    "This is known", not "This happened" — check16 now correctly blocks it
    via can_claim_occurred() allow-list (KNOWLEDGE not in OCCURRED_STATES).
    """
    from runtime.response_gate import _check_cognitive_claim_origin as check16
    from faculties.dream.dream_review import CandidateInsight, STAGE_KNOWLEDGE
    insight = CandidateInsight(content="c", significance=1.0, stage=STAGE_KNOWLEDGE)
    assert can_claim_occurred(insight.cognitive_state) is False
    ok, _, _ = check16(_OCCURRENCE_CLAIM, {"state": insight.cognitive_state})
    assert ok is False


def test_check16_does_flag_the_five_it_covers():
    """All five internally-generated states still flagged after allow-list switch."""
    from runtime.response_gate import _check_cognitive_claim_origin as check16
    for state in (CognitiveState.DREAM, CognitiveState.SIMULATION,
                  CognitiveState.IMAGINATION, CognitiveState.PREDICTION,
                  CognitiveState.HYPOTHESIS):
        ok, _, flags = check16(_OCCURRENCE_CLAIM, {"state": state.value})
        assert ok is False and flags, state
