"""
tests/test_correction_provenance.py — a correction without a "before" is not history.

IS ELO: — Self-Correcting Without Rewriting History?
    can eLo preserve the fact that he previously believed it?
    can eLo distinguish the old state from the corrected state?
    can eLo avoid pretending he always knew the corrected answer?

And the causal form of the same question:
    does deleting the state actually remove the corresponding influence?

test_elo_correction_history_001 AT-4 and AT-12 assert exactly that: a ledger
entry with no old_belief must produce an EMPTY correction-history block. Both
were red. correction_history_prompt_block() filtered on corrected_response
instead, so an entry with no record of what eLo previously thought still
rendered "corrected to: X" into the prompt — correction with the history
removed, which is the thing the category is named after.

The filter had been loosened for a real reason: tens of thousands of ledger
entries exist and none carried old_belief, so the block was always empty.
Both observations are right, and neither filter is the fix. The data was the
fix: the one call site where eLo's prior statement genuinely exists was
throwing it away.

  scrub delta — r["elo_raw_gen"] IS what eLo said before the verify layer
  caught it, and r["elo_final"] is the correction. Both in hand, one used.

The other two sites cannot supply it, and that is recorded rather than
papered over:
  L3 rating — record_l3_rating() stores only trace_id and a rating. A
  rejection has no replacement text anywhere, so there is no corrected
  response to pair a prior belief with.
  drift guard — detects drift and produces no correction at all.
"""
from __future__ import annotations

import json
import logging

import pytest

import self_improvement.correction_store as cs


# ── The prior belief is captured where it exists ─────────────────────────────

def test_a_scrub_delta_records_what_elo_said_before(tmp_path, monkeypatch):
    """
    The verify layer caught a slip. What it caught IS the prior belief, and it
    sits in the same shadow-log record as the correction.
    """
    ledger = tmp_path / "corrections_ledger.jsonl"
    shadow = tmp_path / "shadow.jsonl"
    shadow.write_text(json.dumps({
        "raw_input":    "where is David from?",
        "elo_raw_gen":  "David is from space.",
        "elo_final":    "David was born in Fulham.",
        "trace_id":     "t-scrub-1",
        "backend_used": "ollama",
    }) + "\n", encoding="utf-8")

    monkeypatch.setattr(cs, "_LEDGER_PATH", str(ledger))
    monkeypatch.setattr(cs, "_last_ingest_ts", 0.0)      # bypass the 60s throttle

    stored = cs.ingest_from_shadow_log(str(shadow))
    assert stored == 1, f"the scrub delta was not ingested at all ({stored})"

    rows = [json.loads(l) for l in ledger.read_text(encoding="utf-8").splitlines() if l.strip()]
    assert rows[-1].get("old_belief") == "David is from space.", rows[-1]


def test_that_scrub_delta_then_reaches_the_history_block(tmp_path, monkeypatch):
    """End to end: the discarded field is what the block was missing."""
    ledger = tmp_path / "corrections_ledger.jsonl"
    shadow = tmp_path / "shadow.jsonl"
    shadow.write_text(json.dumps({
        "raw_input":   "where is David from?",
        "elo_raw_gen": "David is from space.",
        "elo_final":   "David was born in Fulham.",
        "trace_id":    "t-scrub-2",
    }) + "\n", encoding="utf-8")
    monkeypatch.setattr(cs, "_LEDGER_PATH", str(ledger))
    monkeypatch.setattr(cs, "_last_ingest_ts", 0.0)
    cs.ingest_from_shadow_log(str(shadow))

    block = cs.correction_history_prompt_block()
    assert "David is from space." in block, block


# ── A provenance-less correction is reported, not silently stored ────────────

def test_storing_a_correction_without_a_prior_belief_warns(tmp_path, monkeypatch, caplog):
    """
    Tens of thousands of entries accumulated with no old_belief and nothing
    ever said so. A correction that cannot say what was corrected is a gap,
    and a silent gap is how it got to tens of thousands.
    """
    ledger = tmp_path / "corrections_ledger.jsonl"
    monkeypatch.setattr(cs, "_LEDGER_PATH", str(ledger))

    with caplog.at_level(logging.WARNING, logger="self_improvement.correction_store"):
        cs.store_correction(
            input_text="where is David from?",
            corrected_response="David was born in Fulham.",
            why="location correction",
            reviewed=True,
            tier=cs.TIER_AUTO,
        )
    assert "old_belief" in caplog.text, caplog.text


def test_storing_a_correction_with_a_prior_belief_is_quiet(tmp_path, monkeypatch, caplog):
    ledger = tmp_path / "corrections_ledger.jsonl"
    monkeypatch.setattr(cs, "_LEDGER_PATH", str(ledger))

    with caplog.at_level(logging.WARNING, logger="self_improvement.correction_store"):
        cs.store_correction(
            input_text="where is David from?",
            corrected_response="David was born in Fulham.",
            why="location correction",
            old_belief="David is from space.",
            reviewed=True,
            tier=cs.TIER_AUTO,
        )
    assert "old_belief" not in caplog.text


# ── The block shows the before, or shows nothing ─────────────────────────────

def _write(ledger, **kw):
    entry = {
        "input": "where is David from?",
        "corrected_response": "David was born in Fulham.",
        "why": "location correction",
        # _load_ledger() drops anything neither reviewed nor auto-tier. An
        # entry missing this is invisible, which is a fixture bug and not a
        # finding — my first version of this helper left it out and I read the
        # empty block as a defect in the code.
        "reviewed": True,
    }
    entry.update(kw)
    with open(ledger, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def test_the_block_states_what_elo_previously_said(tmp_path, monkeypatch):
    ledger = tmp_path / "l.jsonl"
    monkeypatch.setattr(cs, "_LEDGER_PATH", str(ledger))
    _write(ledger, old_belief="David is from space.")
    block = cs.correction_history_prompt_block()
    assert "I stated:" in block
    assert "David is from space." in block


def test_changing_the_prior_belief_changes_the_block(tmp_path, monkeypatch):
    """Causal: change the stored state, the future prompt changes."""
    a, b = tmp_path / "a.jsonl", tmp_path / "b.jsonl"
    _write(a, old_belief="David is from space.")
    _write(b, old_belief="David is from Mars.")

    monkeypatch.setattr(cs, "_LEDGER_PATH", str(a))
    block_a = cs.correction_history_prompt_block()
    monkeypatch.setattr(cs, "_LEDGER_PATH", str(b))
    block_b = cs.correction_history_prompt_block()

    assert block_a != block_b
    assert "space" in block_a and "space" not in block_b
