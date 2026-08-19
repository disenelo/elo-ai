"""
tests/test_wo111_consume_ack.py — Card 0011 (WO-111 Builder half).

Card acceptance (blender/agent_bus/builder/DONE/0011_WO-111_consume_anim_complete.md):
- Wave that completes ⇒ ACK matched, eLo may claim it.
- Wave that fails ⇒ anim_failed ⇒ eLo says it didn't work.
- Clip trigger with no ACK path ⇒ status `unconfirmed`, not success.
- Timeout ⇒ reported failure.

These tests FAIL if the executor stops consuming ACKs and reverts to trusting
the file write — i.e. they fail when the feature is disconnected (Rule 5.3).
"""
from __future__ import annotations

import json
import os
import sys
import threading
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


def _write_ack(events_path: str, seq: int, event_type: str, action_id: str,
               subject: str = "", payload=None) -> None:
    row = {"seq": seq, "type": event_type, "subject": subject,
           "action_id": action_id, "payload": payload or {},
           "_ts": time.time()}
    with open(events_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(row) + "\n")


# ── AT-0011-1: wave complete ⇒ confirmed, honest_outcome may claim it ─────────

def test_wave_complete_ack_lets_elo_claim_it(tmp_path, monkeypatch):
    import blender_bridge.anim_trigger as _at
    from runtime.ack_contract import honest_outcome
    monkeypatch.setattr(_at, "_STATE_PATH", str(tmp_path / "blender_state.json"))
    monkeypatch.setattr(_at, "_EVENTS_PATH", str(tmp_path / "unity_events.json"))

    def emit_ack():
        time.sleep(0.15)
        _write_ack(str(tmp_path / "unity_events.json"), seq=1,
                   event_type="anim_complete", action_id="wave-A", subject="wave")

    t = threading.Thread(target=emit_ack, daemon=True)
    t.start()
    result = _at.fire_ack("wave", action_id="wave-A", timeout_s=3.0)
    t.join(timeout=2.0)

    assert result.is_confirmed, f"expected confirmed, got: {result}"
    assert result.source == "unity_ack"
    sentence = honest_outcome(result, action_label="wave")
    assert "done" in sentence.lower() and "confirmed" in sentence.lower(), (
        f"honest_outcome should let eLo claim the wave; got: {sentence!r}"
    )


# ── AT-0011-2: wave failed ⇒ eLo says it didn't work ─────────────────────────

def test_wave_failed_ack_says_didnt_work(tmp_path, monkeypatch):
    import blender_bridge.anim_trigger as _at
    from runtime.ack_contract import honest_outcome
    monkeypatch.setattr(_at, "_STATE_PATH", str(tmp_path / "blender_state.json"))
    monkeypatch.setattr(_at, "_EVENTS_PATH", str(tmp_path / "unity_events.json"))

    def emit_failure():
        time.sleep(0.15)
        _write_ack(str(tmp_path / "unity_events.json"), seq=1,
                   event_type="anim_failed", action_id="wave-B", subject="wave",
                   payload={"reason": "no component"})

    t = threading.Thread(target=emit_failure, daemon=True)
    t.start()
    result = _at.fire_ack("wave", action_id="wave-B", timeout_s=3.0)
    t.join(timeout=2.0)

    assert result.is_failed, f"expected failed, got: {result}"
    assert result.source == "unity_ack"
    sentence = honest_outcome(result, action_label="wave")
    assert "didn't work" in sentence.lower() or "failure" in sentence.lower(), (
        f"honest_outcome for failure must say it didn't work; got: {sentence!r}"
    )
    # Critically: must NOT claim success.
    assert "done" not in sentence.lower() and "confirmed" not in sentence.lower()


# ── AT-0011-3: clip trigger with no ACK path ⇒ unconfirmed (not success) ─────

def test_clip_trigger_no_ack_path_reports_unconfirmed(tmp_path, monkeypatch):
    """
    Card 0011: "The un-ACKed clip triggers (jump/gun/calm) must report
    `unconfirmed`, not success. Do not let them inherit the old True.
    Designer deferred them honestly; don't undo that on this side."
    """
    import blender_bridge.anim_trigger as _at
    from runtime.ack_contract import honest_outcome
    monkeypatch.setattr(_at, "_STATE_PATH", str(tmp_path / "blender_state.json"))
    monkeypatch.setattr(_at, "_EVENTS_PATH", str(tmp_path / "unity_events.json"))

    for name in ("jump", "gun_check", "gun_run", "gun_fire",
                 "calm_enter", "calm_exit", "celebrate", "spawn_wave"):
        result = _at.fire_ack(name, action_id=f"{name}-x", timeout_s=0.2)
        assert result.is_unconfirmed, (
            f"'{name}' has no anim_complete ACK path — must be unconfirmed, got: {result}"
        )
        assert not result.is_confirmed
        sentence = honest_outcome(result, action_label=name)
        assert "done" not in sentence.lower() and "confirmed" not in sentence.lower(), (
            f"unconfirmed must NOT claim success for '{name}'; got: {sentence!r}"
        )


# ── AT-0011-4: timeout ⇒ reported failure, never silence ─────────────────────

def test_timeout_reports_failure(tmp_path, monkeypatch):
    import blender_bridge.anim_trigger as _at
    from runtime.ack_contract import honest_outcome
    monkeypatch.setattr(_at, "_STATE_PATH", str(tmp_path / "blender_state.json"))
    monkeypatch.setattr(_at, "_EVENTS_PATH", str(tmp_path / "unity_events.json"))

    t0 = time.time()
    result = _at.fire_ack("wave", action_id="wave-timeout", timeout_s=0.4)
    dt = time.time() - t0

    assert result.is_failed, f"timeout must report failure; got: {result}"
    assert result.source == "timeout"
    assert dt < 2.5, f"timeout should honor the requested bound; took {dt:.2f}s"
    sentence = honest_outcome(result, action_label="wave")
    assert "didn't work" in sentence.lower() or "failure" in sentence.lower()


# ── AT-0011-5: dead-executor check — feature disconnects ⇒ tests fail ────────

def test_no_ack_consumer_means_no_confirmation(tmp_path, monkeypatch):
    """
    Rule 5.3: a test must FAIL if the feature is disconnected. If wait_for_ack
    ever regresses to trusting the file write, this test — which never emits
    an ACK — must not return `confirmed`.
    """
    import blender_bridge.anim_trigger as _at
    monkeypatch.setattr(_at, "_STATE_PATH", str(tmp_path / "blender_state.json"))
    monkeypatch.setattr(_at, "_EVENTS_PATH", str(tmp_path / "unity_events.json"))

    result = _at.fire_ack("wave", action_id="wave-dead", timeout_s=0.2)
    assert not result.is_confirmed, (
        "no ACK was ever emitted — a confirmed result means the consumer is fabricating."
    )


# ── AT-0011-6: only new ACKs count (baseline-seq guard) ──────────────────────

def test_pre_existing_ack_does_not_confirm_new_action(tmp_path, monkeypatch):
    """
    A stale ACK row with the SAME action_id from a prior run must NOT confirm
    a new fire_ack() invocation — we snapshot _max_seq() BEFORE writing.
    """
    import blender_bridge.anim_trigger as _at
    monkeypatch.setattr(_at, "_STATE_PATH", str(tmp_path / "blender_state.json"))
    monkeypatch.setattr(_at, "_EVENTS_PATH", str(tmp_path / "unity_events.json"))

    # Pre-existing ACK row for the same action_id.
    _write_ack(str(tmp_path / "unity_events.json"), seq=0,
               event_type="anim_complete", action_id="wave-reuse", subject="wave")

    result = _at.fire_ack("wave", action_id="wave-reuse", timeout_s=0.2)
    assert result.is_failed and result.source == "timeout", (
        f"stale ACK must not confirm a new invocation; got: {result}"
    )
