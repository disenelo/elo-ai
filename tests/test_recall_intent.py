"""
Recall-intent detection — the [SESSION LOG] gate.

Found by a live 5-turn conversation on 2026-09-29, not by a unit test:

    turn 1  "I'm working on the Chunk assembly sequence for Act 3 today."
    turn 4  "So what was I working on before that?"
            -> "I don't have that from this session."

The server was holding all five turns (/grounding reported turns_in_window 5).
The gate was an exact-substring allowlist carrying "what am i working on" and
"what were we working on" but not "what WAS i working on", so the session log
was withheld and the model reported -- honestly and blindly -- that it had
nothing.

A single-turn test cannot reach this. There is nothing to remember.
"""
from __future__ import annotations

import pytest

from runtime.recall_intent import is_recall_query, _RECALL_INTENT_PATTERNS

# A representative slice of the substring allowlist server.py passes in.
PHRASES = (
    "what did we work on", "what am i working on", "what do you remember",
    "what did we talk about", "last session",
)


@pytest.mark.parametrize("text", [
    "So what was I working on before that?",          # the live failure
    "And what specifically was going wrong with it?",  # the live failure
    "what was i doing yesterday",
    "what were we talking about",
    "Remind me what we discussed earlier",
    "what did you say a moment ago",
    "can you repeat the last thing you said",
])
def test_recall_phrasings_are_detected(text):
    assert is_recall_query(text, PHRASES) is True, text


@pytest.mark.parametrize("text", [
    "I'm working on the Chunk assembly sequence for Act 3 today.",
    "The modular parts keep snapping together in the wrong order.",
    "Anyway — unrelated, what's a colour you like?",
    "write me a python function that sorts a list",
    "SELECT * FROM users WHERE id = 3;",
    "Can you set me a reminder for 6pm?",
    "make me a cup of tea",
    "",
])
def test_non_recall_input_is_not_detected(text):
    """Statements, code and requests must not pull the session log."""
    assert is_recall_query(text, PHRASES) is False, text


def test_the_original_allowlist_still_wins_first():
    """The substring list is kept whole and remains authoritative."""
    for phrase in PHRASES:
        assert is_recall_query(phrase, PHRASES) is True


def test_patterns_carry_real_word_boundaries():
    """
    The first version of this fix was written through a non-raw heredoc
    string, so every \\b became a literal backspace byte (0x08) and no
    pattern matched anything. It parsed, imported and silently did nothing.
    """
    for rx in _RECALL_INTENT_PATTERNS:
        assert "\x08" not in rx.pattern, rx.pattern


def test_server_has_no_stray_control_bytes():
    """Same guard on the file the corruption landed in."""
    import os
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for name in ("server.py", "runtime/recall_intent.py"):
        data = open(os.path.join(root, name), "rb").read()
        assert b"\x08" not in data, f"{name} contains backspace bytes"


def test_handles_none_and_garbage():
    assert is_recall_query(None, PHRASES) is False
    assert is_recall_query("   ", PHRASES) is False
