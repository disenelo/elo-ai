"""
tests/test_dream_memory_write.py — a retained dream becomes a memory.

Board, 2026-10-10: `memory_written: false` on every dream cycle. The cause
was that nothing in the dream path had ever called the vault; the flag is
derived from `memory_refs` (a list of topic strings) in
runtime/executive.py:688, so it never reported a write.

These pin the three rules the write keeps: only retained, never as fact,
and never degenerate content.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from faculties.dream import dream_memory as dmem  # noqa: E402


@pytest.fixture(autouse=True)
def _isolated(tmp_path, monkeypatch):
    """Never touch the real cursor or the real vault."""
    monkeypatch.setattr(dmem, "CURSOR_PATH", tmp_path / "cursor.json")
    calls: list[dict] = []

    def _fake_write(**kw):
        calls.append(kw)
        return "SPOT-1"

    import memory.vault_layer as vl
    monkeypatch.setattr(vl, "write_memory", _fake_write)
    return calls


def _entry(**over):
    e = {
        "dream_id": "abc123",
        "retained": True,
        "significance": 0.80,
        "theme": "Fire",
        "insight": "What feels like waiting is actually preparation.",
        "narrative": "eLo moves through corridors built from half-remembered circuits.",
        "symbols": [{"name": "Fire", "meaning": "transformation", "weight": 1.2}],
    }
    e.update(over)
    return e


def test_a_retained_dream_is_written(_isolated):
    assert dmem.write_retained(_entry()) == "SPOT-1"
    assert len(_isolated) == 1


def test_an_unretained_dream_is_not_written(_isolated):
    assert dmem.write_retained(_entry(retained=False)) is None
    assert _isolated == []


def test_a_dream_below_threshold_is_not_written(_isolated):
    """
    retained=True disagreeing with the score means something upstream set the
    flag without the gate. memory_origin.py:116 — "Anything below this must
    NOT enter the main memory vault."
    """
    assert dmem.write_retained(_entry(significance=0.01)) is None
    assert _isolated == []


def test_degenerate_content_is_not_written(_isolated):
    """
    Observed on the first three retained dreams eLo ever had, 2026-10-10:
    insight was the single character "i" and narrative was "n". Writing that
    puts noise into permanent memory that every later recall steps over.
    """
    assert dmem.write_retained(_entry(insight="i", narrative="n")) is None
    assert _isolated == []


def test_a_degenerate_dream_is_not_retried_every_wake(_isolated):
    """It is recorded as handled, so waking does not re-attempt it forever."""
    dmem.write_retained(_entry(insight="i", narrative="n"))
    dmem.write_retained(_entry(insight="i", narrative="n"))
    assert _isolated == []


def test_the_same_dream_is_never_written_twice(_isolated):
    assert dmem.write_retained(_entry()) == "SPOT-1"
    assert dmem.write_retained(_entry()) is None
    assert len(_isolated) == 1


def test_it_is_written_as_hypothesis_never_fact(_isolated):
    """A dream proposes. It is not something eLo knows."""
    dmem.write_retained(_entry())
    kw = _isolated[0]
    assert kw["epistemic_class"] == "HYPOTHESIS"
    assert kw["source_type"] == "DREAM"
    assert "dream" in kw["tags"]
    assert "must not be repeated back as fact" in kw["deep_text"]


def test_the_narrative_carries_when_there_is_no_insight(_isolated):
    dmem.write_retained(_entry(insight=""))
    assert _isolated[0]["summary"].startswith("eLo moves through corridors")
