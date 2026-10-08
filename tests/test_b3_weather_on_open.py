"""
B3 — card 0006 WEATHER-ON-OPEN: get_current_weather() → one Presence key word.
Offline: provider fetch stubbed. Never touches blender/user_location.json.
"""
import pytest

from tools import tool_router as tr


@pytest.mark.parametrize("desc,word", [
    ("Light rain", "rain"), ("Patchy rain nearby", "rain"), ("Light rain shower", "shower"),
    ("Patchy light drizzle", "drizzle"), ("Thundery outbreaks in nearby", "storm"),
    ("Moderate or heavy rain with thunder", "storm"), ("Light sleet", "sleet"),
    ("Ice pellets", "sleet"), ("Blowing snow", "snow"), ("Blizzard", "blizzard"),
    ("Freezing fog", "fog"), ("Mist", "mist"), ("Overcast", "overcast"),
    ("Partly cloudy", "cloud"), ("Sunny", "sunny"), ("Clear", "clear"), ("", ""),
])
def test_presence_word(desc, word):
    assert tr.presence_weather_word(desc) == word


@pytest.fixture
def _fresh(monkeypatch):
    tr._wx_now.update(ts=0.0, word="")
    monkeypatch.setattr(tr, "_last_weather_condition", "")
    monkeypatch.setattr(tr, "_resolve_location", lambda: "Testville")
    yield
    tr._wx_now.update(ts=0.0, word="")


def test_fetch_returns_word_and_publishes_it(_fresh, monkeypatch):
    calls = []
    def fake(q):
        calls.append(q); tr._last_weather_condition = "patchy light rain"; return "Weather in Testville: Patchy light rain, 13°C"
    monkeypatch.setattr(tr, "_agent_weather", fake)
    assert tr.get_current_weather() == "rain"
    assert tr.get_last_weather_condition() == "rain"   # what server.py publishes to `weather`
    assert tr.get_current_weather() == "rain" and len(calls) == 1   # cached within 10 min
    assert tr.get_current_weather(max_age_s=0) == "rain" and len(calls) == 2


def test_no_location_publishes_nothing(_fresh, monkeypatch):
    monkeypatch.setattr(tr, "_resolve_location", lambda: None)
    monkeypatch.setattr(tr, "_agent_weather", lambda q: pytest.fail("must not fetch without a location"))
    assert tr.get_current_weather() == ""


def test_failed_fetch_is_empty_not_stale(_fresh, monkeypatch):
    monkeypatch.setattr(tr, "_last_weather_condition", "sunny")
    def boom(q): raise OSError("offline")
    monkeypatch.setattr(tr, "_agent_weather", boom)
    assert tr.get_current_weather() == ""
    assert tr.get_last_weather_condition() == "sunny"   # previous value kept, not overwritten
