"""
tests/test_spg_claim_linking.py — SPG significance ranking is inert in production.

Live store, read 2026-10-03: 225 SPG nodes, 2226 WKG claims, intersection ZERO.
spg_faculty.query_spg_entities() ranks entities by the SPG significance of
their claims, joining node.id to claim["claim_id"]. Nothing joins, so the sort
is a no-op and the ordering is text relevance — which the INERT warning has
been saying on every live turn since it was added.

The join was never going to work, because nothing ever created a node under a
real claim_id:

  - record_claim() in runtime/wkg_faculty.py is the sole claim writer. It has
    never touched SPG.
  - update_spg_from_claims() exists in spg_faculty for exactly this and has
    ZERO callers.
  - The only producer that ran is server.py's WIRE-1, which mints its own id:
    `f"turn-{int(time.time() * 1000) % 1_000_000}"`. That is not a claim_id and
    cannot become one. Eleven of the 225 nodes carry it. The other 214 are
    legacy UUIDs pointing at claims that no longer exist.

Fixed at record_claim — the one place every claim passes through, so all
callers are covered and the next one is covered in advance. Same reasoning as
putting the spoken-log write inside speak().

Fully isolated: SPGGraph.load/save and the WKG directory are both redirected,
so no test here touches data/spg_graph.json or memory/wkg/.
"""
from __future__ import annotations

import pytest

import memory.spg_graph as spg_graph
import runtime.wkg_faculty as wkg
from memory.spg_graph import SPGGraph


@pytest.fixture
def _isolated(tmp_path, monkeypatch):
    """A throwaway SPG graph and WKG directory. Nothing live is written."""
    # Real schema, throwaway data. Copying relationship_types.json keeps the
    # vocabulary honest — a test that invents its own types would pass on
    # relationships the live store rejects.
    import json as _json
    import os as _os
    d = tmp_path / "wkg"
    d.mkdir()
    (d / "relationship_types.json").write_text(
        _json.dumps(_json.load(open(_os.path.join(
            _os.path.dirname(wkg.__file__), "..", "memory", "wkg",
            "relationship_types.json"), encoding="utf-8"))), encoding="utf-8")
    monkeypatch.setattr(wkg, "_WKG_DIR", str(d))

    graph = SPGGraph()
    monkeypatch.setattr(SPGGraph, "load", classmethod(lambda cls, *a, **k: graph))
    monkeypatch.setattr(SPGGraph, "save", lambda self, *a, **k: None)
    return graph


def _two_entities():
    a = wkg.create_entity(entity_type="CONCEPT", label="eLo", description="")
    b = wkg.create_entity(entity_type="CONCEPT", label="Blender", description="")
    return a["entity_id"], b["entity_id"]


# ── The link ─────────────────────────────────────────────────────────────────

def test_recording_a_claim_creates_a_node_under_the_same_id(_isolated):
    a, b = _two_entities()
    claim = wkg.record_claim(a, "ASSOCIATED_WITH", b, "VERIFIED", source_id="test")
    assert claim["claim_id"] in _isolated._nodes, (
        "the claim was written and SPG never heard about it")


def test_the_node_is_keyed_by_a_real_claim_id_not_a_minted_one(_isolated):
    a, b = _two_entities()
    claim = wkg.record_claim(a, "IS", b, "SOURCE_ATTRIBUTED", source_id="test")
    node_ids = list(_isolated._nodes)
    assert not any(str(i).startswith("turn-") for i in node_ids), node_ids
    assert node_ids == [claim["claim_id"]]


def test_every_claim_gets_a_node(_isolated):
    a, b = _two_entities()
    ids = {wkg.record_claim(a, "IS", b, "VERIFIED", source_id="t")["claim_id"]
           for _ in range(5)}
    assert ids <= set(_isolated._nodes)
    assert len(ids) == 5, "claim_ids must be distinct"


# ── Causal: change the claim, change the node ────────────────────────────────

def test_significance_follows_the_claim(_isolated):
    a, b = _two_entities()
    low = wkg.record_claim(a, "IS", b, "VERIFIED", source_id="t",
                           significance_score=0.1)
    high = wkg.record_claim(a, "IS", b, "VERIFIED", source_id="t",
                            significance_score=0.9)
    assert _isolated._nodes[low["claim_id"]].significance == pytest.approx(0.1)
    assert _isolated._nodes[high["claim_id"]].significance == pytest.approx(0.9)


def test_confidence_carries_the_significance_when_none_is_given(_isolated):
    """
    A VERIFIED claim defaults to confidence 1.0 and SOURCE_ATTRIBUTED to 0.5.
    An unscored claim must not land at 0.0 — a node with no significance is
    indistinguishable from one that was never ranked.
    """
    a, b = _two_entities()
    verified = wkg.record_claim(a, "IS", b, "VERIFIED", source_id="t")
    attributed = wkg.record_claim(a, "IS", b, "SOURCE_ATTRIBUTED", source_id="t")
    assert _isolated._nodes[verified["claim_id"]].significance > \
           _isolated._nodes[attributed["claim_id"]].significance
    assert _isolated._nodes[attributed["claim_id"]].significance > 0.0


def test_the_content_hash_describes_the_triple(_isolated):
    """
    claims.json stores no claim text, which is why the orphaned legacy nodes
    could never be re-linked by hash. The hash has to come from the triple.
    """
    a, b = _two_entities()
    one = wkg.record_claim(a, "ASSOCIATED_WITH", b, "VERIFIED", source_id="t")
    two = wkg.record_claim(a, "IS", b, "VERIFIED", source_id="t")
    h1 = _isolated._nodes[one["claim_id"]].content_hash
    h2 = _isolated._nodes[two["claim_id"]].content_hash
    assert h1 and h2
    assert h1 != h2, "a different relationship must hash differently"


# ── It must never cost a claim ───────────────────────────────────────────────

def test_a_blocked_claim_creates_no_node(_isolated, monkeypatch):
    """DREAM_SIMULATION is refused at the write gate — nothing reaches SPG."""
    a, b = _two_entities()
    with pytest.raises(ValueError):
        wkg.record_claim(a, "IS", b, "VERIFIED", source_id="t",
                         memory_origin="DREAM_SIMULATION")
    assert not _isolated._nodes


def test_an_spg_failure_does_not_lose_the_claim(_isolated, monkeypatch):
    """Fire and forget. A broken graph must never cost a memory."""
    def _boom(*a, **k):
        raise RuntimeError("spg down")
    monkeypatch.setattr(SPGGraph, "load", classmethod(_boom))

    a, b = _two_entities()
    claim = wkg.record_claim(a, "IS", b, "VERIFIED", source_id="t")
    assert claim["claim_id"]
    assert any(c["claim_id"] == claim["claim_id"] for c in wkg._load("claims"))


# ── Retrieval stops being inert ──────────────────────────────────────────────

def test_retrieval_reports_linked_nodes_instead_of_inert(_isolated, caplog):
    import logging
    from memory.spg_faculty import query_spg_entities

    a, b = _two_entities()
    wkg.record_claim(a, "ASSOCIATED_WITH", b, "VERIFIED", source_id="t",
                     significance_score=0.9)

    with caplog.at_level(logging.WARNING, logger="memory.spg_faculty"):
        query_spg_entities("Blender")
    assert "SPG rerank INERT" not in caplog.text, caplog.text
