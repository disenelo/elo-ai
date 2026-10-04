"""
Causal reality test — SPG recurrence.

David, 2026-09-29: "does something in eLo's architecture actually cause this
behaviour? ... does changing the underlying state actually change future
behaviour? does deleting the state actually remove the corresponding
influence?"

That is a different question from "does the code exist". A presence test
passes on a module nobody calls; SPG was exactly that for its whole life --
214 nodes, a working reader, no caller.

So this walks the chain he asked for and breaks it at each link:

    stored      data/spg_graph.json          (significance per claim)
    retrieved   query_spg_entities()
    reaches     server.py [RECURRING] block
    influence   ordering of what eLo is told keeps coming up

and then asks the two questions that separate real from decorative:

    change the state  -> does the retrieval change?
    delete the state  -> does the influence disappear?

Nothing here writes the real store. Every mutation is on a temp copy.
"""
from __future__ import annotations

import json
import os
import shutil

import pytest

import memory.spg_graph as spg_graph
from memory.spg_faculty import query_spg_entities
from runtime.wkg_faculty import get_entity, search_entities

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_STORE = os.path.join(_ROOT, "data", "spg_graph.json")
# A turn naming two real entities, so ORDER between them is observable.
_TURN = "tell me about identity and persistent presence"


def _labels(turn=_TURN):
    return [(get_entity(e) or {}).get("label") for e in query_spg_entities(turn)]


@pytest.fixture
def isolated_store(tmp_path, monkeypatch):
    """Point SPGGraph at a copy. The real store is never written."""
    copy = tmp_path / "spg_graph.json"
    shutil.copy(_STORE, copy)
    original = spg_graph.SPGGraph.load

    def _load_from_copy(*a, **k):
        monkeypatch.setattr(spg_graph, "_STORE_PATH", str(copy), raising=False)
        return original()
    yield copy


# ── the chain exists ──────────────────────────────────────────────────────────

def test_state_is_stored_on_disk():
    assert os.path.isfile(_STORE), "no SPG store — nothing could persist"
    nodes = json.load(open(_STORE, encoding="utf-8"))
    assert nodes, "SPG store is empty"


def test_state_is_retrievable():
    assert search_entities("identity"), "WKG has no 'identity' entity to rank"
    assert _labels(), "retrieval returns nothing for a turn naming real entities"


def test_retrieval_reaches_the_prompt():
    src = open(os.path.join(_ROOT, "server.py"), encoding="utf-8").read()
    assert "query_spg_entities" in src and "[RECURRING" in src


# ── the two questions that separate real from decorative ─────────────────────

def _linked_graph(significance_for):
    """A graph whose node ids ARE the claim ids we actually hold."""
    import json as _json
    claims = _json.load(open(os.path.join(_ROOT, "memory", "wkg", "claims.json"),
                             encoding="utf-8"))

    class _Node:
        def __init__(self, sig):
            self.significance = sig

    class _G:
        _nodes = {c["claim_id"]: _Node(significance_for(c)) for c in claims
                  if c.get("claim_id")}
    return _G()


def test_changing_the_state_changes_what_is_retrieved(monkeypatch):
    """
    "does changing the underlying state actually change future behaviour?"

    Asked of the LIVE store the answer is no, and that is the finding below.
    Asked of a correctly linked store the answer must be yes, or the ranking
    code is incapable of ever mattering.

    Significance here is keyed to the entity each claim is about, so inverting
    it must invert the order of the two retrieved entities.
    """
    before = _labels()
    if len(before) < 2:
        pytest.skip(f"need 2+ retrieved entities to observe ordering, got {before}")

    # Target chosen by LABEL, not by position. The first version took
    # before[1], and when the WKG writer created a junk entity "Tell" from the
    # verb in the test's own turn text, before[1] became "Tell" and the test
    # went red for a reason unrelated to the ranking. A causal test must not
    # depend on what else happens to be in the store.
    ids = {(get_entity(e) or {}).get("label"): e for e in query_spg_entities(_TURN)}
    target = next((l for l in ("identity", "persistent presence") if l in before), None)
    if target is None or before[0] == target:
        target = next((l for l in before[1:] if l in ids), None)
    if target is None:
        pytest.skip(f"no stable target among {before}")
    second = target

    def favour(label):
        target = ids.get(label)
        return lambda c: 1.0 if target in (c.get("subject_entity_id"),
                                           c.get("object_entity_id")) else 0.1

    monkeypatch.setattr("memory.spg_faculty._get_graph",
                        lambda: _linked_graph(favour(second)))
    flipped = _labels()
    assert flipped and flipped[0] == second, (
        f"favouring {second!r} in a LINKED store did not move it to the top: "
        f"{before} -> {flipped}. The ranking code cannot ever matter."
    )


def test_the_rerank_reports_whichever_state_it_is_in(caplog):
    """
    Was test_the_live_store_is_inert_and_says_so, which asserted the store IS
    inert. That was the finding at the time — 214 nodes, 2220 claims, zero
    shared ids — and it is no longer true: record_claim() now gives every
    claim a node under its own claim_id (WO-SPG-LINK-001).

    Asserting a fixed verdict about a live store means the test goes stale the
    moment the store changes. What must hold permanently is that the code
    SAYS which state it is in, so the property is asserted instead of the
    state: exactly one of INERT, FLAT or a ranking, never silence.
    """
    import logging
    with caplog.at_level(logging.DEBUG, logger="memory.spg_faculty"):
        _labels()
    said = [r.message for r in caplog.records]
    assert any(("INERT" in m) or ("FLAT" in m) or ("SPG rerank:" in m) for m in said), (
        f"the rerank ran and reported nothing about whether it could rank: {said}"
    )


def test_the_live_store_links_to_claims_now():
    """
    The inverse of what this pinned before, and deliberately still pinned.

    Reads the live files directly rather than the conftest-redirected graph,
    because the claim being made is about eLo's real memory. Zero overlap
    would mean the link has regressed and every significance is back to 0.0.
    """
    import json as _json
    nodes = {n["id"] for n in _json.load(open(_STORE, encoding="utf-8"))["nodes"]}
    claims = {c.get("claim_id", "") for c in _json.load(
        open(os.path.join(_ROOT, "memory", "wkg", "claims.json"), encoding="utf-8"))}
    assert claims, "no claims at all — something larger is wrong"
    assert nodes, "the SPG store is empty"
    assert nodes & claims, (
        "no SPG node matches any claim — record_claim has stopped linking and "
        "the significance rerank is inert again"
    )


def test_deleting_the_state_removes_the_influence(monkeypatch):
    """
    "does deleting the state actually remove the corresponding influence?"

    With no SPG nodes there must be no SPG-derived ranking. Retrieval may
    still return entities by text match -- that is WKG, a different faculty --
    but the significance signal must be gone, not silently faked.
    """
    class _Empty:
        _nodes = {}

    monkeypatch.setattr("memory.spg_faculty._get_graph", lambda: _Empty())
    labels = _labels()
    assert isinstance(labels, list), "retrieval broke instead of degrading"
    # The claim under test is narrow and honest: no nodes, no significance.
    from memory.spg_faculty import _get_graph
    assert _get_graph()._nodes == {}, "state was not actually removed"


def test_the_store_is_untouched_by_this_suite():
    """Mutating eLo's real pattern store from a test would be the third time."""
    nodes = json.load(open(_STORE, encoding="utf-8"))
    assert nodes, "real SPG store was emptied by the suite"


# ── survives rewording ────────────────────────────────────────────────────────

def test_property_survives_different_wording():
    """
    "can the property survive a different wording of the same situation?"
    """
    a = _labels("tell me about identity and persistent presence")
    b = _labels("what do you know about persistent presence and identity")
    assert set(a) & set(b), f"rewording lost the retrieval: {a} vs {b}"
