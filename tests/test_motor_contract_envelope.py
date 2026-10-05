"""
tests/test_motor_contract_envelope.py — the brain requires a field Unity
cannot send.

Vol XI §1.5/§B: a motion ACK MUST carry at:{surface_id, pos}, so the brain
reads back the REAL position and never assumes the commanded one.
runtime.motor_contract.validate_up_event() has enforced that since
WO-CANON-XI and had zero callers, so nothing ever checked it.

Checked against the emitter 2026-10-05:

    EloOSAvatarReceiver.Ack.cs:113   WriteUnityEvent("sit_complete")
    EloOSAvatarReceiver.Ack.cs:278   WriteUnityEvent(type, extraKey, extraVal, k2, v2)
    EloEventLog.cs:45                {"seq","type","subject","action_id","payload","_ts"}

There is no parameter anywhere on that path that could produce 'at'. So the
contract and the emitter disagree, and the disagreement was invisible only
because the validator was never called.

The validator is therefore wired OBSERVE-ONLY: rejecting invalid ACKs would
reject every real one, eLo would never confirm a sit, and verify-before-speak
would fall to the 15s honest-fallback every single time. Counting the breach
makes it visible; the gate tightens when DesktopBuddy can send the field.

These tests exist to make that a fact someone trips over, not a note.
"""
from __future__ import annotations

import json
import pathlib

from runtime.motor_contract import validate_up_event


def _unity_row(ev_type: str, seq: int = 1, ts: float = 100.0) -> dict:
    """The EXACT row EloEventLog.Append writes — nothing added, nothing left out."""
    return json.loads(json.dumps({
        "seq":       seq,
        "type":      ev_type,
        "subject":   "",
        "action_id": "",
        "payload":   {},
        "_ts":       ts,
    }))


# ── the disagreement ────────────────────────────────────────────────────────

def test_unitys_real_sit_ack_fails_the_brains_contract():
    """
    Not a hypothetical malformed event — this is the row Unity actually
    writes. If this test ever goes green on its own, Unity started sending
    'at' and the observe-only gate in server.py can become a hard gate.
    """
    ok, why = validate_up_event(_unity_row("sit_complete"))

    assert ok is False
    assert "at" in why, f"expected the missing-'at' reason, got: {why}"


def test_the_same_ack_passes_once_unity_adds_at():
    """The contract is satisfiable — the emitter just does not satisfy it."""
    ev = _unity_row("sit_complete")
    ev["at"] = {"surface_id": "desk", "pos": [0, 0]}

    ok, why = validate_up_event(ev)

    assert ok is True, why


def test_a_non_motion_event_needs_no_position():
    """Only motion ACKs carry 'at'; a gaze change legitimately has no position."""
    ok, _ = validate_up_event(_unity_row("gaze_target_changed"))
    assert ok is True


# ── the wire ────────────────────────────────────────────────────────────────

def _server_source() -> str:
    return (pathlib.Path(__file__).resolve().parent.parent / "server.py").read_text()


def test_the_poller_validates_every_body_ack():
    assert "from runtime.motor_contract import validate_up_event" in _server_source()


def test_the_poller_does_not_drop_invalid_acks():
    """
    The whole point of observe-only. If someone later makes this a hard gate
    without Unity sending 'at', eLo stops confirming sits entirely — so the
    accept must stay unconditional and this test must be read before changing
    it.
    """
    code = _server_source()
    i = code.index("_ACK_ENVELOPE_BREACHES[_ev_type]")
    window = code[i:i + 900]

    assert "_ACK_QUEUE.append" in window, "the ACK must still be queued"
    for bail in ("continue", "break", "return"):
        assert f"\n{' ' * 32}{bail}" not in window, (
            f"'{bail}' after the breach count would drop real ACKs"
        )
