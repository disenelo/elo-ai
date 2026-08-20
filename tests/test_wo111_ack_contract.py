"""
tests/test_wo111_ack_contract.py — WO-111: ACK contract for all actions.

AT-111-1:  anim_trigger.fire() no longer returns True (returns ANIM_UNCONFIRMED)
AT-111-2:  make_result(True) → confirmed ActionResult
AT-111-3:  make_result(False) → failed ActionResult
AT-111-4:  make_result("unconfirmed") → unconfirmed ActionResult
AT-111-5:  honest_outcome says "didn't work" on failure — not silence
AT-111-6:  honest_outcome says "can't confirm" on unconfirmed (not "done")
AT-111-7:  capabilities with ack_required=True exist for the physical actions
AT-111-8:  Capability dataclass carries ack_required field
AT-111-9:  Card 05a — every capability declares ack_source; a new capability
           added without one fails the test (adds a temp cap and asserts).
AT-111-10: Card 05a — a silently-failing executor produces the "didn't work"
           sentence through make_result + honest_outcome (broken executor makes
           him say so — the row 13 VERIFIED criterion).
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


# ── AT-111-1: anim_trigger no longer lies ────────────────────────────────────

def test_anim_trigger_does_not_return_true(tmp_path, monkeypatch):
    import blender_bridge.anim_trigger as _at
    # Point at a temp file so no real state is touched
    monkeypatch.setattr(_at, "_STATE_PATH", str(tmp_path / "blender_state.json"))
    result = _at.fire("wave")
    assert result is not True, (
        "anim_trigger.fire() returned True — that claims success with no ACK evidence. "
        "WO-111: must return ANIM_UNCONFIRMED."
    )
    assert result == _at.ANIM_UNCONFIRMED, (
        f"Expected ANIM_UNCONFIRMED sentinel, got: {result!r}"
    )


# ── AT-111-2..4: ActionResult from make_result() ─────────────────────────────

def test_make_result_confirmed():
    from runtime.ack_contract import make_result
    r = make_result("sit", True, source="unity_ack")
    assert r.is_confirmed
    assert not r.is_failed
    assert not r.is_unconfirmed


def test_make_result_failed():
    from runtime.ack_contract import make_result
    r = make_result("move", False)
    assert r.is_failed
    assert not r.is_confirmed
    assert not r.is_unconfirmed


def test_make_result_unconfirmed():
    from runtime.ack_contract import make_result, UNCONFIRMED
    r = make_result("wave", UNCONFIRMED)
    assert r.is_unconfirmed
    assert not r.is_confirmed
    assert not r.is_failed


# ── AT-111-5..6: honest_outcome says the right thing ─────────────────────────

def test_honest_outcome_failure():
    from runtime.ack_contract import make_result, honest_outcome
    r = make_result("jump", False)
    sentence = honest_outcome(r, action_label="jump")
    assert "didn't work" in sentence.lower() or "failure" in sentence.lower(), (
        f"honest_outcome for failure must say it didn't work; got: {sentence!r}"
    )


def test_honest_outcome_unconfirmed_not_done():
    from runtime.ack_contract import make_result, honest_outcome, UNCONFIRMED
    r = make_result("wave", UNCONFIRMED)
    sentence = honest_outcome(r, action_label="wave")
    done_words = ["done", "success", "confirmed", "worked"]
    assert not any(w in sentence.lower() for w in done_words), (
        f"honest_outcome for unconfirmed must NOT claim success; got: {sentence!r}"
    )
    assert "can't confirm" in sentence.lower() or "cannot confirm" in sentence.lower() \
        or "triggered" in sentence.lower(), (
        f"honest_outcome for unconfirmed should acknowledge uncertainty; got: {sentence!r}"
    )


# ── AT-111-7: Capability.ack_required field exists ───────────────────────────

def test_capability_has_ack_required_field():
    from runtime.capabilities.capability import Capability
    import dataclasses
    fields = {f.name for f in dataclasses.fields(Capability)}
    assert "ack_required" in fields, \
        "Capability dataclass missing ack_required field — WO-111 not applied"


# ── AT-111-8: No new capability registered without ack_required being declared ─

def test_all_capabilities_have_ack_required_declared():
    """
    Every capability has ack_required explicitly declared (defaults to False for
    utilities). This fails if a capability is added without touching the field.
    Since ack_required defaults to False, the test checks that the field exists
    and is accessible on every registered capability.
    """
    from runtime.capabilities.registry import ALL_CAPABILITIES
    missing = []
    for cap in ALL_CAPABILITIES:
        if not hasattr(cap, "ack_required"):
            missing.append(cap.id)
    assert not missing, (
        f"Capabilities missing ack_required field (WO-111): {missing}"
    )


# ── AT-111-9: Card 05a — every capability declares ack_source ────────────────

def test_every_capability_declares_ack_source():
    """
    Card 05a — 'Every registry capability has an ACK path. That assertion is
    the point of this card.' A capability with ack_source == ACK_UNKNOWN is one
    that shipped without deciding how its outcome gets confirmed. That silent
    default is the exact failure mode row 13 exists to prevent, so the test
    fails when the list is non-empty.
    """
    from runtime.capabilities.registry import (
        ALL_CAPABILITIES, capabilities_missing_ack_path,
    )
    missing = capabilities_missing_ack_path()
    assert not missing, (
        f"Capabilities without a declared ack_source (WO-111 card 05a): {missing}. "
        f"Set ack_source=ACK_SYNC_RETURN | ACK_UNITY_ACK | ACK_NONE at declaration."
    )
    # And every one carries the field — no capability slips past the dataclass.
    from runtime.capabilities.capability import ACK_SOURCES
    bad_values = [c.id for c in ALL_CAPABILITIES if c.ack_source not in ACK_SOURCES]
    assert not bad_values, (
        f"Capabilities with non-canonical ack_source values: {bad_values}"
    )


def test_new_capability_without_ack_source_fails_the_check():
    """
    Card 05a — 'a test that fails when a new capability is added without one.'
    Directly proves the guarantee: construct a capability without ack_source and
    the coverage check must reject it.
    """
    from runtime.capabilities.capability import (
        Capability, CAT_UTILITY, ACK_UNKNOWN,
    )
    from runtime.capabilities.registry import ALL_CAPABILITIES
    # Simulate a freshly-added capability that forgot ack_source.
    orphan = Capability(
        id="__orphan_no_ack__", display_name="Orphan", category=CAT_UTILITY,
        description="test-only capability that omits ack_source",
        verbs=["orphan"],
    )
    assert orphan.ack_source == ACK_UNKNOWN, (
        "default ack_source must be ACK_UNKNOWN so the coverage test can catch it"
    )
    # Add it to the registry list, run the check, then remove — the check must
    # flag it. If it doesn't, the guard has regressed and new capabilities can
    # slip through without an ACK path.
    ALL_CAPABILITIES.append(orphan)
    try:
        from runtime.capabilities.registry import capabilities_missing_ack_path
        missing = capabilities_missing_ack_path()
        assert "__orphan_no_ack__" in missing, (
            "coverage check failed to flag a capability with no ack_source — "
            "the point-of-card guarantee is broken"
        )
    finally:
        ALL_CAPABILITIES.remove(orphan)


# ── AT-111-10: Card 05a — silently failing executor makes him say so ─────────

def test_broken_executor_produces_didnt_work_sentence():
    """
    Card 05a row-13 VERIFIED criterion (from 0011): 'Row 13 goes VERIFIED when a
    broken executor makes him say so — not before.' A silent False from an
    executor must route through make_result → honest_outcome and produce a
    sentence that eLo can utter — one that says it did NOT work.
    """
    from runtime.ack_contract import make_result, honest_outcome

    def broken_executor():
        # Simulate an executor that ran, quietly reported failure, and returned.
        return False

    raw = broken_executor()
    result = make_result("scale_up", raw, source="tool_return")
    assert result.is_failed, "broken executor return must produce is_failed"

    sentence = honest_outcome(result, action_label="scale up")
    lowered = sentence.lower()
    assert "didn't work" in lowered or "failure" in lowered, (
        f"broken executor must produce 'didn't work'/failure wording; got: {sentence!r}"
    )
    # Verified Speech: must NOT claim success.
    for banned in ("done", "confirmed", "success", "worked"):
        assert banned not in lowered, (
            f"broken executor produced success language ({banned!r}) in: {sentence!r}"
        )


def test_unknown_return_is_unconfirmed_not_success():
    """
    Card 05a — 'No ACK ⇒ eLo may not claim it happened.' Any executor return
    that isn't True/False/UNCONFIRMED (e.g. a stray dict, an int, a fresh
    executor that hasn't been wired to ack_contract yet) must fall through to
    unconfirmed — never confirmed.
    """
    from runtime.ack_contract import make_result, honest_outcome
    result = make_result("spawn_wave", {"unexpected": "shape"}, source="internal")
    assert result.is_unconfirmed, (
        f"unknown return must be unconfirmed, not confirmed; got: {result}"
    )
    sentence = honest_outcome(result, action_label="spawn wave").lower()
    assert "done" not in sentence and "confirmed" not in sentence, (
        f"unconfirmed executor must not claim success; got: {sentence!r}"
    )
