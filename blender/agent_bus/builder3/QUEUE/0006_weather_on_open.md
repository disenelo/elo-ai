**WO:** WEATHER-ON-OPEN · **Seat:** builder3 · **Priority:** P1
**Reserved?** no

## Goal
When the app opens, fetch the real local weather and publish it to `weather` in blender_state.json. Refresh every 10–15 minutes. Presence already reacts to the `weather` field visually (rain → rain on windows, snow → snow builds, fog → fog layers). Right now the state shows `clear` when it's raining outside.

## Trigger
Presence writes `unity_events.json`: type=`weather_request`, subject=`app_open` on every launch.
Builder 1 will consume this event and call Builder 3's weather integration (see FROM_ARCHITECT_2026-10-08_FULL-PRESENCE-WIRE.md Ask 1).

## What to build
1. Confirm weather tool can fetch real local weather (existing tool in `tools/` — see card 0004 and 0005 for current state).
2. Expose a callable function Builder 1 can invoke: `get_current_weather() → str` — returns a weather string matching Presence's key words:
   - `rain` / `drizzle` / `shower` / `storm` for rain conditions
   - `snow` / `sleet` / `blizzard` for snow
   - `fog` / `mist` / `haze` / `cloud` / `overcast` for fog
   - `clear` / `sunny` for clear
3. Builder 1 publishes the result to `weather` in blender_state.json.
4. Builder 3 owns the fetch + format. Builder 1 owns the publish.

## Source
`docs/architecture/_intake/SOURCE_DESIGNER-FULL-PRESENCE-RELAY_2026-10-08.md` §1
Designer commit: 0954664

## Done when
App opens → `weather_request` fires → brain fetches real weather → `weather` key in blender_state.json contains the correct condition string → Presence reacts visually. Committed. Move to BUILT/.

## Result
- commit: ec2b39c
- notes: B3 half built. `from tools.tool_router import get_current_weather` → one Presence key word
  (storm/blizzard/sleet/snow/drizzle/shower/rain/fog/mist/haze/overcast/cloud/sunny/clear), for David's known
  location (Hackney Wick). Cached 10 min, so a 10–15 min refresh only hits the network when stale. Returns "" when
  there's no location or the fetch fails. Publish nothing then; never a stale or guessed value.
  It also sets `get_last_weather_condition()`, which server.py (WO-058, ~L7460) already writes to blender_state `weather`.
  Real fetch 2026-10-08: Hackney Wick → `sunny` (wttr.in at the same time: "Sunny +12°C"). Offline tests: tests/test_b3_weather_on_open.py (20).
- Builder 1 still to do (Ask 1): the consumer for `weather_request`/`app_open` that calls `get_current_weather()` off the turn thread
  (network, up to ~8 s per provider), writes the word to `weather`, and repeats every 10–15 min. Not done until then plus David's visual check.

## Live turn needed
> David opens the app on a rain / clear day and Presence shows matching weather.
> Board closes card on David's visual confirmation.
