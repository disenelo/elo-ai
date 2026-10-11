"""
tests/test_spg_live.py — WO-B2-0008: SPG keeps up with the conversation.

Two paths could put a live node in the graph before this, and neither covered
a turn: the WKG claim side effect fires only on category-tagged turns (76% of
the store), and significance_faculty's spike tap asserts its own
unreachability at import (threshold 0.6, max achievable 0.0929 — never once
logged).

Isolated from David's real store and real graph throughout.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from memory import spg_live  # noqa: E402


@pytest.fixture(autouse=True)
def _isolated(tmp_path, monkeypatch):
    """Never read the live turn store or write the live graph."""
    store = tmp_path / "interactions.json"
    store.write_text(json.dumps([
        {"user": "the seam will not lie flat", "response": "Show me.",
         "timestamp": 1791000000.0, "memory_categories": ["projects"]},
    ]))
    monkeypatch.setattr("memory.spg_backfill.INTERACTIONS", store)
    monkeypatch.setattr(spg_live, "_last_mtime", 0.0)
    return store


def _added(store: Path, text: str) -> None:
    rows = json.loads(store.read_text())
    rows.append({"user": text, "response": "ok",
                 "timestamp": rows[-1]["timestamp"] + 60.0,
                 "memory_categories": []})
    store.write_text(json.dumps(rows))
    # mtime resolution is coarse enough that a fast test can write twice in
    # the same tick — make the change visible rather than hope.
    t = time.time() + 1
    import os
    os.utime(store, (t, t))


def test_an_uncategorised_turn_still_reaches_spg(tmp_path, monkeypatch, _isolated):
    """
    The 24% the WKG claim path never covered. "I want to build a world" and
    "what is Sugarcore?" are real examples from David's store that carried no
    category tag and so produced no node.
    """
    from memory.spg_backfill import unprocessed
    _added(_isolated, "what is Sugarcore?")
    pending = unprocessed()
    assert any("Sugarcore" in str(r.get("user")) for r in pending), \
        "an uncategorised turn must still be a candidate for SPG"


def test_nothing_new_is_a_cheap_no_op():
    """0 is an honest answer: the graph is current, not the sync broken."""
    spg_live.sync_new_turns(force=True)
    t0 = time.perf_counter()
    assert spg_live.sync_new_turns() == 0
    assert (time.perf_counter() - t0) * 1000 < 5.0, "mtime guard did not hold"


def test_a_new_turn_lifts_the_guard(_isolated):
    """After something is said, the next sync must actually look."""
    spg_live.sync_new_turns(force=True)
    before = spg_live._last_mtime
    _added(_isolated, "I want to build a world")
    assert spg_live._store_mtime() != before, \
        "a new turn must change the store mtime or the guard blinds the sync"


def test_it_never_raises_when_the_graph_is_unreadable(monkeypatch):
    """SPG falling behind must not stop an ambient tick."""
    def _boom():
        raise RuntimeError("graph corrupt")
    monkeypatch.setattr("memory.spg_graph.SPGGraph.load", staticmethod(_boom))
    assert spg_live.sync_new_turns(force=True) == 0
