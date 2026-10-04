"""
tests/test_silence_gate.py — IS ELO: Capable of Silence?

    "can eLo decide not to respond?"
    "can eLo resist the pressure to always produce content?"

Answer before this: no, twice over.

  1. action == "silence" was consumed in ONE place in the turn path
     (server.py:704) and it returned a MOVEMENT intent — step_out or idle.
     A body decision. The response generated and was spoken regardless.

  2. Even an empty response could not survive. D-6 turns any empty response
     into "One sec — that came back empty. Ask me again?" — so choosing
     silence would have produced a sentence apologising for having nothing
     to say.
"""
from __future__ import annotations

import pytest

from runtime.silence_gate import (
    _CAL_ACTIONS,
    fallback_for_empty_response,
    is_deliberate_silence,
    last_was_deliberate_silence,
    mark_silence,
)


@pytest.fixture(autouse=True)
def _clean():
    mark_silence(False)
    yield
    mark_silence(False)


# ── Exactly one of the nine is silence ───────────────────────────────────────

def test_only_silence_silences():
    assert is_deliberate_silence("silence")
    for action in _CAL_ACTIONS:
        if action != "silence":
            assert not is_deliberate_silence(action), action


def test_the_nine_are_the_frozen_nine():
    """A tenth action cannot appear here either."""
    from runtime.executive import _CAL_ACTIONS as frozen
    assert _CAL_ACTIONS == frozen


@pytest.mark.parametrize("junk", ["", None, "quiet", "Silence ", "SILENCE"])
def test_only_the_exact_action_counts(junk):
    expected = str(junk or "").strip().lower() == "silence"
    assert is_deliberate_silence(junk) is expected


# ── A chosen silence survives D-6 ────────────────────────────────────────────

def test_a_chosen_silence_gets_no_fallback():
    assert fallback_for_empty_response("silence") is None


def test_an_accidental_empty_response_still_raises_the_alarm():
    """
    D-6 exists because an empty turn after a real question must never reach
    David looking like nothing happened. Silence must not become a hole that
    failures fall through.
    """
    for action in _CAL_ACTIONS:
        if action == "silence":
            continue
        out = fallback_for_empty_response(action)
        assert out and out.strip(), action


def test_repetition_suppression_still_stands():
    assert fallback_for_empty_response("answer", was_repetition_suppression=True) is None


# ── Causal: change the action, change whether eLo speaks ─────────────────────

def test_changing_the_action_changes_whether_anything_is_said():
    silent = fallback_for_empty_response("silence")
    spoken = fallback_for_empty_response("answer")
    assert silent is None and spoken is not None, (silent, spoken)


def test_the_flag_round_trips_and_clears():
    assert not last_was_deliberate_silence()
    mark_silence(True)
    assert last_was_deliberate_silence()
    mark_silence(False)
    assert not last_was_deliberate_silence()


# ── The wiring ───────────────────────────────────────────────────────────────
# Source-asserted, and said plainly: these check that server.py still calls
# the gate, not that the turn behaves. The logic above is the part that is
# behaviourally proven. A structural test that passes while the behaviour is
# dead is the failure mode I already hit once today, so these assert ORDER and
# EXCLUSIVITY — properties that break if the wiring is removed or bypassed,
# rather than the mere presence of an import.

def _server() -> str:
    from pathlib import Path
    return (Path(__file__).resolve().parent.parent / "server.py").read_text(encoding="utf-8")


def test_the_suppression_runs_before_the_empty_response_guard():
    """
    Order is the whole thing. D-6 substitutes a fallback for any empty
    response, so a silence applied after it would be overwritten with
    "One sec — that came back empty."
    """
    src = _server()
    suppress = src.index("is_deliberate_silence as _sg_is")
    guard = src.index("D-6 (card 0020): silent turn")
    assert suppress < guard, "silence is applied after D-6 — it would be overwritten"


def test_d6_asks_the_gate_instead_of_hardcoding_the_fallback():
    src = _server()
    assert "fallback_for_empty_response as _sg_fb" in src
    # The literal may appear exactly once: the except-branch default for when
    # the import itself fails. A second occurrence means D-6 is hardcoding
    # again and a chosen silence apologises for itself.
    assert src.count('"One sec — that came back empty. Ask me again?"') == 1


def test_the_turn_path_has_one_silence_consumer_for_speech():
    """
    Before this there were zero. If a second appears, two places decide
    whether eLo speaks and they can disagree.
    """
    src = _server()
    assert src.count("is_deliberate_silence") == 1
