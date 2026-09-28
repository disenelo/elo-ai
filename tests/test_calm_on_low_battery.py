"""
Low battery -> Calm/Meditation. Never Sleep.

David 2026-09-28: eLo has two rest states and they must not merge.
  Calm = Meditation  — CONSCIOUS. The low-battery visual.
  Sleep = Dream      — UNCONSCIOUS, one coupled state, gated ONLY on
                       dream_phase. A battery threshold must never reach it.

The load-bearing test here is test_low_battery_never_touches_any_sleep_field.
"""
from __future__ import annotations

import pytest

import ambient.ambient_engine as ae


@pytest.fixture(autouse=True)
def _neutral(monkeypatch):
    """Awake, silent, uncommanded, not already calm in presence_state."""
    monkeypatch.setattr(ae, "_is_calm", lambda: False)
    monkeypatch.setattr(ae, "_is_speaking", lambda: False)
    monkeypatch.setattr(ae, "_is_commanded", lambda: False)
    monkeypatch.setattr(ae, "_brain_calm_asserted", False, raising=False)
    import faculties.dream.dream_faculty as df
    monkeypatch.setattr(df, "_is_dreaming", False, raising=False)
    yield
    ae._brain_calm_asserted = False


@pytest.mark.parametrize("state", ["low", "critical"])
def test_low_battery_enters_calm(state):
    out = ae._calm_on_low_battery(state, {"mode": "idle"})
    assert out["calm_mode"] is True
    assert out["motion"]["animation"] == "calm"
    assert out["motion"]["mode"] == "calm"


@pytest.mark.parametrize("state", ["normal", "full"])
def test_healthy_battery_does_not_enter_calm(state):
    out = ae._calm_on_low_battery(state, {"mode": "idle"})
    assert out["calm_mode"] is False
    assert "motion" not in out


@pytest.mark.parametrize("state", ["low", "critical"])
def test_low_battery_never_touches_any_sleep_field(state):
    """
    The rule this module exists for. Calm must never reach sleep -- sleep is
    Dream, structurally gated on dream_phase alone. A battery threshold that
    wrote any dream field would disconnect sleep from dream.
    """
    out = ae._calm_on_low_battery(state, {"mode": "idle"})
    forbidden = {"dream_phase", "dream_cycle", "dream_intensity", "asleep", "sleep"}
    assert not (forbidden & set(out)), out
    assert out["motion"]["animation"] != "sleep"


def test_a_dream_in_progress_is_not_overwritten(monkeypatch):
    """Sleep=Dream owns the body while it runs."""
    import faculties.dream.dream_faculty as df
    monkeypatch.setattr(df, "_is_dreaming", True, raising=False)
    out = ae._calm_on_low_battery("critical", {"mode": "idle"})
    assert "motion" not in out, "calm overwrote a running dream"


def test_speech_and_commands_are_not_interrupted(monkeypatch):
    monkeypatch.setattr(ae, "_is_speaking", lambda: True)
    assert "motion" not in ae._calm_on_low_battery("low", {"mode": "idle"})
    monkeypatch.setattr(ae, "_is_speaking", lambda: False)
    monkeypatch.setattr(ae, "_is_commanded", lambda: True)
    assert "motion" not in ae._calm_on_low_battery("low", {"mode": "idle"})


def test_calm_is_not_restarted_every_tick():
    """Already resting -> assert the flag, do not rewrite the animation."""
    first = ae._calm_on_low_battery("low", {"mode": "idle"})
    assert "motion" in first
    again = ae._calm_on_low_battery("low", {"mode": "calm"})
    assert again == {"calm_mode": True}


def test_calm_resumes_if_something_else_took_the_body():
    """Self-healing: motion drifted off calm while still low -> re-assert."""
    ae._calm_on_low_battery("low", {"mode": "idle"})
    resumed = ae._calm_on_low_battery("low", {"mode": "walk"})
    assert resumed["motion"]["mode"] == "calm"


def test_recovery_releases_calm_so_calmexit_can_play():
    ae._calm_on_low_battery("critical", {"mode": "idle"})
    out = ae._calm_on_low_battery("normal", {"mode": "calm"})
    assert out["calm_mode"] is False
    assert out["motion"]["mode"] == "idle"


def test_release_happens_once_not_every_tick():
    ae._calm_on_low_battery("low", {"mode": "idle"})
    ae._calm_on_low_battery("normal", {"mode": "calm"})
    assert ae._calm_on_low_battery("normal", {"mode": "idle"}) == {"calm_mode": False}


def test_presence_calm_still_reported_when_battery_is_healthy(monkeypatch):
    """Unity's own calm state is not masked by this path."""
    monkeypatch.setattr(ae, "_is_calm", lambda: True)
    assert ae._calm_on_low_battery("normal", {"mode": "calm"})["calm_mode"] is True
