"""
tests/test_spg_content_index.py — WO-B2-0011.

An SPG node carried id, hash, significance, embodiment, ts — and nothing
readable. SPG could say THAT a moment mattered, never WHAT it was. Builder 1
hit it from the mock-backend side: nothing can read a node and get anything
back.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from faculties.spg import content_index as ci  # noqa: E402


@pytest.fixture(autouse=True)
def _isolated(tmp_path, monkeypatch):
    monkeypatch.setattr(ci, "INDEX_PATH", tmp_path / "spg_content.json")
    store = tmp_path / "interactions.json"
    store.write_text(json.dumps([
        {"user": "the seam will not lie flat", "response": "Show me.",
         "timestamp": "2026-10-01T10:00:00"},
        {"user": "User asked: what is Sugarcore?", "response": "A world.",
         "timestamp": "2026-10-01T10:01:00"},
    ]))
    monkeypatch.setattr("memory.spg_backfill.INTERACTIONS", store)
    return store


def test_a_node_becomes_readable():
    assert ci.sync_from_interactions() == 2
    got = ci.content_for("bf-00000-2026-10-01T10:00:00")
    assert "the seam will not lie flat" in got
    assert "Show me." in got


def test_the_key_is_the_node_id_the_graph_stores():
    """Joined on the same key build() mints, not on a guess about ordering."""
    ci.sync_from_interactions()
    assert ci.content_for("bf-00001-2026-10-01T10:01:00")


def test_prompt_scaffolding_is_stripped():
    """
    "User asked:" is assembled-prompt scaffolding, not something David said.
    It contaminated the corrections ledger the same way, which is why
    david_said() exists.
    """
    ci.sync_from_interactions()
    got = ci.content_for("bf-00001-2026-10-01T10:01:00")
    assert "User asked:" not in got
    assert "what is Sugarcore?" in got


def test_a_missing_node_reads_empty_not_wrong():
    """"" means this node predates the capture, not that the turn was empty."""
    assert ci.content_for("bf-99999-nope") == ""
    assert ci.content_for("") == ""


def test_syncing_twice_adds_nothing():
    assert ci.sync_from_interactions() == 2
    assert ci.sync_from_interactions() == 0


def test_text_is_bounded():
    assert ci.record_content("n1", "x" * 5000)
    assert len(ci.content_for("n1")) <= ci.MAX_CHARS


def test_empty_text_is_not_stored():
    assert ci.record_content("n2", "   ") is False
    assert ci.content_for("n2") == ""
