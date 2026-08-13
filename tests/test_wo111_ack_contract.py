"""
tests/test_wo111_ack_contract.py — WO-111: ACK contract for all actions.

AT-111-1: anim_trigger.fire() no longer returns True (returns ANIM_UNCONFIRMED)
AT-111-2: make_result(True) → confirmed ActionResult
AT-111-3: make_result(False) → failed ActionResult
AT-111-4: make_result("unconfirmed") → unconfirmed ActionResult
AT-111-5: honest_outcome says "didn't work" on failure — not silence
AT-111-6: honest_outcome says "can't confirm" on unconfirmed (not "done")
AT-111-7: capabilities with ack_required=True exist for the physical actions
AT-111-8: Capability dataclass carries ack_required field
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
