"""
tests/test_symbol_engine_topic_weight.py — the symbol engine must track the
conversation, not the ambient state.

Builder 2 reported 2026-10-11: ten dreams forced across ten distinct topics
(the seam, the studio at night, barkcloth, Hackney Wick, something unfinished)
every one came back themed "Moon". The dream model had just started working;
what the test revealed is that `inner_events=["quiet"]` seeded "moon" at
weight 1.2, higher than any single topic match at 1.0, so the ambient state
dominated every dream regardless of what the conversation was about.

This pins the fix: a single matched topic now outranks a single matched
inner-event seed. "quiet"-moon stays as a fallback for turns with no topic
match, but it no longer crowds out real content.
"""
from __future__ import annotations

from faculties.dream.symbol_engine import SYMBOLS, map_to_symbols


def _top(symbols):
    return symbols[0]["symbol"] if symbols else None


def test_a_matched_topic_outranks_the_quiet_moon_seed():
    syms = map_to_symbols(
        topics=["the seam"],
        inner_events=["quiet"],
        focal_thread="",
    )
    assert _top(syms) == "Weave", (
        f"topic 'seam' must outrank the ambient 'quiet' seed, got {syms!r}"
    )


def test_quiet_still_wins_when_no_topic_is_there_to_outrank_it():
    syms = map_to_symbols(topics=[], inner_events=["quiet"], focal_thread="")
    assert _top(syms) == "Moon", (
        f"'quiet' fallback must still produce Moon when nothing else is in play, got {syms!r}"
    )


def test_the_ten_topics_from_the_filing_now_map_to_distinct_symbols():
    topics_from_filing = [
        "the seam",                  # Weave
        "the studio at night",       # Workshop (studio) + Night
        "barkcloth",                 # Weave (cloth)
        "Hackney Wick",              # Place
        "something unfinished",      # LooseEnd
    ]
    symbol_set: set[str] = set()
    for t in topics_from_filing:
        syms = map_to_symbols([t], ["quiet"], "")
        symbol_set.add(_top(syms))

    # Before the fix: every one of these returned "Moon".
    assert "Moon" not in symbol_set, (
        f"topics still swamped by 'quiet'-Moon seed: {symbol_set!r}"
    )
    assert len(symbol_set) >= 4, (
        f"ten topics must produce at least four distinct top symbols, got {symbol_set!r}"
    )


def test_focal_thread_still_wins_over_a_topic_match():
    """
    The thread is the most specific signal of what eLo is holding across the
    session. A session-wide focus must still outrank a single mentioned topic.
    """
    syms = map_to_symbols(
        topics=["blender"],
        inner_events=[],
        focal_thread="the seam",
    )
    assert _top(syms) == "Weave"


def test_multiple_matched_topics_still_accumulate():
    """
    Previously-passing behaviour: four topics all pointing at the same symbol
    accumulate weight. This is what test_wo012_dream_phases Ch2-FT-1 pins.
    """
    garden_topics = ["garden city", "digital garden",
                     "grow the project", "garden of ideas"]
    syms = map_to_symbols(garden_topics, [], "")
    garden = [s for s in syms if s["symbol"] == "Garden"]
    assert len(garden) == 1
    assert garden[0]["weight"] >= 3.0, (
        f"four garden topics must still accumulate to ≥3.0, got {garden[0]!r}"
    )


def test_the_textile_vocabulary_is_in_the_library():
    """The DISENELO Seams and Plushies work happens in these words."""
    for keyword in ("seam", "stitch", "pattern", "fabric", "cloth", "plush"):
        assert keyword in SYMBOLS, f"missing textile keyword: {keyword!r}"


def test_the_night_and_studio_vocabulary_is_in_the_library():
    for keyword in ("night", "studio", "workshop"):
        assert keyword in SYMBOLS, f"missing place/time keyword: {keyword!r}"


def test_the_loose_end_vocabulary_is_in_the_library():
    for keyword in ("unfinished", "pending", "loose"):
        assert keyword in SYMBOLS, f"missing loose-end keyword: {keyword!r}"
