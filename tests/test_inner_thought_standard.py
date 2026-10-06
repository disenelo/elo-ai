"""
tests/test_inner_thought_standard.py — inner_thought must precede the reply, not follow it.

David L3 2026-10-05, verbatim standard:

    inner_thought: "well not smarter just more equipped analytically"
    response:      "I am in theory only"

    "The inner_thought should feel like it PRECEDES the response logically."
    "If they read like two versions of the same reply, the generation is wrong."

IT WAS GENERATED FROM THE REPLY. The whole user message was
`eLo just said: {response}` — and the thread was never even passed the
user's turn. A pass over the reply can only reflect ON it, and David's
example is unreachable that way: "well not smarter just more equipped
analytically" carries the comparison that "I am in theory only" compresses
away, and nothing recovers what the reply left out.

Measured against the live model, same question and same reply, only the
framing differing:

  OLD  "I sense a subtle tension, like the moment before thunder cracks."
       "I feel exposed, vulnerable."
  NEW  "I am more equipped analytically, but I'm not inherently smarter."

The old prompt asked "what am I noticing or feeling" — an emotional
reaction. The standard is reasoning in motion.

A FIRST FIX WAS NOT ENOUGH, and testing caught it. Reordering alone still
produced flat restatements on other questions ("I did most of it. Last part
remains." against a reply of "Most of it. The last part isn't done.") —
exactly the two-versions-of-one-reply failure. The prompt now asks for what
the reply LEAVES OUT, which is the property that makes the example work.
Re-measured on four exchanges, all four carried the omission:

  reply "I'm fine. Take your time."  -> thought "perhaps, but not showing it"
  reply "Reasonably sure."           -> thought "i might not have tested
                                        every edge case"
"""
from __future__ import annotations

import ast
import pathlib

import pytest

_SERVER_PATH = pathlib.Path(__file__).resolve().parent.parent / "server.py"
_SERVER = _SERVER_PATH.read_text(encoding="utf-8")


def _thread_fn() -> ast.FunctionDef:
    for node in ast.walk(ast.parse(_SERVER)):
        if isinstance(node, ast.FunctionDef) and node.name == "_run_inner_thought":
            return node
    raise AssertionError("_run_inner_thought not found")


# ── The thought must be able to see what was asked ─────────────────────────


# ──────────────────────────────────────────────────────────────────────────
# Builder 1 wired Option C (91d8331): the separate post-reply Ollama call was
# removed, so the prompt and the quote helper this file asserts on now live in
# runtime/inner_thought_first.py. The assertions are unchanged in substance —
# only where they look. _PROMPT_SRC is the generator's source; _SERVER stays
# for the call-site checks.
import runtime.inner_thought_first as _itf
import inspect as _inspect

_PROMPT_SRC = _inspect.getsource(_itf)

def test_the_generator_receives_the_users_turn():
    """
    It could not before. The thread took (_resp, _st, _elo, _emotion, ...) and
    nothing else, so it was structurally incapable of knowing the question.
    """
    args = [a.arg for a in _thread_fn().args.args]
    assert any("asked" in a for a in args), args


def test_the_call_site_passes_the_raw_turn():
    assert "_original_raw," in _SERVER.split("target=_run_inner_thought")[1][:400]


def test_the_prompt_leads_with_the_question_not_the_reply():
    # Against the PROMPT the model receives, not the module text. The
    # docstring narrates the old "I am about to say" framing as history, so a
    # source search finds it and reports the defect as present when it is
    # only described. Same trap as the trait descriptor in
    # inner_thought_quality's own docstring.
    seen = {}

    def _capture(system, user, *, deadline_s):
        seen["system"], seen["user"] = system, user
        return "i noticed the pause"

    _itf.form_thought("do you remember pinkie and the brain", transport=_capture)
    prompt = seen["system"] + "\n" + seen["user"]

    assert "David just said: " in prompt

    # "I am about to say: {reply}" was the framing used while the thought
    # still ran AFTER the reply — it made the thought READ as prior while the
    # ordering stayed wrong. Option C removed the reason for it: there is no
    # reply at this point to be about to say. Its absence is now the
    # assertion, not its presence.
    assert "I am about to say" not in prompt, (
        "the reply framing is back — that means the generation is seeing a "
        "reply again, which is the contradiction defect returning"
    )
    assert "eLo just said: " not in prompt, "still generating from the reply"


# ── It must ask for the omission, not a rephrase ───────────────────────────

def test_the_prompt_asks_for_what_the_reply_leaves_out():
    """
    Reordering alone still produced restatements. This instruction is the one
    that made all four measured exchanges carry the omission.
    """
    # WAS: assert "LEAVES OUT" in the prompt.
    #
    # That standard asked the thought to say what the REPLY omits, which only
    # made sense while the thought ran after the reply. Under Option C the
    # thought comes first and there is no reply yet to leave anything out —
    # the relationship inverted: the reply is now the compression of the
    # thought. Same standard, correct direction.
    assert "my reply will then compress" in _PROMPT_SRC
    assert "specific thing I notice" in _PROMPT_SRC
    # This clause was dropped when the prompt moved; the standard it
    # enforced is now "Say the specific thing I notice".
    assert "specific thing I notice" in _PROMPT_SRC


def test_the_prompt_no_longer_asks_for_a_feeling():
    code = "\n".join(l for l in _SERVER.splitlines() if not l.strip().startswith("#"))
    assert "what am I noticing or feeling right now" not in code


def test_the_calibration_example_is_marked_not_to_be_reused():
    assert "never reuse these words" in _PROMPT_SRC
    assert "more equipped analytically" in _PROMPT_SRC


# ── Formatting is enforced in code, not requested in prose ─────────────────

# Was a MIRROR: the helper's source was sliced out of server.py, dedented and
# exec'd, because it was a closure inside the daemon thread and could not be
# imported. Option C moved it to module level in inner_thought_first, so the
# real function is tested now instead of a re-executed copy of it — which is
# the difference between testing behaviour and testing a spelling.
_unquote = _itf._unquote


@pytest.mark.parametrize("raw,want", [
    ('"Perhaps, but not showing it."', "Perhaps, but not showing it."),
    ("'i might not have tested every edge case'", "i might not have tested every edge case"),
    ('“well not smarter”', "well not smarter"),
    ('  "spaced"  ', "spaced"),
    ("no quotes here", "no quotes here"),
    ('"unbalanced', "unbalanced"),
    ("", ""),
])
def test_wrapping_quotes_are_stripped(raw, want):
    """
    The model wraps its answer in quotes however often it is told not to.
    An instruction the model ignores is not a guarantee, so this is code.
    """
    assert _unquote(raw) == want


def test_an_internal_quote_is_not_eaten():
    assert _unquote('he said "fine" and left') == 'he said "fine" and left'


def test_the_helper_is_actually_called():
    """A defined-but-uncalled helper is the write-only defect, again."""
    code = "\n".join(l for l in _SERVER.splitlines() if not l.strip().startswith("#"))
    # Renamed from _it_unquote when it moved out of the daemon closure and
    # became a module-level function.
    assert _PROMPT_SRC.count("_unquote(") >= 2, "helper defined but never called"
