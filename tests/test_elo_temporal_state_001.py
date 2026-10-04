"""
tests/test_elo_temporal_state_001.py — Temporal state / now vs past vs planned

AT-1  read_temporal_frame() with no signals, no intentions → empty frame, no crash
AT-2  recent_edge_hints populated from SPG signals
AT-3  total_signals counts all signals
AT-4  active_intentions populated when intentions store has ACTIVE entries
AT-5  deferred_intentions populated when intentions store has DEFERRED entries
AT-6  deferred_reasons match the stored reason
AT-7  temporal_state_prompt_block() returns "" when frame is empty
AT-8  temporal_state_prompt_block() returns non-empty block with signal data
AT-9  block contains TEMPORAL STATE header
AT-10 block distinguishes NOW vs PAUSED vs RECENT
AT-11 temporal_state_prompt_block() never raises (resilient)
AT-12 server.py wiring: temporal_state_prompt_block import present
AT-13 py_compile clean
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

import runtime.temporal_state as ts_mod
from runtime.temporal_state import (
    read_temporal_frame,
    temporal_state_prompt_block,
    TemporalFrame,
    RECENT_SIGNALS_N,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _write_signals(path: Path, signals: list[dict]) -> None:
    with open(path, "w") as f:
        for s in signals:
            f.write(json.dumps(s) + "\n")


def _signal(edge: str, sig_type: str = "memory_write", ts: float = 1700000000.0) -> dict:
    return {"ts": ts, "signal_type": sig_type, "edge_hint": edge, "context_tags": [], "significance": {}}


# ── AT-1 ──────────────────────────────────────────────────────────────────────

def test_at1_no_data_returns_empty_frame(tmp_path):
    with patch.object(ts_mod, "_SIGNALS", tmp_path / "nonexistent.jsonl"):
        frame = read_temporal_frame()
    assert isinstance(frame, TemporalFrame), "AT-1: must return TemporalFrame"
    assert frame.is_empty, "AT-1: frame with no data should be empty"


# ── AT-2 ──────────────────────────────────────────────────────────────────────

def test_at2_recent_edge_hints_from_signals(tmp_path):
    path = tmp_path / "spg.jsonl"
    signals = [_signal("close", ts=1700000000.0 + i) for i in range(5)]
    signals += [_signal("reflect", ts=1700000000.0 + 5 + i) for i in range(3)]
    _write_signals(path, signals)
    with patch.object(ts_mod, "_SIGNALS", path):
        frame = read_temporal_frame()
    assert "reflect" in frame.recent_edge_hints, (
        f"AT-2: recent edge hints should contain 'reflect', got {frame.recent_edge_hints}"
    )


# ── AT-3 ──────────────────────────────────────────────────────────────────────

def test_at3_total_signals_counted(tmp_path):
    path = tmp_path / "spg.jsonl"
    _write_signals(path, [_signal("close", ts=1700000000.0 + i) for i in range(25)])
    with patch.object(ts_mod, "_SIGNALS", path):
        frame = read_temporal_frame()
    assert frame.total_signals == 25, (
        f"AT-3: total_signals should be 25, got {frame.total_signals}"
    )


# ── AT-4 ──────────────────────────────────────────────────────────────────────

def test_at4_active_intentions_populated():
    mock_active = ["Build the novelty detector", "Review SPG signals"]
    mock_deferred = []

    def _mock_open():
        from dataclasses import dataclass

        @dataclass
        class MockInt:
            text: str
            status: str
            deferred_reason: str = ""

        return [MockInt(text=t, status="ACTIVE") for t in mock_active]

    with patch("runtime.temporal_state._read_intentions", return_value=(mock_active, [], [], [])):
        frame = read_temporal_frame()

    assert frame.has_active, "AT-4: has_active should be True when intentions are ACTIVE"
    assert len(frame.active_intentions) == 2, (
        f"AT-4: expected 2 active intentions, got {len(frame.active_intentions)}"
    )
    assert "Build the novelty detector" in frame.active_intentions


# ── AT-5 ──────────────────────────────────────────────────────────────────────

def test_at5_deferred_intentions_populated():
    deferred_texts = ["Wire relationship_faculty to server"]
    deferred_reasons = ["paused to handle higher-priority task"]

    with patch("runtime.temporal_state._read_intentions",
               return_value=([], deferred_texts, deferred_reasons, [])):
        frame = read_temporal_frame()

    assert frame.has_deferred, "AT-5: has_deferred should be True"
    assert frame.deferred_intentions[0] == "Wire relationship_faculty to server"


# ── AT-6 ──────────────────────────────────────────────────────────────────────

def test_at6_deferred_reasons_match():
    deferred_texts = ["Build the test suite"]
    deferred_reasons = ["waiting for requirements to stabilise"]

    with patch("runtime.temporal_state._read_intentions",
               return_value=([], deferred_texts, deferred_reasons, [])):
        frame = read_temporal_frame()

    assert "waiting for requirements" in frame.deferred_reasons[0], (
        f"AT-6: deferred reason should match, got {frame.deferred_reasons}"
    )


# ── AT-7 ──────────────────────────────────────────────────────────────────────

def test_at7_prompt_block_empty_when_frame_empty(tmp_path):
    with patch.object(ts_mod, "_SIGNALS", tmp_path / "nonexistent.jsonl"):
        block = temporal_state_prompt_block()
    assert block == "", (
        f"AT-7: empty frame should produce empty block, got {block[:80]!r}"
    )


# ── AT-8 ──────────────────────────────────────────────────────────────────────

def test_at8_prompt_block_non_empty_with_signals(tmp_path):
    path = tmp_path / "spg.jsonl"
    _write_signals(path, [_signal("close", ts=1700000000.0 + i) for i in range(15)])
    with patch.object(ts_mod, "_SIGNALS", path):
        block = temporal_state_prompt_block()
    assert block, "AT-8: with 15 signals, prompt block should be non-empty"


# ── AT-9 ──────────────────────────────────────────────────────────────────────

def test_at9_block_contains_temporal_state_header(tmp_path):
    path = tmp_path / "spg.jsonl"
    _write_signals(path, [_signal("close", ts=1700000000.0 + i) for i in range(10)])
    with patch.object(ts_mod, "_SIGNALS", path):
        block = temporal_state_prompt_block()
    assert "TEMPORAL STATE" in block, "AT-9: block must contain TEMPORAL STATE header"


# ── AT-10 ─────────────────────────────────────────────────────────────────────

def test_at10_block_makes_temporal_distinctions(tmp_path):
    path = tmp_path / "spg.jsonl"
    _write_signals(path, [_signal("close", ts=1700000000.0 + i) for i in range(10)])
    with patch("runtime.temporal_state._read_intentions",
               return_value=(["Active task A"], ["Deferred task B"], ["reason X"], [])):
        with patch.object(ts_mod, "_SIGNALS", path):
            block = temporal_state_prompt_block()
    assert "NOW" in block or "ACTIVE" in block, "AT-10: block must mention NOW/ACTIVE"
    assert "PAUSED" in block or "DEFERRED" in block, "AT-10: block must mention PAUSED/DEFERRED"
    assert "discussed" in block.lower() or "decided" in block.lower() or "implemented" in block.lower(), (
        "AT-10: block must reference the discussed/decided/implemented distinction"
    )


# ── AT-11 ─────────────────────────────────────────────────────────────────────

def test_at11_prompt_block_resilient():
    def _boom(*a, **kw):
        raise RuntimeError("forced failure")

    with patch.object(ts_mod, "read_temporal_frame", _boom):
        try:
            result = temporal_state_prompt_block()
            assert isinstance(result, str), "AT-11: must return str on error"
        except Exception as exc:
            pytest.fail(f"AT-11: temporal_state_prompt_block raised: {exc}")


# ── AT-12 ─────────────────────────────────────────────────────────────────────

def test_at12_server_wiring():
    server_path = os.path.join(ROOT, "server.py")
    with open(server_path, encoding="utf-8") as f:
        source = f.read()
    assert "temporal_state_prompt_block" in source, (
        "AT-12 FAIL: temporal_state_prompt_block not in server.py"
    )
    assert "runtime.temporal_state" in source, (
        "AT-12 FAIL: runtime.temporal_state import missing from server.py"
    )


# ── AT-13 ─────────────────────────────────────────────────────────────────────

def test_at13_py_compile_clean():
    files = [
        os.path.join(ROOT, "runtime", "temporal_state.py"),
        os.path.join(ROOT, "server.py"),
    ]
    for path in files:
        try:
            py_compile.compile(path, doraise=True)
        except py_compile.PyCompileError as exc:
            pytest.fail(f"AT-13: {os.path.basename(path)} compile error: {exc}")
