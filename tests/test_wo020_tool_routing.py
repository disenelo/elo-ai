"""
tests/test_wo020_tool_routing.py — Acceptance tests for the WO-020 tool-layer
routing fix (GS-ROUTE-03).

The bug: tools/tool_router.py imported `is_playlist_intent` /
`is_search_play_intent` from tools/spotify_agent.py, but those functions did not
exist. The ImportError dropped the whole agent-import block into `except`,
setting `_HAS_LLM_FILE = False` — silently disabling the entire tool / search /
play path. Separately, "play the Joe Budden Podcast" did not match any
spotify/utility play pattern, so it fell through to plain conversation.

This test covers:
  T-1  spotify_agent.is_search_play_intent — named-thing play requests
  T-2  spotify_agent.is_search_play_intent — negatives (generic/control/not-play)
  T-3  spotify_agent.is_playlist_intent — playlist requests vs non-playlist
  T-4  "play the Joe Budden Podcast" routes to a play/media intent
  T-5  negative — "what's the weather" is NOT a play intent
  T-6  tools.tool_router imports cleanly → tool layer enabled (_HAS_LLM_FILE)

Run: python3 tests/test_wo020_tool_routing.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PASS = 0
FAIL = 0
TOTAL = 6


def ok(n):
    global PASS
    PASS += 1
    print(f"  ✅ {n}")


def fail(n, r):
    global FAIL
    FAIL += 1
    print(f"  ❌ {n}: {r}")


from tools.spotify_agent import is_playlist_intent, is_search_play_intent
from runtime.router.intent_engine import detect as _intent_detect
from tools import tool_router as _tr

_PLAY_INTENTS = {"utility_spotify", "spotify", "spotify_search", "spotify_playlist"}


# ── T-1: search+play fires on named things ────────────────────────────────────
try:
    for q in [
        "play the Joe Budden Podcast",
        "play Nights by Frank Ocean",
        "put on Fela Kuti",
        "play the latest episode of Darknet Diaries",
    ]:
        assert is_search_play_intent(q), f"is_search_play_intent should fire on {q!r}"
    ok("T-1: is_search_play_intent fires on named song/artist/podcast requests")
except AssertionError as e:
    fail("T-1", e)


# ── T-2: search+play does NOT fire on generic / control / non-play input ──────
try:
    for q in [
        "play",
        "play music",
        "play some music",
        "play something",
        "play that",
        "pause the song",
        "skip",
        "what's playing",
        "what's the weather",
    ]:
        assert not is_search_play_intent(q), (
            f"is_search_play_intent should NOT fire on {q!r}"
        )
    ok("T-2: is_search_play_intent stays quiet on generic/control/non-play input")
except AssertionError as e:
    fail("T-2", e)


# ── T-3: playlist intent ──────────────────────────────────────────────────────
try:
    for q in ["play my workout playlist", "put on the focus playlist",
              "shuffle my liked playlist"]:
        assert is_playlist_intent(q), f"is_playlist_intent should fire on {q!r}"
    for q in ["play the Joe Budden Podcast", "play some music", "what's the weather"]:
        assert not is_playlist_intent(q), f"is_playlist_intent should NOT fire on {q!r}"
    ok("T-3: is_playlist_intent fires only on real playlist requests")
except AssertionError as e:
    fail("T-3", e)


# ── T-4: "play the Joe Budden Podcast" routes to a play/media intent ──────────
try:
    intent = _intent_detect("play the Joe Budden Podcast").get("intent")
    assert intent in _PLAY_INTENTS, (
        f"intent_engine routed to {intent!r}, expected a play intent {_PLAY_INTENTS}"
    )
    ok(f"T-4: 'play the Joe Budden Podcast' routes to play intent ({intent})")
except AssertionError as e:
    fail("T-4", e)


# ── T-5: negative — weather is not a play intent ──────────────────────────────
try:
    intent = _intent_detect("what's the weather").get("intent")
    assert intent not in _PLAY_INTENTS, (
        f"'what's the weather' mis-routed to a play intent ({intent})"
    )
    assert not is_search_play_intent("what's the weather")
    ok(f"T-5: 'what's the weather' is NOT a play intent (routed {intent})")
except AssertionError as e:
    fail("T-5", e)


# ── T-6: tool layer imports cleanly (ImportError no longer swallowed) ─────────
try:
    assert _tr._HAS_LLM_FILE is True, (
        "_HAS_LLM_FILE is False — the agent import block is still failing"
    )
    assert _tr._agent_spotify is not None, "spotify agent did not import"
    assert _tr._is_playlist_intent is is_playlist_intent, (
        "tool_router bound a different is_playlist_intent (fell into except)"
    )
    assert _tr._is_search_play_intent is is_search_play_intent, (
        "tool_router bound a different is_search_play_intent (fell into except)"
    )
    ok("T-6: tools.tool_router imports cleanly — tool layer enabled")
except AssertionError as e:
    fail("T-6", e)


print(f"\nResult: {PASS}/{TOTAL} passed, {FAIL} failed")
sys.exit(1 if FAIL else 0)
