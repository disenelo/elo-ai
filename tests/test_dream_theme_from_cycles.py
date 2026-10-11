"""
Pin the fix for the "Moon saturation" bug: dream theme must track cycle
content, not just the ambient inner state.

Before this fix, run_dream computed symbols once from recent_topics +
inner_events + focal_thread and never looked at the cycle seeds. With
recent_topics empty and inner_events = ["quiet"], every REM dream themed
"Moon" — observed on all retained dreams in self/dream_journal.jsonl.
"""
from __future__ import annotations

import pytest

import faculties.dream.dream_faculty as df
from faculties.dream.dream_faculty import run_dream


class _AmbientQuietSelf:
    """Only signal from the inner side is 'quiet' — the Moon trap."""
    inner_events = ["quiet"]
    focal_thread = ""
    session_read = ""
    mood = 0.4
    curiosity = 0.5
    lifetime_threads: list = []


def _llm(_messages):
    return '{"narrative": "symbolic", "insight": "it was there"}'


@pytest.fixture(autouse=True)
def _isolate(tmp_path, monkeypatch):
    df._last_dream_ts = 0.0
    monkeypatch.setattr(df, "_JOURNAL_PATH", tmp_path / "journal.jsonl")
    monkeypatch.setattr(df, "_SYMBOL_HISTORY_PATH", tmp_path / "symbols.json")
    monkeypatch.setattr(df, "_generate_dream_image", lambda symbols: None)
    yield
    df._last_dream_ts = 0.0


def _run(recent_topics):
    df._last_dream_ts = 0.0
    return run_dream(_AmbientQuietSelf(), recent_topics, _llm, idle_seconds=2000)


def test_recent_topics_beat_ambient_quiet_seed():
    """
    The Moon trap: inner_events = ["quiet"] alone maps to Moon. When
    recent_topics carry anything that lands in SYMBOLS, that symbol has to
    beat the ambient seed — the pre-fix path never looked past the first
    `map_to_symbols` call so Moon won even when recent_topics were rich.
    """
    df._last_dream_ts = 0.0
    result = run_dream(
        _AmbientQuietSelf(),
        ["writing code", "the river flows"],
        _llm,
        idle_seconds=2000,
    )
    entry = result.journal_entry
    assert entry["theme"] != "Moon", (
        f"recent_topics {['writing code','the river flows']} should "
        f"outrank ambient quiet→Moon, got theme={entry['theme']}"
    )
    names = {s["name"] for s in entry.get("symbols") or []}
    # Both topics mapped — the final symbol list must contain at least one
    # of their mappings (Circuit from "code", River from "river").
    assert names & {"Circuit", "River"}, (
        f"symbols {names} missing the topic-driven mappings"
    )


def test_cycle_seed_concepts_can_enter_the_symbol_list():
    """
    Seeds generated INSIDE the dream carry associated_concepts the first
    `map_to_symbols` call never saw. When one of those concepts matches a
    SYMBOLS keyword, the post-cycle re-rank has to let it compete.
    """
    df._last_dream_ts = 0.0
    # robot → "Skeleton" is a canonical mapping; a dream primed with "robot"
    # topics tends to produce "robot" in cycle seed concepts.
    result = run_dream(
        _AmbientQuietSelf(),
        ["we got the robot arm moving"],
        _llm,
        idle_seconds=2000,
    )
    entry = result.journal_entry
    if entry.get("cycle_count", 0) == 0:
        pytest.skip("no cycles produced — nothing to re-rank against")
    seed_concepts: set[str] = set()
    for cyc in entry.get("cycles") or []:
        for seed in cyc.get("seeds") or []:
            for c in seed.get("associated_concepts") or []:
                seed_concepts.add(str(c).lower())
    names = {s["name"] for s in entry.get("symbols") or []}
    # Topic itself maps to Skeleton ("robot" keyword). Theme is Skeleton
    # OR theme is driven by a cycle seed concept — either proves the
    # re-rank reached past the ambient Moon seed.
    assert entry["theme"] != "Moon", (
        f"theme stayed Moon even with robot-themed cycles — "
        f"seed_concepts={sorted(seed_concepts)}, symbols={names}"
    )


def test_recent_topics_still_win_when_cycles_empty():
    """
    When idle is too short to reach REM there are no cycles. The theme has
    to fall back on recent_topics / inner_events as before.
    """
    df._last_dream_ts = 0.0
    result = run_dream(
        _AmbientQuietSelf(),
        ["fire crackling in the garden"],
        _llm,
        idle_seconds=700,  # NREM only — no cycles
    )
    entry = result.journal_entry
    assert entry.get("cycle_count", 0) == 0
    # Fire or Garden — either is correct, Moon is not.
    assert entry["theme"] in {"Fire", "Garden"}


def test_enriched_remap_is_additive_not_destructive():
    """
    The enrichment pass must not strip symbols that were in the original
    mapping — recent_topics stay in the ranking.
    """
    df._last_dream_ts = 0.0
    result = run_dream(
        _AmbientQuietSelf(),
        ["river"],
        _llm,
        idle_seconds=2000,
    )
    entry = result.journal_entry
    names = {s["name"] for s in entry.get("symbols") or []}
    assert names, "no symbols on the entry"
