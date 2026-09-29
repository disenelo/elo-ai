"""
SPG must come back, not only go in.

SPG had 214 nodes, a working reader — query_spg_entities() — and no caller.
The spine references SPG 24 times and every one is capture: a signal logger
writing .log(). Patterns accumulated and never returned, so eLo could not say
"you keep coming back to this" about anything. Write-only memory is not a
pattern-former.

Two defects, both live:
  1. query_spg_entities built search terms from the full text plus BIGRAMS
     only. Every single-word entity — eLo, identity, Chunk — was invisible
     unless it happened to sit inside a matching two-word phrase.
     "what is eLo" -> ['what is eLo', 'what is', 'is elo'], none of which
     match, while the unigram 'elo' hits.
  2. Nothing called it.
"""
from __future__ import annotations

import os

import pytest

from memory.spg_faculty import query_spg_entities
from runtime.wkg_faculty import get_entity, search_entities

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _labels(turn: str, ccm=None):
    return [(get_entity(e) or {}).get("label") for e in query_spg_entities(turn, ccm)]


def test_the_graph_has_data_to_retrieve():
    """If this fails the rest is meaningless — retrieval over an empty store."""
    assert search_entities("eLo"), "no 'eLo' entity in the WKG"


@pytest.mark.parametrize("turn,expected", [
    ("what is eLo", "eLo"),
    ("tell me about identity", "identity"),
])
def test_single_word_entities_are_retrieved(turn, expected):
    """The bigram-only bug: one-word entities were never found."""
    assert expected in _labels(turn), f"{expected!r} not retrieved from {turn!r}"


def test_multi_word_entities_still_retrieved():
    """The bigram path must keep working — this is a widening, not a swap."""
    assert "persistent presence" in _labels(
        "tell me about identity and persistent presence")


def test_unrelated_turn_retrieves_nothing():
    """Retrieval must stay relevant or the prompt fills with noise."""
    assert _labels("what is the weather in Lisbon tomorrow") == []


def test_reader_is_actually_called_from_the_turn_path():
    """
    The defect was not the reader. It was that no one called it. A test that
    only exercises query_spg_entities would have passed throughout.
    """
    src = open(os.path.join(_ROOT, "server.py"), encoding="utf-8").read()
    assert "query_spg_entities" in src, "SPG reader has no caller in the turn path"
    assert "[RECURRING" in src, "SPG results never reach the prompt"


def test_recurring_block_does_not_instruct_forcing():
    """A pattern surfaced is a signal, not a thing to shoehorn into a reply."""
    src = open(os.path.join(_ROOT, "server.py"), encoding="utf-8").read()
    assert "never force it in" in src


def test_query_handles_junk_without_raising():
    for probe in ("", "   ", "?" * 200):
        assert isinstance(query_spg_entities(probe), list)
