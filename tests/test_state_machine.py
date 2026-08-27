"""
tests/test_state_machine.py

WP_F gap: runtime/state_machine.py — eLo OS v2.1 Runtime State Machine.
Verifies the strict runtime state contract: no hidden states, correct mode
derivation, loop-counter threshold enforcement, stability clamping.

Run: ~/miniconda3/bin/python3 -m pytest tests/test_state_machine.py -q
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from runtime.state_machine import (
    fresh,
    update,
    is_stabilisation_forced,
    mode_from,
    stability,
)


def test_fresh_returns_valid_default_state():
    """AT-1: fresh() returns dict with all required keys at documented defaults."""
    state = fresh()
    assert state["mode"] == "CONVERSATIONAL", (
        f"AT-1: default mode must be CONVERSATIONAL; got {state['mode']!r}"
    )
    assert state["loop_counter"] == 0, (
        f"AT-1: default loop_counter must be 0; got {state['loop_counter']}"
    )
    assert state["stability"] == 1.0, (
        f"AT-1: default stability must be 1.0; got {state['stability']}"
    )
    assert state["emotional_state"] == "present", (
        f"AT-1: default emotional_state must be 'present'; got {state['emotional_state']!r}"
    )


def test_fresh_does_not_mutate_on_repeated_calls():
    """AT-2: fresh() returns a new dict each call — no shared state."""
    a = fresh()
    b = fresh()
    assert a is not b, "AT-2: fresh() must return a new dict each call"
    a["mode"] = "DIRECT"
    assert b["mode"] == "CONVERSATIONAL", "AT-2: mutating one fresh() dict must not affect another"


def test_update_derives_mode_from_response_goal():
    """AT-3: mode is derived from exec_decision.response_goal via _GOAL_MODE."""
    state = fresh()
    attn = {"intent": "conversation", "emotional_context": {}}
    for goal, expected_mode in [
        ("clarify", "DIRECT"),
        ("stabilise", "GENTLE_GROUNDED"),
        ("explore", "CREATIVE"),
        ("create", "CREATIVE"),
        ("answer", "CONVERSATIONAL"),
        ("reflect", "CONVERSATIONAL"),
    ]:
        result = update(state, attn, {"response_goal": goal})
        assert result["mode"] == expected_mode, (
            f"AT-3: response_goal={goal!r} must yield mode={expected_mode!r}; got {result['mode']!r}"
        )


def test_update_does_not_mutate_input():
    """AT-4: update() returns a new dict — current is not mutated."""
    state = fresh()
    original_mode = state["mode"]
    attn = {"intent": "conversation", "emotional_context": {}}
    _ = update(state, attn, {"response_goal": "clarify"})
    assert state["mode"] == original_mode, (
        "AT-4: update() must not mutate the current state dict"
    )


def test_loop_counter_increments_on_loop_signal():
    """AT-5: loop_signal=True increments loop_counter."""
    state = fresh()
    attn = {"intent": "conversation", "emotional_context": {}}
    result = update(state, attn, {"response_goal": "answer"}, loop_signal=True)
    assert result["loop_counter"] == 1, (
        f"AT-5: loop_counter must increment to 1 on loop_signal; got {result['loop_counter']}"
    )


def test_loop_counter_decays_on_clean_turns():
    """AT-6: loop_counter decrements on clean turns (min 0)."""
    state = fresh()
    state["loop_counter"] = 2
    attn = {"intent": "conversation", "emotional_context": {}}
    result = update(state, attn, {"response_goal": "answer"}, loop_signal=False)
    assert result["loop_counter"] == 1, (
        f"AT-6: loop_counter must decay from 2 to 1 on clean turn; got {result['loop_counter']}"
    )


def test_stabilisation_forced_above_threshold():
    """AT-7: is_stabilisation_forced() returns True when loop_counter > 3."""
    assert is_stabilisation_forced({"loop_counter": 4}), (
        "AT-7: stabilisation must be forced when loop_counter > 3"
    )
    assert not is_stabilisation_forced({"loop_counter": 3}), (
        "AT-7: stabilisation must NOT be forced when loop_counter == 3"
    )
    assert not is_stabilisation_forced({"loop_counter": 0}), (
        "AT-7: stabilisation must NOT be forced when loop_counter == 0"
    )


def test_stability_clamps_to_zero_one():
    """AT-8: stability is clamped to [0.0, 1.0] on update."""
    state = fresh()
    state["stability"] = 0.05  # near bottom
    attn = {"intent": "conversation", "emotional_context": {"inferred_state": "overwhelmed"}}
    result = update(state, attn, {"response_goal": "answer"})
    assert 0.0 <= result["stability"] <= 1.0, (
        f"AT-8: stability must be clamped to [0.0, 1.0]; got {result['stability']}"
    )
    # overwhelmed → -0.30 delta → 0.05 - 0.30 = -0.25 → clamp to 0.0
    assert result["stability"] == 0.0, (
        f"AT-8: stability at 0.05 with overwhelmed (-0.30) must clamp to 0.0; got {result['stability']}"
    )


if __name__ == "__main__":
    _tests = [
        ("AT-1", test_fresh_returns_valid_default_state),
        ("AT-2", test_fresh_does_not_mutate_on_repeated_calls),
        ("AT-3", test_update_derives_mode_from_response_goal),
        ("AT-4", test_update_does_not_mutate_input),
        ("AT-5", test_loop_counter_increments_on_loop_signal),
        ("AT-6", test_loop_counter_decays_on_clean_turns),
        ("AT-7", test_stabilisation_forced_above_threshold),
        ("AT-8", test_stability_clamps_to_zero_one),
    ]
    _passed = _failed = 0
    for label, fn in _tests:
        try:
            fn()
            print(f"  ✅ {label}: {fn.__name__}")
            _passed += 1
        except Exception as _e:
            print(f"  ❌ {label}: {fn.__name__} — {_e}")
            _failed += 1
    print()
    print("=" * 62)
    print(f"state_machine   {_passed}/{_passed + _failed} passed, {_failed} failed")
    if _failed:
        sys.exit(1)
