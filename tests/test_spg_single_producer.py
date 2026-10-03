"""
tests/test_spg_single_producer.py — SPG nodes have one producer: record_claim.

server.py's WIRE-1 wrote an SPG node per response under an id it minted
itself:

    _spg_claim_id = f"turn-{int(time.time() * 1000) % 1_000_000}"

Three things wrong with it, any one fatal:

  - It is not a claim_id. query_spg_entities() joins node.id to
    claim["claim_id"], so every node WIRE-1 ever wrote was unreachable the
    moment it was written. Eleven of the live store's 225 nodes are these.
  - `% 1_000_000` of a millisecond clock wraps every ~16.7 minutes, so the
    ids collide with each other and silently overwrite.
  - It inflated the node count, which made the store look healthier than it
    was while the significance rerank reported INERT.

Its stated intent — "eLo's own statements feed SPG" — is now genuinely met.
The turn path at server.py:6145 already records real claims
(David ASSOCIATED_WITH <topic>), and since WO-SPG-LINK-001 every claim gets a
node under its own claim_id. So this removes a stub that satisfied the intent
in name only, and leaves the implementation that satisfies it for real.

Not a feature being dropped: no reader could reach what it wrote.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

_SERVER = (Path(__file__).resolve().parent.parent / "server.py").read_text(encoding="utf-8")


def test_server_mints_no_spg_node_ids():
    """
    Asserts on the SPG symbols specifically. A broad scan for
    "turn-{int(time.time()" also matches episode_ref at server.py:7105, which
    is a legitimate unrelated id with no modulo and nothing to do with SPG —
    a test that fails on it would be pointing at the wrong line.
    """
    assert "_spg_claim_id" not in _SERVER
    assert "add_node_for_claim" not in _SERVER
    assert "% 1_000_000" not in _SERVER


def test_record_claim_is_the_only_spg_node_producer():
    """
    One producer, so a node's id is always a real claim_id. A second writer
    is how the store filled with 214 orphans in the first place.
    """
    root = Path(__file__).resolve().parent.parent
    callers: list[str] = []
    for path in root.rglob("*.py"):
        if "/tests/" in str(path) or path.name in ("spg_faculty.py", "spg_graph.py"):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except Exception:
            continue
        if "add_node_for_claim" in text or "update_spg_from_claims" in text:
            callers.append(str(path.relative_to(root)))
    assert callers == ["runtime/wkg_faculty.py"], callers


def test_a_recorded_claim_still_feeds_spg(tmp_path, monkeypatch):
    """The intent WIRE-1 claimed, met through the path that actually joins."""
    import runtime.wkg_faculty as wkg
    from memory.spg_graph import SPGGraph

    d = tmp_path / "wkg"
    d.mkdir()
    src = Path(wkg.__file__).resolve().parent.parent / "memory" / "wkg" / "relationship_types.json"
    (d / "relationship_types.json").write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(wkg, "_WKG_DIR", str(d))

    graph = SPGGraph()
    monkeypatch.setattr(SPGGraph, "load", classmethod(lambda cls, *a, **k: graph))
    monkeypatch.setattr(SPGGraph, "save", lambda self, *a, **k: None)

    a = wkg.create_entity(entity_type="PERSON", label="David Charles", description="")
    b = wkg.create_entity(entity_type="CONCEPT", label="memory", description="")
    claim = wkg.record_claim(a["entity_id"], "ASSOCIATED_WITH", b["entity_id"],
                             "SOURCE_ATTRIBUTED", source_id="interaction:answer",
                             confidence=0.7)

    node_ids = set(graph._nodes)
    assert claim["claim_id"] in node_ids
    assert not any(str(i).startswith("turn-") for i in node_ids)
    # The join the reader performs, done here against the real store.
    assert {c["claim_id"] for c in wkg.all_claims()} & node_ids == {claim["claim_id"]}
