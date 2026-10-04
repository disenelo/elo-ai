"""
tests/test_cognitive_authorship_origin.py — IS ELO: Capable of Ownership?

    "can eLo correctly say 'that was my idea' when it actually was?"
    "can he recognise his own previous contribution?"
    "can he avoid falsely attributing its own initiatives to the user?"

runtime/cognitive_authorship.py exists to answer these. Its own docstring
names the failure it prevents:

    "Failure mode B: eLo says 'you mentioned this' when eLo raised it via
     initiative."

Measured against the live journal, 5727 entries, 2026-10-04:

    user_directed  5363
    collaborative   364
    elo_origin        0

Not one. And 94 of those entries carry trigger_source="ambient_daemon" —
turns the system itself recorded as self-initiated, written by the ambient
path that sets intent_source "self". All 94 classify as user_directed.

eLo has 94 recorded occasions of starting something himself and attributes
every one of them to David. The module produces precisely the failure mode
it was written to prevent.

WHY. _classify_origin() pattern-matches free text in `trigger` against
{"initiative", "proactive", "self_initiation", "novel_connection", ...}.
Nothing in the live journal's trigger field contains any of them — the real
values are "factual question", "building momentum, stay in build mode",
"lesson: Completed a capability milestone", "bypass:TRANSPORT". Meanwhile
the authoritative origin signal is already recorded, structured, one key
away: trigger_source and exec_decision.intent_source.

Fixed by reading the structured fields, not by widening the keyword set.
Adding "ambient" to the pattern list would work until the next trigger
string is phrased differently; the fields are what the writer actually
asserts.
"""
from __future__ import annotations

import json

import pytest

from runtime.cognitive_authorship import _classify_origin, read_cognitive_authorship


def _entry(**kw) -> dict:
    base = {"turn": "t", "action": "answer", "trigger": "factual question",
            "intent": "conversation"}
    base.update(kw)
    return base


def _write(path, entries):
    with open(path, "w", encoding="utf-8") as f:
        for e in entries:
            f.write(json.dumps(e) + "\n")


# ── The structured signal wins ───────────────────────────────────────────────

def test_an_ambient_daemon_turn_is_elo_origin():
    """The exact shape of the 94 live entries that were all mis-attributed."""
    assert _classify_origin(
        "building momentum, stay in build mode", "build", "conversation",
        trigger_source="ambient_daemon",
    ) == "elo_origin"


def test_intent_source_self_is_elo_origin():
    """What the ambient path writes into exec_decision."""
    assert _classify_origin(
        "unknown", "reflect", "", intent_source="self",
    ) == "elo_origin"


def test_a_user_message_is_still_user_directed():
    assert _classify_origin(
        "factual question", "answer", "conversation",
        trigger_source="user_message",
    ) == "user_directed"


def test_the_text_heuristic_still_works_when_no_field_is_present():
    assert _classify_origin("elo_initiative", "answer", "") == "elo_origin"
    assert _classify_origin("creative intent", "build", "") == "collaborative"


def test_the_conservative_default_is_unchanged():
    """Ambiguous stays user_directed — eLo must not overclaim initiative."""
    assert _classify_origin("", "", "") == "user_directed"
    assert _classify_origin("bypass:TRANSPORT", "answer", "") == "user_directed"


# ── Causal: remove the signal, lose the attribution ─────────────────────────

def test_deleting_the_origin_field_removes_the_attribution():
    with_field = _classify_origin("unknown", "reflect", "",
                                  trigger_source="ambient_daemon")
    without = _classify_origin("unknown", "reflect", "")
    assert with_field == "elo_origin"
    assert without == "user_directed"


# ── Through the real reader ─────────────────────────────────────────────────

def test_the_reader_counts_a_self_initiated_turn(tmp_path):
    path = tmp_path / "decision_journal.jsonl"
    _write(path, [
        _entry(trigger_source="user_message"),
        _entry(trigger="unknown", action="reflect", trigger_source="ambient_daemon",
               exec_decision={"intent_source": "self"}),
    ])
    read = read_cognitive_authorship(journal_path=path)
    assert read.elo_count == 1, (read.elo_count, [a.origin for a in read.actions])
    assert read.has_elo_actions is True


def test_the_reader_passes_trigger_source_on_its_own(tmp_path):
    """
    Isolated. The combined test above sets BOTH origin fields, so dropping
    either one still passed — a wire-cut on trigger_source went green and
    that is how this gap was found. Each field is now proven to reach the
    classifier by itself.
    """
    path = tmp_path / "decision_journal.jsonl"
    _write(path, [_entry(trigger="unknown", trigger_source="ambient_daemon")])
    assert read_cognitive_authorship(journal_path=path).elo_count == 1


def test_the_reader_passes_intent_source_on_its_own(tmp_path):
    path = tmp_path / "decision_journal.jsonl"
    _write(path, [_entry(trigger="unknown",
                         exec_decision={"intent_source": "self"})])
    assert read_cognitive_authorship(journal_path=path).elo_count == 1


def test_the_reader_used_to_see_none_of_them(tmp_path):
    """
    Same two entries with the origin fields stripped — the state the live
    journal was effectively in, as far as the classifier could see.
    """
    path = tmp_path / "decision_journal.jsonl"
    _write(path, [_entry(), _entry(trigger="unknown", action="reflect")])
    read = read_cognitive_authorship(journal_path=path)
    assert read.elo_count == 0
    assert read.has_elo_actions is False
