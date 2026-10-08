"""
B3 card 0006 — ambient_engine._publish_weather: David's real weather word → blender_state "weather".
Offline: fetch and state write stubbed. Not live evidence.
"""
import time
import pytest
from ambient import ambient_engine as ae
import tools.tool_router as tr
import blender_bridge.state_writer as sw


@pytest.fixture
def _stubs(monkeypatch):
    written, asked = [], []
    monkeypatch.setattr(sw, "patch", lambda d: written.append(d))
    monkeypatch.setattr(tr, "get_current_weather", lambda max_age_s=600: asked.append(max_age_s) or "rain")
    monkeypatch.setattr(ae, "_LAST_WEATHER_FETCH", 0.0)
    monkeypatch.setattr(ae, "_WEATHER_BUSY", False)
    return written, asked


def _settle():
    for _ in range(50):
        if not ae._WEATHER_BUSY:
            return
        time.sleep(0.02)


def test_app_open_publishes_plain_word(_stubs):
    written, asked = _stubs
    ae._publish_weather(force=True); _settle()
    assert written == [{"weather": "rain"}] and asked == [0]


def test_refresh_waits_for_interval(_stubs):
    written, _ = _stubs
    ae._publish_weather(); _settle()
    ae._publish_weather(); _settle()             # within 12 min → no second fetch
    assert written == [{"weather": "rain"}]


def test_nothing_published_without_a_word(_stubs, monkeypatch):
    written, _ = _stubs
    monkeypatch.setattr(tr, "get_current_weather", lambda max_age_s=600: "")
    ae._publish_weather(force=True); _settle()
    assert written == []


def test_no_hard_coded_city_left():
    src = open(ae.__file__).read()
    assert 'city = "London"' not in src
