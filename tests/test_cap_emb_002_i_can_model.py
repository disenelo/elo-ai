"""
WO-CAP-EMB-002 — every embodiment needs an "I can..." model.

EMB-002 was TESTED ❌ FAIL on 2026-09-20 for two reasons, and both are
regression-tested here by name:

  1. a capability question answered by the conversation pattern observer
     ("You explored emotion, identity with a neutral tone")
  2. eLo denying capabilities it actually holds
     ("I can't control your computer directly" while holding
      WORLD_MEDIA_CONTROL / WORLD_REMINDERS_WRITE / WORLD_LIGHTS_CONTROL)

test_every_source_line_is_represented is the Board cross-check, executable:
it parses §2's VERBATIM SOURCE out of the work order.
"""
from __future__ import annotations

import os
import re

import pytest

from runtime import embodiment_capabilities as ec

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_WO = os.path.join(_ROOT, "engineering", "work_orders",
                   "WO-CAP-EMB-002_every_embodiment_needs_an_i_can_model.md")

_HEADINGS = {"Can:": "can", "Cannot:": "cannot", "Can eventually:": "can_eventually"}


def _source_model() -> dict[str, dict[str, list[str]]]:
    """Parse §2's body → Can/Cannot/Can eventually lists from the work order."""
    body = open(_WO, encoding="utf-8").read()
    block = body.split("**VERBATIM SOURCE — §2:**", 1)[1].split("**Acceptance test:**", 1)[0]
    lines = [ln.strip()[1:].strip() for ln in block.splitlines()
             if ln.strip().startswith(">")]
    lines = [ln for ln in lines if ln]
    lines = lines[lines.index("For example:") + 1:]
    lines = lines[:lines.index("So the cognitive question becomes:")]

    label_to_key = {v: k for k, v in ec.SOURCE_LABELS.items()}
    model: dict[str, dict[str, list[str]]] = {}
    body_key = mode = None
    for ln in lines:
        if ln in label_to_key:
            body_key = label_to_key[ln]
            model.setdefault(body_key, {"can": [], "cannot": [], "can_eventually": []})
            mode = None
        elif ln in _HEADINGS:
            mode = _HEADINGS[ln]
        elif body_key and mode:
            model[body_key][mode].append(ln)
    return model


def test_source_names_five_bodies():
    assert set(_source_model()) == set(ec.bodies())


def test_every_source_line_is_represented():
    """The Board cross-check, executable. Unmatched source line = FAIL."""
    unmatched = []
    for body, spec in _source_model().items():
        built = {
            "can": list(ec.CAN.get(body, ())),
            "cannot": list(ec.CANNOT.get(body, ())),
            "can_eventually": list(ec.CAN_EVENTUALLY.get(body, ())),
        }
        for kind, items in spec.items():
            if built[kind] != items:
                unmatched.append((body, kind, items, built[kind]))
    assert not unmatched, f"source and build differ: {unmatched}"


def test_nothing_invented_beyond_the_source():
    src = _source_model()
    for body in ec.bodies():
        assert list(ec.CAN.get(body, ())) == src[body]["can"], body
        assert list(ec.CAN_EVENTUALLY.get(body, ())) == src[body]["can_eventually"], body


def test_the_framing_question_is_verbatim():
    assert ec.COGNITIVE_QUESTION == "What can eLo do through this body?"
    assert ec.NOT_THE_QUESTION == "What can this separate AI do?"


def test_manipulate_appears_twice_for_the_robot():
    """Rule 4b — the source lists 'manipulate' and 'manipulate objects'."""
    robot = ec.CAN_EVENTUALLY[ec.ROBOT]
    assert "manipulate" in robot and "manipulate objects" in robot


# ── failure 1: the capability answer must not leak conversation state ─────────

def test_capability_answer_contains_no_conversation_state():
    """
    The 2026-09-20 failure: "what can you do right now through this terminal"
    was answered with "You explored emotion, identity with a neutral tone" --
    the pattern observer leaking into a capability question.

    Checked structurally, not by keyword: every string the answer carries must
    come from §2's own lists or from the live registry. Nothing derived from
    the conversation can satisfy that, so the leak is impossible rather than
    merely absent. A keyword scan was the first version of this test and it
    flagged "express emotion physically" -- a real §2 capability.
    """
    source = _source_model()
    live = set(ec._registered())
    for body in ec.bodies():
        answer = ec.capability_answer(body)
        allowed = set(source[body]["can"]) | set(source[body]["can_eventually"]) \
            | set(source[body]["cannot"]) | live | {body, ec.SOURCE_LABELS[body]}
        carried = set(answer["can"]) | set(answer["can_eventually"]) \
            | set(answer["cannot"]) | set(answer["registered_capabilities"]) \
            | set(answer["unsubstantiated"]) | {answer["body"], answer["label"]}
        assert carried <= allowed, (
            f"{body}: answer carries strings from neither §2 nor the registry: "
            f"{carried - allowed}"
        )


def test_capability_answer_is_about_the_body_only():
    answer = ec.capability_answer(ec.TERMINAL)
    assert answer["body"] == ec.TERMINAL
    assert answer["can"] == list(ec.CAN[ec.TERMINAL])
    assert set(answer) == {
        "body", "label", "can", "can_eventually", "cannot",
        "cannot_specified", "registered_capabilities", "unsubstantiated",
    }


# ── failure 2: eLo must not deny what it can actually do ──────────────────────

@pytest.mark.parametrize("claim", [
    "I can't do things like control your computer directly",
    "I cannot control your machine",
    "I can't open apps",
    "I'm not able to play music",
    "I can't set reminders for you",
    "I can't search the web",
])
def test_false_denials_are_caught(claim):
    """
    The second 2026-09-20 failure. Each of these contradicts a capability
    that is registered right now.
    """
    is_false, proof = ec.denial_is_false(claim)
    assert is_false, claim
    assert proof, claim


def test_a_true_denial_is_not_flagged():
    assert ec.denial_is_false("I can't physically walk") == (False, ())
    assert ec.denial_is_false("I cannot manipulate physical objects") == (False, ())
    assert ec.denial_is_false("") == (False, ())


def test_denial_check_is_grounded_in_the_live_registry(monkeypatch):
    """Remove the capability and the denial stops being false. Not hardcoded."""
    import runtime.capability_registry as cr
    trimmed = {k: v for k, v in cr.CAPABILITY_REGISTRY.items()
               if k not in ("WORLD_MEDIA_CONTROL", "WORLD_LIGHTS_CONTROL")}
    monkeypatch.setattr(cr, "CAPABILITY_REGISTRY", trimmed)
    assert ec.denial_is_false("I can't control your computer") == (False, ())


# ── the robot has not been built ──────────────────────────────────────────────

@pytest.mark.parametrize("action", ["see", "hear", "move", "touch", "manipulate"])
def test_robot_abilities_are_future_tense(action):
    """
    §2 gives the robot "Can eventually" -- the only body with a future tense.
    A body that does not exist yet can do nothing now. Same call EMB-051
    makes when it fails an unknown body safe to simulated.
    """
    assert ec.can(action, ec.ROBOT) is False
    assert ec.can_eventually(action, ec.ROBOT) is True


def test_no_other_body_has_an_eventually_list():
    for body in ec.bodies():
        if body != ec.ROBOT:
            assert ec.CAN_EVENTUALLY.get(body, ()) == ()


# ── absent is not empty ───────────────────────────────────────────────────────

def test_unspecified_cannot_returns_none_not_false():
    """
    §2 gives a Cannot list for the terminal only. Answering False for the
    others would read as "so it can" -- which is how eLo came to assert
    things about bodies the source never described.
    """
    assert ec.cannot("physically walk", ec.TERMINAL) is True
    assert ec.cannot("fly", ec.TERMINAL) is False
    for body in (ec.DESKTOP, ec.UNITY, ec.ROBOT, ec.ALEXA):
        assert ec.cannot("anything at all", body) is None, body


def test_current_body_reuses_the_emb_051_signal():
    """One embodiment signal, not a second source of truth."""
    from runtime import memory_origin
    for probe, expected in [("desktop", ec.DESKTOP), ("robot", ec.ROBOT),
                            ("unity", ec.UNITY), ("terminal", ec.TERMINAL),
                            ("pi5", ec.ROBOT), ("nonsense", ec.DESKTOP)]:
        assert ec.current_body.__module__ == "runtime.embodiment_capabilities"
        import unittest.mock as m
        with m.patch.object(memory_origin, "current_embodiment", lambda d="desktop", p=probe: p):
            assert ec.current_body() == expected, probe


def test_drift_from_the_registry_is_surfaced(monkeypatch):
    """A §2 line whose capability disappears is reported, not asserted."""
    import runtime.capability_registry as cr
    monkeypatch.setattr(cr, "CAPABILITY_REGISTRY",
                        {k: v for k, v in cr.CAPABILITY_REGISTRY.items()
                         if k != "WORLD_WEB_RESEARCH"})
    assert "research" in ec.unsubstantiated(ec.TERMINAL)
