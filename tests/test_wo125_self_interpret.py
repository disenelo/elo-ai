"""
tests/test_wo125_self_interpret.py — Row 25 SELF-INTERPRET.

Proof: eLo names a pattern in himself traceable to logged actions.

"Traceable to logged actions" means the chain:
  record_behaviour(state, verb)  → state.recent_behavior counter
  top_habits(state)              → ranked pattern
  emergent_block(state, ...)     → pattern emitted to Executive prompt

Each test calls record_behaviour (the real action log path, not seeded state)
so the trace is complete: action call → state → Executive-visible output.

AT-125-1: record_behaviour increments recent_behavior counter
AT-125-2: top_habits returns correct ranking from logged calls
AT-125-3: emergent_block emits pattern when count >= 2 (the Executive sees it)
AT-125-4: pattern is absent from prompt when recent_behavior is empty (no false claims)
AT-125-5: trace is end-to-end — 5 sit calls → "sit" in the Executive block
AT-125-6: compile() exposes recent_behaviour to Executive (round-trip proof)
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


# ── AT-125-1: record_behaviour increments the counter ────────────────────────

def test_record_behaviour_increments_counter():
    from self.elo_self_model import EloSelfState, record_behaviour

    state = EloSelfState()
    assert state.recent_behavior == {}, "Fresh state must have empty recent_behavior"

    record_behaviour(state, "sit")
    assert state.recent_behavior.get("sit") == 1, (
        "After one 'sit' call, counter must be 1"
    )
    record_behaviour(state, "sit")
    record_behaviour(state, "sit")
    assert state.recent_behavior.get("sit") == 3, (
        "After three 'sit' calls, counter must be 3"
    )


# ── AT-125-2: top_habits returns correct ranking ──────────────────────────────

def test_top_habits_ranks_by_count():
    from self.elo_self_model import EloSelfState, record_behaviour
    from self.emergent_cognition import top_habits

    state = EloSelfState()
    for _ in range(5):
        record_behaviour(state, "sit")
    for _ in range(2):
        record_behaviour(state, "wave")
    record_behaviour(state, "move")

    ranked = top_habits(state, n=3)
    assert ranked, "top_habits must return non-empty list when recent_behavior has data"
    assert ranked[0] == ("sit", 5), f"Most frequent must be 'sit ×5', got {ranked[0]}"
    assert ranked[1] == ("wave", 2), f"Second must be 'wave ×2', got {ranked[1]}"
    assert ranked[2] == ("move", 1), f"Third must be 'move ×1', got {ranked[2]}"


# ── AT-125-3: emergent_block emits the pattern to the Executive ───────────────

def test_emergent_block_emits_habits_when_count_reaches_threshold():
    from self.elo_self_model import EloSelfState, record_behaviour
    from self.emergent_cognition import emergent_block

    state = EloSelfState(
        focal_thread="testing",
        lifetime_threads=[["test", 3]],
    )
    for _ in range(3):
        record_behaviour(state, "sit")
    for _ in range(2):
        record_behaviour(state, "move")

    block = emergent_block(state, idle_seconds=0.0)
    assert block, "emergent_block must emit content when habits exist (count >= 2)"
    assert "sit" in block, (
        f"Habit 'sit' (×3) must appear in the Executive prompt block.\nBlock:\n{block}"
    )
    assert "move" in block, (
        f"Habit 'move' (×2) must appear in the Executive prompt block.\nBlock:\n{block}"
    )


# ── AT-125-4: empty recent_behavior → no false habit claim in prompt ──────────

def test_emergent_block_silent_when_no_habits():
    from self.elo_self_model import EloSelfState
    from self.emergent_cognition import emergent_block

    # No history at all → no block emitted
    state = EloSelfState()
    block = emergent_block(state, idle_seconds=0.0)
    assert not block, (
        "emergent_block must return empty string for bare state — no fabricated habits"
    )


# ── AT-125-5: end-to-end trace — 5 sit record calls → "sit" in block ─────────

def test_end_to_end_trace_sit_x5():
    """
    Row 25 SELF-INTERPRET core proof.
    The trace is: record_behaviour × 5 → recent_behavior counter → top_habits → emergent_block.
    If ANY link in this chain breaks, this test fails.
    """
    from self.elo_self_model import EloSelfState, record_behaviour
    from self.emergent_cognition import emergent_block, top_habits

    state = EloSelfState(
        focal_thread="a real thread",
        lifetime_threads=[["sitting", 2]],
    )

    # Simulate 5 body ACKs (the way server.py does it at each ACK path)
    for _ in range(5):
        record_behaviour(state, "sit")

    # Trace step 1: counter is correct
    assert state.recent_behavior.get("sit") == 5, (
        "Trace step 1 failed: recent_behavior counter not incremented by record_behaviour"
    )

    # Trace step 2: top_habits surfaces the pattern
    habits = top_habits(state, n=1)
    assert habits and habits[0][0] == "sit", (
        f"Trace step 2 failed: top_habits did not surface 'sit': {habits}"
    )

    # Trace step 3: emergent_block emits pattern to Executive
    block = emergent_block(state, idle_seconds=0.0)
    assert "sit" in block, (
        f"Trace step 3 failed: 'sit' not visible in Executive block.\nBlock:\n{block}"
    )

    # Confirm count ×5 is visible (traceable to exactly 5 calls)
    assert "×5" in block or "x5" in block or "5" in block, (
        f"Count (×5) not visible in block — cannot trace to 5 action calls.\nBlock:\n{block}"
    )


# ── AT-125-6: compile() exposes recent_behaviour to Executive ─────────────────

def test_compile_exposes_recent_behaviour_to_executive():
    """
    the_moment.compile() must include recent_behaviour so the Executive can read the pattern.
    """
    from self.elo_self_model import EloSelfState, record_behaviour
    from runtime.the_moment import compile as compile_moment

    state = EloSelfState()
    record_behaviour(state, "sit")
    record_behaviour(state, "sit")
    record_behaviour(state, "sit")

    moment = compile_moment(state)
    assert "recent_behaviour" in moment, (
        "compile() must include recent_behaviour key — Executive cannot see pattern otherwise"
    )
    assert moment["recent_behaviour"].get("sit") == 3, (
        f"recent_behaviour must reflect 3 sit calls, got: {moment['recent_behaviour']}"
    )
