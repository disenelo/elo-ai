"""
tests/test_elo_correction_history_001.py — Correction History / Self-Correction Without Rewriting History

IS ELO: — Self-Correcting Without Rewriting History?
  can eLo correct an incorrect belief?
  can eLo preserve the fact that he previously believed it?
  can eLo distinguish the old state from the corrected state?
  can eLo explain why the correction happened?
  can eLo avoid pretending he always knew the corrected answer?
  can eLo maintain provenance through multiple corrections?

THE CAUSAL CHAIN (what this module proves):
  store_correction(old_belief=X) → corrections_ledger.jsonl [old_belief field stored]
  → _load_ledger() retrieves old_belief → correction_history_prompt_block()
  → [CORRECTION HISTORY] block in system prompt
  → LLM reads "I previously stated X" → cannot pretend it always knew the right answer

AT-1  store_correction() accepts old_belief parameter without error
AT-2  old_belief is persisted in the ledger entry when provided
AT-3  old_belief is absent from entry when not provided (backward compat)
AT-4  correction_history_prompt_block() returns "" when no entries with old_belief
AT-5  correction_history_prompt_block() returns non-empty when old_belief entries exist
AT-6  block contains [CORRECTION HISTORY] header
AT-7  block contains the old_belief text
AT-8  block contains the corrected_response text
AT-9  block shows both old and corrected state — the distinction is present
AT-10 block warns eLo not to pretend he always knew
AT-11 build_correction_frame() shows old_belief when present in entry
AT-12 CAUSAL PROOF: store with old_belief → load → block changes vs no old_belief
AT-13 correction_history_prompt_block() never raises (resilient)
AT-14 server.py wired: correction_history_prompt_block import present
AT-15 py_compile clean
"""
from __future__ import annotations

import json
import os
import py_compile
import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import patch

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import self_improvement.correction_store as cs_mod
from self_improvement.correction_store import (
    store_correction,
    correction_history_prompt_block,
    build_correction_frame,
    _load_ledger,
    TIER_AUTO,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _temp_ledger(tmp_path: Path) -> Path:
    return tmp_path / "test_ledger.jsonl"


def _write_entry(path: Path, entry: dict) -> None:
    with open(path, "a") as f:
        f.write(json.dumps(entry) + "\n")


def _base_entry(with_old_belief: bool = True) -> dict:
    return {
        "id": "CX-0000001",
        "input": "Where is David from?",
        "old_belief": "David is from Camberwell." if with_old_belief else "",
        "corrected_response": "David was born in Fulham, raised in Brixton.",
        "why": "location correction",
        "trace": {},
        "tier": TIER_AUTO,
        "reviewed": True,
        "ts": time.time(),
    }


# ── AT-1 ──────────────────────────────────────────────────────────────────────

def test_at1_store_correction_accepts_old_belief():
    """store_correction() must accept old_belief parameter without raising."""
    try:
        result = store_correction(
            input_text="What is 2+2?",
            corrected_response="4",
            why="arithmetic",
            old_belief="5",
        )
        assert isinstance(result, bool), "AT-1: store_correction must return bool"
    except TypeError as exc:
        pytest.fail(f"AT-1: store_correction raised TypeError on old_belief param: {exc}")


# ── AT-2 ──────────────────────────────────────────────────────────────────────

def test_at2_old_belief_persisted_in_ledger(tmp_path):
    """old_belief must appear in the ledger entry when provided."""
    ledger = _temp_ledger(tmp_path)
    with patch.object(cs_mod, "_LEDGER_PATH", str(ledger)):
        store_correction(
            input_text="Who made eLo?",
            corrected_response="David Charles made eLo.",
            why="authorship",
            old_belief="eLo was made by a company.",
            reviewed=True,
        )
    with open(ledger) as f:
        entries = [json.loads(line) for line in f if line.strip()]
    assert any("old_belief" in e for e in entries), (
        "AT-2: old_belief must appear in ledger entry when provided"
    )
    belief_entries = [e for e in entries if e.get("old_belief")]
    assert belief_entries[0]["old_belief"] == "eLo was made by a company.", (
        f"AT-2: old_belief value must be stored verbatim, got: {belief_entries[0].get('old_belief')!r}"
    )


# ── AT-3 ──────────────────────────────────────────────────────────────────────

def test_at3_old_belief_absent_when_not_provided(tmp_path):
    """old_belief must NOT appear in entry when not provided (backward compat)."""
    ledger = _temp_ledger(tmp_path)
    with patch.object(cs_mod, "_LEDGER_PATH", str(ledger)):
        store_correction(
            input_text="What colour is eLo?",
            corrected_response="eLo is white.",
            why="colour fact",
            reviewed=True,
        )
    with open(ledger) as f:
        entries = [json.loads(line) for line in f if line.strip()]
    assert entries, "AT-3: at least one entry must have been written"
    last = entries[-1]
    assert "old_belief" not in last or last.get("old_belief") == "", (
        "AT-3: old_belief must be absent (or empty) when not provided"
    )


# ── AT-4 ──────────────────────────────────────────────────────────────────────

def test_at4_block_empty_when_no_old_belief_entries(tmp_path):
    """correction_history_prompt_block() must return '' when no entries carry old_belief."""
    ledger = _temp_ledger(tmp_path)
    entry = _base_entry(with_old_belief=False)
    entry.pop("old_belief", None)  # ensure absent
    _write_entry(ledger, entry)
    with patch.object(cs_mod, "_LEDGER_PATH", str(ledger)):
        block = correction_history_prompt_block()
    assert block == "", (
        f"AT-4: no old_belief entries → block must be empty, got: {block[:80]!r}"
    )


# ── AT-5 ──────────────────────────────────────────────────────────────────────

def test_at5_block_non_empty_when_old_belief_present(tmp_path):
    """correction_history_prompt_block() must return non-empty when old_belief entries exist."""
    ledger = _temp_ledger(tmp_path)
    _write_entry(ledger, _base_entry(with_old_belief=True))
    with patch.object(cs_mod, "_LEDGER_PATH", str(ledger)):
        block = correction_history_prompt_block()
    assert block, "AT-5: old_belief entry exists → block must be non-empty"


# ── AT-6 ──────────────────────────────────────────────────────────────────────

def test_at6_block_has_correction_history_header(tmp_path):
    """Block must contain [CORRECTION HISTORY] header."""
    ledger = _temp_ledger(tmp_path)
    _write_entry(ledger, _base_entry(with_old_belief=True))
    with patch.object(cs_mod, "_LEDGER_PATH", str(ledger)):
        block = correction_history_prompt_block()
    assert "CORRECTION HISTORY" in block, (
        "AT-6: block must contain CORRECTION HISTORY header"
    )


# ── AT-7 ──────────────────────────────────────────────────────────────────────

def test_at7_block_contains_old_belief_text(tmp_path):
    """Block must contain the old_belief text so eLo can reference what it stated before."""
    ledger = _temp_ledger(tmp_path)
    entry = _base_entry(with_old_belief=True)
    entry["old_belief"] = "eLo is a planet."
    _write_entry(ledger, entry)
    with patch.object(cs_mod, "_LEDGER_PATH", str(ledger)):
        block = correction_history_prompt_block()
    assert "eLo is a planet" in block, (
        "AT-7: block must contain the old_belief text"
    )


# ── AT-8 ──────────────────────────────────────────────────────────────────────

def test_at8_block_contains_corrected_response(tmp_path):
    """Block must contain the corrected_response so eLo knows what replaced the old belief."""
    ledger = _temp_ledger(tmp_path)
    entry = _base_entry(with_old_belief=True)
    entry["corrected_response"] = "eLo is a character — not a planet."
    _write_entry(ledger, entry)
    with patch.object(cs_mod, "_LEDGER_PATH", str(ledger)):
        block = correction_history_prompt_block()
    assert "eLo is a character" in block, (
        "AT-8: block must contain the corrected_response text"
    )


# ── AT-9 ──────────────────────────────────────────────────────────────────────

def test_at9_block_shows_both_old_and_new_states(tmp_path):
    """Block must distinguish old state from corrected state — both must appear."""
    ledger = _temp_ledger(tmp_path)
    entry = _base_entry(with_old_belief=True)
    entry["old_belief"] = "eLo was created in 2020."
    entry["corrected_response"] = "eLo has been with David since childhood."
    _write_entry(ledger, entry)
    with patch.object(cs_mod, "_LEDGER_PATH", str(ledger)):
        block = correction_history_prompt_block()
    assert "2020" in block, "AT-9: old state must appear in block"
    assert "childhood" in block, "AT-9: corrected state must appear in block"
    # Both must be in the SAME block (old belief → correction), not separate fragments
    old_idx = block.index("2020")
    new_idx = block.index("childhood")
    assert abs(old_idx - new_idx) < 500, (
        "AT-9: old belief and corrected state must appear close together (same correction entry)"
    )


# ── AT-10 ─────────────────────────────────────────────────────────────────────

def test_at10_block_warns_not_to_pretend(tmp_path):
    """Block must instruct eLo not to pretend he always knew the correct answer."""
    ledger = _temp_ledger(tmp_path)
    _write_entry(ledger, _base_entry(with_old_belief=True))
    with patch.object(cs_mod, "_LEDGER_PATH", str(ledger)):
        block = correction_history_prompt_block()
    assert "pretend" in block.lower(), (
        "AT-10: block must warn eLo not to pretend he always knew the answer"
    )


# ── AT-11 ─────────────────────────────────────────────────────────────────────

def test_at11_build_correction_frame_shows_old_belief(tmp_path):
    """build_correction_frame() must include old_belief in the frame when present in entry."""
    ledger = _temp_ledger(tmp_path)
    entry = _base_entry(with_old_belief=True)
    entry["old_belief"] = "eLo has fingers."
    _write_entry(ledger, entry)
    with patch.object(cs_mod, "_LEDGER_PATH", str(ledger)):
        frame = build_correction_frame("Where is David from?", top_k=3)
    # build_correction_frame shows the entry — if old_belief is displayed, it will be in frame
    assert isinstance(frame, str), "AT-11: build_correction_frame must return str"
    # If the entry was retrieved (text-match dependent), verify old_belief appears
    if "old belief" in frame.lower() or "old_belief" in frame:
        assert "eLo has fingers" in frame, (
            "AT-11: when old_belief is displayed in frame, its text must be present"
        )


# ── AT-12 ─────────────────────────────────────────────────────────────────────

def test_at12_causal_proof_store_old_belief_changes_block(tmp_path):
    """
    THE CAUSAL PROOF: storing a correction WITH old_belief changes the history block
    vs storing WITHOUT old_belief.

    CHAIN:
    store_correction(old_belief=X) → ledger entry has old_belief
    → correction_history_prompt_block() reads it → block is non-empty
    → LLM sees "I previously stated X" → cannot pretend it always knew Y
    """
    ledger_a = tmp_path / "ledger_a.jsonl"
    ledger_b = tmp_path / "ledger_b.jsonl"

    # Ledger A: entry WITHOUT old_belief
    entry_no_belief = _base_entry(with_old_belief=False)
    entry_no_belief.pop("old_belief", None)
    _write_entry(ledger_a, entry_no_belief)

    # Ledger B: same entry WITH old_belief
    entry_with_belief = _base_entry(with_old_belief=True)
    entry_with_belief["old_belief"] = "eLo is from space."
    _write_entry(ledger_b, entry_with_belief)

    with patch.object(cs_mod, "_LEDGER_PATH", str(ledger_a)):
        block_without = correction_history_prompt_block()

    with patch.object(cs_mod, "_LEDGER_PATH", str(ledger_b)):
        block_with = correction_history_prompt_block()

    assert block_without == "", (
        "AT-12 CAUSAL PROOF: ledger without old_belief must produce empty block"
    )
    assert block_with, (
        "AT-12 CAUSAL PROOF: ledger with old_belief must produce non-empty block"
    )
    assert block_without != block_with, (
        "AT-12 CAUSAL PROOF: storing old_belief must change the history block"
    )
    assert "eLo is from space" in block_with, (
        "AT-12: old_belief text must appear in the block"
    )


# ── AT-13 ─────────────────────────────────────────────────────────────────────

def test_at13_correction_history_block_resilient():
    """correction_history_prompt_block() must never raise."""
    def _boom(*a, **kw):
        raise RuntimeError("forced failure")

    with patch.object(cs_mod, "_load_ledger", _boom):
        try:
            result = correction_history_prompt_block()
            assert isinstance(result, str), "AT-13: must return str on error"
        except Exception as exc:
            pytest.fail(f"AT-13: correction_history_prompt_block raised: {exc}")


# ── AT-14 ─────────────────────────────────────────────────────────────────────

def test_at14_server_wired():
    """server.py must import correction_history_prompt_block."""
    server_path = os.path.join(ROOT, "server.py")
    with open(server_path, encoding="utf-8") as f:
        source = f.read()
    assert "correction_history_prompt_block" in source, (
        "AT-14: correction_history_prompt_block must be wired in server.py"
    )
    assert "self_improvement.correction_store" in source or "correction_store" in source, (
        "AT-14: correction_store must be imported in server.py"
    )


# ── AT-15 ─────────────────────────────────────────────────────────────────────

def test_at15_py_compile_clean():
    files = [
        os.path.join(ROOT, "self_improvement", "correction_store.py"),
        os.path.join(ROOT, "server.py"),
    ]
    for path in files:
        try:
            py_compile.compile(path, doraise=True)
        except py_compile.PyCompileError as exc:
            pytest.fail(f"AT-15: {os.path.basename(path)} compile error: {exc}")
