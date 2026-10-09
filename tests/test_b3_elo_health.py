"""
B3 — "battery" is eLo's, never David's Mac (David 2026-10-09): robot = battery,
DISENELO Presence = health, by the body he's in. Offline.
"""
import pytest
import tools.tool_router as tr
import tools.system_agent as sa


@pytest.mark.parametrize("q", ["What's my battery?", "what's your battery", "how's your health", "health?",
                               "are you tired?", "eLo, how much charge have you got", "how's eLo's battery"])
def test_elo_battery_questions_get_his_health(q):
    c = tr._elo_health_context(q.lower())
    assert c and "HEALTH" in c and "not David's Mac" in c
    assert sa.detect_direct(q) is None                     # the Mac never answers these


@pytest.mark.parametrize("q", ["what's my Mac's battery", "what's the battery on my laptop", "computer battery?"])
def test_explicit_mac_battery_still_reads_the_mac(q):
    assert tr._elo_health_context(q.lower()) is None
    assert sa.detect_direct(q) == ("battery", "get")


@pytest.mark.parametrize("q", ["my mouse battery is low", "I love my new battery pack", "health insurance is expensive"])
def test_unrelated_mentions_left_alone(q):
    assert tr._elo_health_context(q.lower()) is None


def test_robot_body_with_hardware_reports_robot_battery(monkeypatch):
    import core.health_battery as hb
    import runtime.embodiment_capabilities as emb
    monkeypatch.setattr(emb, "current_body", lambda: emb.ROBOT)
    monkeypatch.setattr(hb, "_hardware_enabled", lambda: True)
    c = tr._elo_health_context("what's your battery")
    assert c.startswith("Your robot body's battery")


def test_intercept_is_context_for_the_brain_not_a_written_reply(monkeypatch):
    out = tr._direct_intercepts("what's your battery?")
    assert out and out[1] == "elo_health" and out[0].startswith("[CONTEXT: ")
    assert tr.get_direct_result() is None                  # eLo's brain words it
