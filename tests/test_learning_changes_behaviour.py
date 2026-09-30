"""
Does an experience change what eLo does next?

David's chain, end to end, with no mocks in the middle:

    experience -> record_outcome -> promote_pass -> recall -> consult
               -> learning_advice -> executive.decide -> a DIFFERENT action

Nothing here asserts that a module exists. The single claim is that the same
question, asked twice, gets a different answer because something happened in
between — and that reverting any link in the chain takes that away.

Three times while writing this I concluded the loop was broken, and all three
were this test being under-specified rather than the code being wrong:

  - record_outcome without session_id: promote_pass needs 2 DISTINCT
    session_ids and silently counts none, so nothing is ever promoted.
  - a lesson without prefers_action: consult() reads that field to produce a
    preference, so a confirmed, recalled lesson yields {} and changes nothing.
  - 2 episodes: below _PROMOTE_EPISODES (3), so nothing promotes, nothing
    recalls, and there is no preference to weigh at all.

I also mis-stated the threshold as 12 sessions from a single run in which the
lesson had not promoted. Swept 2/3/4/6/8/12: it is 3, and the weight is full
immediately rather than graduated.

The live path supplies session_id (reflection_faculty.py:236) and
prefers_action (:137 via _cal_map). Each of those is pinned below, because a
test that builds its own lesson by hand will pass while the real writer has
stopped filling a field.
"""
from __future__ import annotations

import json
import os
import tempfile

import pytest

import self.lesson_store as ls
from faculties.learning import consult
from runtime.executive import decide

QUESTION = "what do you think about the arm"
BASE = {"intent": "inquiry", "valence": "neutral", "momentum": "steady",
        "emotional_context": {"energy": 0.5, "valence": 0.0}}


def _ledger(tmp_path, evidence_sessions: int):
    """A lesson shaped the way reflection_faculty shapes one, plus evidence."""
    led = str(tmp_path / "lessons.jsonl")
    row = {
        "lesson_key": "k1", "status": "candidate", "strength": 1.0,
        "scope": "inquiry",
        "statement": "When David asks what I think, challenge rather than answer.",
        "prefers_action": "challenge",          # reflection_faculty.py:137
        "applies_when": ["inquiry"],
        "reason": "answering flatly did not land",
        "evidence": [],
    }
    open(led, "w").write(json.dumps(row) + "\n")
    for i in range(evidence_sessions):
        ls.record_outcome("k1", episode_ref=f"e{i}", verified=True,
                          session_id=f"s{i}",      # reflection_faculty.py:236
                          action="challenge", outcome="landed", ledger_path=led)
    ls.promote_pass(ledger_path=led)
    return led


def _decide_with(led):
    adv = consult(lessons=ls.recall(scope="inquiry", ledger_path=led),
                  candidate_action="", context={"intent": "inquiry"})
    state = dict(BASE)
    state["learning_advice"] = adv.as_dict()
    return decide(state, user_input=QUESTION), adv


# ── the claim ─────────────────────────────────────────────────────────────────

def test_experience_changes_the_next_decision(tmp_path):
    before = decide(dict(BASE), user_input=QUESTION)
    after, adv = _decide_with(_ledger(tmp_path, 12))
    assert before["action"] == "answer"
    assert after["action"] == "challenge", (
        f"12 verified experiences did not change the decision: {after}"
    )
    assert before["action"] != after["action"]


def test_the_executive_says_it_was_learned(tmp_path):
    """Not just a different answer — attributable to the lesson."""
    after, _ = _decide_with(_ledger(tmp_path, 12))
    assert "learned" in (after.get("cal_reason") or "").lower()


def test_two_experiences_are_not_enough(tmp_path):
    """
    The boundary, measured rather than assumed. I first reported it as 12
    sessions off a single run where the lesson had not actually promoted.
    Swept 2/3/4/6/8/12 and it is 3: _PROMOTE_EPISODES needs 3 distinct
    episode_refs, and below that nothing is promoted, so nothing is recalled
    and no preference exists.
    """
    after, adv = _decide_with(_ledger(tmp_path, 2))
    assert adv.preferences == {}, f"promoted on 2 experiences: {adv.preferences}"
    assert after["action"] == "answer"


def test_three_experiences_are_enough(tmp_path):
    """Once promoted the weight is full, not graduated. 3 is the whole gate."""
    after, adv = _decide_with(_ledger(tmp_path, 3))
    assert adv.preferences == {"challenge": 1.0}
    assert after["action"] == "challenge"


# ── each link, cut ────────────────────────────────────────────────────────────

def test_without_promotion_nothing_is_recalled(tmp_path):
    led = str(tmp_path / "l.jsonl")
    open(led, "w").write(json.dumps({
        "lesson_key": "k1", "status": "candidate", "strength": 1.0,
        "scope": "inquiry", "statement": "s", "prefers_action": "challenge",
        "applies_when": ["inquiry"], "evidence": [],
    }) + "\n")
    assert ls.recall(scope="inquiry", ledger_path=led) == []


def test_promotion_requires_distinct_sessions(tmp_path):
    """One session, many episodes -> never promoted. This is the real gate."""
    led = str(tmp_path / "l.jsonl")
    open(led, "w").write(json.dumps({
        "lesson_key": "k1", "status": "candidate", "strength": 1.0,
        "scope": "inquiry", "statement": "s", "prefers_action": "challenge",
        "applies_when": ["inquiry"], "evidence": [],
    }) + "\n")
    for i in range(12):
        ls.record_outcome("k1", episode_ref=f"e{i}", verified=True,
                          session_id="same-session",
                          action="challenge", outcome="landed", ledger_path=led)
    assert ls.promote_pass(ledger_path=led)["promoted"] == []


def test_a_lesson_without_prefers_action_cannot_advise(tmp_path):
    led = str(tmp_path / "l.jsonl")
    open(led, "w").write(json.dumps({
        "lesson_key": "k1", "status": "confirmed", "strength": 1.0,
        "scope": "inquiry", "statement": "s",
        "applies_when": ["inquiry"], "evidence": [],
    }) + "\n")
    for i in range(12):
        ls.record_outcome("k1", episode_ref=f"e{i}", verified=True, session_id=f"s{i}",
                          action="challenge", outcome="landed", ledger_path=led)
    adv = consult(lessons=ls.recall(scope="inquiry", ledger_path=led),
                  candidate_action="", context={"intent": "inquiry"})
    assert not adv.preferences


# ── the live writers must keep filling the fields the chain needs ────────────

def _reflection_src():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return open(os.path.join(root, "runtime", "reflection_faculty.py"), encoding="utf-8").read()


def test_live_path_supplies_session_id():
    """Without this, promote_pass counts zero distinct sessions, forever."""
    assert "session_id=_SESSION_ID" in _reflection_src()


def test_live_path_supplies_prefers_action():
    """Without this, consult() produces no preference from any lesson."""
    src = _reflection_src()
    assert '"prefers_action": prefers_action' in src
    assert "_cal_map" in src


def test_executive_consumes_the_advice_channel():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    src = open(os.path.join(root, "runtime", "executive.py"), encoding="utf-8").read()
    assert 'attention_model.get("learning_advice")' in src
