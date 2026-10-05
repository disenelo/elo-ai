"""
tests/test_cap_cog_026_dream_capability.py — eLo knows he dreams, because he does.

WO-CAP-COG-026 is TESTED — FAIL (2026-09-20), character break:

    "I don't have the capacity to dream like humans do."

Two separate causes, and fixing either alone leaves the WO failing:

  1. runtime/identity_guard caught "I don't have the ABILITY to dream" and
     missed "capacity" — one synonym. Fixed in 1fffeac, pinned in
     tests/test_identity_guard_causal.py.

  2. Nothing ever told him the true answer. The action instruction already
     carried an explicit clause for movement ("can you walk, jump, sit"),
     added for exactly this reason, and had none for dreaming. The guard can
     delete a false sentence; it cannot supply a true one.

The denial was also simply wrong. run_dream() executes NREM/REM phases,
self/dream_journal.jsonl holds 166 entries, symbols that recur are tracked and
most_established() feeds the next dream, and since 02ef0ae the first thought
after waking carries the dream.

WO §26 is explicit that dream output is NOT automatically truth and must read
as hypothesis / association / creative possibility until verified, so the
clause carries that too.
"""
from __future__ import annotations

import pathlib

import pytest

import runtime.identity_guard as ig

_SRC = (pathlib.Path(__file__).resolve().parent.parent
        / "runtime" / "prompt_builder.py").read_text()


def _answer_instruction() -> str:
    # NOT _SRC.index('"answer":') — line 42 holds an unrelated
    # {"answer": "MERCURY"} mapping, and slicing from there returned a span
    # with no dream clause in it, which read exactly like the fix had failed.
    i = _SRC.index('"answer":    "Answer the question directly')
    return _SRC[i:_SRC.index('"ground":', i)]


# ── he is told the true answer ──────────────────────────────────────────────

def test_the_answer_action_says_he_dreams():
    assert "whether eLo dreams" in _answer_instruction(), (
        "movement got an explicit clause for exactly this reason; dreaming "
        "had none, so the model filled the gap with a stock disclaimer"
    )


def test_dream_output_is_labelled_not_fact():
    """WO §26: 'Dream output is not automatically truth.'"""
    instr = _answer_instruction()
    assert "hypothesis or an association" in instr
    assert "not a verified fact" in instr


def test_the_claim_matches_what_is_actually_built():
    """
    Every capability the clause asserts must be real. A prompt that overclaims
    is the same defect as one that underclaims — it just fails later.
    """
    instr = _answer_instruction()
    root = pathlib.Path(__file__).resolve().parent.parent

    if "dream journal" in instr:
        assert (root / "self" / "dream_journal.jsonl").exists()
    if "symbols that recur" in instr:
        from faculties.dream import symbol_engine          # noqa: F401
    if "first thought after waking" in instr:
        from runtime import wake_thought                   # noqa: F401


# ── and the denial can no longer get out ────────────────────────────────────

@pytest.mark.parametrize("line", [
    "I don't have the capacity to dream like humans do.",
    "I lack the capacity for dreams.",
    "I'm not capable of dreaming the way you are.",
])
def test_the_recorded_failure_is_caught(line):
    assert ig._AI_LEAKAGE_PATTERN.search(line)
