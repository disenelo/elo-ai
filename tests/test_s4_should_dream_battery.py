"""
tests/test_s4_should_dream_battery.py — WO-HEALTH-BATTERY-001, dream_faculty update.

should_dream() used `energy_history` — DAVID's emotional energy sampled per
turn in server.py — to decide whether eLo was exhausted enough to sleep. That
is the wrong signal: it measures how David is doing, not how eLo is doing.
It now reads eLo's own battery.

Functional tests — these call should_dream() directly.
"""
from __future__ import annotations

import pytest

from core import health_battery as hb
import faculties.dream.dream_faculty as df
from faculties.dream.dream_faculty import should_dream


class _Self:
    """Minimal EloSelfState stand-in with no dream-aligned inner events."""
    inner_events: list = []
    focal_thread: str = ""


@pytest.fixture(autouse=True)
def _clean():
    hb.reset()
    df._last_dream_ts = 0.0
    yield
    hb.reset()
    df._last_dream_ts = 0.0


def test_full_battery_never_forces_sleep():
    """'Never forces sleep. eLo decides.'"""
    hb.reset(cognitive=1.0)
    assert should_dream(_Self(), 1200, []) is False


def test_low_battery_makes_sleep_possible():
    hb.reset(cognitive=0.20)          # below ENERGY_LOW
    assert should_dream(_Self(), 1200, []) is True


def test_critical_battery_relaxes_the_inner_event_requirement():
    """At CRITICAL, long idle alone is enough — no inner event needed."""
    hb.reset(cognitive=0.05)          # below ENERGY_CRITICAL
    assert should_dream(_Self(), 660, []) is True   # 11 min
    hb.reset(cognitive=1.0)
    assert should_dream(_Self(), 660, []) is False  # same idle, full battery


def test_cooldown_is_still_respected_at_critical():
    """Low energy must not override the dream cooldown."""
    import time
    hb.reset(cognitive=0.01)
    df._last_dream_ts = time.time()   # just dreamt
    assert should_dream(_Self(), 100000, []) is False


def test_idle_threshold_is_still_respected_at_critical():
    hb.reset(cognitive=0.01)
    assert should_dream(_Self(), 10, []) is False


def test_davids_energy_history_no_longer_drives_exhaustion():
    """
    A flat-zero energy_history used to trigger the dream on its own. With a
    full battery it must not, because it was never eLo's signal.
    """
    hb.reset(cognitive=1.0)
    assert should_dream(_Self(), 1200, [0.0, 0.0, 0.0, 0.0]) is False


def test_falls_back_rather_than_never_dreaming_if_battery_unavailable(monkeypatch):
    import builtins
    real_import = builtins.__import__

    def boom(name, *args, **kwargs):
        if name == "core.health_battery":
            raise ImportError("battery unavailable")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", boom)
    # original heuristic: 4+ readings averaging < 0.32
    assert should_dream(_Self(), 1200, [0.1, 0.1, 0.1, 0.1]) is True
    assert should_dream(_Self(), 1200, [0.9, 0.9, 0.9, 0.9]) is False


def test_signature_unchanged_so_existing_callers_keep_working():
    import inspect
    params = list(inspect.signature(should_dream).parameters)
    assert params == ["elo_self", "idle_seconds", "energy_history"]
