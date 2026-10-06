"""
tests/test_spg_topic_ranking.py — ROOT-4, the half that makes the graph matter.

Brief's definition of done:

    "David mentions something repeatedly (a pattern). SPG identifies it as
     significant. That significance score CHANGES HOW ELO RETRIEVES AND
     WEIGHTS related memories."

The backfill did the first two sentences. The third was still false and
quietly so: query_spg_entities ranks entities by the SPG node of their CLAIMS,
keyed by claim_id, while the backfill writes TURN-keyed nodes
("bf-00788-2026-08-13T02:49:33"). Two node populations, one reader, zero
overlap — so loading four months into the graph changed retrieval by nothing.

It also could not have worked even with perfect keys: 2,212 of 2,226 live
claims are SOURCE_ATTRIBUTED at confidence 0.7, so every claim-derived score
is identical and sorting on them is a no-op. Topic significance has 1,241
distinct values.
"""
from __future__ import annotations

import pytest

from memory import spg_topic_index as sti
from memory.spg_graph import Edge, Node, SPGGraph


@pytest.fixture(autouse=True)
def _fresh():
    sti._cache, sti._cache_at = {}, 0.0
    yield
    sti._cache, sti._cache_at = {}, 0.0


def _graph(pairs):
    """pairs: (topic, significance) -> a two-turn semantic link at that score."""
    g = SPGGraph()
    for i, (topic, sig) in enumerate(pairs):
        a, b = f"bf-{i}a", f"bf-{i}b"
        g.add_node(Node(id=a, significance=sig))
        g.add_node(Node(id=b, significance=sig))
        g.add_edge(Edge(from_node=a, to_node=b, link_type="semantic",
                        weight=0.5, evidence=f"topic:{topic}"))
    return g


def _install(monkeypatch, g):
    monkeypatch.setattr(SPGGraph, "load", classmethod(lambda cls, *a, **k: g))


# ── the index ───────────────────────────────────────────────────────────────

def test_a_recurring_topic_carries_its_turns_significance(monkeypatch):
    _install(monkeypatch, _graph([("robot", 0.9), ("hem", 0.2)]))
    idx = sti.topic_significance(force=True)
    assert idx["robot"] == pytest.approx(0.9)
    assert idx["hem"] == pytest.approx(0.2)


def test_a_topic_takes_its_most_significant_turn(monkeypatch):
    g = _graph([("robot", 0.3)])
    g.add_node(Node(id="bf-hi", significance=0.95))
    g.add_edge(Edge(from_node="bf-hi", to_node="bf-0a", link_type="semantic",
                    weight=0.5, evidence="topic:robot"))
    _install(monkeypatch, g)
    assert sti.topic_significance(force=True)["robot"] == pytest.approx(0.95)


def test_something_never_discussed_scores_zero(monkeypatch):
    _install(monkeypatch, _graph([("robot", 0.9)]))
    idx = sti.topic_significance(force=True)
    assert sti.score_label("quantum chromodynamics", idx) == 0.0, (
        "this is the test that the ranking reads DAVID and not generic "
        "salience"
    )


def test_a_label_mostly_made_of_his_vocabulary_outranks_one_that_brushes_it(monkeypatch):
    """
    WAS: scored on its strongest word alone.

    That let one shared common noun carry a whole entity — on the live store
    "Arabic Language" and "Modernist Design" outranked "eLo robot design
    constraints", because they each touched one mid-frequency topic while the
    robot entity touches three. Strength AND coverage now.
    """
    _install(monkeypatch, _graph([("robot", 0.9), ("design", 0.9),
                                  ("constraints", 0.9)]))
    idx = sti.topic_significance(force=True)

    his = sti.score_label("robot design constraints", idx)
    brushing = sti.score_label("Modernist Design Of Victorian Railways", idx)

    assert his > brushing, (
        "an entity that happens to contain one of his words is not one of his "
        "threads"
    )


def test_a_label_with_no_recurring_words_scores_zero(monkeypatch):
    _install(monkeypatch, _graph([("robot", 0.9)]))
    idx = sti.topic_significance(force=True)
    assert sti.score_label("Akan Culture", idx) == 0.0


def test_an_empty_graph_yields_an_empty_index(monkeypatch):
    _install(monkeypatch, SPGGraph())
    assert sti.topic_significance(force=True) == {}
    assert sti.score_label("robot") == 0.0


def test_non_topic_edges_are_ignored(monkeypatch):
    g = SPGGraph()
    g.add_node(Node(id="a", significance=0.9))
    g.add_node(Node(id="b", significance=0.9))
    g.add_edge(Edge(from_node="a", to_node="b", link_type="temporal",
                    weight=0.5, evidence="42s apart"))
    _install(monkeypatch, g)
    assert sti.topic_significance(force=True) == {}


def test_the_index_is_cached(monkeypatch):
    calls = {"n": 0}

    def _counting(cls, *a, **k):
        calls["n"] += 1
        return _graph([("robot", 0.9)])

    monkeypatch.setattr(SPGGraph, "load", classmethod(_counting))
    sti.topic_significance(force=True)
    for _ in range(5):
        sti.topic_significance()
    assert calls["n"] == 1, "rereading 13,000 edges per turn is not free"


# ── the join into retrieval ─────────────────────────────────────────────────

def test_the_ranker_consults_the_topic_index():
    import pathlib
    src = (pathlib.Path(__file__).resolve().parent.parent
           / "memory" / "spg_faculty.py").read_text()
    assert "from memory.spg_topic_index import" in src, (
        "the backfill populates turn-keyed nodes this ranker cannot read; "
        "without the topic join, filling the graph changes retrieval by "
        "nothing"
    )


def test_the_inert_warning_tells_you_which_signal_is_missing():
    """
    Two signals feed the ranking now, so 'nothing scored' has two causes.
    Conflating them sends the next reader to the wrong place — the exact
    failure this module's own history is made of.
    """
    import pathlib
    src = (pathlib.Path(__file__).resolve().parent.parent
           / "memory" / "spg_faculty.py").read_text()
    assert "recurring topics" in src
    assert "run scripts/spg_backfill_run.py" in src


# ── against the live graph ──────────────────────────────────────────────────

def test_the_live_graph_actually_discriminates():
    # conftest redirects _GRAPH_PATH for every test, so topic_significance()
    # sees an empty temp graph and this skipped itself while reporting "not
    # backfilled" — a false negative about live data. The conftest note
    # allows the exception it needs: "a test that genuinely needs the live
    # store reads it by its own path". Read-only.
    import json
    import pathlib as _pl

    live = (_pl.Path(__file__).resolve().parent.parent / "data" / "spg_graph.json")
    if not live.exists():
        pytest.skip("no live graph on this machine")
    raw = json.loads(live.read_text())
    if raw.get("node_count", 0) < 500:
        pytest.skip("graph not backfilled on this machine")

    sig = {n["id"]: float(n.get("significance", 0.0)) for n in raw["nodes"]}
    idx: dict = {}
    for e in raw.get("edges", []):
        ev = str(e.get("evidence", "") or "")
        if not ev.startswith("topic:"):
            continue
        topic = ev[6:].strip().lower()
        for key in ("from_node", "to_node"):
            v = sig.get(e.get(key, ""), 0.0)
            if v > idx.get(topic, 0.0):
                idx[topic] = v
    if len(idx) < 50:
        pytest.skip("graph has no recurring topics")

    import runtime.wkg_faculty as wkg
    labels = [e.get("label", "") for e in wkg._load("entities")]
    if len(labels) < 50:
        pytest.skip("entity store too small")

    scores = [sti.score_label(l, idx) for l in labels]
    nonzero = [s for s in scores if s > 0]

    assert len(set(nonzero)) > 5, (
        "a ranking key with one value is a no-op sort — the exact FLAT "
        "failure the claim-derived scores already have"
    )
    assert 0 < len(nonzero) < len(scores), (
        "everything or nothing scoring means the key separates no entities"
    )
