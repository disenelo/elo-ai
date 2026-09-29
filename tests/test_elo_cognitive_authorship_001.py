"""
tests/test_elo_cognitive_authorship_001.py — Cognitive Authorship Tracking

IS ELO: — Capable of Ownership?
  can eLo distinguish "I did" from "you did" from "we did"?
  can eLo avoid claiming credit for user-directed actions?
  can eLo avoid falsely attributing its own initiatives to the user?

THE CAUSAL CHAIN:
  decision_journal.jsonl (trigger field) → _classify_origin()
  → CognitiveAuthorshipRead (elo_count, user_count, collab_count)
  → cognitive_authorship_prompt_block() → [COGNITIVE AUTHORSHIP] block
  → LLM correctly attributes "I / you / we"

AT-1  read_cognitive_authorship() with no file → no crash, empty state
AT-2  trigger "user request" → classified as user_directed
AT-3  trigger "initiative" → classified as elo_origin
AT-4  trigger "build" → classified as collaborative (when no user/request in intent)
AT-5  default trigger (empty) → classified as user_directed (conservative)
AT-6  CognitiveAuthorshipRead.has_elo_actions True when elo_count > 0
AT-7  CognitiveAuthorshipRead.has_elo_actions False when elo_count == 0
AT-8  cognitive_authorship_prompt_block() returns "" when no eLo-origin actions
AT-9  cognitive_authorship_prompt_block() returns non-empty when eLo actions exist
AT-10 block contains [COGNITIVE AUTHORSHIP] header
AT-11 block labels eLo-origin actions as ELO-ORIGIN
AT-12 block contains attribution rule (I / you / we)
AT-13 CAUSAL PROOF: changing trigger from user_request to initiative changes the block
AT-14 cognitive_authorship_prompt_block() never raises (resilient)
AT-15 server.py wired: cognitive_authorship_prompt_block import present
AT-16 py_compile clean
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

import runtime.cognitive_authorship as ca_mod
from runtime.cognitive_authorship import (
    read_cognitive_authorship,
    cognitive_authorship_prompt_block,
    CognitiveAuthorshipRead,
    AttributedAction,
    _classify_origin,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _write_journal(path: Path, entries: list[dict]) -> None:
    with open(path, "w") as f:
        for entry in entries:
            f.write(json.dumps(entry) + "\n")


def _entry(trigger: str, action: str = "answer", intent: str = "inquiry", turn: str = "hi") -> dict:
    return {
        "ts": 1789000000.0,
        "turn": turn,
        "action": action,
        "trigger": trigger,
        "intent": intent,
        "tone": "NEUTRAL",
        "outcome": "success",
    }


# ── AT-1 ──────────────────────────────────────────────────────────────────────

def test_at1_no_file_stable_default(tmp_path):
    state = read_cognitive_authorship(journal_path=tmp_path / "nonexistent.jsonl")
    assert isinstance(state, CognitiveAuthorshipRead), "AT-1: must return CognitiveAuthorshipRead"
    assert state.total_analysed == 0, "AT-1: no file → 0 analysed"
    assert not state.has_elo_actions, "AT-1: no file → no eLo actions"


# ── AT-2 ──────────────────────────────────────────────────────────────────────

def test_at2_user_request_trigger_classified_user_directed():
    origin = _classify_origin("user request", "answer", "inquiry")
    assert origin == "user_directed", (
        f"AT-2: 'user request' trigger must → user_directed, got {origin!r}"
    )


# ── AT-3 ──────────────────────────────────────────────────────────────────────

def test_at3_initiative_trigger_classified_elo_origin():
    origin = _classify_origin("initiative", "build", "creation")
    assert origin == "elo_origin", (
        f"AT-3: 'initiative' trigger must → elo_origin, got {origin!r}"
    )


# ── AT-4 ──────────────────────────────────────────────────────────────────────

def test_at4_build_trigger_classified_collaborative():
    origin = _classify_origin("build", "build", "creation")
    assert origin == "collaborative", (
        f"AT-4: 'build' trigger (no user/request in intent) must → collaborative, got {origin!r}"
    )


# ── AT-5 ──────────────────────────────────────────────────────────────────────

def test_at5_empty_trigger_defaults_user_directed():
    origin = _classify_origin("", "", "")
    assert origin == "user_directed", (
        f"AT-5: empty trigger must default to user_directed (conservative), got {origin!r}"
    )


# ── AT-6 ──────────────────────────────────────────────────────────────────────

def test_at6_has_elo_actions_true_when_elo_count_gt_0(tmp_path):
    path = tmp_path / "journal.jsonl"
    _write_journal(path, [_entry("initiative", "build")])
    state = read_cognitive_authorship(journal_path=path)
    assert state.has_elo_actions, "AT-6: one initiative entry → has_elo_actions must be True"
    assert state.elo_count == 1, f"AT-6: elo_count must be 1, got {state.elo_count}"


# ── AT-7 ──────────────────────────────────────────────────────────────────────

def test_at7_has_elo_actions_false_when_all_user_directed(tmp_path):
    path = tmp_path / "journal.jsonl"
    _write_journal(path, [
        _entry("user request", "answer"),
        _entry("pure greeting", "celebrate"),
        _entry("factual question", "answer"),
    ])
    state = read_cognitive_authorship(journal_path=path)
    assert not state.has_elo_actions, (
        "AT-7: all user_directed entries → has_elo_actions must be False"
    )


# ── AT-8 ──────────────────────────────────────────────────────────────────────

def test_at8_block_empty_when_no_elo_actions(tmp_path):
    path = tmp_path / "journal.jsonl"
    _write_journal(path, [_entry("user request", "answer")])
    block = cognitive_authorship_prompt_block(journal_path=path)
    assert block == "", (
        f"AT-8: no eLo-origin actions → block must be empty, got: {block[:80]!r}"
    )


# ── AT-9 ──────────────────────────────────────────────────────────────────────

def test_at9_block_non_empty_when_elo_actions_exist(tmp_path):
    path = tmp_path / "journal.jsonl"
    _write_journal(path, [_entry("initiative", "build")])
    block = cognitive_authorship_prompt_block(journal_path=path)
    assert block, "AT-9: eLo-origin action → block must be non-empty"


# ── AT-10 ─────────────────────────────────────────────────────────────────────

def test_at10_block_has_cognitive_authorship_header(tmp_path):
    path = tmp_path / "journal.jsonl"
    _write_journal(path, [_entry("initiative", "build")])
    block = cognitive_authorship_prompt_block(journal_path=path)
    assert "COGNITIVE AUTHORSHIP" in block, "AT-10: block must contain COGNITIVE AUTHORSHIP header"


# ── AT-11 ─────────────────────────────────────────────────────────────────────

def test_at11_block_labels_elo_actions_as_elo_origin(tmp_path):
    path = tmp_path / "journal.jsonl"
    _write_journal(path, [_entry("initiative", "build")])
    block = cognitive_authorship_prompt_block(journal_path=path)
    assert "ELO-ORIGIN" in block, "AT-11: block must label eLo-origin actions as [ELO-ORIGIN]"


# ── AT-12 ─────────────────────────────────────────────────────────────────────

def test_at12_block_contains_attribution_rule(tmp_path):
    path = tmp_path / "journal.jsonl"
    _write_journal(path, [_entry("initiative", "build")])
    block = cognitive_authorship_prompt_block(journal_path=path)
    assert "Rule" in block or "rule" in block.lower(), (
        "AT-12: block must contain attribution rule"
    )
    assert "you" in block.lower(), "AT-12: block must mention 'you' (for user-directed label)"
    assert "we" in block.lower(), "AT-12: block must mention 'we' (for collaborative label)"


# ── AT-13 ─────────────────────────────────────────────────────────────────────

def test_at13_causal_proof_trigger_change_changes_block(tmp_path):
    """
    THE CAUSAL PROOF: changing trigger from user-directed to initiative changes the block.
    user_request trigger → empty block (no eLo actions to surface).
    initiative trigger   → non-empty block (eLo-origin detected, attribution needed).
    This proves cognitive authorship has causal reality:
      stored trigger in journal → classification → block injected → LLM attribution changes.
    """
    path_user = tmp_path / "user_journal.jsonl"
    path_elo  = tmp_path / "elo_journal.jsonl"

    _write_journal(path_user, [_entry("user request", "answer")])
    _write_journal(path_elo,  [_entry("initiative",   "build")])

    block_user_directed = cognitive_authorship_prompt_block(journal_path=path_user)
    block_elo_origin    = cognitive_authorship_prompt_block(journal_path=path_elo)

    assert block_user_directed == "", (
        "AT-13 CAUSAL PROOF: user_request trigger → block must be empty (no eLo actions)"
    )
    assert block_elo_origin, (
        "AT-13 CAUSAL PROOF: initiative trigger → block must be non-empty"
    )
    assert block_user_directed != block_elo_origin, (
        "AT-13: changing trigger must change the cognitive authorship block"
    )


# ── AT-14 ─────────────────────────────────────────────────────────────────────

def test_at14_prompt_block_resilient():
    """cognitive_authorship_prompt_block() must never raise."""
    from unittest.mock import patch
    def _boom(*a, **kw):
        raise RuntimeError("forced failure")

    with patch.object(ca_mod, "read_cognitive_authorship", _boom):
        try:
            result = cognitive_authorship_prompt_block()
            assert isinstance(result, str), "AT-14: must return str on error"
        except Exception as exc:
            pytest.fail(f"AT-14: cognitive_authorship_prompt_block raised: {exc}")


# ── AT-15 ─────────────────────────────────────────────────────────────────────

def test_at15_server_wired():
    server_path = os.path.join(ROOT, "server.py")
    with open(server_path, encoding="utf-8") as f:
        source = f.read()
    assert "cognitive_authorship_prompt_block" in source, (
        "AT-15: cognitive_authorship_prompt_block must be wired in server.py"
    )
    assert "runtime.cognitive_authorship" in source, (
        "AT-15: runtime.cognitive_authorship must be in server.py"
    )


# ── AT-16 ─────────────────────────────────────────────────────────────────────

def test_at16_py_compile_clean():
    files = [
        os.path.join(ROOT, "runtime", "cognitive_authorship.py"),
        os.path.join(ROOT, "server.py"),
    ]
    for path in files:
        try:
            py_compile.compile(path, doraise=True)
        except py_compile.PyCompileError as exc:
            pytest.fail(f"AT-16: {os.path.basename(path)} compile error: {exc}")
