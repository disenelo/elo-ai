"""HEALTH-CHAIN-003 Missing A: _maybe_emit_dream_intent — dream intent signal under low battery + calm."""
import pytest
import ambient.ambient_engine as _ae


def _reset_ts():
    _ae._dream_trigger_ts = 0.0


def test_no_signal_when_battery_high():
    _reset_ts()
    result = _ae._maybe_emit_dream_intent(
        {"elo_battery": 0.8},
        {"is_calm": True},
    )
    assert result == {}


def test_no_signal_when_not_calm():
    _reset_ts()
    result = _ae._maybe_emit_dream_intent(
        {"elo_battery": 0.1},
        {"is_calm": False},
    )
    assert result == {}


def test_signal_when_low_battery_and_calm():
    _reset_ts()
    result = _ae._maybe_emit_dream_intent(
        {"elo_battery": 0.1},
        {"is_calm": True},
    )
    assert result == {"intent": "dream"}


def test_no_signal_when_already_dreaming():
    _reset_ts()
    result = _ae._maybe_emit_dream_intent(
        {"elo_battery": 0.1},
        {"is_calm": True, "dream_phase": "NREM"},
    )
    assert result == {}


def test_rate_limited_after_fire():
    _reset_ts()
    # First fire should succeed
    r1 = _ae._maybe_emit_dream_intent({"elo_battery": 0.1}, {"is_calm": True})
    assert r1 == {"intent": "dream"}
    # Immediate second fire should be rate-limited
    r2 = _ae._maybe_emit_dream_intent({"elo_battery": 0.1}, {"is_calm": True})
    assert r2 == {}
