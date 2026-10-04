"""
tests/test_decision_journal_shared_file.py — IS ELO: One Brain? / Capable of Failure?

    "can two different systems write contradictory state?"
    "does failure produce learning?"
    "can eLo recognise repeated failure?"
    "a system capable of knowing why he made a decision?"

Two modules own self/journals/action_reliability.json and disagree about
what shape it is.

  self/decision_journal.py       — a DICT: action -> reliability score.
      _load_reliability() returns {} on error, get_reliability() does
      .get(action, 1.0) on the result.

  runtime/executive_candidates.py — a LIST of decision events.
      _load_log() returns [], record_failure/record_success append and save
      a list.

The file on disk is a list, written 2026-09-27. So:

    >>> from self.decision_journal import get_reliability
    >>> get_reliability("walk")
    AttributeError: 'list' object has no attribute 'get'

json.load succeeds — the list is valid JSON — so _load_reliability()'s
try/except never fires, and the AttributeError lands in get_reliability()
where there is no guard at all.

get_reliability() is called from explain_last(), which is how eLo answers
"why did you do that?". That answer has been raising instead of returning.

And the collision runs both ways: decision_journal._save_reliability() writes
a dict, which would silently destroy every entry executive_candidates had
appended.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

import runtime.executive_candidates as ec
import self.decision_journal as dj


_LIST_SHAPED = [
    {"ts": "2026-09-27T06:42:30", "intent": "explore_upper_surface",
     "chosen": "wall_jump", "result": "PASS"},
]


# ── The crash ────────────────────────────────────────────────────────────────

def test_reliability_survives_a_list_shaped_file(tmp_path, monkeypatch):
    path = tmp_path / "action_reliability.json"
    path.write_text(json.dumps(_LIST_SHAPED), encoding="utf-8")
    monkeypatch.setattr(dj, "_RELIABILITY", str(path))
    # Must not raise. Unknown action → the documented default.
    assert dj.get_reliability("walk") == 1.0


def test_a_wrong_shaped_file_is_reported_not_swallowed(tmp_path, monkeypatch, caplog):
    import logging
    path = tmp_path / "action_reliability.json"
    path.write_text(json.dumps(_LIST_SHAPED), encoding="utf-8")
    monkeypatch.setattr(dj, "_RELIABILITY", str(path))
    with caplog.at_level(logging.WARNING):
        dj.get_reliability("walk")
    assert "action_reliability" in caplog.text.lower(), caplog.text


def test_a_correctly_shaped_file_still_reads(tmp_path, monkeypatch):
    path = tmp_path / "action_reliability.json"
    path.write_text(json.dumps({"answer": 0.55}), encoding="utf-8")
    monkeypatch.setattr(dj, "_RELIABILITY", str(path))
    assert dj.get_reliability("answer") == 0.55
    assert dj.get_reliability("never_seen") == 1.0


def test_explain_last_does_not_raise_on_a_list_shaped_file(tmp_path, monkeypatch):
    """The 'why did you do that?' answer. It was raising."""
    rel = tmp_path / "action_reliability.json"
    rel.write_text(json.dumps(_LIST_SHAPED), encoding="utf-8")
    journal = tmp_path / "decision_journal.jsonl"
    journal.write_text(json.dumps({
        "action": "answer", "trigger": "david asked", "outcome": "success",
    }) + "\n", encoding="utf-8")
    monkeypatch.setattr(dj, "_RELIABILITY", str(rel))
    monkeypatch.setattr(dj, "_JOURNAL", str(journal))
    out = dj.explain_last()
    assert "answer" in out


# ── One file, one owner ─────────────────────────────────────────────────────

def test_the_two_modules_no_longer_share_a_file():
    assert Path(ec._RELIABILITY_LOG).name != Path(dj._RELIABILITY).name, (
        "executive_candidates and decision_journal still write the same file "
        "in incompatible shapes"
    )


def test_each_module_round_trips_its_own_shape(tmp_path, monkeypatch):
    ec_path = tmp_path / "action_candidates.json"
    dj_path = tmp_path / "action_reliability.json"
    monkeypatch.setattr(ec, "_RELIABILITY_LOG", ec_path)
    monkeypatch.setattr(dj, "_RELIABILITY", str(dj_path))

    ec.record_failure("explore", "wall_jump", "ledge too high")
    ec.record_success("explore", "walk")
    entries = json.loads(ec_path.read_text(encoding="utf-8"))
    assert isinstance(entries, list) and len(entries) == 2
    assert entries[0]["result"] == "FAIL"

    dj._save_reliability({"answer": 0.4})
    assert json.loads(dj_path.read_text(encoding="utf-8")) == {"answer": 0.4}
    # And neither clobbered the other.
    assert isinstance(json.loads(ec_path.read_text(encoding="utf-8")), list)
