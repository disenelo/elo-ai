"""
tests/test_wkg_deprecate_entity.py — retire a junk entity without deleting it.

Four entities in the live WKG are artefacts of the writer defect fixed in
WO-WKG-JUNK-001:

    Tell · What · You   — sentence openers, captured because the extractor
                          matched any capitalised word
    Raspberry           — a fragment of "Raspberry Pi", captured again on
                          its own

They are not knowledge. "What" matched the question "what is the weather in
Lisbon tomorrow" during SPG retrieval, which is how they were found.

The writer no longer produces them, but these four were already stored, and
deleting rows from eLo's memory is not how this project corrects things —
information gets superseded, not removed.

So: deprecation. The row stays, with a reason, a timestamp, and for a
fragment the id of the entity that supersedes it. What changes is
DISCOVERY: search_entities() stops offering them. Claims that reference
them still resolve, because a claim recorded against "Raspberry" really was
recorded, and breaking that would be rewriting history to tidy the index.
"""
from __future__ import annotations

import json

import pytest

import runtime.wkg_faculty as wkg


@pytest.fixture
def _store(tmp_path, monkeypatch):
    d = tmp_path / "wkg"
    d.mkdir()
    src = __import__("pathlib").Path(wkg.__file__).resolve().parent.parent / "memory" / "wkg"
    (d / "relationship_types.json").write_text(
        (src / "relationship_types.json").read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(wkg, "_WKG_DIR", str(d))
    from memory.spg_graph import SPGGraph
    monkeypatch.setattr(SPGGraph, "load", classmethod(lambda cls, *a, **k: SPGGraph()))
    monkeypatch.setattr(SPGGraph, "save", lambda self, *a, **k: None)
    return d


# ── The row survives ────────────────────────────────────────────────────────

def test_deprecating_keeps_the_row(_store):
    e = wkg.create_entity(entity_type="CONCEPT", label="What", description="")
    wkg.deprecate_entity(e["entity_id"], reason="function word")
    rows = json.loads((_store / "entities.json").read_text(encoding="utf-8"))
    assert len(rows) == 1, "the row was deleted"
    assert rows[0]["entity_id"] == e["entity_id"]


def test_the_reason_and_time_are_recorded(_store):
    e = wkg.create_entity(entity_type="CONCEPT", label="Tell", description="")
    wkg.deprecate_entity(e["entity_id"], reason="sentence opener, WO-WKG-JUNK-001")
    row = json.loads((_store / "entities.json").read_text(encoding="utf-8"))[0]
    assert row["deprecated"] is True
    assert "WO-WKG-JUNK-001" in row["deprecated_reason"]
    assert row["deprecated_at"] > 0


def test_a_fragment_points_at_what_supersedes_it(_store):
    pi = wkg.create_entity(entity_type="CONCEPT", label="Raspberry Pi", description="")
    frag = wkg.create_entity(entity_type="CONCEPT", label="Raspberry", description="")
    wkg.deprecate_entity(frag["entity_id"], reason="fragment",
                         superseded_by=pi["entity_id"])
    rows = {r["entity_id"]: r for r in
            json.loads((_store / "entities.json").read_text(encoding="utf-8"))}
    assert rows[frag["entity_id"]]["superseded_by"] == pi["entity_id"]
    assert rows[pi["entity_id"]].get("deprecated") is not True


# ── Discovery stops; the record does not ────────────────────────────────────

def test_search_no_longer_offers_a_deprecated_entity(_store):
    e = wkg.create_entity(entity_type="CONCEPT", label="You", description="")
    assert wkg.search_entities("You")
    wkg.deprecate_entity(e["entity_id"], reason="function word")
    assert wkg.search_entities("You") == []


def test_it_can_still_be_found_on_purpose(_store):
    e = wkg.create_entity(entity_type="CONCEPT", label="You", description="")
    wkg.deprecate_entity(e["entity_id"], reason="function word")
    found = wkg.search_entities("You", include_deprecated=True)
    assert [f["entity_id"] for f in found] == [e["entity_id"]]


def test_a_live_entity_is_unaffected(_store):
    wkg.create_entity(entity_type="CONCEPT", label="Blender", description="")
    e = wkg.create_entity(entity_type="CONCEPT", label="What", description="")
    wkg.deprecate_entity(e["entity_id"], reason="function word")
    assert [x["label"] for x in wkg.search_entities("Blender")] == ["Blender"]


def test_claims_about_a_deprecated_entity_still_resolve(_store):
    """
    History is not rewritten to tidy the index. A claim recorded against
    "Raspberry" really was recorded.
    """
    pi = wkg.create_entity(entity_type="CONCEPT", label="Raspberry Pi", description="")
    frag = wkg.create_entity(entity_type="CONCEPT", label="Raspberry", description="")
    claim = wkg.record_claim(frag["entity_id"], "PART_OF", pi["entity_id"],
                             "VERIFIED", source_id="t")
    wkg.deprecate_entity(frag["entity_id"], reason="fragment",
                         superseded_by=pi["entity_id"])
    about = wkg.get_claims_about(frag["entity_id"])
    assert [c["claim_id"] for c in about] == [claim["claim_id"]]
    assert wkg.get_entity(frag["entity_id"]) is not None


# ── Causal ──────────────────────────────────────────────────────────────────

def test_undeprecating_restores_discovery(_store):
    """Reversible. A wrong call must not be a one-way door."""
    e = wkg.create_entity(entity_type="CONCEPT", label="Chunk", description="")
    wkg.deprecate_entity(e["entity_id"], reason="mistake")
    assert wkg.search_entities("Chunk") == []
    wkg.deprecate_entity(e["entity_id"], reason="", undo=True)
    assert [x["label"] for x in wkg.search_entities("Chunk")] == ["Chunk"]


def test_deprecating_an_unknown_id_changes_nothing(_store):
    wkg.create_entity(entity_type="CONCEPT", label="Chunk", description="")
    before = (_store / "entities.json").read_text(encoding="utf-8")
    assert wkg.deprecate_entity("no-such-id", reason="x") is False
    assert (_store / "entities.json").read_text(encoding="utf-8") == before
