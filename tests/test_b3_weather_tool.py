"""
B3 card 0004 (WEATHER-ROUTING) — the weather tool works, is wired, and the
Executive's real capability step proposes it. Needs network for the provider
call; no side effects (no server, no files written).

Call signature (for anyone wiring it):
  tools.tool_router._AGENTS["weather"](query: str) -> str
      e.g. "Weather in Hackney Wick: Overcast, 20°C, feels like 20°C, humidity …"
  tools.tool_router._spoken_weather(that_string) -> eLo's line
      "Overcast in Hackney Wick — 20°C."
  tools.tool_router._resolve_location() -> David's location from eLo's knowledge
"""
import re

import tools.tool_router as tr


def test_location_comes_from_elos_knowledge():
    assert tr._resolve_location(), "no location — weather would ask instead of answering"


def test_weather_tool_returns_data():
    out = tr._AGENTS["weather"]("what's the weather like right now")
    assert "No location saved" not in out
    assert re.search(r"-?\d+(?:\.\d+)?°[CF]", out), f"no temperature in {out!r}"


def test_spoken_line_from_tool_output():
    line = tr._spoken_weather("Weather in Hackney Wick: Partly sunny, 20°C, feels like 24°C, humidity 65%, wind 0 km/h.")
    assert line == "Partly sunny in Hackney Wick — 20°C, feels like 24°C."


def test_executive_proposes_weather_first():
    import runtime.spine.spine as sp
    for t in ("what's the weather like right now", "what's the weather", "is it going to rain today"):
        lang = sp._language_faculty(t)
        cands = sp._capability_faculty(lang["meaning"], lang.get("capability_hint", ""))
        assert cands and cands[0]["id"] == "weather", f"{t!r} → {[c['id'] for c in cands]}"


def test_selected_weather_is_answered_directly():
    enriched, agent = tr.enrich_from_plan("what's the weather like right now", [("weather", "what's the weather")])
    assert agent == "weather" and "[CONTEXT" not in enriched and re.search(r"°[CF]", enriched)
