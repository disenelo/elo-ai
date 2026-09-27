"""
tests/test_dream_symbol_history.py — WO-DREAM-ENGINE-001 PHASE 10.

Recurring symbol tracking. Meanings are OBSERVED from context, never
hardcoded, and they evolve across dreams.

Every test uses tmp_path — the real lexicon at self/dream_symbols.json is
never touched (see tests/test_no_live_state_writes.py for why that matters).
"""
from __future__ import annotations

import json

import pytest

from faculties.dream import symbol_history as sh


@pytest.fixture
def lex(tmp_path):
    return tmp_path / "dream_symbols.json"


def test_missing_file_is_an_empty_lexicon(tmp_path):
    assert sh.load(tmp_path / "nope.json") == {}
    assert sh.recurring(tmp_path / "nope.json") == {}
    assert sh.most_established(tmp_path / "nope.json") == ""


def test_corrupt_file_is_an_empty_lexicon(lex):
    lex.write_text("{not json", encoding="utf-8")
    assert sh.load(lex) == {}


def test_symbol_normalisation_keeps_one_entry():
    assert sh.normalise("Mechanical birds") == sh.normalise("mechanical_bird")
    assert sh.normalise("  A Machine Breathing ") == "a_machine_breathing"
    assert sh.normalise("") == ""


def test_plural_and_singular_do_not_split_the_count(lex):
    sh.record_dream("d1", ["mechanical birds"], meaning="freedom", path=lex)
    sh.record_dream("d2", ["mechanical_bird"], meaning="escape", path=lex)
    records = sh.load(lex)
    assert len(records) == 1
    assert next(iter(records.values())).count == 2


def test_one_dream_counts_a_symbol_once(lex):
    sh.record_dream("d1", ["a staircase", "a staircase", "staircases"],
                    meaning="starting again", path=lex)
    assert sh.load(lex)[sh.normalise("a staircase")].count == 1


def test_rerunning_the_same_dream_does_not_inflate_the_count(lex):
    sh.record_dream("d1", ["mechanical bird"], meaning="freedom", path=lex)
    sh.record_dream("d1", ["mechanical bird"], meaning="freedom", path=lex)
    assert sh.load(lex)[sh.normalise("mechanical bird")].count == 1


def test_recurrence_threshold_is_three(lex):
    key = sh.normalise("mechanical bird")
    for i in range(1, 4):
        sh.record_dream(f"d{i}", ["mechanical bird"], meaning=f"m{i}", path=lex)
        record = sh.load(lex)[key]
        assert record.is_recurring == (i >= sh.RECURRENCE_THRESHOLD)
    assert key in sh.recurring(lex)


def test_meaning_evolves_and_current_association_is_the_latest(lex):
    for dream, meaning in (("001", "freedom"), ("002", "escape"),
                           ("003", "invention"), ("004", "transformation")):
        sh.record_dream(dream, ["mechanical bird"], meaning=meaning, path=lex)

    record = sh.load(lex)[sh.normalise("mechanical bird")]
    assert record.count == 4
    assert [e["meaning"] for e in record.evolution] == [
        "freedom", "escape", "invention", "transformation"]
    assert record.current_association == "transformation"
    assert sh.current_association("mechanical birds", lex) == "transformation"


def test_no_meaning_is_recorded_when_none_is_observed(lex):
    """This module never invents a meaning."""
    sh.record_dream("d1", ["small doors set too high"], path=lex)
    record = sh.load(lex)[sh.normalise("small doors set too high")]
    assert record.evolution[0]["meaning"] == ""
    assert record.current_association == ""


def test_current_association_falls_back_past_empty_meanings(lex):
    sh.record_dream("d1", ["rooms inside rooms"], meaning="memory", path=lex)
    sh.record_dream("d2", ["rooms inside rooms"], path=lex)
    assert sh.current_association("rooms inside rooms", lex) == "memory"


def test_first_appeared_is_preserved(lex):
    sh.record_dream("d1", ["a machine breathing"], when="2026-09-15", path=lex)
    sh.record_dream("d2", ["a machine breathing"], when="2026-09-20", path=lex)
    assert sh.load(lex)[sh.normalise("a machine breathing")].first_appeared == "2026-09-15"


def test_most_established_needs_recurrence_first(lex):
    sh.record_dream("d1", ["unlit windows"], path=lex)
    sh.record_dream("d2", ["unlit windows"], path=lex)
    assert sh.most_established(lex) == "", "promoted a symbol below threshold"
    sh.record_dream("d3", ["unlit windows"], path=lex)
    assert sh.most_established(lex) == "unlit windows"   # display form, not the slug


def test_most_established_picks_the_strongest(lex):
    for i in range(5):
        sh.record_dream(f"a{i}", ["mechanical bird"], path=lex)
    for i in range(3):
        sh.record_dream(f"b{i}", ["unlit windows"], path=lex)
    assert sh.most_established(lex) == "mechanical bird"


def test_evolution_is_capped_but_keeps_the_origin(lex):
    for i in range(sh.MAX_EVOLUTION + 10):
        sh.record_dream(f"d{i}", ["a machine breathing"],
                        meaning=f"m{i}", when="2026-09-15", path=lex)
    record = sh.load(lex)[sh.normalise("a machine breathing")]
    assert len(record.evolution) <= sh.MAX_EVOLUTION
    assert record.evolution[0]["dream"] == "d0", "origin entry dropped"
    assert record.count == sh.MAX_EVOLUTION + 10, "count must not be capped"


def test_persisted_shape_matches_the_wo(lex):
    sh.record_dream("001", ["mechanical bird"], meaning="freedom",
                    when="2026-09-15", path=lex)
    raw = json.loads(lex.read_text(encoding="utf-8"))
    entry = raw[sh.normalise("mechanical bird")]
    # The WO's four keys must all be present; `display` is additive because
    # the WO schema has nowhere to keep the original wording.
    assert {"first_appeared", "count", "evolution", "current_association"} <= set(entry)
    assert entry["display"] == "mechanical bird"
    assert entry["first_appeared"] == "2026-09-15"
    assert entry["evolution"][0]["dream"] == "001"


def test_lexicon_summary_is_strongest_first(lex):
    for i in range(4):
        sh.record_dream(f"a{i}", ["mechanical bird"], path=lex)
    sh.record_dream("b0", ["unlit windows"], path=lex)
    summary = sh.lexicon_summary(lex)
    assert summary[0]["symbol"] == sh.normalise("mechanical bird")
    assert summary[0]["recurring"] is True
    assert summary[-1]["recurring"] is False


def test_save_failure_does_not_raise(lex, monkeypatch):
    """A lexicon write must never be able to break a dream."""
    monkeypatch.setattr(sh.Path, "mkdir", lambda *a, **k: (_ for _ in ()).throw(OSError("ro")))
    assert sh.record_dream("d1", ["x"], path=lex) is not None


def test_most_established_returns_a_display_form_that_round_trips(lex):
    """It goes straight into an image prompt, so it must not read as a slug."""
    for i in range(3):
        sh.record_dream(f"d{i}", ["a machine breathing"], path=lex)
    name = sh.most_established(lex)
    assert "_" not in name
    assert sh.normalise(name) in sh.load(lex)
