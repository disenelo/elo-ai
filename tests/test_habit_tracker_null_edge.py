"""
tests/test_habit_tracker_null_edge.py — 7070 observations, zero habits reported.

IS ELO: — Skills & Habits / Developing?
    "a system capable of developing habits?"
    "a system capable of recognising when something has become habitual?"
    "can we demonstrate habit formation?"
    "does eLo know when a faculty failed?"

Live data, 14175 signals:

    close    7070      HABITUAL_THRESHOLD is 30
    reflect  3861
    answer   1434
    build     499
    ground    391
    silence   336

habit_tracker_prompt_block() returns "".

    AttributeError: 'NoneType' object has no attribute 'strip'

read_habit_state() does `row.get("edge_hint", "").strip()`. The default
only applies when the key is ABSENT; 43 of those rows carry
edge_hint: null, where .get returns None and .strip() raises. The inner
handler catches json.JSONDecodeError only, so the AttributeError escapes to
the outer one, which abandons the WHOLE FILE and returns an empty
HabitState.

43 rows out of 14175 — 0.3% of the data disabling 100% of the faculty.

And the failure is indistinguishable from the truth. HabitState() with no
habits is exactly what "eLo has no habits yet" looks like, so the caller
cannot tell a crash from a quiet life. That is why read_failed exists now.
"""
from __future__ import annotations

import json

import pytest

from runtime.habit_tracker import (
    FORMING_THRESHOLD, HABITUAL_THRESHOLD, habit_tracker_prompt_block,
    read_habit_state,
)


def _signals(tmp_path, rows):
    p = tmp_path / "spg_signals.jsonl"
    with open(p, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    return p


# ── The bug ────────────────────────────────────────────────────────────────

def test_a_null_edge_hint_does_not_destroy_the_whole_file(tmp_path):
    rows = [{"edge_hint": "close"}] * 40 + [{"edge_hint": None}]
    st = read_habit_state(_signals(tmp_path, rows))
    assert st.total_signals == 40, "one null row zeroed 40 good ones"
    assert [h.edge_hint for h in st.habits] == ["close"]


def test_a_missing_edge_hint_key_is_also_fine(tmp_path):
    rows = [{"edge_hint": "reflect"}] * 15 + [{"signal_type": "x"}]
    assert read_habit_state(_signals(tmp_path, rows)).total_signals == 15


def test_a_malformed_row_skips_that_row_not_the_file(tmp_path):
    p = tmp_path / "spg_signals.jsonl"
    p.write_text("\n".join(
        [json.dumps({"edge_hint": "close"})] * 12 + ["{not json", json.dumps({"edge_hint": 5})]
    ), encoding="utf-8")
    st = read_habit_state(p)
    assert st.total_signals >= 12
    assert st.read_failed is False


# ── A failure must be distinguishable from a quiet life ────────────────────

def test_an_empty_file_is_no_habits_not_a_failure(tmp_path):
    st = read_habit_state(_signals(tmp_path, []))
    assert st.habits == [] and st.read_failed is False


def test_a_read_failure_says_so(tmp_path, monkeypatch):
    """
    HabitState() with no habits looks exactly like "eLo has no habits yet".
    The caller could not tell a crash from a quiet life, which is how 7070
    observations read as zero for as long as they did.
    """
    import runtime.habit_tracker as ht
    monkeypatch.setattr(ht.Path, "exists", lambda self: (_ for _ in ()).throw(OSError("boom")))
    st = read_habit_state(tmp_path / "nope.jsonl")
    assert st.read_failed is True
    assert st.habits == []


# ── It reports habits when there are habits ────────────────────────────────

def test_the_thresholds_classify(tmp_path):
    rows = ([{"edge_hint": "habitual"}] * (HABITUAL_THRESHOLD + 1)
            + [{"edge_hint": "forming"}] * (FORMING_THRESHOLD + 1)
            + [{"edge_hint": "rare"}] * 2)
    levels = {h.edge_hint: h.level for h in read_habit_state(_signals(tmp_path, rows)).habits}
    assert "habitual" in levels and "forming" in levels
    assert "rare" not in levels
    assert levels["habitual"] != levels["forming"]


def test_the_block_is_non_empty_when_habits_exist(tmp_path):
    rows = [{"edge_hint": "close"}] * (HABITUAL_THRESHOLD + 5)
    assert habit_tracker_prompt_block(_signals(tmp_path, rows)).strip()


# ── Against the live store ─────────────────────────────────────────────────

def test_the_live_store_now_reports_the_habits_it_always_had():
    st = read_habit_state()
    if st.total_signals == 0:
        pytest.skip("no live signals")
    assert st.read_failed is False
    assert st.habits, "live signals present and still no habits"
    assert st.total_signals > 1000, st.total_signals
