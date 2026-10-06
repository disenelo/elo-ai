"""
tests/test_spg_backfill.py — ROOT-4: the pattern graph from what already
happened.

The framework's answer to "what can eLo become through experience that we did
not program him to become?" is "nothing, until ROOT-1 and ROOT-4 are wired."
ROOT-4 is this: four months of conversation existed and SPG had never been
loaded with it.

Measured 2026-10-06, before:

    memory/interactions.json   3,309 turns, 2026-06-06 -> 2026-10-06
    data/spg_graph.json        3 nodes, 0 edges
    data/spg_signals.jsonl     13,919 signals, 13,877 of them (99.7%) with
                               turn_id="" — so spg_graph's node id
                               f"{turn_id}:{signal_type}" collapsed them to 44
"""
from __future__ import annotations

import json

import pytest

from memory import spg_backfill as bf


def _row(user, *, mode="answer", ts="2026-09-01T10:00:00+00:00", tag="elo_core"):
    return {"timestamp": ts, "mode": mode, "user": user, "response": "ok",
            "project_tag": tag, "concepts": []}


# ── the scaffolding problem ─────────────────────────────────────────────────
#
# 1,076 of 3,309 `user` fields are the ASSEMBLED PROMPT, not David: a bracketed
# context block with his words after "User asked:". Scored raw, the top
# "topics David keeps returning to" came back as world, asked, user, answer,
# knowledge, confidence, verified — the graph measuring its own scaffolding.

def test_the_injected_context_block_is_not_david():
    raw = (
        "[WORLD_KNOWLEDGE — from eLo's own world (verified, confidence 1.0 — "
        "answer from this, not from web)]\n"
        "eLo Robot: A physical animatronic version of eLo.\n"
        "User asked: eLo, are you there? say something short"
    )
    assert bf.david_said(raw) == "eLo, are you there? say something short"


def test_web_search_scaffolding_is_stripped_too():
    raw = ("[WEB_SEARCH: your back up]\n[WEB_SEARCH_RESULTS]\n"
           "• PUT/GET SOMEONE'S BACK UP - Cambridge Dictionary\n"
           "User asked: What is your back up?")
    assert bf.david_said(raw) == "What is your back up?"


def test_a_plain_message_is_left_alone():
    assert bf.david_said("can you control spotify?") == "can you control spotify?"


def test_scaffolding_words_do_not_become_topics():
    rows = [_row("[WORLD_KNOWLEDGE — verified, confidence 1.0]\n"
                 "User asked: how is the robot coming along")] * 5
    topics = dict(bf.recurring_topics(rows, 20))
    for ghost in ("verified", "confidence", "knowledge", "asked"):
        assert ghost not in topics, (
            f"{ghost!r} is scaffolding — the graph would be measuring itself"
        )
    assert "robot" in topics


def test_substance_measures_his_words_not_the_block():
    short = _row("[WORLD_KNOWLEDGE — " + "x" * 400 + "]\nUser asked: hi")
    assert bf._substance(short) < 0.1


# ── significance means repetition ───────────────────────────────────────────

def test_a_repeated_topic_scores_above_a_one_off():
    rows = [_row("the robot shell needs rework")] * 6 + [_row("unrelated singular musing")]
    counts = bf.topic_counts(rows)
    repeated = bf.score(rows[0], counts)
    one_off = bf.score(rows[-1], counts)
    assert repeated > one_off, (
        "the brief's definition of done is that repetition reads as "
        "significance"
    )


def test_a_topic_below_the_floor_is_not_a_pattern():
    rows = [_row("robot robot")] * 2
    assert bf._recurrence({"robot"}, bf.topic_counts(rows)) == 0.0


def test_mode_shifts_the_score():
    rows = [_row("same words here", mode="build"),
            _row("same words here", mode="social_reflex")]
    counts = bf.topic_counts(rows)
    assert bf.score(rows[0], counts) > bf.score(rows[1], counts)


# ── the graph ───────────────────────────────────────────────────────────────

def test_one_node_per_turn():
    rows = [_row(f"turn number {i} about the robot", ts=f"2026-09-01T10:{i:02d}:00+00:00")
            for i in range(5)]
    g = bf.build(rows)
    assert len(g._nodes) == 5


def test_backfilled_nodes_are_identifiable_as_backfilled():
    """
    A graph that cannot say which of its memories were reconstructed cannot be
    trusted about its own past.
    """
    g = bf.build([_row("hello")])
    assert all(n.startswith("bf-") for n in g._nodes)


def test_turns_in_one_session_are_linked_and_distant_ones_are_not():
    near = [_row("robot work", ts="2026-09-01T10:00:00+00:00"),
            _row("robot work", ts="2026-09-01T10:05:00+00:00")]
    far = [_row("robot work", ts="2026-09-01T10:00:00+00:00"),
           _row("robot work", ts="2026-09-03T10:00:00+00:00")]

    assert any(e.link_type == "temporal" for e in bf.build(near)._edges)
    assert not any(e.link_type == "temporal" for e in bf.build(far)._edges)


def test_a_recurring_topic_links_turns_across_time():
    rows = [_row("the robot shell", ts=f"2026-0{m}-01T10:00:00+00:00")
            for m in range(6, 10)]
    sem = [e for e in bf.build(rows)._edges if e.link_type == "semantic"]
    assert sem, "a topic in four separate months formed no link"
    assert any("robot" in e.evidence for e in sem)


def test_an_empty_history_is_an_empty_graph_not_a_crash():
    g = bf.build([])
    assert len(g._nodes) == 0 and len(g._edges) == 0


def test_a_malformed_timestamp_does_not_abort_the_backfill():
    rows = [_row("fine"), {"timestamp": "not-a-date", "user": "still counted",
                           "mode": "answer"}]
    assert len(bf.build(rows)._nodes) == 2


# ── against the real history ────────────────────────────────────────────────

@pytest.mark.parametrize("_", [0])
def test_the_real_history_produces_a_real_graph(_):
    rows = bf.load_interactions()
    if len(rows) < 500:
        pytest.skip("interactions.json not present at full size on this machine")

    g = bf.build(rows)
    assert len(g._nodes) == len(rows)
    assert len(g._edges) > 1000

    sig = [n.significance for n in g._nodes.values()]
    assert len(set(sig)) > 100, (
        "significance barely varies — the 0.3 backfill constant this replaces "
        "had exactly one value"
    )
    assert max(sig) > 0.5
