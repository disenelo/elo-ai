"""
tests/test_wkg_junk_entities.py — the WKG entity writer creates junk.

Live store, read 2026-10-03: 34 entities, three of them "Tell", "Raspberry"
and "What". All three are CONCEPT entities created by
memory_faculty.populate_wkg_from_turn().

They are not cosmetic. test_spg_feedback_loop::test_unrelated_turn_retrieves_
nothing started failing the day "What" appeared, because SPG retrieval now
searches unigrams and "what is the weather in Lisbon tomorrow" matches an
entity called What. Junk in the store becomes junk in retrieval becomes junk
in the prompt.

Two separate defects in _extract_wkg_topics():

  1. `\\b[A-Z][a-zA-Z]{2,}\\b` matches ANY capitalised word, so the first word
     of a sentence becomes an entity. "What is eLo?" → What. "Tell me about
     Chunk" → Tell.
  2. A word already inside a captured multi-word run is captured AGAIN on its
     own, so "Raspberry Pi" yields both "Raspberry Pi" and "Raspberry".

Fixed at the writer, not at retrieval. Filtering these out when reading would
leave the store growing junk forever and hide it from the next reader.
"""
from __future__ import annotations

import pytest

from memory.memory_faculty import _extract_wkg_topics


def _labels(text: str) -> list[str]:
    return _extract_wkg_topics(text)


# ── Defect 1: sentence openers ────────────────────────────────────────────────

@pytest.mark.parametrize("text,junk", [
    ("What is eLo?", "What"),
    ("Tell me about Chunk", "Tell"),
    ("How does K-7 work", "How"),
    ("Why did the build fail", "Why"),
    ("When are you free", "When"),
    ("Can you open Blender", "Can"),
    ("Does the servo need calibration", "Does"),
    ("Should we ship the addon", "Should"),
    ("The pattern is finished", "The"),
    ("This is the plan", "This"),
])
def test_a_sentence_opener_is_not_an_entity(text, junk):
    assert junk not in _labels(text), f"{text!r} → {_labels(text)}"


def test_the_three_that_are_actually_in_the_live_store():
    """The exact shapes that produced Tell, What and Raspberry."""
    assert "Tell" not in _labels("Tell me about the robot")
    assert "What" not in _labels("What is the weather in Lisbon tomorrow")
    assert "Raspberry" not in _labels("the Raspberry Pi 5 runs the brain")


# ── Defect 2: fragments of multi-word entities ───────────────────────────────

def test_a_word_inside_a_multiword_entity_is_not_also_its_own_entity():
    out = _labels("the Raspberry Pi 5 drives the NeoPixel ring")
    assert "Raspberry Pi" in out
    assert "Raspberry" not in out
    assert "NeoPixel ring" in out or "NeoPixel" in out


def test_the_multiword_form_is_the_one_kept():
    out = _labels("Marvelous Designer exports the pattern")
    assert "Marvelous Designer" in out
    assert "Marvelous" not in out
    assert "Designer" not in out


# ── Still extracts what it should ────────────────────────────────────────────

@pytest.mark.parametrize("text,wanted", [
    ("eLo needs a new Blender addon", "Blender"),
    ("Chunk becomes the vehicle", "Chunk"),
    ("the shell is printed in TPU", "TPU"),
    ("push the NLA strips to Unity", "NLA"),
    ("working on DISENELO Seams today", "DISENELO Seams"),
])
def test_real_topics_survive(text, wanted):
    assert wanted in _labels(text), f"{text!r} → {_labels(text)}"


def test_a_quoted_phrase_is_still_a_topic():
    assert "forward kinematics" in _labels('explain "forward kinematics" to me')


def test_a_capitalised_opener_that_is_also_a_real_topic_survives_mid_sentence():
    """
    "Can" is a stopword; a genuine topic that happens to open a sentence must
    still be found when it appears anywhere else.
    """
    out = _labels("Blender is open. I use Blender daily.")
    assert "Blender" in out


# ── The read side of the same rule ───────────────────────────────────────────

def test_retrieval_does_not_search_the_store_for_function_words():
    """
    Adding unigrams to SPG retrieval was mine (0372243) and it was half a
    change. A function word identifies no entity, whatever the store happens
    to hold, so "what" should never have been a search term — independent of
    the writer defect that put a What in there.

    Bigrams and the full text are deliberately untouched: "the shell" is a
    real phrase and filtering it would lose real retrievals.
    """
    import memory.spg_faculty as spg

    searched: list[str] = []

    def _spy(term):
        searched.append(term)
        return []

    import runtime.wkg_faculty as wkg
    orig = wkg.search_entities
    wkg.search_entities = _spy
    try:
        spg.query_spg_entities("what is the weather in Lisbon tomorrow")
    finally:
        wkg.search_entities = orig

    unigrams = [t for t in searched if " " not in t]
    assert "what" not in unigrams, unigrams
    assert "the" not in unigrams, unigrams
    assert "lisbon" in unigrams, "a real unigram must still be searched"
    assert any(" " in t for t in searched), "bigrams must survive the filter"


# ── Second junk class: code tokens and string literals ──────────────────────
#
# Found 2026-10-04 by auditing entities the running server created AFTER the
# sentence-opener fix. The function-word class is gone; this one is not:
#
#   'Hello, {name}!'    a template string
#   'Hello, World!\n'   a string literal, escape sequence and all
#   '...'               punctuation, no letters at all
#   'Console'           half of Console.WriteLine
#   'WriteLine'         the other half
#
# Different cause, same result. The quoted-phrase rule takes anything
# between quotes, and the capitalised-token rule takes both halves of a
# dotted identifier.
#
# NOT ATTEMPTED: rejecting CamelCase identifiers generally. "WriteLine" is
# the same shape as "NeoPixel" and "DISENELO", and no rule tells them apart
# without knowing the text is code. Only the unambiguous cases are rejected
# here; a CamelCase word that is not part of a dotted path still gets in,
# and that is the honest limit of a shape-based extractor.

@pytest.mark.parametrize("text,junk", [
    ('print("Hello, {name}!")',      "Hello, {name}!"),
    (r'print("Hello, World!\n")',    "Hello, World!\\n"),
    ('he said "..." and stopped',    "..."),
    ('use "x = y;" there',           "x = y;"),
    ('try "foo()" instead',          "foo()"),
])
def test_a_code_string_is_not_a_concept(text, junk):
    assert junk not in _labels(text), f"{text!r} -> {_labels(text)}"


def test_a_dotted_identifier_is_not_two_concepts():
    out = _labels("call Console.WriteLine to print it")
    assert "Console" not in out, out
    assert "WriteLine" not in out, out


def test_a_sentence_boundary_is_not_a_dotted_identifier():
    """"Blender. Then Unity." must still yield both — the dot has a space."""
    out = _labels("I opened Blender. Then Unity loaded.")
    assert "Blender" in out and "Unity" in out, out


def test_a_real_quoted_phrase_still_survives():
    assert "forward kinematics" in _labels('explain "forward kinematics" to me')


def test_camelcase_product_names_still_survive():
    """The limit, asserted so it is a decision and not an accident."""
    out = _labels("the NeoPixel ring on the DISENELO build")
    assert "NeoPixel" in out or "NeoPixel ring" in out, out
