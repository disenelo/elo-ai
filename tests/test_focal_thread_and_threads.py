"""
What eLo says he keeps returning to must be what he keeps returning to.

Live, self/elo_self_state.json, 2026-09-29:

    focal thread this session: "wrong"
    what eLo keeps returning to across sessions: about, [world_knowledge,
                                                 elo's, (verified

Two separate defects behind one sentence:

  focal_thread took meaningful[-1] — the LAST content word of the turn. For
  "the modular parts keep snapping together in the wrong order" that is
  "wrong". Word order, not attention.

  lifetime_threads tokenised the enriched `raw`, so prompt syntax accumulated
  ~1000 counts, and the len>4 filter passed function words, so "about" (103)
  outranked "stuck" (38) and "building" (21).
"""
from __future__ import annotations

import json
import os
import re

import pytest

from self.elo_self_model import _update_focal_thread, _accumulate_lifetime

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_LIFETIME = [["stuck", 38], ["building", 21], ["chunk", 12]]


def test_focal_thread_prefers_what_recurs_over_what_came_last():
    assert _update_focal_thread("", ["chunk", "assembly", "sequence"], _LIFETIME) == "chunk"
    assert _update_focal_thread("", ["hello", "building"], _LIFETIME) == "building"


def test_focal_thread_is_not_the_last_word():
    """The live failure: 'wrong' was chosen because it came last."""
    topics = ["modular", "parts", "snapping", "together", "wrong", "order"]
    assert _update_focal_thread("", topics, _LIFETIME) != "wrong"
    assert _update_focal_thread("", topics, _LIFETIME) != "order"


def test_focal_thread_kept_when_turn_offers_nothing():
    assert _update_focal_thread("the seam", ["a", "it", "is"], _LIFETIME) == "the seam"


def test_focal_thread_changes_when_history_changes():
    """Causal: the same turn resolves differently under different history."""
    topics = ["chunk", "building"]
    a = _update_focal_thread("", topics, [["chunk", 99], ["building", 1]])
    b = _update_focal_thread("", topics, [["chunk", 1], ["building", 99]])
    assert a == "chunk" and b == "building", (a, b)


# ── the live store ────────────────────────────────────────────────────────────

def _live_threads():
    p = os.path.join(_ROOT, "self", "elo_self_state.json")
    if not os.path.isfile(p):
        pytest.skip("no live self-state on this machine")
    return json.load(open(p, encoding="utf-8")).get("lifetime_threads", [])


def test_no_prompt_fragments_in_lifetime_threads():
    stray = [t[0] for t in _live_threads()
             if isinstance(t, (list, tuple)) and t
             and (str(t[0]).startswith(("[", "("))
                  or str(t[0]).lower() in {"world_knowledge", "verified", "elo's"})]
    assert not stray, f"prompt syntax in eLo's lifetime threads: {stray}"


def test_no_stopwords_in_lifetime_threads():
    src = open(os.path.join(_ROOT, "server.py"), encoding="utf-8").read()
    i = src.index("_so_skip = frozenset({")
    skip = set(re.findall(r'"([a-z\']+)"', src[i:src.index("})", i)]))
    stray = [t[0] for t in _live_threads()
             if isinstance(t, (list, tuple)) and t and str(t[0]).lower() in skip]
    assert not stray, f"stopwords ranked as lifelong threads: {stray}"


def test_the_skip_list_covers_common_function_words():
    """These outranked real threads before being added."""
    src = open(os.path.join(_ROOT, "server.py"), encoding="utf-8").read()
    i = src.index("_so_skip = frozenset({")
    skip = set(re.findall(r'"([a-z\']+)"', src[i:src.index("})", i)]))
    for w in ("about", "these", "there", "would", "just", "think", "really"):
        assert w in skip, f"{w!r} would accumulate as a lifetime thread"


def test_accumulator_still_counts_real_topics():
    out = _accumulate_lifetime([["chunk", 3]], ["chunk", "assembly"])
    counts = {t[0]: t[1] for t in out}
    assert counts["chunk"] == 4 and counts["assembly"] == 1
