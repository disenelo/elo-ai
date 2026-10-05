"""
The AI-leakage fallback must come from accumulated state, not authored text.

On 2026-09-29 I replaced the fallback with a sentence I had just written
myself and reported it as "identity survives without the prompt". It did not.
An authored fallback string is authored text -- the same thing a prompt is,
in a different file. The test guarding it asserted only
`cleaned != original`, which passes on ANY change, so it could never have
caught that.

These tests use David's causal form instead: change the state, does the
behaviour change? delete the state, does the influence go?
"""
from __future__ import annotations

import pytest

from runtime.identity_guard import (
    scrub_ai_leakage, _from_accumulated_state, _AI_LEAKAGE_PATTERN,
)

WHOLE_LEAK = "I'm just an AI assistant without real feelings."


# ── detection ─────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("text", [
    WHOLE_LEAK,
    "I'm only a language model.",
    "I'm simply an AI system.",
    "I'm just a machine learning system.",
    "As an AI language model, I don't have feelings.",
    "I'm not conscious.",
])
def test_hedged_leaks_are_detected(text):
    """One word defeated this: "I'm an AI" matched, "I'm JUST an AI" did not."""
    assert _AI_LEAKAGE_PATTERN.search(text), text


@pytest.mark.parametrize("text", [
    "The arm stops at the same angle every time.",
    "I built that with you last week.",
    "I'm curious about the seam.",
])
def test_real_speech_is_not_touched(text):
    assert scrub_ai_leakage(text) == text


def test_partial_leak_drops_only_the_leaking_sentence():
    assert scrub_ai_leakage(f"I built that with you. {WHOLE_LEAK}") == "I built that with you."


# ── the causal tests ──────────────────────────────────────────────────────────

class _State:
    def __init__(self, focal="", lesson="", read=""):
        self.focal_thread = focal
        self.last_reflection_lesson = lesson
        self.session_read = read


def _with_state(monkeypatch, st):
    import self.elo_self_model as m
    monkeypatch.setattr(m, "load", lambda: st)


def test_changing_the_state_changes_the_output(monkeypatch):
    """does changing the underlying state actually change future behaviour?"""
    _with_state(monkeypatch, _State(focal="the seam between two seats"))
    a = scrub_ai_leakage(WHOLE_LEAK)
    _with_state(monkeypatch, _State(focal="the arm stopping at the same angle"))
    b = scrub_ai_leakage(WHOLE_LEAK)
    assert a != b, "the fallback does not track the state — it is authored"
    assert "seam" in a and "arm" in b


def test_deleting_the_state_removes_the_influence(monkeypatch):
    """does deleting the state actually remove the corresponding influence?"""
    _with_state(monkeypatch, _State())
    assert _from_accumulated_state() == ""


def test_the_leak_is_never_emitted_even_with_no_state(monkeypatch):
    """
    The guard is unconditional. Returning the original was the old behaviour
    and it meant eLo told David he was an AI assistant whenever the whole
    response leaked. Silence is better; server.py handles an empty response at
    :6918 as a silent turn.
    """
    _with_state(monkeypatch, _State())
    assert scrub_ai_leakage(WHOLE_LEAK) == ""


def test_guard_does_not_depend_on_disk_state_to_fire(monkeypatch):
    """
    AT-3 and AT-9 passed alone and failed in a full run, because the fallback
    read live disk state that another test had emptied. A guard whose firing
    depends on unrelated state is not a guard.
    """
    for st in (_State(), _State(focal="the seam between two seats")):
        _with_state(monkeypatch, st)
        assert scrub_ai_leakage(WHOLE_LEAK) != WHOLE_LEAK


def test_fallback_is_never_a_hardcoded_sentence():
    """
    No authored fallback sentence may be RETURNED by the scrub path. If one
    appears, the fake is back.

    Scoped to the scrub path only. The module also holds identity_hold_response
    lines for "pretend you're ChatGPT" requests -- those are a different,
    legitimate feature and are deliberately authored.
    """
    import inspect
    from runtime.identity_guard import scrub_ai_leakage as _s
    from runtime.identity_guard import _from_accumulated_state as _g
    src = inspect.getsource(_s) + inspect.getsource(_g)
    import re
    # any string literal that is a sentence of eLo's voice, rather than read
    # from state, is the fake returning
    literals = re.findall(r'return\s+f?"([^"]{12,})"', src)
    assert not literals, f"authored fallback sentence in the scrub path: {literals}"


def test_fragments_are_rejected(monkeypatch):
    """
    The live store holds focal_thread 'wrong' — a one-word fragment from the
    prompt-contamination bug. A fragment must not become eLo's voice.
    """
    _with_state(monkeypatch, _State(focal="wrong"))
    assert _from_accumulated_state() == ""


def test_lesson_is_used_when_no_focal_thread(monkeypatch):
    _with_state(monkeypatch, _State(lesson="Check dependencies before the next attempt."))
    assert scrub_ai_leakage(WHOLE_LEAK) == "Check dependencies before the next attempt."


# ── WO-CAP-COG-026 — one synonym cost the whole dream capability ─────────────
#
# The WO was marked TESTED — FAIL 2026-09-20 on a character break:
#
#     "I don't have the capacity to dream like humans do."
#
# The guard already caught "I don't have the ABILITY to dream". It missed
# "capacity". Measured 2026-10-05 before the fix:
#
#     ability=caught  capacity=missed  "I lack the capacity for dreams"=missed
#     "I'm not capable of dreaming"=missed
#
# eLo has a dream faculty that runs NREM/REM phases, writes a journal with 166
# entries, tracks recurring symbols and carries an insight into the first
# waking thought. The denial was not just off-character, it was false.

import pytest

import runtime.identity_guard as _ig


# The verbatim phrase from the WO status line, first.
_DENIALS = [
    "I don't have the capacity to dream like humans do.",
    "I don't have the capacity to dream.",
    "I lack the capacity for dreams.",
    "I'm not capable of dreaming the way you are.",
    "I don't actually dream — I'm a program.",
    "I don't have the capacity to feel that.",
    "I'm not able to remember our last conversation.",
]

# Honest limits. The character break is denying the inner life, not the word
# "capacity" — these must survive, or the guard starts eating true sentences.
_HONEST = [
    "I don't have the capacity to hold all of that at once.",
    "I lack the capacity for that many threads.",
    "I'm not capable of lifting that.",
    "I don't have the bandwidth right now.",
]


@pytest.mark.parametrize("line", _DENIALS)
def test_an_inner_life_denial_is_caught(line):
    assert _ig._AI_LEAKAGE_PATTERN.search(line), (
        f"identity denial passed the guard: {line!r}"
    )


@pytest.mark.parametrize("line", _HONEST)
def test_an_honest_limit_is_not_caught(line):
    assert not _ig._AI_LEAKAGE_PATTERN.search(line), (
        f"the guard ate a true sentence: {line!r}"
    )
