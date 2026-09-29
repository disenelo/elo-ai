"""
tests/test_elo_silence_faculty_001.py — Silence Faculty

IS ELO: — Capable of Silence?
  can eLo decide not to respond?
  can eLo decide that no explanation is necessary?
  can eLo resist the pressure to always produce content?

THE CAUSAL CHAIN (what this module proves):
  edge_hint = 'silence' → read_silence() → SilenceRead.is_silence_turn=True
  → silence_faculty_prompt_block() → [SILENCE PERMISSION] block
  → LLM reads block → produces less or no content

AT-1  read_silence() with no file → stable default (no crash)
AT-2  read_silence() with edge_hint='silence' → is_silence_turn=True
AT-3  read_silence() with edge_hint='close' → is_silence_turn=False
AT-4  read_silence() with silence rate > SILENCE_RATE_WARN → should_warn=True
AT-5  read_silence() with silence rate > SILENCE_RATE_CALL → should_call=True
AT-6  read_silence() with low silence rate → should_warn=False, should_call=False
AT-7  silence_faculty_prompt_block() returns "" when no silence and no warning
AT-8  silence_faculty_prompt_block() returns non-empty when edge_hint='silence'
AT-9  silence_faculty_prompt_block() block contains SILENCE PERMISSION header
AT-10 silence_faculty_prompt_block() returns non-empty when should_warn is True
AT-11 silence_faculty_prompt_block() never raises (resilient)
AT-12 CAUSAL PROOF: switching edge_hint from 'close' to 'silence' changes block
AT-13 server.py wired: silence_faculty_prompt_block import present
AT-14 py_compile clean
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

import runtime.silence_faculty as sf_mod
from runtime.silence_faculty import (
    read_silence,
    silence_faculty_prompt_block,
    SilenceRead,
    SILENCE_RATE_WARN,
    SILENCE_RATE_CALL,
    RECENT_N,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _write_signals(path: Path, edges: list[str]) -> None:
    with open(path, "w") as f:
        for i, edge in enumerate(edges):
            f.write(json.dumps({"ts": 1700000000.0 + i, "edge_hint": edge}) + "\n")


# ── AT-1 ──────────────────────────────────────────────────────────────────────

def test_at1_no_file_stable_default(tmp_path):
    result = read_silence(edge_hint="close", signals_path=tmp_path / "nonexistent.jsonl")
    assert isinstance(result, SilenceRead), "AT-1: must return SilenceRead"
    assert result.recent_silence_rate == 0.0, "AT-1: no file → rate should be 0.0"
    assert not result.should_warn, "AT-1: no file → should_warn must be False"


# ── AT-2 ──────────────────────────────────────────────────────────────────────

def test_at2_silence_edge_hint_detected(tmp_path):
    path = tmp_path / "spg.jsonl"
    _write_signals(path, ["close"] * 10)
    result = read_silence(edge_hint="silence", signals_path=path)
    assert result.is_silence_turn is True, (
        "AT-2: edge_hint='silence' must set is_silence_turn=True"
    )


# ── AT-3 ──────────────────────────────────────────────────────────────────────

def test_at3_non_silence_edge_hint_not_detected(tmp_path):
    path = tmp_path / "spg.jsonl"
    _write_signals(path, ["close"] * 10)
    result = read_silence(edge_hint="close", signals_path=path)
    assert result.is_silence_turn is False, (
        "AT-3: edge_hint='close' must NOT set is_silence_turn=True"
    )


# ── AT-4 ──────────────────────────────────────────────────────────────────────

def test_at4_high_silence_rate_triggers_warn(tmp_path):
    path = tmp_path / "spg.jsonl"
    # Build a dataset where silence rate just exceeds SILENCE_RATE_WARN
    n_silence = int(RECENT_N * (SILENCE_RATE_WARN + 0.05)) + 1  # clearly above threshold
    n_other   = RECENT_N - n_silence
    edges = ["close"] * n_other + ["silence"] * n_silence
    _write_signals(path, ["close"] * 50 + edges)  # 50 prefix to pad global
    result = read_silence(edge_hint="close", signals_path=path)
    assert result.should_warn, (
        f"AT-4: with {n_silence}/{RECENT_N} silence in recent window, should_warn must be True"
    )


# ── AT-5 ──────────────────────────────────────────────────────────────────────

def test_at5_very_high_silence_rate_triggers_call(tmp_path):
    path = tmp_path / "spg.jsonl"
    n_silence = int(RECENT_N * (SILENCE_RATE_CALL + 0.05)) + 1
    n_other   = RECENT_N - n_silence
    edges = ["close"] * n_other + ["silence"] * n_silence
    _write_signals(path, ["close"] * 50 + edges)
    result = read_silence(edge_hint="close", signals_path=path)
    assert result.should_call, (
        f"AT-5: with {n_silence}/{RECENT_N} silence in recent window, should_call must be True"
    )


# ── AT-6 ──────────────────────────────────────────────────────────────────────

def test_at6_low_silence_rate_no_warn(tmp_path):
    path = tmp_path / "spg.jsonl"
    # Only 1 silence in RECENT_N signals — well below threshold
    edges = ["close"] * (RECENT_N - 1) + ["silence"]
    _write_signals(path, edges)
    result = read_silence(edge_hint="close", signals_path=path)
    assert not result.should_warn, (
        f"AT-6: with 1/{RECENT_N} silence, should_warn must be False"
    )


# ── AT-7 ──────────────────────────────────────────────────────────────────────

def test_at7_block_empty_when_no_silence_signal(tmp_path):
    path = tmp_path / "spg.jsonl"
    _write_signals(path, ["close"] * 20)
    block = silence_faculty_prompt_block(edge_hint="close", signals_path=path)
    assert block == "", (
        f"AT-7: no silence signal → block should be empty, got: {block[:80]!r}"
    )


# ── AT-8 ──────────────────────────────────────────────────────────────────────

def test_at8_block_non_empty_for_silence_edge(tmp_path):
    path = tmp_path / "spg.jsonl"
    _write_signals(path, ["close"] * 20)
    block = silence_faculty_prompt_block(edge_hint="silence", signals_path=path)
    assert block, "AT-8: edge_hint='silence' must produce non-empty prompt block"


# ── AT-9 ──────────────────────────────────────────────────────────────────────

def test_at9_block_contains_silence_permission_header(tmp_path):
    path = tmp_path / "spg.jsonl"
    _write_signals(path, ["close"] * 20)
    block = silence_faculty_prompt_block(edge_hint="silence", signals_path=path)
    assert "SILENCE PERMISSION" in block, (
        "AT-9: block must contain SILENCE PERMISSION header"
    )


# ── AT-10 ─────────────────────────────────────────────────────────────────────

def test_at10_block_non_empty_when_warn_threshold_exceeded(tmp_path):
    path = tmp_path / "spg.jsonl"
    n_silence = int(RECENT_N * (SILENCE_RATE_WARN + 0.05)) + 1
    n_other   = RECENT_N - n_silence
    edges = ["close"] * n_other + ["silence"] * n_silence
    _write_signals(path, ["close"] * 50 + edges)
    block = silence_faculty_prompt_block(edge_hint="close", signals_path=path)
    assert block, (
        "AT-10: when should_warn is True, prompt block must be non-empty"
    )


# ── AT-11 ─────────────────────────────────────────────────────────────────────

def test_at11_prompt_block_resilient():
    def _boom(*a, **kw):
        raise RuntimeError("forced failure")

    with patch.object(sf_mod, "read_silence", _boom):
        try:
            result = silence_faculty_prompt_block(edge_hint="silence")
            assert isinstance(result, str), "AT-11: must return str on error"
        except Exception as exc:
            pytest.fail(f"AT-11: silence_faculty_prompt_block raised: {exc}")


# ── AT-12 ─────────────────────────────────────────────────────────────────────

def test_at12_causal_proof_edge_hint_changes_block(tmp_path):
    """
    THE CAUSAL PROOF: switching edge_hint from 'close' to 'silence' changes the block.
    This proves the silence faculty has a causal path from input to output.
    """
    path = tmp_path / "spg.jsonl"
    _write_signals(path, ["close"] * 20)

    block_close   = silence_faculty_prompt_block(edge_hint="close",   signals_path=path)
    block_silence = silence_faculty_prompt_block(edge_hint="silence", signals_path=path)

    assert block_close != block_silence, (
        "AT-12 CAUSAL PROOF: different edge_hint must produce different block"
    )
    assert not block_close, (
        "AT-12: 'close' edge with no silence history → must produce empty block"
    )
    assert block_silence, (
        "AT-12: 'silence' edge → must produce non-empty block"
    )


# ── AT-13 ─────────────────────────────────────────────────────────────────────

def test_at13_server_wired():
    server_path = os.path.join(ROOT, "server.py")
    with open(server_path, encoding="utf-8") as f:
        source = f.read()
    assert "silence_faculty_prompt_block" in source, (
        "AT-13: silence_faculty_prompt_block must be wired in server.py"
    )
    assert "runtime.silence_faculty" in source, (
        "AT-13: runtime.silence_faculty import must be in server.py"
    )


# ── AT-14 ─────────────────────────────────────────────────────────────────────

def test_at14_py_compile_clean():
    files = [
        os.path.join(ROOT, "runtime", "silence_faculty.py"),
        os.path.join(ROOT, "server.py"),
    ]
    for path in files:
        try:
            py_compile.compile(path, doraise=True)
        except py_compile.PyCompileError as exc:
            pytest.fail(f"AT-14: {os.path.basename(path)} compile error: {exc}")
