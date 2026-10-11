"""
tests/test_dream_gate_daemon_status.py — card 0113

Proves two things:
  1. EloDaemon.status() returns the fields ambient_engine's dream-intent
     gate relies on (state, last_request_ts, resting_since_ts, tick_count,
     running).
  2. _maybe_emit_dream_intent() returns {} when the daemon reports idle
     < 300s — i.e. the sit→dream regression (David typing, eLo lays down)
     is now actually prevented, not just intended-to-be-prevented.

Headless: no live server, no LLM, no blender_state file writes.
"""
from __future__ import annotations

import time
from unittest.mock import patch

from runtime.elo_daemon import EloDaemon, LifeState


# ── 1. status() payload shape ──────────────────────────────────────────────────

def test_status_returns_fields_the_dream_gate_reads():
    d = EloDaemon()
    d.start()
    try:
        st = d.status()
        assert set(st.keys()) >= {
            "state", "last_request_ts", "resting_since_ts", "tick_count", "running",
        }
        assert st["state"] == LifeState.AWAKE.value
        assert st["running"] is True
        assert isinstance(st["last_request_ts"], float)
        # Freshly started → recent timestamp
        assert time.time() - st["last_request_ts"] < 5.0
    finally:
        d.stop()


# ── 2. dream intent is suppressed when daemon is AWAKE ────────────────────────

def test_dream_intent_suppressed_when_david_active():
    from ambient import ambient_engine as ae

    # Reset the module-level cooldown so a prior test cannot mask the gate.
    ae._dream_trigger_ts = 0.0

    battery = {"mind_battery": 0.10}  # well under ENERGY_LOW
    blender_state = {
        "calm_mode":   True,
        "dream_phase": "",
        "asleep":      False,
    }

    # Stub daemon.status() → very recent request (David just typed).
    class _FakeDaemon:
        def status(self) -> dict:
            return {"last_request_ts": time.time() - 10.0}  # 10 s ago

    with patch("runtime.elo_daemon.get_daemon", return_value=_FakeDaemon()):
        out = ae._maybe_emit_dream_intent(battery, blender_state)

    assert out == {}, (
        "dream intent fired while David was active in conversation "
        "(idle=10s). The AWAKE gate did not block it."
    )
