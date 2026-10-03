"""
tests/test_spg_ccm_filter.py — the CCM dim filter in query_spg_entities is dead.

_CCM_DIM_RELEVANT_RELS maps each CCM dimension to the WKG relationship types
"relevant in that context", and the filter then calls get_claims_by_type()
for each. Checked against memory/wkg/relationship_types.json on 2026-10-03:

    FEELS  WORKING_ON  STATED  DECIDED  FACT  OBSERVATION  BELIEF  RELATIONSHIP

None of those eight is in the 19-type vocabulary. Eleven of the map's twelve
names cannot exist on a claim, so get_claims_by_type() returns [] every time
and the filter selects nothing, for every dim, on every turn. Only
ASSOCIATED_WITH was real.

This is the same shape as the node/claim join in the function above it: a
layer that looks live, runs on every turn, and contributes nothing — and it
survived because an unknown relationship name fails SILENTLY. The guard below
is the part that matters more than the remap: a name that does not exist must
be loud, or the next edit reintroduces this.
"""
from __future__ import annotations

import json
import logging
import os

import pytest

import memory.spg_faculty as spg


def _vocabulary() -> set[str]:
    path = os.path.join(os.path.dirname(spg.__file__), "wkg",
                        "relationship_types.json")
    with open(path, encoding="utf-8") as f:
        return set(json.load(f))


# ── The defect ────────────────────────────────────────────────────────────────

def test_every_mapped_relationship_exists_in_the_vocabulary():
    vocab = _vocabulary()
    bad = {
        dim: [r for r in rels if r not in vocab]
        for dim, rels in spg._CCM_DIM_RELEVANT_RELS.items()
    }
    bad = {d: r for d, r in bad.items() if r}
    assert not bad, f"relationship types that cannot exist on a claim: {bad}"


def test_every_dimension_maps_to_something_usable():
    """A dim with no valid types is a dim that can never filter."""
    vocab = _vocabulary()
    for dim, rels in spg._CCM_DIM_RELEVANT_RELS.items():
        assert [r for r in rels if r in vocab], dim


# ── The guard that stops it coming back ──────────────────────────────────────

def test_an_unknown_relationship_name_is_reported_not_swallowed(caplog):
    """
    The map was wrong for its whole life because a bad name costs nothing —
    get_claims_by_type() just returns []. Checked and logged instead.
    """
    with caplog.at_level(logging.WARNING, logger="memory.spg_faculty"):
        unknown = spg._unknown_relationship_types({"d": ["IS", "NOT_A_REAL_TYPE"]})
    assert unknown == {"d": ["NOT_A_REAL_TYPE"]}
    assert "NOT_A_REAL_TYPE" in caplog.text


def test_the_live_map_passes_its_own_guard(caplog):
    with caplog.at_level(logging.WARNING, logger="memory.spg_faculty"):
        assert spg._unknown_relationship_types() == {}
    assert "cannot exist" not in caplog.text


def test_the_guard_survives_a_missing_vocabulary(monkeypatch):
    """No vocabulary file is not a reason to start reporting everything bad."""
    monkeypatch.setattr(spg, "_relationship_vocabulary", lambda: set())
    assert spg._unknown_relationship_types({"d": ["ANYTHING"]}) == {}


# ── It actually selects now ──────────────────────────────────────────────────

def test_the_filter_selects_on_a_real_claim(tmp_path, monkeypatch):
    import runtime.wkg_faculty as wkg
    from memory.spg_graph import SPGGraph

    d = tmp_path / "wkg"
    d.mkdir()
    (d / "relationship_types.json").write_text(
        json.dumps(sorted(_vocabulary())), encoding="utf-8")
    monkeypatch.setattr(wkg, "_WKG_DIR", str(d))
    graph = SPGGraph()
    monkeypatch.setattr(SPGGraph, "load", classmethod(lambda cls, *a, **k: graph))
    monkeypatch.setattr(SPGGraph, "save", lambda self, *a, **k: None)

    hit = wkg.create_entity(entity_type="CONCEPT", label="Blender", description="")
    other = wkg.create_entity(entity_type="CONCEPT", label="Chunk", description="")
    wkg.record_claim(hit["entity_id"], "PART_OF", other["entity_id"],
                     "VERIFIED", source_id="t")

    dim = next(k for k, v in spg._CCM_DIM_RELEVANT_RELS.items() if "PART_OF" in v)
    out = spg.query_spg_entities("Blender Chunk", ccm={dim: 1.0})
    assert hit["entity_id"] in out
