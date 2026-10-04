"""
tests/test_turn_result_shape.py — S2 Phase 1: one shape for every turn.

Audited with ast: _process_turn() has 52 returns, 43 of them turn-shaped,
and 41 of those carry only {"response", "mode", "backend"}. Every fast path
— the file agent, identity answers, animation commands, every bypass —
drops inner_thought, emotion and intent.

A consumer reading result["intent"] gets a KeyError on those turns, and
inner_thought is ABSENT rather than empty, which is indistinguishable from
a turn on which eLo thought nothing.
"""
from __future__ import annotations

import ast
import pathlib

import pytest

from runtime.turn_result import REQUIRED_KEYS, is_complete, normalise

_SERVER_PATH = pathlib.Path(__file__).resolve().parent.parent / "server.py"


# ── Every key present ───────────────────────────────────────────────────────

def test_a_fast_path_result_gains_the_missing_keys():
    """The exact shape 41 returns use."""
    out = normalise({"response": "Done.", "mode": "direct", "backend": "direct"})
    assert is_complete(out)
    for k in REQUIRED_KEYS:
        assert k in out


def test_nothing_the_turn_already_set_is_overwritten():
    full = {"inner_thought": "mine", "response": "r", "emotion": "joy",
            "intent": "build", "mode": "build", "backend": "ollama"}
    assert normalise(full) == full


def test_normalising_twice_changes_nothing():
    once = normalise({"response": "x", "mode": "direct"})
    assert normalise(once) == once


# ── The defaults are honest ─────────────────────────────────────────────────

def test_an_absent_inner_thought_is_empty_not_invented():
    """
    A placeholder sentence here would be authored text passed off as eLo's
    thought — the exact thing I was caught doing on 2026-09-29.
    """
    assert normalise({"response": "x"})["inner_thought"] == ""


def test_intent_is_taken_from_mode_not_guessed():
    """On the main path intent and mode are the same value (_action)."""
    assert normalise({"response": "x", "mode": "direct"})["intent"] == "direct"


def test_emotion_falls_back_to_the_documented_default():
    assert normalise({"response": "x"})["emotion"] == "neutral"


# ── Degenerate inputs ───────────────────────────────────────────────────────

def test_a_bare_string_becomes_a_response():
    assert normalise("hello")["response"] == "hello"


def test_none_is_a_reported_error_turn(caplog):
    import logging
    with caplog.at_level(logging.WARNING, logger="elo.turn_result"):
        out = normalise(None)
    assert out["intent"] == "error" and is_complete(out)
    assert caplog.text


def test_a_non_dict_is_not_silently_dropped():
    assert normalise(42)["response"] == "42"


# ── The audit, as a ratchet ────────────────────────────────────────────────

def _turn_shaped_returns() -> list[tuple[int, set]]:
    tree = ast.parse(_SERVER_PATH.read_text(encoding="utf-8"))
    found = []
    for fn in ast.walk(tree):
        if not isinstance(fn, ast.FunctionDef) or fn.name != "_process_turn":
            continue
        for n in ast.walk(fn):
            if isinstance(n, ast.Return) and isinstance(n.value, ast.Dict):
                ks = {k.value for k in n.value.keys if isinstance(k, ast.Constant)}
                if "response" in ks or "inner_thought" in ks:
                    found.append((n.lineno, ks))
    return found


def test_every_turn_exit_is_normalised_by_the_one_call_site():
    """
    41 partial exits is not a defect to fix 41 times. It is a defect to fix
    once, where they all land. This asserts the chokepoint still exists —
    if it goes, all 41 go partial again at once.
    """
    src = _SERVER_PATH.read_text(encoding="utf-8")
    code = "\n".join(l for l in src.splitlines() if not l.strip().startswith("#"))
    assert "from runtime.turn_result import normalise" in code
    assert "result = _tr_norm(result)" in code
    assert code.count("_process_turn(text)") == 1, "a second call site would bypass it"


def test_the_partial_exits_are_still_the_known_set():
    """
    A ratchet, not a cleanup order. Partial returns are fine BECAUSE the
    chokepoint normalises them — but if the count grows a lot, someone is
    adding exits without knowing the shape contract exists.
    """
    partial = [ln for ln, ks in _turn_shaped_returns()
               if not set(REQUIRED_KEYS) <= ks]
    assert len(partial) <= 45, f"{len(partial)} partial turn exits — was 41"


def test_at_least_one_exit_carries_the_full_object_itself():
    """The main path must not come to rely on the normaliser."""
    complete = [ln for ln, ks in _turn_shaped_returns()
                if set(REQUIRED_KEYS) <= ks]
    assert complete, "no exit builds the full turn object any more"
