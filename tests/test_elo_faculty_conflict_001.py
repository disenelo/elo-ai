"""
tests/test_elo_faculty_conflict_001.py — Faculty Conflict Detection

IS ELO: — Internally Consistent?
  can two faculties disagree about something?
  if they disagree, does Executive resolve the conflict?
  can one faculty silently override another?

IS ELO: — One Brain?
  is there actually one Executive?
  can a faculty independently decide what eLo should do?

THE CAUSAL CHAIN:
  assembled system prompt (with contradictory faculty blocks)
  → detect_conflicts() → FacultyConflict list
  → faculty_conflict_prompt_block() → [FACULTY CONFLICT] block
  → LLM / Executive reads the conflict → resolves consciously rather than silently defaulting

AT-1  detect_conflicts() returns empty list on empty prompt (no crash)
AT-2  detect_conflicts() returns empty list when no conflict present
AT-3  detect_conflicts() detects silence_vs_novelty conflict
AT-4  detect_conflicts() does NOT flag silence alone (no conflict without counterpart)
AT-5  detect_conflicts() does NOT flag novelty alone (no conflict without counterpart)
AT-6  detect_conflicts() detects active_vs_deferred conflict
AT-7  detect_conflicts() returns empty when only active (no deferred counterpart)
AT-8  faculty_conflict_prompt_block() returns "" when no conflict
AT-9  faculty_conflict_prompt_block() returns non-empty when conflict present
AT-10 block contains [FACULTY CONFLICT] header
AT-11 block names both conflicting faculties
AT-12 block instructs Executive to resolve (not let one silently win)
AT-13 CAUSAL PROOF: adding silence signal to a prompt with novelty signal changes block
AT-14 faculty_conflict_prompt_block() never raises (resilient)
AT-15 server.py wired: faculty_conflict_prompt_block import present
AT-16 py_compile clean
"""
from __future__ import annotations

import os
import py_compile
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from runtime.faculty_conflict_detector import (
    detect_conflicts,
    faculty_conflict_prompt_block,
    FacultyConflict,
)


# ── Fixtures / helpers ────────────────────────────────────────────────────────

SILENCE_BLOCK = """[SILENCE PERMISSION — this is a moment where less is more]
  The current signal is: SILENCE.
  do not fill the space.
  Permission granted: you do not have to speak."""

NOVELTY_BLOCK = """[NOVEL SIGNAL — something new]
  This edge_hint has not been seen before.
  significant enough to surface.
  Engage with this input."""

ACTIVE_BLOCK = """[TEMPORAL STATE]
  [NOW] ACTIVE: Build the silence faculty
  Recent interaction signals..."""

DEFERRED_BLOCK = """[TEMPORAL STATE]
  [PAUSED] DEFERRED: Build the silence faculty
  Paused to handle higher-priority task."""

NEUTRAL_BLOCK = """[RELATIONSHIP EVOLUTION]
  Stage: forming. Trend: stable.
  Interact naturally."""


# ── AT-1 ──────────────────────────────────────────────────────────────────────

def test_at1_empty_prompt_no_crash():
    result = detect_conflicts("")
    assert isinstance(result, list), "AT-1: detect_conflicts must return list"
    assert len(result) == 0, "AT-1: empty prompt must produce no conflicts"


# ── AT-2 ──────────────────────────────────────────────────────────────────────

def test_at2_no_conflict_in_neutral_prompt():
    result = detect_conflicts(NEUTRAL_BLOCK)
    assert len(result) == 0, (
        f"AT-2: neutral block must produce no conflicts, got {result}"
    )


# ── AT-3 ──────────────────────────────────────────────────────────────────────

def test_at3_detects_silence_vs_novelty():
    combined = SILENCE_BLOCK + "\n\n" + NOVELTY_BLOCK
    conflicts = detect_conflicts(combined)
    types = [c.conflict_type for c in conflicts]
    assert "silence_vs_novelty" in types, (
        f"AT-3: silence+novelty must produce silence_vs_novelty conflict, got {types}"
    )


# ── AT-4 ──────────────────────────────────────────────────────────────────────

def test_at4_silence_alone_no_conflict():
    conflicts = detect_conflicts(SILENCE_BLOCK)
    types = [c.conflict_type for c in conflicts]
    assert "silence_vs_novelty" not in types, (
        "AT-4: silence alone (no novelty block) must NOT produce silence_vs_novelty"
    )


# ── AT-5 ──────────────────────────────────────────────────────────────────────

def test_at5_novelty_alone_no_conflict():
    conflicts = detect_conflicts(NOVELTY_BLOCK)
    types = [c.conflict_type for c in conflicts]
    assert "silence_vs_novelty" not in types, (
        "AT-5: novelty alone (no silence block) must NOT produce silence_vs_novelty"
    )


# ── AT-6 ──────────────────────────────────────────────────────────────────────

def test_at6_detects_active_vs_deferred():
    combined = ACTIVE_BLOCK + "\n\n" + DEFERRED_BLOCK
    conflicts = detect_conflicts(combined)
    types = [c.conflict_type for c in conflicts]
    assert "active_vs_deferred" in types, (
        f"AT-6: ACTIVE+DEFERRED must produce active_vs_deferred conflict, got {types}"
    )


# ── AT-7 ──────────────────────────────────────────────────────────────────────

def test_at7_active_alone_no_temporal_conflict():
    conflicts = detect_conflicts(ACTIVE_BLOCK)
    types = [c.conflict_type for c in conflicts]
    assert "active_vs_deferred" not in types, (
        "AT-7: ACTIVE alone (no DEFERRED) must NOT produce active_vs_deferred"
    )


# ── AT-8 ──────────────────────────────────────────────────────────────────────

def test_at8_block_empty_when_no_conflict():
    block = faculty_conflict_prompt_block(NEUTRAL_BLOCK)
    assert block == "", (
        f"AT-8: no conflict → block must be empty, got: {block[:80]!r}"
    )


# ── AT-9 ──────────────────────────────────────────────────────────────────────

def test_at9_block_non_empty_when_conflict_present():
    combined = SILENCE_BLOCK + "\n\n" + NOVELTY_BLOCK
    block = faculty_conflict_prompt_block(combined)
    assert block, "AT-9: silence_vs_novelty conflict → block must be non-empty"


# ── AT-10 ─────────────────────────────────────────────────────────────────────

def test_at10_block_has_faculty_conflict_header():
    combined = SILENCE_BLOCK + "\n\n" + NOVELTY_BLOCK
    block = faculty_conflict_prompt_block(combined)
    assert "FACULTY CONFLICT" in block, (
        "AT-10: block must contain FACULTY CONFLICT header"
    )


# ── AT-11 ─────────────────────────────────────────────────────────────────────

def test_at11_block_names_both_faculties():
    combined = SILENCE_BLOCK + "\n\n" + NOVELTY_BLOCK
    block = faculty_conflict_prompt_block(combined)
    assert "silence_faculty" in block, (
        "AT-11: block must name silence_faculty as one conflicting faculty"
    )
    assert "novelty_detector" in block, (
        "AT-11: block must name novelty_detector as the other conflicting faculty"
    )


# ── AT-12 ─────────────────────────────────────────────────────────────────────

def test_at12_block_instructs_executive_to_resolve():
    combined = SILENCE_BLOCK + "\n\n" + NOVELTY_BLOCK
    block = faculty_conflict_prompt_block(combined)
    assert "Executive" in block or "resolve" in block.lower(), (
        "AT-12: block must instruct Executive to resolve the conflict"
    )
    assert "silently" in block.lower() or "override" in block.lower(), (
        "AT-12: block must warn against silent override"
    )


# ── AT-13 ─────────────────────────────────────────────────────────────────────

def test_at13_causal_proof_adding_silence_changes_block():
    """
    THE CAUSAL PROOF: adding a silence signal to a prompt that already has a novelty
    signal produces a conflict block. Without the silence signal, no conflict.

    This proves the conflict detector has causal reality:
      input state → detected → behaviour change (conflict block injected)
    """
    novelty_only = NOVELTY_BLOCK
    silence_and_novelty = SILENCE_BLOCK + "\n\n" + NOVELTY_BLOCK

    block_without_silence = faculty_conflict_prompt_block(novelty_only)
    block_with_silence    = faculty_conflict_prompt_block(silence_and_novelty)

    assert block_without_silence == "", (
        "AT-13 CAUSAL PROOF: novelty alone must NOT produce conflict block"
    )
    assert block_with_silence, (
        "AT-13 CAUSAL PROOF: silence+novelty must produce conflict block"
    )
    assert block_without_silence != block_with_silence, (
        "AT-13: adding silence signal must change the output block"
    )


# ── AT-14 ─────────────────────────────────────────────────────────────────────

def test_at14_prompt_block_resilient():
    """faculty_conflict_prompt_block() must never raise."""
    from unittest.mock import patch
    import runtime.faculty_conflict_detector as fcd_mod

    def _boom(*a, **kw):
        raise RuntimeError("forced failure")

    with patch.object(fcd_mod, "detect_conflicts", _boom):
        try:
            result = faculty_conflict_prompt_block("anything")
            assert isinstance(result, str), "AT-14: must return str on error"
        except Exception as exc:
            pytest.fail(f"AT-14: faculty_conflict_prompt_block raised: {exc}")


# ── AT-15 ─────────────────────────────────────────────────────────────────────

def test_at15_server_wired():
    server_path = os.path.join(ROOT, "server.py")
    with open(server_path, encoding="utf-8") as f:
        source = f.read()
    assert "faculty_conflict_prompt_block" in source, (
        "AT-15: faculty_conflict_prompt_block must be wired in server.py"
    )
    assert "faculty_conflict_detector" in source, (
        "AT-15: runtime.faculty_conflict_detector must be in server.py"
    )


# ── AT-16 ─────────────────────────────────────────────────────────────────────

def test_at16_py_compile_clean():
    files = [
        os.path.join(ROOT, "runtime", "faculty_conflict_detector.py"),
        os.path.join(ROOT, "server.py"),
    ]
    for path in files:
        try:
            py_compile.compile(path, doraise=True)
        except py_compile.PyCompileError as exc:
            pytest.fail(f"AT-16: {os.path.basename(path)} compile error: {exc}")
