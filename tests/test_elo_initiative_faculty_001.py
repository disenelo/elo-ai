"""
tests/test_elo_initiative_faculty_001.py — Initiative Faculty

IS ELO: — Capable of Initiative?
  can eLo initiate something?
  can he connect initiative to an active thread?
  can he distinguish useful initiative from interruption?
  can he defer an initiative?

THE CAUSAL CHAIN:
  active_intentions + signal pattern → read_initiative_state()
  → InitiativeRead with suggestions → initiative_faculty_prompt_block()
  → [INITIATIVE] block in system prompt (with reason + thread connection)
  → LLM can choose to raise the initiative or defer it

AT-1  read_initiative_state() with no data → no crash, empty state
AT-2  read_initiative_state() with no active intentions → no suggestions
AT-3  active intentions present → suggestions generated
AT-4  suggestions connect to active thread (thread field non-empty)
AT-5  each suggestion has a reason
AT-6  all suggestions are deferrable
AT-7  initiative_faculty_prompt_block() returns "" with no active threads
AT-8  initiative_faculty_prompt_block() returns non-empty when active threads exist
AT-9  block contains [INITIATIVE] header
AT-10 block states initiative is deferrable
AT-11 block connects to the active thread text
AT-12 CAUSAL PROOF: presence of active intention changes the block
AT-13 initiative_faculty_prompt_block() never raises (resilient)
AT-14 server.py wired: initiative_faculty_prompt_block import present
AT-15 py_compile clean
"""
from __future__ import annotations

import os
import py_compile
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import runtime.initiative_faculty as init_mod
from runtime.initiative_faculty import (
    read_initiative_state,
    initiative_faculty_prompt_block,
    InitiativeRead,
    InitiativeSuggestion,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _mock_intentions(active: list, deferred: list = None):
    """Patch _read_intentions_safe to return controlled data."""
    return patch.object(
        init_mod,
        "_read_intentions_safe",
        return_value=(active, deferred or []),
    )


# ── AT-1 ──────────────────────────────────────────────────────────────────────

def test_at1_no_data_stable_default(tmp_path):
    with _mock_intentions([]):
        state = read_initiative_state(signals_path=tmp_path / "nonexistent.jsonl")
    assert isinstance(state, InitiativeRead), "AT-1: must return InitiativeRead"
    assert not state.has_suggestions, "AT-1: no data → no suggestions"


# ── AT-2 ──────────────────────────────────────────────────────────────────────

def test_at2_no_active_intentions_no_suggestions(tmp_path):
    with _mock_intentions(active=[], deferred=[]):
        state = read_initiative_state(signals_path=tmp_path / "nonexistent.jsonl")
    assert not state.has_suggestions, (
        "AT-2: no active intentions → no suggestions (nothing to initiate around)"
    )
    assert state.active_threads == [], "AT-2: no active threads when no intentions"


# ── AT-3 ──────────────────────────────────────────────────────────────────────

def test_at3_active_intentions_generate_suggestions(tmp_path):
    active = ["Build the habit tracker", "Wire initiative into server.py"]
    with _mock_intentions(active=active):
        state = read_initiative_state(signals_path=tmp_path / "nonexistent.jsonl")
    assert state.has_suggestions, (
        "AT-3: active intentions → suggestions must be generated"
    )
    assert len(state.suggestions) > 0, "AT-3: at least one suggestion expected"


# ── AT-4 ──────────────────────────────────────────────────────────────────────

def test_at4_suggestions_connect_to_active_thread(tmp_path):
    active = ["Build the silence faculty"]
    with _mock_intentions(active=active):
        state = read_initiative_state(signals_path=tmp_path / "nonexistent.jsonl")
    for s in state.suggestions:
        if s.thread:
            assert "silence" in s.thread.lower() or "Build" in s.thread, (
                f"AT-4: suggestion must connect to active thread, got thread: {s.thread!r}"
            )


# ── AT-5 ──────────────────────────────────────────────────────────────────────

def test_at5_suggestions_have_reasons(tmp_path):
    active = ["Build the silence faculty"]
    with _mock_intentions(active=active):
        state = read_initiative_state(signals_path=tmp_path / "nonexistent.jsonl")
    for s in state.suggestions:
        assert s.reason, f"AT-5: every suggestion must have a reason, got empty in {s}"


# ── AT-6 ──────────────────────────────────────────────────────────────────────

def test_at6_all_suggestions_deferrable(tmp_path):
    active = ["Build the silence faculty", "Wire faculty conflict detector"]
    with _mock_intentions(active=active):
        state = read_initiative_state(signals_path=tmp_path / "nonexistent.jsonl")
    for s in state.suggestions:
        assert s.can_defer is True, (
            f"AT-6: all initiative suggestions must be deferrable, got can_defer={s.can_defer}"
        )


# ── AT-7 ──────────────────────────────────────────────────────────────────────

def test_at7_block_empty_without_active_threads(tmp_path):
    with _mock_intentions(active=[], deferred=["Old deferred thing"]):
        block = initiative_faculty_prompt_block(signals_path=tmp_path / "nonexistent.jsonl")
    assert block == "", (
        f"AT-7: no active threads → block must be empty, got: {block[:80]!r}"
    )


# ── AT-8 ──────────────────────────────────────────────────────────────────────

def test_at8_block_non_empty_with_active_threads(tmp_path):
    active = ["Build the silence faculty"]
    with _mock_intentions(active=active):
        block = initiative_faculty_prompt_block(signals_path=tmp_path / "nonexistent.jsonl")
    assert block, (
        "AT-8: active thread present → initiative block must be non-empty"
    )


# ── AT-9 ──────────────────────────────────────────────────────────────────────

def test_at9_block_has_initiative_header(tmp_path):
    active = ["Build the silence faculty"]
    with _mock_intentions(active=active):
        block = initiative_faculty_prompt_block(signals_path=tmp_path / "nonexistent.jsonl")
    assert "INITIATIVE" in block, "AT-9: block must contain INITIATIVE header"


# ── AT-10 ─────────────────────────────────────────────────────────────────────

def test_at10_block_states_initiative_is_deferrable(tmp_path):
    active = ["Build the silence faculty"]
    with _mock_intentions(active=active):
        block = initiative_faculty_prompt_block(signals_path=tmp_path / "nonexistent.jsonl")
    assert "defer" in block.lower() or "deferrable" in block.lower(), (
        "AT-10: block must state initiative is deferrable"
    )


# ── AT-11 ─────────────────────────────────────────────────────────────────────

def test_at11_block_contains_active_thread_text(tmp_path):
    active = ["Build the SPECIFIC_FEATURE_XYZ"]
    with _mock_intentions(active=active):
        block = initiative_faculty_prompt_block(signals_path=tmp_path / "nonexistent.jsonl")
    assert "SPECIFIC_FEATURE_XYZ" in block, (
        "AT-11: active thread text must appear in the initiative block"
    )


# ── AT-12 ─────────────────────────────────────────────────────────────────────

def test_at12_causal_proof_active_intention_changes_block(tmp_path):
    """
    THE CAUSAL PROOF: presence of an active intention changes the initiative block.
    No intention → empty block. With intention → non-empty block.
    This proves initiative has causal reality: stored state → retrieved → behaviour changed.
    """
    sig_path = tmp_path / "nonexistent.jsonl"

    with _mock_intentions(active=[]):
        block_no_intention = initiative_faculty_prompt_block(signals_path=sig_path)

    with _mock_intentions(active=["Build the habit tracker — active work in progress"]):
        block_with_intention = initiative_faculty_prompt_block(signals_path=sig_path)

    assert block_no_intention == "", (
        "AT-12 CAUSAL PROOF: no active intention → block must be empty"
    )
    assert block_with_intention, (
        "AT-12 CAUSAL PROOF: active intention present → block must be non-empty"
    )
    assert block_no_intention != block_with_intention, (
        "AT-12: adding an active intention must change the block"
    )


# ── AT-13 ─────────────────────────────────────────────────────────────────────

def test_at13_prompt_block_resilient():
    """initiative_faculty_prompt_block() must never raise."""
    def _boom(*a, **kw):
        raise RuntimeError("forced failure")

    with patch.object(init_mod, "read_initiative_state", _boom):
        try:
            result = initiative_faculty_prompt_block()
            assert isinstance(result, str), "AT-13: must return str on error"
        except Exception as exc:
            pytest.fail(f"AT-13: initiative_faculty_prompt_block raised: {exc}")


# ── AT-14 ─────────────────────────────────────────────────────────────────────

def test_at14_server_wired():
    server_path = os.path.join(ROOT, "server.py")
    with open(server_path, encoding="utf-8") as f:
        source = f.read()
    assert "initiative_faculty_prompt_block" in source, (
        "AT-14: initiative_faculty_prompt_block must be wired in server.py"
    )
    assert "runtime.initiative_faculty" in source, (
        "AT-14: runtime.initiative_faculty must be in server.py"
    )


# ── AT-15 ─────────────────────────────────────────────────────────────────────

def test_at15_py_compile_clean():
    files = [
        os.path.join(ROOT, "runtime", "initiative_faculty.py"),
        os.path.join(ROOT, "server.py"),
    ]
    for path in files:
        try:
            py_compile.compile(path, doraise=True)
        except py_compile.PyCompileError as exc:
            pytest.fail(f"AT-15: {os.path.basename(path)} compile error: {exc}")
