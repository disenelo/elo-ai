"""
tests/test_elo_habit_tracker_001.py — Habit Formation Tracker

IS ELO: — Developing? (habit formation)
  can we demonstrate habit formation?
  a system capable of developing habits?
  a system capable of forming low-latency responses from repeated experience?
  a system capable of recognising when something has become habitual?

THE CAUSAL CHAIN:
  experience (SPG signals) → stored in spg_signals.jsonl → counts above threshold
  → habit detected → [HABIT STATE] block in system prompt
  → LLM reads habitual patterns as learned priors

AT-1  read_habit_state() with no file → empty state (no crash)
AT-2  read_habit_state() counts edge_hints correctly
AT-3  edge_hint below FORMING_THRESHOLD → not in habits
AT-4  edge_hint at FORMING_THRESHOLD → level 'forming'
AT-5  edge_hint at HABITUAL_THRESHOLD → level 'habitual'
AT-6  edge_hint at DEEP_THRESHOLD → level 'deep_habit'
AT-7  HabitState.has_habits is True when habitual entries exist
AT-8  HabitState.has_habits is False when only forming entries
AT-9  habit_tracker_prompt_block() returns "" when no habits formed
AT-10 habit_tracker_prompt_block() returns non-empty when habits present
AT-11 block contains [HABIT STATE] header
AT-12 block marks habits as learned priors, not verified facts
AT-13 block distinguishes habitual from forming
AT-14 CAUSAL PROOF: adding signals above threshold changes the block
AT-15 habit_tracker_prompt_block() never raises (resilient)
AT-16 server.py wired: habit_tracker_prompt_block import present
AT-17 py_compile clean
"""
from __future__ import annotations

import json
import os
import py_compile
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import runtime.habit_tracker as ht_mod
from runtime.habit_tracker import (
    read_habit_state,
    habit_tracker_prompt_block,
    HabitState,
    HabitEntry,
    FORMING_THRESHOLD,
    HABITUAL_THRESHOLD,
    DEEP_THRESHOLD,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _write_signals(path: Path, edges: list[str]) -> None:
    with open(path, "w") as f:
        for i, edge in enumerate(edges):
            f.write(json.dumps({"ts": 1700000000.0 + i, "edge_hint": edge}) + "\n")


# ── AT-1 ──────────────────────────────────────────────────────────────────────

def test_at1_no_file_stable_default(tmp_path):
    state = read_habit_state(signals_path=tmp_path / "nonexistent.jsonl")
    assert isinstance(state, HabitState), "AT-1: must return HabitState"
    assert not state.has_habits, "AT-1: no file → no habits"
    assert state.total_signals == 0, "AT-1: no file → 0 signals"


# ── AT-2 ──────────────────────────────────────────────────────────────────────

def test_at2_counts_edge_hints(tmp_path):
    path = tmp_path / "spg.jsonl"
    _write_signals(path, ["close"] * 20 + ["reflect"] * 5)
    state = read_habit_state(signals_path=path)
    assert state.total_signals == 25, f"AT-2: expected 25 total, got {state.total_signals}"
    assert state.unique_edges == 2, f"AT-2: expected 2 unique edges, got {state.unique_edges}"


# ── AT-3 ──────────────────────────────────────────────────────────────────────

def test_at3_below_forming_threshold_not_in_habits(tmp_path):
    path = tmp_path / "spg.jsonl"
    n_below = FORMING_THRESHOLD - 1
    _write_signals(path, ["rare"] * n_below)
    state = read_habit_state(signals_path=path)
    edges = [h.edge_hint for h in state.habits]
    assert "rare" not in edges, (
        f"AT-3: {n_below} occurrences < FORMING_THRESHOLD({FORMING_THRESHOLD}) — must not be in habits"
    )


# ── AT-4 ──────────────────────────────────────────────────────────────────────

def test_at4_at_forming_threshold_level_is_forming(tmp_path):
    path = tmp_path / "spg.jsonl"
    _write_signals(path, ["close"] * FORMING_THRESHOLD)
    state = read_habit_state(signals_path=path)
    match = next((h for h in state.habits if h.edge_hint == "close"), None)
    assert match is not None, f"AT-4: 'close' at {FORMING_THRESHOLD}x must appear in habits"
    assert match.level == "forming", (
        f"AT-4: {FORMING_THRESHOLD}x must give level 'forming', got {match.level!r}"
    )


# ── AT-5 ──────────────────────────────────────────────────────────────────────

def test_at5_at_habitual_threshold_level_is_habitual(tmp_path):
    path = tmp_path / "spg.jsonl"
    _write_signals(path, ["close"] * HABITUAL_THRESHOLD)
    state = read_habit_state(signals_path=path)
    match = next((h for h in state.habits if h.edge_hint == "close"), None)
    assert match is not None, f"AT-5: 'close' at {HABITUAL_THRESHOLD}x must appear in habits"
    assert match.level == "habitual", (
        f"AT-5: {HABITUAL_THRESHOLD}x must give level 'habitual', got {match.level!r}"
    )


# ── AT-6 ──────────────────────────────────────────────────────────────────────

def test_at6_at_deep_threshold_level_is_deep_habit(tmp_path):
    path = tmp_path / "spg.jsonl"
    _write_signals(path, ["close"] * DEEP_THRESHOLD)
    state = read_habit_state(signals_path=path)
    match = next((h for h in state.habits if h.edge_hint == "close"), None)
    assert match is not None, f"AT-6: 'close' at {DEEP_THRESHOLD}x must appear in habits"
    assert match.level == "deep_habit", (
        f"AT-6: {DEEP_THRESHOLD}x must give level 'deep_habit', got {match.level!r}"
    )


# ── AT-7 ──────────────────────────────────────────────────────────────────────

def test_at7_has_habits_true_when_habitual(tmp_path):
    path = tmp_path / "spg.jsonl"
    _write_signals(path, ["close"] * HABITUAL_THRESHOLD)
    state = read_habit_state(signals_path=path)
    assert state.has_habits, "AT-7: state.has_habits must be True when habitual entry exists"


# ── AT-8 ──────────────────────────────────────────────────────────────────────

def test_at8_has_habits_false_when_only_forming(tmp_path):
    path = tmp_path / "spg.jsonl"
    _write_signals(path, ["close"] * FORMING_THRESHOLD)
    state = read_habit_state(signals_path=path)
    assert not state.has_habits, (
        "AT-8: state.has_habits must be False when only 'forming' entries exist (not yet habitual)"
    )


# ── AT-9 ──────────────────────────────────────────────────────────────────────

def test_at9_block_empty_when_no_habits(tmp_path):
    path = tmp_path / "spg.jsonl"
    # Only 5 signals — nothing forms
    _write_signals(path, ["close"] * 5)
    block = habit_tracker_prompt_block(signals_path=path)
    assert block == "", (
        f"AT-9: no habits formed → block must be empty, got: {block[:80]!r}"
    )


# ── AT-10 ─────────────────────────────────────────────────────────────────────

def test_at10_block_non_empty_when_habitual(tmp_path):
    path = tmp_path / "spg.jsonl"
    _write_signals(path, ["close"] * HABITUAL_THRESHOLD)
    block = habit_tracker_prompt_block(signals_path=path)
    assert block, "AT-10: habitual edge → block must be non-empty"


# ── AT-11 ─────────────────────────────────────────────────────────────────────

def test_at11_block_has_habit_state_header(tmp_path):
    path = tmp_path / "spg.jsonl"
    _write_signals(path, ["close"] * HABITUAL_THRESHOLD)
    block = habit_tracker_prompt_block(signals_path=path)
    assert "HABIT STATE" in block, "AT-11: block must contain HABIT STATE header"


# ── AT-12 ─────────────────────────────────────────────────────────────────────

def test_at12_block_marks_habits_as_learned_priors(tmp_path):
    path = tmp_path / "spg.jsonl"
    _write_signals(path, ["close"] * HABITUAL_THRESHOLD)
    block = habit_tracker_prompt_block(signals_path=path)
    assert "prior" in block.lower() or "learned" in block.lower(), (
        "AT-12: block must mark habits as learned priors, not verified facts"
    )
    assert "not" in block.lower() and ("fact" in block.lower() or "certain" in block.lower()), (
        "AT-12: block must warn that habits are NOT verified facts"
    )


# ── AT-13 ─────────────────────────────────────────────────────────────────────

def test_at13_block_distinguishes_habitual_from_forming(tmp_path):
    path = tmp_path / "spg.jsonl"
    # 'close' at habitual, 'reflect' at forming
    _write_signals(path, ["close"] * HABITUAL_THRESHOLD + ["reflect"] * FORMING_THRESHOLD)
    block = habit_tracker_prompt_block(signals_path=path)
    assert "habitual" in block.lower() or "low-latency" in block.lower(), (
        "AT-13: block must label habitual entries distinctly"
    )
    assert "forming" in block.lower() or "emerging" in block.lower(), (
        "AT-13: block must distinguish forming from habitual"
    )


# ── AT-14 ─────────────────────────────────────────────────────────────────────

def test_at14_causal_proof_adding_signals_changes_block(tmp_path):
    """
    THE CAUSAL PROOF: before HABITUAL_THRESHOLD, block is empty.
    After crossing HABITUAL_THRESHOLD, block is non-empty.
    This proves habit formation has causal reality:
      experience accumulated → threshold crossed → behaviour change (block injected).
    """
    path = tmp_path / "spg.jsonl"

    # Phase 1: below threshold — no habit
    _write_signals(path, ["close"] * (HABITUAL_THRESHOLD - 1))
    block_before = habit_tracker_prompt_block(signals_path=path)

    # Phase 2: add one more signal to cross threshold
    with open(path, "a") as f:
        f.write(json.dumps({"ts": 1700099999.0, "edge_hint": "close"}) + "\n")
    block_after = habit_tracker_prompt_block(signals_path=path)

    assert block_before == "", (
        f"AT-14 CAUSAL PROOF: below HABITUAL_THRESHOLD → block must be empty, got: {block_before[:80]!r}"
    )
    assert block_after, (
        "AT-14 CAUSAL PROOF: at HABITUAL_THRESHOLD → block must be non-empty"
    )
    assert block_before != block_after, (
        "AT-14 CAUSAL PROOF: crossing threshold must change behaviour (block changed)"
    )


# ── AT-15 ─────────────────────────────────────────────────────────────────────

def test_at15_prompt_block_resilient():
    """habit_tracker_prompt_block() must never raise."""
    def _boom(*a, **kw):
        raise RuntimeError("forced failure")

    with patch.object(ht_mod, "read_habit_state", _boom):
        try:
            result = habit_tracker_prompt_block()
            assert isinstance(result, str), "AT-15: must return str on error"
        except Exception as exc:
            pytest.fail(f"AT-15: habit_tracker_prompt_block raised: {exc}")


# ── AT-16 ─────────────────────────────────────────────────────────────────────

def test_at16_server_wired():
    server_path = os.path.join(ROOT, "server.py")
    with open(server_path, encoding="utf-8") as f:
        source = f.read()
    assert "habit_tracker_prompt_block" in source, (
        "AT-16: habit_tracker_prompt_block must be wired in server.py"
    )
    assert "runtime.habit_tracker" in source, (
        "AT-16: runtime.habit_tracker import must be in server.py"
    )


# ── AT-17 ─────────────────────────────────────────────────────────────────────

def test_at17_py_compile_clean():
    files = [
        os.path.join(ROOT, "runtime", "habit_tracker.py"),
        os.path.join(ROOT, "server.py"),
    ]
    for path in files:
        try:
            py_compile.compile(path, doraise=True)
        except py_compile.PyCompileError as exc:
            pytest.fail(f"AT-17: {os.path.basename(path)} compile error: {exc}")
