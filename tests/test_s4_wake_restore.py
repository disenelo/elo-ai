"""
tests/test_s4_wake_restore.py — WO-HEALTH-BATTERY-001 PART A.3 /
WO-DREAM-ENGINE-001 PHASE 11.

Waking from a dream restores eLo's battery: +0.30 for a full NREM+REM cycle,
+0.12 for NREM alone. Functional — calls wake_from_dream() directly.
"""
from __future__ import annotations

import pytest

from core import health_battery as hb
from faculties.dream.dream_faculty import DreamResult, wake_from_dream


class _Self:
    mood = 0.5
    curiosity = 0.5
    satisfaction = 0.5
    inner_events: list = []
    session_read = ""


@pytest.fixture(autouse=True)
def _clean(monkeypatch):
    hb.reset()
    # wake_from_dream() calls health_battery.publish(), which deep-merges into
    # the REAL blender/blender_state.json. Without this stub the suite mutates
    # live runtime state on every run — observed writing elo_battery=0.4
    # (0.10 + 0.30) into the running system.
    monkeypatch.setattr(hb, "publish", lambda: True)
    yield
    hb.reset()


def _wake(phase: str):
    return wake_from_dream(
        DreamResult(insight="something settled", journal_entry={"phase": phase}),
        _Self(),
    )


def test_full_cycle_restores_thirty():
    hb.reset(cognitive=0.10)
    _wake("NREM+REM")
    assert hb.get_energy() == pytest.approx(0.40, abs=1e-6)


def test_nrem_only_restores_twelve():
    hb.reset(cognitive=0.10)
    _wake("NREM")
    assert hb.get_energy() == pytest.approx(0.22, abs=1e-6)


def test_wake_lifts_eLo_out_of_critical():
    hb.reset(cognitive=0.05)
    assert hb.get_state() == "critical"
    _wake("NREM+REM")
    assert hb.get_state() == "normal"


def test_missing_phase_defaults_to_the_smaller_restore():
    hb.reset(cognitive=0.10)
    wake_from_dream(DreamResult(insight="x", journal_entry={}), _Self())
    assert hb.get_energy() == pytest.approx(0.22, abs=1e-6)


def test_lying_down_rests_the_body_too_once_physical_is_engaged():
    hb.reset(cognitive=0.10)
    hb.drain_physical(0.60)           # engages the physical track
    before = hb.get_physical()
    _wake("NREM+REM")
    assert hb.get_physical() > before


def test_physical_stays_untouched_on_desktop():
    """No motion reported -> physical track never engages."""
    hb.reset(cognitive=0.10)
    _wake("NREM+REM")
    assert hb.get_physical() == 1.0
    assert "physical_battery" not in hb.snapshot()


def test_existing_self_state_boosts_are_preserved():
    """The battery restore is an addition — it must not replace the old work."""
    hb.reset(cognitive=0.10)
    out = _wake("NREM+REM")
    assert out.curiosity == pytest.approx(0.62, abs=1e-6)   # +0.12
    assert out.mood == pytest.approx(0.58, abs=1e-6)        # +0.08
    assert "connection" in out.inner_events
    assert out.session_read.startswith("woke from dream")


def test_wake_is_fail_quiet_without_the_battery(monkeypatch):
    import builtins
    real_import = builtins.__import__

    def boom(name, *args, **kwargs):
        if name == "core.health_battery":
            raise ImportError("battery unavailable")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", boom)
    out = _wake("NREM+REM")        # must not raise
    assert out.mood == pytest.approx(0.58, abs=1e-6)
