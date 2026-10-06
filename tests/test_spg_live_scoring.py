"""
tests/test_spg_live_scoring.py — ROOT-4 P1: a live turn reaches the graph.

Brief: "SPG live scoring from live turns — P1. After backfill confirms the
pipeline works."

The pipeline is wkg_faculty.record_claim -> _link_claim_to_spg ->
spg_faculty.add_node_for_claim -> SPGGraph. wkg_faculty's own comment records
why it needed wiring at all: it is "the sole claim writer — never touched
SPG".

These prove the live half works, so when the backfill lands the graph is
whole: history from interactions.json, new turns from here. No third writer —
one behaviour with several writers is the mistake this codebase keeps making.

runtime/wkg_faculty.py is Builder 1's file. It is exercised here, never edited.
"""
from __future__ import annotations

import json

import pytest

import memory.spg_faculty as spgf
import memory.spg_graph as spgg
import runtime.wkg_faculty as wkg


@pytest.fixture(autouse=True)
def _isolated(tmp_path, monkeypatch):
    """
    Never the live stores. The SPG graph was destroyed once by a test whose
    save() path was bound at class-definition time; conftest redirects
    _GRAPH_PATH, and _WKG_DIR is redirected here.
    """
    wkg_dir = tmp_path / "wkg"
    wkg_dir.mkdir()
    live = tmp_path.parent / "live_vocab"
    import os
    src = os.path.join(os.path.dirname(wkg.__file__), "..", "memory", "wkg")
    import shutil
    for vocab in ("relationship_types.json", "entity_types.json"):
        p = os.path.join(src, vocab)
        if os.path.exists(p):
            shutil.copy2(p, wkg_dir / vocab)
    for data in ("claims.json", "entities.json", "sources.json"):
        (wkg_dir / data).write_text(json.dumps([]))

    monkeypatch.setattr(wkg, "_WKG_DIR", str(wkg_dir))
    monkeypatch.setattr(spgg, "_GRAPH_PATH", tmp_path / "spg_graph.json")


def _entities():
    a = wkg.create_entity("PERSON", "Livescore Subject")
    b = wkg.create_entity("CONCEPT", "Livescore Notion")
    return a["entity_id"], b["entity_id"]


def test_a_live_claim_becomes_a_graph_node():
    subj, obj = _entities()
    claim = wkg.record_claim(
        subj, "CAUSES", obj,
        epistemic_class="SOURCE_ATTRIBUTED", source_id="turn:live",
        confidence=0.8,
    )

    graph = spgg.SPGGraph.load()
    assert graph._nodes, (
        "a claim was written and the graph stayed empty — the live half of "
        "ROOT-4 is not connected"
    )
    assert any(claim["claim_id"] in nid for nid in graph._nodes), (
        "the node is not keyed to the claim that created it"
    )


def test_the_node_carries_a_real_significance_not_a_constant():
    subj, obj = _entities()
    strong = wkg.record_claim(subj, "CAUSES", obj,
                              epistemic_class="VERIFIED", source_id="s1")
    weak = wkg.record_claim(subj, "ASSOCIATED_WITH", obj,
                            epistemic_class="HYPOTHESIS", source_id="s2")

    graph = spgg.SPGGraph.load()
    sig = {nid: n.significance for nid, n in graph._nodes.items()}

    s_strong = next(v for k, v in sig.items() if strong["claim_id"] in k)
    s_weak = next(v for k, v in sig.items() if weak["claim_id"] in k)

    assert s_strong != s_weak, (
        "CAUSES/VERIFIED scored the same as ASSOCIATED_WITH/HYPOTHESIS — "
        "that is the 0.3 backfill constant behaviour this replaces"
    )
    assert s_strong > s_weak


def test_the_relationship_weight_is_what_separates_them():
    from memory.spg_significance import RELATIONSHIP_WEIGHT
    assert RELATIONSHIP_WEIGHT["CAUSES"] > RELATIONSHIP_WEIGHT["ASSOCIATED_WITH"]


def test_there_is_exactly_one_live_writer_into_the_graph():
    """
    One behaviour with several writers is the mistake WO-TIRED-SIT-001 made
    with two sit emitters and dream_request warns about with two dream
    executors. The live path is record_claim; the backfill is a separate,
    explicit, offline run.
    """
    import pathlib
    root = pathlib.Path(__file__).resolve().parent.parent
    callers = []
    for p in root.rglob("*.py"):
        s = str(p)
        if any(x in s for x in ("venv", "__pycache__", "/tests/", "spg_faculty.py")):
            continue
        if "add_node_for_claim" in p.read_text(errors="replace"):
            callers.append(p.relative_to(root))

    assert len(callers) == 1, f"expected one live writer, found {callers}"
    assert str(callers[0]) == "runtime/wkg_faculty.py"


def test_a_graph_write_failure_never_breaks_the_claim(monkeypatch):
    """A claim is durable before SPG is touched; SPG must not be able to undo that."""
    def _boom(*a, **k):
        raise RuntimeError("graph unavailable")
    monkeypatch.setattr(spgf, "add_node_for_claim", _boom)

    subj, obj = _entities()
    claim = wkg.record_claim(subj, "CAUSES", obj,
                             epistemic_class="VERIFIED", source_id="s")
    assert claim["claim_id"]
    assert any(c["claim_id"] == claim["claim_id"] for c in wkg.all_claims())
