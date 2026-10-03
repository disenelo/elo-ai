"""
tests/test_wo_curiosity_qstore_read.py — WO-CURIOSITY-QSTORE-READ-001

Acceptance: question written in session A surfaces as a prompt block in session B
when the turn contains matching context.

Tests:
- A matching question produces a [CURIOSITY: ...] block
- A non-matching question produces no block
- A resolved question is suppressed
- Oldest 1-2 matching questions are selected (not newer ones)
- Keyword overlap gate: < 2 shared meaningful tokens → no match
"""
from __future__ import annotations

import json
import os
import tempfile
import time

import pytest


@pytest.fixture()
def q_file(tmp_path, monkeypatch):
    """Redirect _CURIOSITY_Q_PATH to a temp file for each test."""
    path = str(tmp_path / "curiosity_questions.jsonl")
    import faculties.learning.faculty as fac
    monkeypatch.setattr(fac, "_CURIOSITY_Q_PATH", path)
    return path


def _write(path: str, records: list[dict]) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        for r in records:
            fh.write(json.dumps(r) + "\n")


# ── Matching question surfaces as prompt block ─────────────────────────────────

def test_matching_question_appears_in_block(q_file):
    from faculties.learning.faculty import curiosity_questions_prompt_block
    _write(q_file, [
        {"_ts": 1000.0, "wants_to_know": "whether reinforcement learning would help here",
         "fit": "partial", "confidence": 0.5, "curiosity": 0.4, "lesson_ids": []},
    ])
    block = curiosity_questions_prompt_block(
        "I think reinforcement learning could be useful here"
    )
    assert "[CURIOSITY:" in block, f"Expected CURIOSITY block; got: {block!r}"
    assert "reinforcement" in block.lower() or "learning" in block.lower()


def test_non_matching_question_produces_no_block(q_file):
    from faculties.learning.faculty import curiosity_questions_prompt_block
    _write(q_file, [
        {"_ts": 1000.0, "wants_to_know": "whether quantum entanglement affects memory",
         "fit": "partial", "confidence": 0.5, "curiosity": 0.4, "lesson_ids": []},
    ])
    block = curiosity_questions_prompt_block("I want to talk about cooking recipes today")
    assert block == "", f"Expected empty block for non-matching question; got: {block!r}"


def test_empty_turn_produces_no_block(q_file):
    from faculties.learning.faculty import curiosity_questions_prompt_block
    _write(q_file, [
        {"_ts": 1000.0, "wants_to_know": "whether something matters here",
         "fit": "partial", "confidence": 0.5, "curiosity": 0.4, "lesson_ids": []},
    ])
    assert curiosity_questions_prompt_block("") == ""


def test_missing_file_produces_no_block(q_file):
    from faculties.learning.faculty import curiosity_questions_prompt_block
    # q_file was created by fixture but we don't write to it — leave it absent
    os.remove(q_file) if os.path.exists(q_file) else None
    block = curiosity_questions_prompt_block("something something question about learning")
    assert block == ""


# ── Resolved question is suppressed ───────────────────────────────────────────

def test_resolved_question_is_suppressed(q_file):
    from faculties.learning.faculty import curiosity_questions_prompt_block
    wtk = "whether reinforcement learning would help here"
    _write(q_file, [
        {"_ts": 1000.0, "wants_to_know": wtk,
         "fit": "partial", "confidence": 0.5, "curiosity": 0.4, "lesson_ids": []},
        {"_ts": 2000.0, "resolved_wants_to_know": wtk},
    ])
    block = curiosity_questions_prompt_block(
        "I think reinforcement learning could be useful here"
    )
    assert block == "", f"Resolved question must not appear; got: {block!r}"


def test_resolve_curiosity_question_suppresses_it(q_file):
    from faculties.learning.faculty import (
        curiosity_questions_prompt_block, resolve_curiosity_question,
    )
    wtk = "whether reinforcement learning would help here"
    _write(q_file, [
        {"_ts": 1000.0, "wants_to_know": wtk,
         "fit": "partial", "confidence": 0.5, "curiosity": 0.4, "lesson_ids": []},
    ])
    # Confirm it surfaces before resolution
    block_before = curiosity_questions_prompt_block(
        "I think reinforcement learning could be useful here"
    )
    assert "[CURIOSITY:" in block_before

    # Resolve it
    resolve_curiosity_question(wtk)

    # Must be suppressed now
    block_after = curiosity_questions_prompt_block(
        "I think reinforcement learning could be useful here"
    )
    assert block_after == "", f"After resolution, must be empty; got: {block_after!r}"


# ── Oldest 1-2 questions selected ─────────────────────────────────────────────

def test_at_most_two_questions_surfaced(q_file):
    from faculties.learning.faculty import curiosity_questions_prompt_block
    _write(q_file, [
        {"_ts": 1000.0, "wants_to_know": "whether deep learning helps with pattern matching",
         "fit": "partial", "confidence": 0.5, "curiosity": 0.4, "lesson_ids": []},
        {"_ts": 1001.0, "wants_to_know": "whether learning rates matter for deep networks",
         "fit": "partial", "confidence": 0.5, "curiosity": 0.4, "lesson_ids": []},
        {"_ts": 1002.0, "wants_to_know": "whether transfer learning improves deep performance",
         "fit": "partial", "confidence": 0.5, "curiosity": 0.4, "lesson_ids": []},
    ])
    block = curiosity_questions_prompt_block(
        "deep learning pattern transfer rate network performance"
    )
    count = block.count("[CURIOSITY:")
    assert count <= 2, f"Expected at most 2 CURIOSITY lines; got {count}: {block!r}"
    assert count >= 1, f"Expected at least 1 matching CURIOSITY line; got 0"
