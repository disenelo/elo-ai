**WO:** WEATHER-ROUTING · **Seat:** builder3 · **Priority:** P1
**Reserved?** no

## Goal
"What's the weather?" routes to the weather tool, not screen-reading.

## What's broken
"What's the weather" currently routes to screen-reading instead of the weather tool. The executive never proposes weather/clipboard tools — it's a spine-side routing failure.
Note: the fix lives in spine (Builder 1 owns spine). Builder 3's job: verify the weather tool itself is working correctly and wired, so when the routing is fixed it works end-to-end.

## Scope — exactly this, nothing more
- Verify `tools/web_search.py` or weather tool exists and returns a valid result
- Write a test that calls the weather tool directly and gets weather data back
- Document the exact tool name and call signature so Builder 1 can wire it into the executive routing

## Files to touch
`tools/web_search.py` · `capability_registry.py`

## Test
Direct call to weather tool → returns weather data for a location.

## Done when
Weather tool verified working. Call signature documented. Capability registered. Committed. Move to BUILT/.

## Live turn needed (seat fills this in — exact words)
> David says to eLo: "What's the weather like?"
> eLo should use the weather tool and give a real answer, not describe the screen.
> eLo should respond: "<conditions> in Hackney Wick — <temp>°C[, feels like <x>°C]."

## Result
- commit: ed376bc (test). Tool + routing work landed earlier: 1eb5844 (Hackney Wick from eLo's knowledge, spoken line), 8db420e (defers to the Executive's plan), f180010 (WO-018 gate)
- test: `python3 -m pytest tests/test_b3_weather_tool.py` → 5 passed (tool returns live weather with a temperature; location from eLo's knowledge; spoken line; Executive's real capability step puts weather FIRST for 3 phrasings; a plan selecting weather → direct answer, no raw [CONTEXT])
- notes: **The "what's broken" premise is wrong, and it came from Builder 3.** The Executive does propose weather. B3's 2026-10-07 offline check passed {} as the intent, which disabled the router pre-route. Corrected in TO_BOARD_2026-10-07_CORRECTION.md. **No spine fix is needed.** Call signature: `tools.tool_router._AGENTS["weather"](query) -> "Weather in <place>: <cond>, <t>°C, …"`; `_spoken_weather(str) -> eLo's line`; `_resolve_location() -> place` (session > eLo's knowledge > file). Registered capability id `weather` (runtime/capabilities/registry.py). Live real-server turn 2026-10-06 (audit 5d184274): "Partly sunny in Hackney Wick — 20°C, feels like 24°C." `direct:weather`.
