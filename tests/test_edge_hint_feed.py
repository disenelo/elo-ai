"""
tests/test_edge_hint_feed.py — three faculties fed an edge_hint that never existed.

"a system capable of noticing novelty?"
"a system capable of recognising prediction error?"
"can eLo decide not to respond?"

server.py injects three faculties that all key off edge_hint — the
interaction type for the turn. All three were fed nothing, each in a
different way:

  novelty_detector     _plan.edge_hint, guarded by hasattr(...). CognitivePlan
  expectation_tracker  has NO edge_hint field, so hasattr is False and both
                       received "" on every turn. novelty_prompt_block("")
                       scores an empty hint, never clears the threshold, and
                       returns "" for the life of the process.

  silence_faculty      reads a bare `_edge_hint`. That name appears exactly
                       ONCE in server.py — on the line that reads it. It is
                       never assigned. NameError, swallowed by the
                       surrounding except, block never reaches the prompt.

The faculties themselves work: called directly with a real edge_hint they
all produce content. Three correct components, three empty seams, three
different causes, all silent.

THE RIGHT SOURCE, not a guess. spine.py writes edge_hint into the signals
from plan.execution_report.planned_action and from the relationship
posture, which is why the live store's values are the nine CAL actions plus
"close". The plan field carrying that is conversation_action.
"""
from __future__ import annotations

import ast
import dataclasses
import pathlib

import pytest

from runtime.spine.plan import CognitivePlan

_SERVER_PATH = pathlib.Path(__file__).resolve().parent.parent / "server.py"
_SERVER = _SERVER_PATH.read_text(encoding="utf-8")


# ── Why it was broken ──────────────────────────────────────────────────────

def test_the_plan_has_no_edge_hint_field():
    """
    Documents the cause rather than asserting it away. _plan.edge_hint could
    never have resolved, and the hasattr guard turned that into "" instead of
    an error — so it failed silently for the life of the process.
    """
    names = {f.name for f in dataclasses.fields(CognitivePlan)}
    assert "edge_hint" not in names


def test_the_plan_does_carry_the_conversation_action():
    names = {f.name for f in dataclasses.fields(CognitivePlan)}
    assert "conversation_action" in names


# ── One derivation, defined before it is used ──────────────────────────────

def test_edge_hint_is_assigned_before_any_read():
    """
    The silence block read a name that was never assigned anywhere in the
    file. An undefined read inside a try/except is invisible — it looks
    exactly like a faculty with nothing to say.
    """
    assigns, reads = [], []
    for node in ast.walk(ast.parse(_SERVER)):
        if isinstance(node, ast.Name) and node.id == "_edge_hint":
            (assigns if isinstance(node.ctx, ast.Store) else reads).append(node.lineno)
    assert assigns, "_edge_hint is read but never assigned"
    assert min(assigns) < min(reads), (min(assigns), min(reads))


def test_all_three_faculties_use_the_same_derivation():
    """Three copies of a derivation is three chances to drift."""
    for marker in ("_nov_pb(edge_hint=_edge_hint",
                   "_exp_pb(edge_hint=_edge_hint",
                   "_silence_pb(edge_hint=_edge_hint"):
        assert marker in _SERVER.replace(" ", "").replace("\n", "") or \
               marker.replace("(", "(") in _SERVER, marker


def test_the_derivation_names_a_field_the_plan_actually_has():
    """
    Checks the PROPERTY, not a spelling. An earlier version asserted
    "_plan.edge_hint" was absent, and a wire-cut to
    getattr(_plan, "edge_hint", "") sailed past it — same defect, different
    syntax, and getattr's default makes it silent all over again.
    """
    code = "\n".join(l for l in _SERVER.splitlines() if not l.strip().startswith("#"))
    line = next(l for l in code.splitlines() if "_edge_hint =" in l)

    names = {f.name for f in dataclasses.fields(CognitivePlan)}
    used = {m for m in __import__("re").findall(r'getattr\(_plan,\s*"(\w+)"', line)}
    used |= {m for m in __import__("re").findall(r'_plan\.(\w+)', line)}
    assert used, f"no plan field read in: {line.strip()}"
    assert used <= names, f"derives from fields CognitivePlan does not have: {used - names}"


# ── The faculties work when fed ────────────────────────────────────────────

def test_silence_faculty_produces_content_for_a_real_hint():
    from runtime.silence_faculty import silence_faculty_prompt_block
    assert silence_faculty_prompt_block(edge_hint="silence").strip()


def test_expectation_tracker_produces_content_for_a_real_hint():
    from memory.expectation_tracker import expectation_prompt_block
    assert expectation_prompt_block(edge_hint="answer").strip()


def test_an_empty_hint_is_what_silenced_novelty():
    """
    novelty returns "" for an empty hint — correct behaviour, and exactly
    what it received on every turn.
    """
    from memory.novelty_detector import novelty_prompt_block
    assert novelty_prompt_block(edge_hint="") == ""


# ── The vocabulary matches ─────────────────────────────────────────────────

def test_the_conversation_actions_are_the_edge_hints_the_store_holds():
    """
    If the plan's vocabulary did not match the signals', feeding it would
    swap one silent faculty for one that never matches anything.
    """
    import json
    from runtime.executive import _CAL_ACTIONS
    path = pathlib.Path(__file__).resolve().parent.parent / "data" / "spg_signals.jsonl"
    if not path.exists():
        pytest.skip("no live signals")
    seen = set()
    with open(path, encoding="utf-8") as f:
        for line in f:
            try:
                h = json.loads(line).get("edge_hint")
            except Exception:
                continue
            if h:
                seen.add(h)
    assert seen & set(_CAL_ACTIONS), (sorted(seen)[:10], _CAL_ACTIONS)
