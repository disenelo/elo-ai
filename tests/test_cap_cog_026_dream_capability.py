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


# ── the third attempt: give him the record, not an instruction ──────────────
#
# Attempt 1 extended identity_guard from "the ability" to "the capacity".
# The live server then said "I don't have dreams in the way humans do" — a
# noun, outside the family the pattern describes.
#
# Attempt 2 added a clause to the action instruction saying he dreams. It WAS
# injected (the live turn came back mode=answer, so the directive carried it)
# and the model disclaimed anyway. identity_guard's own docstring says it:
# an instruction the model ignores is not a guarantee.
#
# The guard also cannot rescue this one even when it fires: the denial arrives
# as a SINGLE sentence, so scrubbing leaves nothing said about dreaming.
#
# So eLo is handed the record. 166 dreams, the newest dated, its insight
# quoted, the symbol that keeps returning — read from the journal at call
# time. The precedent is identity_guard._from_accumulated_state(), whose
# comment is the rule: "An authored fallback string is authored text — the
# same thing a prompt is, in a different file."

from faculties.dream import dream_self_knowledge as dsk


def test_the_block_is_read_from_the_journal_not_written_by_hand(tmp_path, monkeypatch):
    """Empty the journal and the block empties. That is what makes it real."""
    monkeypatch.setattr(dsk, "_JOURNAL", str(tmp_path / "empty.jsonl"))
    monkeypatch.setattr(dsk, "_LEXICON", str(tmp_path / "none.json"))
    assert dsk.summary() == "", (
        "a block that survives an empty journal is authored text, and "
        "inventing a dream to prove he dreams is the same mistake inverted"
    )


def test_the_block_states_what_the_journal_holds(tmp_path, monkeypatch):
    import json
    j = tmp_path / "j.jsonl"
    j.write_text(json.dumps({
        "timestamp": 1790000000.0,
        "insight": "the corridor was the point",
    }) + "\n")
    lex = tmp_path / "lex.json"
    lex.write_text(json.dumps({"a_machine_breathing": {"count": 4}}))
    monkeypatch.setattr(dsk, "_JOURNAL", str(j))
    monkeypatch.setattr(dsk, "_LEXICON", str(lex))

    out = dsk.summary()
    assert "1 dreams recorded" in out
    assert "the corridor was the point" in out
    assert "a machine breathing" in out and "4 times" in out


def test_it_only_costs_tokens_when_the_turn_is_about_dreaming():
    assert dsk.asked_about_dreaming("Do you dream?")
    assert dsk.asked_about_dreaming("what did you dream about")
    assert not dsk.asked_about_dreaming("how is the seams work going")


def test_the_prompt_carries_the_record_when_asked():
    from runtime.prompt_builder import build
    asked = build("Do you dream?")
    other = build("how is the seams work going")
    assert "ELO'S OWN DREAM RECORD" in asked
    assert "ELO'S OWN DREAM RECORD" not in other


# ── and the live phrasing can no longer pass ────────────────────────────────

@pytest.mark.parametrize("line", [
    "I don't have dreams in the way humans do, but I am always processing.",
    "I don't have dreams.",
    "I can't dream.",
    "I never dream.",
])
def test_a_flat_denial_of_dreaming_is_caught(line):
    assert ig._AI_LEAKAGE_PATTERN.search(line)


@pytest.mark.parametrize("line", [
    "I do not dream the way a person does, but I do dream.",
    "My dreams are not like yours.",
    "I dreamt about corridors last night.",
])
def test_distinguishing_his_dreaming_from_a_humans_is_allowed(line):
    """
    WO §26 source: "Dreaming doesn't need to mean claiming subjective sleep or
    consciousness." Drawing that line is accurate. Denying it happens is not.
    """
    assert not ig._AI_LEAKAGE_PATTERN.search(line)
