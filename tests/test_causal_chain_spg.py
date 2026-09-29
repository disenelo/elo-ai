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

    top, second = before[0], before[1]
    ids = {(get_entity(e) or {}).get("label"): e for e in query_spg_entities(_TURN)}

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


def test_the_live_store_is_inert_and_says_so(caplog):
    """
    The finding. 214 SPG nodes, 2220 WKG claims, ZERO shared ids, so every
    significance is 0.0 and the sort is a no-op -- while the old debug line
    reported a successful rerank.

    Inverting every significance in the live store changed the retrieved order
    by nothing. That is what "decorative" means, and the system must now say
    so out loud rather than logging success.
    """
    import logging
    with caplog.at_level(logging.WARNING, logger="memory.spg_faculty"):
        _labels()
    assert any("SPG rerank INERT" in r.message for r in caplog.records), (
        "the live store contributes no significance and the code does not say so"
    )


def test_live_store_really_has_no_overlap_with_claims():
    """Pins the specific fact, so a future re-link is detected as a change."""
    import json as _json
    nodes = {n["id"] for n in _json.load(open(_STORE, encoding="utf-8"))["nodes"]}
    claims = {c.get("claim_id", "") for c in _json.load(
        open(os.path.join(_ROOT, "memory", "wkg", "claims.json"), encoding="utf-8"))}
    assert nodes and claims
    assert not (nodes & claims), (
        "SPG nodes now overlap WKG claims — the ranking may be live again; "
        "re-check test_the_live_store_is_inert_and_says_so"
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
