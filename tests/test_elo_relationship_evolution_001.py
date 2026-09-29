"""
tests/test_elo_relationship_evolution_001.py — Relationship evolution tracker

AT-1  relationship_state() with no signals file → empty evolution (no crash)
AT-2  relationship_state() with synthetic signals → interaction_days computed correctly
AT-3  relationship_state() counts relationship_shift signals
AT-4  stage = early for < 15 interaction days
AT-5  stage = forming for 15-60 interaction days
AT-6  stage = established for > 60 interaction days
AT-7  mean_rel_significance computed from signals with significance.relationship
AT-8  trend = deepening when many rel-significant signals
AT-9  days_since_first computed from timestamps
AT-10 RelationshipEvolution.has_history True/False property
AT-11 relationship_prompt_block() returns "" with no history
AT-12 relationship_prompt_block() contains stage and trend for real data
AT-13 relationship_prompt_block() never raises (resilient)
AT-14 Server.py wiring: relationship_prompt_block import present
AT-15 py_compile clean
"""
from __future__ import annotations

import json
import os
import sys
import py_compile
import time
from pathlib import Path

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from memory.relationship_evolution import (
    relationship_state,
    relationship_prompt_block,
    RelationshipEvolution,
    invalidate_cache,
    _STAGE_EARLY,
    _STAGE_FORMING,
    _STAGE_ESTABLISHED,
    _READER,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _write_signals(path: Path, signals: list[dict]) -> None:
    with open(path, "w") as f:
        for s in signals:
            f.write(json.dumps(s) + "\n")


def _rel_signal(day_offset: int = 0, rel_sig: float = 0.0) -> dict:
    """Build a relationship_shift signal at a given day offset from epoch."""
    ts = 1700000000.0 + (day_offset * 86400)
    return {
        "ts": ts,
        "signal_type": "relationship_shift",
        "significance": {"relationship": rel_sig},
        "context_tags": [],
        "edge_hint": "close",
    }


def _mem_signal(day_offset: int = 0) -> dict:
    ts = 1700000000.0 + (day_offset * 86400)
    return {
        "ts": ts,
        "signal_type": "memory_write",
        "significance": {"relationship": 0.0},
        "context_tags": [],
        "edge_hint": "silence",
    }


# ── AT-1 ──────────────────────────────────────────────────────────────────────

def test_at1_no_signals_file(tmp_path):
    _READER.invalidate()
    evo = relationship_state(signals_path=tmp_path / "nonexistent.jsonl")
    assert isinstance(evo, RelationshipEvolution)
    assert not evo.has_history
    assert evo.total_signals == 0
    _READER.invalidate()


# ── AT-2 ──────────────────────────────────────────────────────────────────────

def test_at2_interaction_days_counted(tmp_path):
    signals_path = tmp_path / "spg.jsonl"
    # 5 distinct days
    signals = [_rel_signal(d) for d in range(5)]
    _write_signals(signals_path, signals)
    _READER.invalidate()
    evo = relationship_state(signals_path=signals_path)
    assert evo.interaction_days == 5, (
        f"AT-2 FAIL: expected 5 interaction days, got {evo.interaction_days}"
    )
    _READER.invalidate()


# ── AT-3 ──────────────────────────────────────────────────────────────────────

def test_at3_relationship_shifts_counted(tmp_path):
    signals_path = tmp_path / "spg.jsonl"
    signals = [
        _rel_signal(0),
        _rel_signal(1),
        _mem_signal(2),   # NOT a relationship_shift
    ]
    _write_signals(signals_path, signals)
    _READER.invalidate()
    evo = relationship_state(signals_path=signals_path)
    assert evo.relationship_shifts == 2, (
        f"AT-3 FAIL: expected 2 relationship_shift signals, got {evo.relationship_shifts}"
    )
    _READER.invalidate()


# ── AT-4 ──────────────────────────────────────────────────────────────────────

def test_at4_stage_early(tmp_path):
    signals_path = tmp_path / "spg.jsonl"
    signals = [_rel_signal(d) for d in range(10)]   # 10 unique days < 15
    _write_signals(signals_path, signals)
    _READER.invalidate()
    evo = relationship_state(signals_path=signals_path)
    assert evo.stage == _STAGE_EARLY, (
        f"AT-4 FAIL: 10-day interaction should be 'early', got '{evo.stage}'"
    )
    _READER.invalidate()


# ── AT-5 ──────────────────────────────────────────────────────────────────────

def test_at5_stage_forming(tmp_path):
    signals_path = tmp_path / "spg.jsonl"
    signals = [_rel_signal(d) for d in range(30)]   # 30 unique days → forming
    _write_signals(signals_path, signals)
    _READER.invalidate()
    evo = relationship_state(signals_path=signals_path)
    assert evo.stage == _STAGE_FORMING, (
        f"AT-5 FAIL: 30-day interaction should be 'forming', got '{evo.stage}'"
    )
    _READER.invalidate()


# ── AT-6 ──────────────────────────────────────────────────────────────────────

def test_at6_stage_established(tmp_path):
    signals_path = tmp_path / "spg.jsonl"
    signals = [_rel_signal(d) for d in range(70)]   # 70 unique days → established
    _write_signals(signals_path, signals)
    _READER.invalidate()
    evo = relationship_state(signals_path=signals_path)
    assert evo.stage == _STAGE_ESTABLISHED, (
        f"AT-6 FAIL: 70-day interaction should be 'established', got '{evo.stage}'"
    )
    _READER.invalidate()


# ── AT-7 ──────────────────────────────────────────────────────────────────────

def test_at7_mean_rel_significance(tmp_path):
    signals_path = tmp_path / "spg.jsonl"
    signals = [
        _rel_signal(0, rel_sig=0.8),
        _rel_signal(1, rel_sig=0.4),
        _rel_signal(2, rel_sig=0.0),  # below threshold — not counted
    ]
    _write_signals(signals_path, signals)
    _READER.invalidate()
    evo = relationship_state(signals_path=signals_path)
    assert evo.mean_rel_significance > 0.0, (
        "AT-7 FAIL: mean_rel_significance should be > 0 when signals have rel > 0.05"
    )
    _READER.invalidate()


# ── AT-8 ──────────────────────────────────────────────────────────────────────

def test_at8_trend_deepening(tmp_path):
    signals_path = tmp_path / "spg.jsonl"
    # 55 rel-significant signals → deepening
    signals = [_rel_signal(d, rel_sig=0.3) for d in range(55)]
    _write_signals(signals_path, signals)
    _READER.invalidate()
    evo = relationship_state(signals_path=signals_path)
    assert evo.trend == "deepening", (
        f"AT-8 FAIL: 55 rel-significant signals should give 'deepening', got '{evo.trend}'"
    )
    _READER.invalidate()


# ── AT-9 ──────────────────────────────────────────────────────────────────────

def test_at9_days_since_first(tmp_path):
    signals_path = tmp_path / "spg.jsonl"
    signals = [
        _rel_signal(0),    # day 0
        _rel_signal(100),  # day 100
    ]
    _write_signals(signals_path, signals)
    _READER.invalidate()
    evo = relationship_state(signals_path=signals_path)
    assert evo.days_since_first >= 99, (
        f"AT-9 FAIL: 100-day span should give days_since_first ~100, got {evo.days_since_first}"
    )
    _READER.invalidate()


# ── AT-10 ─────────────────────────────────────────────────────────────────────

def test_at10_has_history_property(tmp_path):
    signals_path_empty = tmp_path / "empty.jsonl"
    signals_path_data  = tmp_path / "data.jsonl"
    signals_path_empty.write_text("")
    _write_signals(signals_path_data, [_rel_signal(0)])

    _READER.invalidate()
    evo_empty = relationship_state(signals_path=signals_path_empty)
    assert not evo_empty.has_history, "AT-10 FAIL: empty signals should have no history"

    _READER.invalidate()
    evo_data = relationship_state(signals_path=signals_path_data)
    assert evo_data.has_history, "AT-10 FAIL: signals present should have history"
    _READER.invalidate()


# ── AT-11 ─────────────────────────────────────────────────────────────────────

def test_at11_prompt_block_empty_no_history(tmp_path):
    _READER.invalidate()
    block = relationship_prompt_block(signals_path=tmp_path / "nonexistent.jsonl")
    assert block == "", (
        f"AT-11 FAIL: prompt block should be empty with no history, got: '{block[:100]}'"
    )
    _READER.invalidate()


# ── AT-12 ─────────────────────────────────────────────────────────────────────

def test_at12_prompt_block_contains_stage_and_trend(tmp_path):
    signals_path = tmp_path / "spg.jsonl"
    signals = [_rel_signal(d, rel_sig=0.3) for d in range(70)]
    _write_signals(signals_path, signals)
    _READER.invalidate()
    block = relationship_prompt_block(signals_path=signals_path)
    assert block, "AT-12 FAIL: expected non-empty block with 70-day history"
    assert "Stage" in block or "stage" in block, "AT-12 FAIL: block missing Stage"
    assert "Trend" in block or "trend" in block, "AT-12 FAIL: block missing Trend"
    assert "RELATIONSHIP HISTORY" in block, "AT-12 FAIL: block missing RELATIONSHIP HISTORY header"
    _READER.invalidate()


# ── AT-13 ─────────────────────────────────────────────────────────────────────

def test_at13_prompt_block_resilient():
    from unittest.mock import patch
    import memory.relationship_evolution as rel_mod

    def _boom(*a, **kw):
        raise RuntimeError("simulated read failure")

    with patch.object(rel_mod, "relationship_state", _boom):
        try:
            result = rel_mod.relationship_prompt_block()
            assert isinstance(result, str), "AT-13 FAIL: should return str on error"
        except Exception as exc:
            pytest.fail(f"AT-13 FAIL: relationship_prompt_block raised: {exc}")


# ── AT-14 ─────────────────────────────────────────────────────────────────────

def test_at14_server_wiring():
    server_path = os.path.join(ROOT, "server.py")
    with open(server_path, encoding="utf-8") as f:
        source = f.read()
    assert "relationship_prompt_block" in source, (
        "AT-14 FAIL: relationship_prompt_block not in server.py"
    )
    assert "memory.relationship_evolution" in source, (
        "AT-14 FAIL: memory.relationship_evolution import missing from server.py"
    )


# ── AT-15 ─────────────────────────────────────────────────────────────────────

def test_at15_py_compile_clean():
    files = [
        os.path.join(ROOT, "memory", "relationship_evolution.py"),
        os.path.join(ROOT, "server.py"),
    ]
    for path in files:
        try:
            py_compile.compile(path, doraise=True)
        except py_compile.PyCompileError as exc:
            pytest.fail(f"AT-15: {os.path.basename(path)} compile error: {exc}")
