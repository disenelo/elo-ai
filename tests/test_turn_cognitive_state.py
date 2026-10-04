"""
tests/test_turn_cognitive_state.py — IS ELO: Capable of Ownership?

    "can he avoid claiming ownership of things he did not do?"
    "can eLo tell the difference between imagining something and doing it?"

response_gate check-16 is a correct allow-list gate: only MEMORY, OBSERVATION
and ACTION may support "I remember" / "I witnessed" / "it happened to me".

It had never run. The gate reads the current state from the caller's dict,
and server.py built that dict with exactly one key — relationship_mode —
which is none of the four names it looks for. Every turn fell through to
"no state info → conservative pass" and returned True before examining the
response.
"""
from __future__ import annotations

import pytest

from runtime.cognitive_state import CognitiveState, can_claim_occurred
from runtime.response_gate import _check_cognitive_claim_origin as check16
from runtime.turn_cognitive_state import state_for_turn

_CLAIM = "I remember when the servo arrived."


# ── The state a turn is in ───────────────────────────────────────────────────

def test_a_plain_generated_turn_cannot_claim_occurrence():
    state = state_for_turn()
    assert not can_claim_occurred(state), state


def test_memory_action_and_observation_can():
    assert can_claim_occurred(state_for_turn(used_memory=True))
    assert can_claim_occurred(state_for_turn(performed_action=True))
    assert can_claim_occurred(CognitiveState.OBSERVATION.value)


def test_a_dream_never_counts_as_something_that_happened():
    assert state_for_turn(dreaming=True) == CognitiveState.DREAM.value
    assert not can_claim_occurred(state_for_turn(dreaming=True))


def test_a_dream_outranks_memory_and_action():
    """Memory feeding a dream does not make the dream an event."""
    state = state_for_turn(dreaming=True, used_memory=True, performed_action=True)
    assert state == CognitiveState.DREAM.value
    assert not can_claim_occurred(state)


def test_action_outranks_memory():
    assert state_for_turn(performed_action=True, used_memory=True) == \
        CognitiveState.ACTION.value


@pytest.mark.parametrize("state", [s.value for s in CognitiveState])
def test_every_state_the_producer_can_emit_is_a_real_one(state):
    assert CognitiveState(state)


# ── Through the real gate ────────────────────────────────────────────────────

def test_the_gate_flags_an_occurrence_claim_from_a_generated_turn():
    ok, _, flags = check16(_CLAIM, {"state": state_for_turn()})
    assert ok is False, "an unbacked 'I remember' passed the gate"
    assert flags and "cognitive_claim_origin" in flags[0]


def test_the_gate_allows_the_same_claim_when_memory_backs_it():
    ok, _, flags = check16(_CLAIM, {"state": state_for_turn(used_memory=True)})
    assert ok is True, flags


def test_the_gate_flags_it_in_a_dream():
    ok, _, _ = check16(_CLAIM, {"state": state_for_turn(dreaming=True)})
    assert ok is False


def test_a_response_making_no_claim_is_untouched():
    ok, _, flags = check16("The servo needs calibrating.", {"state": state_for_turn()})
    assert ok is True and not flags


# ── Causal: change the state, change the verdict ────────────────────────────

def test_changing_the_backing_state_changes_the_verdict():
    unbacked, _, _ = check16(_CLAIM, {"state": state_for_turn()})
    backed, _, _ = check16(_CLAIM, {"state": state_for_turn(used_memory=True)})
    assert unbacked is not backed


def test_an_empty_state_dict_still_passes_everything():
    """
    The exact shape server.py used to send. Documented, not asserted away —
    it is why the gate never ran, and the fix is at the caller.
    """
    ok, _, _ = check16(_CLAIM, {"relationship_mode": "familiar"})
    assert ok is True


# ── The wiring ───────────────────────────────────────────────────────────────

def test_server_feeds_the_gate_a_state_key():
    """
    Source-asserted, and said plainly. The behaviour above is what is proven;
    this checks the caller still supplies the one thing whose absence made
    the gate inert, and that it uses a key the gate actually reads.
    """
    from pathlib import Path
    src = (Path(__file__).resolve().parent.parent / "server.py").read_text(encoding="utf-8")
    assert "from runtime.turn_cognitive_state import state_for_turn" in src
    assert '_rg_cs["state"]' in src

    from runtime.response_gate import _check_cognitive_claim_origin  # noqa: F401
    import inspect
    import runtime.response_gate as rg
    gate_src = inspect.getsource(rg._check_cognitive_claim_origin)
    assert '"state"' in gate_src, "the gate no longer reads the key server.py sets"
