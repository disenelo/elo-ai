"""
tests/test_wo_identity_state_001.py — WO-IDENTITY-STATE-001: persistent identity state

Acceptance criteria:
  IDS-1: load() returns a dict with non-zero session_count (seeded at 124)
  IDS-2: as_prompt_block() produces [PERSISTENT IDENTITY] block with session count
  IDS-3: stable_behaviour_baseline appears in the prompt block
  IDS-4: increment_session() increments session_count by 1
  IDS-5: model change increments model_changes counter
  IDS-6: [PERSISTENT IDENTITY] block appears in build_prompt() output
"""
import pytest


def _load():
    from runtime.identity_state_manager import load
    return load()


def test_ids1_session_count_seeded():
    """IDS-1: session_count is seeded (non-zero) — eLo knows its history"""
    state = _load()
    assert state.get("session_count", 0) >= 124


def test_ids2_prompt_block_has_session_count():
    """IDS-2: as_prompt_block includes [PERSISTENT IDENTITY] header and session count"""
    from runtime.identity_state_manager import as_prompt_block
    block = as_prompt_block(_load())
    assert "[PERSISTENT IDENTITY" in block
    assert "sessions completed:" in block


def test_ids3_stable_baseline_in_prompt():
    """IDS-3: stable_behaviour_baseline appears in prompt block"""
    from runtime.identity_state_manager import as_prompt_block
    block = as_prompt_block(_load())
    state = _load()
    baseline = state.get("stable_behaviour_baseline", "")
    assert baseline and baseline[:40] in block


def test_ids4_increment_session():
    """IDS-4: increment_session increments session_count by exactly 1"""
    from runtime.identity_state_manager import increment_session
    state = _load()
    count_before = state.get("session_count", 0)
    state2 = increment_session(state)
    assert state2["session_count"] == count_before + 1
    # Does not mutate original
    assert state.get("session_count") == count_before


def test_ids5_model_change_tracking():
    """IDS-5: switching model increments model_changes"""
    from runtime.identity_state_manager import increment_session
    state = _load()
    state["last_model"] = "ollama/llama3.1:8b"
    state2 = increment_session(state, model="claude-sonnet-4-6")
    assert state2["model_changes"] == (state.get("model_changes", 0) + 1)
    assert state2["last_model"] == "claude-sonnet-4-6"


def test_ids6_block_in_build_prompt():
    """IDS-6: [PERSISTENT IDENTITY] block appears in build_prompt output"""
    from runtime.prompt_builder import build as build_prompt
    result = build_prompt(
        user_input="test",
        vault_context="",
        state_context="",
        attention=None,
        exec_decision=None,
        graph_context="",
        personality_block="",
        self_block="",
        lessons=[],
        grounding_block="",
    )
    assert "[PERSISTENT IDENTITY" in result
