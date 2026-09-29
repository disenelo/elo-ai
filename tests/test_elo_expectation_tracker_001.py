"""
tests/test_elo_expectation_tracker_001.py — Expectation tracker / prediction error

AT-1  score_expectation() with no signals file → returns level=expected, no crash
AT-2  score_expectation() with synthetic data → high-frequency edge gets high expected_prob
AT-3  score_expectation() unseen edge_hint → prob=0.0, level=strong_surprise
AT-4  prediction_error = 1.0 - expected_prob (arithmetic invariant)
AT-5  top_expected lists only other edges, not the incoming one
AT-6  local context window shifts blended prediction
AT-7  expectation_prompt_block() returns "" with no history
AT-8  expectation_prompt_block() returns non-empty block for known edge
AT-9  expectation_prompt_block() includes ⚠ for strong_surprise edge
AT-10 expectation_prompt_block() never raises (resilient)
AT-11 invalidate() forces rebuild on next call
AT-12 score_expectation() with MIN_SIGNALS_FOR_MODEL -1 data → stable fallback
AT-13 server.py wiring: expectation_prompt_block import present
AT-14 py_compile clean
"""
from __future__ import annotations

import json
import os
import py_compile
import sys
from pathlib import Path

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import memory.expectation_tracker as et_mod
from memory.expectation_tracker import (
    score_expectation,
    expectation_prompt_block,
    invalidate,
    ExpectationViolation,
    MIN_SIGNALS_FOR_MODEL,
    SURPRISE_THRESHOLD,
    STRONG_THRESHOLD,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _write_signals(path: Path, signals: list[dict]) -> None:
    with open(path, "w") as f:
        for s in signals:
            f.write(json.dumps(s) + "\n")


def _signal(edge: str, ts: float = 1700000000.0) -> dict:
    return {"ts": ts, "signal_type": "memory_write", "edge_hint": edge,
            "context_tags": [], "significance": {}}


def _reset():
    et_mod._MODEL.invalidate()


# ── AT-1 ──────────────────────────────────────────────────────────────────────

def test_at1_no_signals_no_crash(tmp_path):
    _reset()
    v = score_expectation("close", signals_path=tmp_path / "nonexistent.jsonl")
    assert isinstance(v, ExpectationViolation)
    assert v.level == "expected"
    _reset()


# ── AT-2 ──────────────────────────────────────────────────────────────────────

def test_at2_high_freq_edge_high_prob(tmp_path):
    path = tmp_path / "spg.jsonl"
    # 80 close, then 10 reflect, then 10 more close
    # local window (last 20): 10 reflect + 10 close → local close = 0.5
    # global: close = 90/100 = 0.90
    # blended = 0.60 * 0.90 + 0.40 * 0.50 = 0.54 + 0.20 = 0.74
    signals = [_signal("close", 1700000000.0 + i) for i in range(80)]
    signals += [_signal("reflect", 1700000000.0 + 80 + i) for i in range(10)]
    signals += [_signal("close", 1700000000.0 + 90 + i) for i in range(10)]
    _write_signals(path, signals)
    _reset()
    v = score_expectation("close", signals_path=path)
    assert v.expected_prob > 0.50, (
        f"AT-2 FAIL: 90 close / 10 reflect (with 10 close at end) → expected_prob should be >0.50, got {v.expected_prob}"
    )
    _reset()


# ── AT-3 ──────────────────────────────────────────────────────────────────────

def test_at3_unseen_edge_strong_surprise(tmp_path):
    path = tmp_path / "spg.jsonl"
    signals = [_signal("close", 1700000000.0 + i) for i in range(50)]
    _write_signals(path, signals)
    _reset()
    v = score_expectation("challenge", signals_path=path)
    assert v.expected_prob == 0.0, (
        f"AT-3 FAIL: never-seen edge should have expected_prob=0.0, got {v.expected_prob}"
    )
    assert v.level == "strong_surprise", (
        f"AT-3 FAIL: never-seen edge should be strong_surprise, got {v.level}"
    )
    _reset()


# ── AT-4 ──────────────────────────────────────────────────────────────────────

def test_at4_prediction_error_arithmetic(tmp_path):
    path = tmp_path / "spg.jsonl"
    signals = [_signal("close", 1700000000.0 + i) for i in range(30)]
    signals += [_signal("reflect", 1700000000.0 + 30 + i) for i in range(20)]
    _write_signals(path, signals)
    _reset()
    for edge in ("close", "reflect", "answer"):
        v = score_expectation(edge, signals_path=path)
        # Allow for floating point: error ≈ 1.0 - prob (within rounding at 4dp)
        diff = abs(v.prediction_error - (1.0 - v.expected_prob))
        assert diff < 0.001, (
            f"AT-4 FAIL: error ({v.prediction_error}) != 1-prob ({1.0-v.expected_prob}) for {edge!r}"
        )
    _reset()


# ── AT-5 ──────────────────────────────────────────────────────────────────────

def test_at5_top_expected_excludes_incoming(tmp_path):
    path = tmp_path / "spg.jsonl"
    signals = (
        [_signal("close", 1700000000.0 + i) for i in range(60)] +
        [_signal("reflect", 1700000000.0 + 60 + i) for i in range(30)] +
        [_signal("answer", 1700000000.0 + 90 + i) for i in range(10)]
    )
    _write_signals(path, signals)
    _reset()
    v = score_expectation("close", signals_path=path)
    assert "close" not in v.top_expected, (
        f"AT-5 FAIL: top_expected must not include the incoming edge 'close', got {v.top_expected}"
    )
    _reset()


# ── AT-6 ──────────────────────────────────────────────────────────────────────

def test_at6_local_context_shifts_prediction(tmp_path):
    path = tmp_path / "spg.jsonl"
    # First 80 signals: mostly 'close'. Last 20: all 'reflect'.
    signals = [_signal("close", 1700000000.0 + i) for i in range(80)]
    signals += [_signal("reflect", 1700000000.0 + 80 + i) for i in range(20)]
    _write_signals(path, signals)
    _reset()

    # 'reflect' should have a boosted blended prob (all 20 recent signals are 'reflect')
    v = score_expectation("reflect", signals_path=path)
    # Local prob for reflect = 20/20 = 1.0 → blended boost
    # blended = 0.6 * 0.20 + 0.4 * 1.0 = 0.12 + 0.40 = 0.52
    assert v.expected_prob > 0.30, (
        f"AT-6 FAIL: after 20 recent 'reflect' signals, expected_prob should be >0.30, got {v.expected_prob}"
    )
    _reset()


# ── AT-7 ──────────────────────────────────────────────────────────────────────

def test_at7_prompt_block_empty_no_history(tmp_path):
    _reset()
    block = expectation_prompt_block("close", signals_path=tmp_path / "none.jsonl")
    assert block == "", (
        f"AT-7 FAIL: expected empty block with no history, got: {block[:80]!r}"
    )
    _reset()


# ── AT-8 ──────────────────────────────────────────────────────────────────────

def test_at8_prompt_block_non_empty_with_history(tmp_path):
    path = tmp_path / "spg.jsonl"
    signals = [_signal("close", 1700000000.0 + i) for i in range(50)]
    _write_signals(path, signals)
    _reset()
    block = expectation_prompt_block("close", signals_path=path)
    assert block, "AT-8 FAIL: expected non-empty block with 50-signal history"
    assert "LEARNED EXPECTATIONS" in block, "AT-8 FAIL: block must contain LEARNED EXPECTATIONS header"
    assert "close" in block, "AT-8 FAIL: block must reference 'close' as top pattern"
    _reset()


# ── AT-9 ──────────────────────────────────────────────────────────────────────

def test_at9_strong_surprise_flagged(tmp_path):
    path = tmp_path / "spg.jsonl"
    signals = [_signal("close", 1700000000.0 + i) for i in range(50)]
    _write_signals(path, signals)
    _reset()
    block = expectation_prompt_block("never_seen_in_history", signals_path=path)
    assert "PREDICTION ERROR" in block or "⚠" in block, (
        "AT-9 FAIL: strong_surprise turn must flag PREDICTION ERROR in block"
    )
    _reset()


# ── AT-10 ─────────────────────────────────────────────────────────────────────

def test_at10_prompt_block_resilient():
    from unittest.mock import patch

    def _boom(*a, **kw):
        raise RuntimeError("forced failure")

    with patch.object(et_mod._MODEL, "predict", _boom):
        try:
            result = et_mod.expectation_prompt_block("close")
            assert isinstance(result, str), "AT-10 FAIL: must return str on error"
        except Exception as exc:
            pytest.fail(f"AT-10 FAIL: expectation_prompt_block raised: {exc}")


# ── AT-11 ─────────────────────────────────────────────────────────────────────

def test_at11_invalidate_forces_rebuild(tmp_path):
    path = tmp_path / "spg.jsonl"
    signals = [_signal("close", 1700000000.0 + i) for i in range(20)]
    _write_signals(path, signals)
    _reset()

    # First build
    score_expectation("close", signals_path=path)
    assert et_mod._MODEL._built is True, "AT-11 FAIL: model should be built after first call"

    # Invalidate
    invalidate()
    assert et_mod._MODEL._built is False, "AT-11 FAIL: model should be un-built after invalidate"

    # Add more signals then rebuild
    with open(path, "a") as f:
        for i in range(20):
            f.write(json.dumps(_signal("answer", 1700000000.0 + 20 + i)) + "\n")

    v = score_expectation("answer", signals_path=path)
    assert isinstance(v, ExpectationViolation), "AT-11 FAIL: rebuild after invalidate must succeed"
    _reset()


# ── AT-12 ─────────────────────────────────────────────────────────────────────

def test_at12_insufficient_signals_stable_fallback(tmp_path):
    path = tmp_path / "spg.jsonl"
    # Write MIN_SIGNALS_FOR_MODEL - 1 signals (not enough to trust the model)
    signals = [_signal("close", 1700000000.0 + i) for i in range(MIN_SIGNALS_FOR_MODEL - 1)]
    _write_signals(path, signals)
    _reset()
    v = score_expectation("challenge", signals_path=path)
    # With insufficient data, should return a stable fallback
    assert isinstance(v, ExpectationViolation), "AT-12 FAIL: fallback must return ExpectationViolation"
    assert v.level == "expected", "AT-12 FAIL: insufficient data → stable 'expected' fallback"
    _reset()


# ── AT-13 ─────────────────────────────────────────────────────────────────────

def test_at13_server_wiring():
    server_path = os.path.join(ROOT, "server.py")
    with open(server_path, encoding="utf-8") as f:
        source = f.read()
    assert "expectation_prompt_block" in source, (
        "AT-13 FAIL: expectation_prompt_block not in server.py"
    )
    assert "memory.expectation_tracker" in source, (
        "AT-13 FAIL: memory.expectation_tracker import missing from server.py"
    )


# ── AT-14 ─────────────────────────────────────────────────────────────────────

def test_at14_py_compile_clean():
    files = [
        os.path.join(ROOT, "memory", "expectation_tracker.py"),
        os.path.join(ROOT, "server.py"),
    ]
    for path in files:
        try:
            py_compile.compile(path, doraise=True)
        except py_compile.PyCompileError as exc:
            pytest.fail(f"AT-14: {os.path.basename(path)} compile error: {exc}")
