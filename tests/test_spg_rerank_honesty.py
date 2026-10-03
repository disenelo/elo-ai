"""
tests/test_spg_rerank_honesty.py — the rerank must not claim to rank when it cannot.

WO-SPG-LINK-001 made claims and nodes join. That raises a new way for this to
go quietly wrong, and it is the one I would have caused myself.

2212 of the 2226 live claims are SOURCE_ATTRIBUTED with confidence 0.7, so
they all land on significance 0.7. Backfill nodes for them and `_linked`
jumps from zero to thousands — the INERT warning stops, the debug line says
"SPG rerank: N entities, N linked", and the sort runs. But sorting on a key
that is identical for every entity is a no-op. The ordering would still be
text relevance, and the only thing that said so would be gone.

An honest "this is doing nothing" replaced by a silent "this is working" is
worse than the original defect, because nobody looks again.

Three states, all reported:
    no linked nodes      → INERT
    linked, one value    → FLAT (cannot discriminate)
    linked, many values  → ranks, and says what it ranked on
"""
from __future__ import annotations

import logging

import pytest

import memory.spg_faculty as spg


@pytest.fixture
def _store(tmp_path, monkeypatch):
    """Throwaway WKG + SPG. Nothing live is read or written."""
    import runtime.wkg_faculty as wkg
    from pathlib import Path
    from memory.spg_graph import SPGGraph

    d = tmp_path / "wkg"
    d.mkdir()
    src = Path(wkg.__file__).resolve().parent.parent / "memory" / "wkg" / "relationship_types.json"
    (d / "relationship_types.json").write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(wkg, "_WKG_DIR", str(d))

    graph = SPGGraph()
    monkeypatch.setattr(SPGGraph, "load", classmethod(lambda cls, *a, **k: graph))
    monkeypatch.setattr(SPGGraph, "save", lambda self, *a, **k: None)
    return wkg, graph


def _entity(wkg, label):
    return wkg.create_entity(entity_type="CONCEPT", label=label, description="")["entity_id"]


def _claim(wkg, a, b, significance):
    return wkg.record_claim(a, "ASSOCIATED_WITH", b, "SOURCE_ATTRIBUTED",
                            source_id="t", significance_score=significance)


def test_no_linked_nodes_reports_inert(_store, caplog):
    wkg, graph = _store
    _entity(wkg, "Blender")
    graph._nodes.clear()
    with caplog.at_level(logging.WARNING, logger="memory.spg_faculty"):
        spg.query_spg_entities("Blender")
    assert "INERT" in caplog.text


def test_linked_but_uniform_significance_reports_flat(_store, caplog):
    """
    The state a bulk backfill of confidence-0.7 claims would produce. Linked,
    sorted, and completely unable to discriminate.
    """
    wkg, graph = _store
    a, b, c = _entity(wkg, "Blender"), _entity(wkg, "Chunk"), _entity(wkg, "Unity")
    for pair in ((a, b), (b, c), (a, c)):
        _claim(wkg, pair[0], pair[1], 0.7)
    with caplog.at_level(logging.WARNING, logger="memory.spg_faculty"):
        spg.query_spg_entities("Blender Chunk Unity")
    assert "FLAT" in caplog.text, caplog.text
    assert "INERT" not in caplog.text


def test_varied_significance_ranks_without_warning(_store, caplog):
    wkg, graph = _store
    a, b, c = _entity(wkg, "Blender"), _entity(wkg, "Chunk"), _entity(wkg, "Unity")
    _claim(wkg, a, b, 0.9)
    _claim(wkg, b, c, 0.2)
    with caplog.at_level(logging.WARNING, logger="memory.spg_faculty"):
        out = spg.query_spg_entities("Blender Chunk Unity")
    assert "INERT" not in caplog.text
    assert "FLAT" not in caplog.text
    assert out


def test_significance_actually_reorders(_store):
    """Causal: raise one claim's significance, its entity moves up."""
    wkg, graph = _store
    low, high = _entity(wkg, "Chunk"), _entity(wkg, "Blender")
    _claim(wkg, low, high, 0.1)

    order_before = spg.query_spg_entities("Chunk Blender")
    for node in graph._nodes.values():
        node.significance = 0.1
    # Lift only the claim whose SUBJECT is `low`, so it should outrank.
    for claim in wkg.all_claims():
        if claim["subject_entity_id"] == low:
            graph._nodes[claim["claim_id"]].significance = 0.99
    order_after = spg.query_spg_entities("Chunk Blender")
    assert order_after[0] == low, (order_before, order_after)


def test_a_uniform_backfill_cannot_silence_the_warning(_store, caplog):
    """
    The specific regression this file exists to prevent: importing a node for
    every claim at one significance must NOT read as a working rerank.
    """
    wkg, graph = _store
    ids = [_entity(wkg, n) for n in ("Blender", "Chunk", "Unity", "memory")]
    for i in range(len(ids) - 1):
        _claim(wkg, ids[i], ids[i + 1], 0.7)
    for node in graph._nodes.values():
        node.significance = 0.7            # the backfill
    with caplog.at_level(logging.WARNING, logger="memory.spg_faculty"):
        spg.query_spg_entities("Blender Chunk Unity memory")
    assert "FLAT" in caplog.text
