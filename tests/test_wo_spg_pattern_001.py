"""
tests/test_wo_spg_pattern_001.py — WO-SPG-PATTERN-001
SPG Pattern Observer: real signal data → SPGObservation → prompt block.

AT-1  detect_patterns() returns observations (not empty — 12,817 signals exist)
AT-2  SPGObservation schema fields are correct
AT-3  EMERGING threshold: <3 occurrences → CANDIDATE; >=3 → EMERGING or ESTABLISHED
AT-4  ESTABLISHED threshold: >=20 occurrences → ESTABLISHED
AT-5  Pattern observation text is plain language (no interpretation/diagnosis)
AT-6  spg_prompt_block() returns non-empty string from real data
AT-7  spg_prompt_block() never raises (resilient to bad data / missing file)
AT-8  Server.py wiring: SPG block injection present in source
AT-9  py_compile clean on spg_observer.py and server.py
"""
from __future__ import annotations

import os
import sys
import py_compile

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from memory.spg_observer import (
    detect_patterns,
    top_observations,
    spg_prompt_block,
    SPGObservation,
    STATUS_CANDIDATE,
    STATUS_EMERGING,
    STATUS_ESTABLISHED,
    _MIN_EMERGING,
    _MIN_ESTABLISHED,
    _action_patterns,
    _context_tag_patterns,
    _continuity_patterns,
)


# ── AT-1: detect_patterns returns observations ─────────────────────────────────

def test_at1_detect_patterns_returns_observations():
    """12,817 signals exist — detect_patterns() must return at least 1 observation."""
    obs = detect_patterns()
    assert len(obs) > 0, (
        "AT-1 FAIL: detect_patterns() returned 0 observations. "
        "12,817 signals are logged — at least action patterns must be detectable."
    )


# ── AT-2: SPGObservation schema ────────────────────────────────────────────────

def test_at2_spg_observation_schema():
    """SPGObservation must carry all required fields per WO spec."""
    obs = detect_patterns()
    assert obs, "AT-2 FAIL: no observations to inspect"
    first = obs[0]
    assert isinstance(first.pattern_id, str) and first.pattern_id, "pattern_id missing"
    assert isinstance(first.pattern_type, str) and first.pattern_type, "pattern_type missing"
    assert isinstance(first.observation, str) and first.observation, "observation missing"
    assert isinstance(first.evidence_keys, list), "evidence_keys must be a list"
    assert isinstance(first.recurrence_count, int), "recurrence_count must be int"
    assert isinstance(first.significance_score, float), "significance_score must be float"
    assert first.status in (STATUS_CANDIDATE, STATUS_EMERGING, STATUS_ESTABLISHED, "DECLINING"), (
        f"status must be a valid status string, got {first.status!r}"
    )
    # as_dict and as_prompt_line must work
    d = first.as_dict()
    assert "pattern_id" in d and "observation" in d
    line = first.as_prompt_line()
    assert isinstance(line, str) and len(line) > 10


# ── AT-3: EMERGING threshold ───────────────────────────────────────────────────

def test_at3_emerging_threshold():
    """
    Patterns with < _MIN_EMERGING (3) occurrences must NOT appear in output.
    Patterns with >= _MIN_EMERGING must be at least EMERGING.
    """
    # Build synthetic signals to test threshold
    low_signals = [
        {"edge_hint": "rare_action", "signal_type": "memory_write", "context_tags": [], "ts": 1.0}
        for _ in range(_MIN_EMERGING - 1)   # 2 occurrences — below threshold
    ]
    emerging_signals = [
        {"edge_hint": "common_action", "signal_type": "memory_write", "context_tags": [], "ts": float(i)}
        for i in range(_MIN_EMERGING)   # exactly 3 — should be EMERGING
    ]

    low_obs = _action_patterns(low_signals)
    emerging_obs = _action_patterns(emerging_signals)

    assert not low_obs, (
        f"AT-3 FAIL: {len(low_obs)} observations from {_MIN_EMERGING-1} signals — "
        f"below threshold ({_MIN_EMERGING}). SPG must not flag single-session coincidences."
    )

    assert emerging_obs, (
        f"AT-3 FAIL: 0 observations from {_MIN_EMERGING} signals — "
        "should be EMERGING at minimum threshold."
    )
    assert emerging_obs[0].status in (STATUS_EMERGING, STATUS_ESTABLISHED)


# ── AT-4: ESTABLISHED threshold ───────────────────────────────────────────────

def test_at4_established_threshold():
    """Patterns with >= _MIN_ESTABLISHED (20) occurrences must be ESTABLISHED."""
    established_signals = [
        {"edge_hint": "reflect", "signal_type": "memory_write", "context_tags": [], "ts": float(i)}
        for i in range(_MIN_ESTABLISHED)   # exactly 20
    ]
    obs = _action_patterns(established_signals)
    assert obs, "AT-4 FAIL: no observation from 20 signals"
    assert obs[0].status == STATUS_ESTABLISHED, (
        f"AT-4 FAIL: 20 occurrences should be ESTABLISHED, got {obs[0].status!r}"
    )


# ── AT-5: Observations are plain language — no diagnosis/interpretation ────────

def test_at5_observations_are_not_interpretations():
    """
    SPG observes — it does not diagnose. Per David L3:
    'David switches projects when blocked' — OK
    'David has commitment issues' — FORBIDDEN

    Check that observations don't contain diagnostic/clinical language.
    """
    FORBIDDEN_WORDS = [
        "commitment issue", "anxiety", "avoidance", "disorder",
        "problem", "dysfunction", "patholog", "symptom",
        "defect", "inability", "failure to",
    ]
    obs = detect_patterns()
    for o in obs:
        text = o.observation.lower()
        for fw in FORBIDDEN_WORDS:
            assert fw not in text, (
                f"AT-5 FAIL: SPGObservation contains diagnostic language '{fw}': "
                f"{o.observation!r}. SPG observes, it does not diagnose."
            )


# ── AT-6: spg_prompt_block returns non-empty string ───────────────────────────

def test_at6_spg_prompt_block_returns_content():
    """spg_prompt_block() must return a non-empty string from real data."""
    block = spg_prompt_block(n=3)
    assert isinstance(block, str), "AT-6 FAIL: spg_prompt_block() did not return a string"
    assert len(block) > 20, (
        f"AT-6 FAIL: spg_prompt_block() returned too-short string ({len(block)} chars): {block!r}"
    )
    assert "[SPG" in block, (
        f"AT-6 FAIL: spg_prompt_block() missing [SPG] header: {block!r}"
    )


# ── AT-7: spg_prompt_block is resilient ───────────────────────────────────────

def test_at7_spg_prompt_block_resilient_to_bad_data():
    """spg_prompt_block() must never raise — bad paths return empty string."""
    from unittest.mock import patch
    import memory.spg_observer as obs_mod

    # Simulate missing file
    with patch.object(obs_mod, "_SIGNALS", obs_mod._ROOT / "data" / "does_not_exist.jsonl"):
        result = spg_prompt_block(n=3)
        assert isinstance(result, str), "AT-7 FAIL: spg_prompt_block() raised instead of returning ''"


# ── AT-8: Server.py wiring ────────────────────────────────────────────────────

def test_at8_server_wiring():
    """SPG block injection must be present in server.py source."""
    server_path = os.path.join(ROOT, "server.py")
    with open(server_path, encoding="utf-8") as f:
        source = f.read()
    assert "spg_observer" in source, (
        "AT-8 FAIL: 'spg_observer' not found in server.py — SPG block is not wired."
    )
    assert "spg_prompt_block" in source, (
        "AT-8 FAIL: 'spg_prompt_block' not found in server.py — SPG block call missing."
    )


# ── AT-9: py_compile clean ────────────────────────────────────────────────────

def test_at9_py_compile_clean():
    files = [
        os.path.join(ROOT, "memory", "spg_observer.py"),
        os.path.join(ROOT, "server.py"),
    ]
    for path in files:
        try:
            py_compile.compile(path, doraise=True)
        except py_compile.PyCompileError as exc:
            pytest.fail(f"AT-9 FAIL: {os.path.basename(path)} does not compile: {exc}")
