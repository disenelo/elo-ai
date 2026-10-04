"""
tests/test_spg_store_isolation.py — the test suite must not write eLo's memory.

Measured 2026-10-04: a full `pytest tests/` run added 8 nodes to the LIVE
data/spg_graph.json. 340 before, 348 after. Across today's runs that is ~112
of the store's growth — nodes created by testing, sitting in eLo's memory.

It is my regression. tests/test_wo_wkg_001_phase1_schema.py isolates itself
properly, patching _WKG_DIR to a temp directory, and it calls record_claim()
ten times. WO-SPG-LINK-001 then gave record_claim a side effect that test
could not have known about: an SPG node write, which goes to a path the WKG
isolation does not cover.

Worse, it corrupted the measurement the fix was argued from. "225 nodes, zero
overlap" was a real finding — the zero is real — but part of that node count
was created by running the tests that looked at it.

Fixed at the mechanism rather than in the one test that happened to trip it:

  1. SPGGraph.save/load bound _GRAPH_PATH as a DEFAULT ARGUMENT, evaluated
     once at class-definition time, so monkeypatching the module constant did
     nothing and isolation was effectively impossible. Now resolved at call
     time.
  2. conftest redirects the graph to a temp file for every test, so the next
     test to acquire a store-writing side effect cannot leak either.

This is the third live artefact tests have been found writing, after
blender_state.json and the symbol lexicon.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

import memory.spg_graph as spg_graph
from memory.spg_graph import SPGGraph

_LIVE = Path(__file__).resolve().parent.parent / "data" / "spg_graph.json"


def test_the_graph_path_is_redirected_during_tests():
    assert Path(spg_graph._GRAPH_PATH).resolve() != _LIVE.resolve(), (
        "tests are pointed at eLo's real SPG store")


def test_the_path_is_resolved_at_call_time_not_bound_at_definition(tmp_path, monkeypatch):
    """
    The reason isolation was impossible: `def save(self, path=_GRAPH_PATH)`
    captures the constant once, when the class is defined. Patching the module
    attribute afterwards changed nothing, so every caller wrote the live file
    no matter what a test did.
    """
    target = tmp_path / "graph.json"
    monkeypatch.setattr(spg_graph, "_GRAPH_PATH", target)

    g = SPGGraph()
    g.add_node(spg_graph.Node(id="abc", content_hash="h", significance=0.5))
    g.save()
    assert target.exists(), "save() ignored the patched path"
    assert SPGGraph.load().node_count() == 1


def test_recording_a_claim_writes_no_node_to_the_live_store(tmp_path, monkeypatch):
    """
    The exact leak: WKG isolated, SPG not, record_claim writing to both.
    """
    import runtime.wkg_faculty as wkg

    before = _LIVE.read_text(encoding="utf-8") if _LIVE.exists() else None

    d = tmp_path / "wkg"
    d.mkdir()
    src = _LIVE.parent.parent / "memory" / "wkg" / "relationship_types.json"
    (d / "relationship_types.json").write_text(src.read_text(encoding="utf-8"),
                                               encoding="utf-8")
    monkeypatch.setattr(wkg, "_WKG_DIR", str(d))

    a = wkg.create_entity(entity_type="CONCEPT", label="IsolationProbe", description="")
    b = wkg.create_entity(entity_type="CONCEPT", label="IsolationTarget", description="")
    claim = wkg.record_claim(a["entity_id"], "ASSOCIATED_WITH", b["entity_id"],
                             "VERIFIED", source_id="isolation-test")

    after = _LIVE.read_text(encoding="utf-8") if _LIVE.exists() else None
    assert after == before, "the test suite wrote a node into eLo's live memory"
    if after:
        assert claim["claim_id"] not in after
