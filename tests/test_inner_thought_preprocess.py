"""
tests/test_inner_thought_preprocess.py — inner thought BEFORE the answer.

David, 2026-10-10: "inner thoughts can alter the outcome, and that makes him
more real to what eLo should be."

The thing these pin is the gate. An inner thought that fires on every turn is
how eLo started narrating his own telemetry, and a short factual ask must stay
short: "5 x 52?" -> "5*52 = 260". So the tests care at least as much about
what is NOT injected.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from faculties.inner_thought import preprocess as pp  # noqa: E402


@pytest.fixture(autouse=True)
def _isolated(tmp_path, monkeypatch):
    """
    Never read David's live state. Learned twice in two days -- a test that
    reaches into a live store passes or fails on what his machine is doing.
    """
    state = tmp_path / "self_state.json"
    state.write_text(json.dumps({"open_threads": ["the robot shell seam"]}))
    qs = tmp_path / "open_questions.json"
    qs.write_text(json.dumps([
        {"text": "how does the seam hold?", "topic": "seam", "surfaced": "False"},
    ]))
    monkeypatch.setattr(pp, "_SELF_STATE", state)
    monkeypatch.setattr(pp, "_OPEN_QUESTIONS", qs)
    monkeypatch.setattr(
        "faculties.inner_thought.working_memory.as_context",
        lambda: "[WORKING MEMORY]\n13:54 Code\n13:55 Chrome")


# ── what must NOT happen ─────────────────────────────────────────────────────

def test_a_short_factual_ask_is_untouched():
    """The arithmetic turn. Brevity is correct here, not drift."""
    p = pp.pre_thought("5 x 52?")
    assert p["complex"] is False
    assert p["inject"] == ""


def test_a_weather_question_is_untouched():
    p = pp.pre_thought("What's the weather like right now?")
    assert p["inject"] == ""


def test_working_memory_is_not_injected_into_an_unrelated_turn():
    """
    The timeline is app focus -- "13:54 Code". It answers "what were you
    doing" and is noise everywhere else. Injecting it on every complex turn
    is the telemetry-narration defect.
    """
    p = pp.pre_thought("How are you feeling about the robot shell seam today?")
    assert "working_memory" not in p["signals"]


def test_it_never_raises_on_junk():
    for junk in (None, "", "   ", 12345, {"not": "a string"}):
        assert pp.pre_thought(junk)["inject"] == "" or True  # must not raise


# ── what must happen ─────────────────────────────────────────────────────────

def test_an_anaphoric_turn_is_complex():
    """"that thing" means nothing without the last turn."""
    ok, why = pp.is_complex("Can you carry on with that from earlier?")
    assert ok and "anaphoric" in why


def test_a_turn_about_him_is_complex():
    # Not "how are you finding it?" -- "it" is anaphoric and that rule fires
    # first. Both verdicts are correct; this pins the about-him rule alone.
    ok, why = pp.is_complex("How are you today?")
    assert ok and "about him" in why


def test_asking_what_he_was_doing_reaches_working_memory():
    p = pp.pre_thought("What were you just doing?")
    assert "working_memory" in p["signals"]
    assert "13:55 Chrome" in p["inject"]


def test_a_turn_overlapping_an_open_thread_surfaces_it():
    p = pp.pre_thought("I have been thinking more about the seam on that shell")
    assert "open_threads" in p["signals"]
    assert "the robot shell seam" in p["inject"]


def test_the_injection_tells_the_model_not_to_recite_it():
    """Context for him, not material to read out."""
    p = pp.pre_thought("What were you just doing?")
    assert "do not quote it" in p["inject"].lower()
    assert "not material to recite" in p["inject"].lower()


def test_it_resolves_fast_enough_to_sit_before_generation():
    """
    The whole reason this is not the LLM inner voice: that one measured 4
    tokens in 17.8s under contention. This must be free.
    """
    p = pp.pre_thought("Can you carry on with that from earlier?")
    assert p["elapsed_ms"] < 50, p["elapsed_ms"]


def test_the_verdict_is_inspectable():
    """`why` exists so a later reader can audit the decision."""
    assert pp.pre_thought("5 x 52?")["why"]
    assert pp.pre_thought("What were you just doing?")["why"]


# ── the thought must be readable, not only audible ───────────────────────────

def test_a_collected_thought_is_published_to_the_ui(monkeypatch):
    """
    David, 2026-10-11: "I hear it" but "the -- thoughts don't show anymore".

    Unity surfaces `inner_thought_text` from blender_state.json. server.py
    wrote that key from its POST-response block, gated on the thought it
    collected there. WO-INNER-THOUGHT-ORDERING moved speaking to Beat 2,
    before the response, so the later collect() correctly returned ""
    (idempotent — eLo must not say it twice) and the UI write was gated on the
    same empty string. Spoken, never written.
    """
    from faculties.inner_thought import early_runner as er

    written: list[dict] = []
    monkeypatch.setattr("blender_bridge.state_writer.patch", written.append)

    class _Handle:
        def collect(self, timeout_s=None):
            return "  i keep circling the same seam  "

    assert er.collect(_Handle()).strip() == "i keep circling the same seam"
    assert written == [{"inner_thought_text": "i keep circling the same seam"}]


def test_no_thought_writes_nothing(monkeypatch):
    """An empty collect must not blank the UI — the last thought stands."""
    from faculties.inner_thought import early_runner as er

    written: list[dict] = []
    monkeypatch.setattr("blender_bridge.state_writer.patch", written.append)

    class _Empty:
        def collect(self, timeout_s=None):
            return ""

    assert er.collect(_Empty()) == ""
    assert er.collect(None) == ""
    assert written == []


def test_publishing_failure_never_costs_the_thought(monkeypatch):
    """A thought that cannot be published is still a thought."""
    from faculties.inner_thought import early_runner as er

    def _boom(_payload):
        raise RuntimeError("bridge down")

    monkeypatch.setattr("blender_bridge.state_writer.patch", _boom)

    class _Handle:
        def collect(self, timeout_s=None):
            return "still a thought"

    assert er.collect(_Handle()) == "still a thought"
