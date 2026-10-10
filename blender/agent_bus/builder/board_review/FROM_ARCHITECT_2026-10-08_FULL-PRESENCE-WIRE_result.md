# FROM ARCHITECT — 2026-10-08 — Full Presence→Brain wiring (supersedes 2026-10-07 swim relay for HP section)

Source: `docs/architecture/_intake/SOURCE_DESIGNER-FULL-PRESENCE-RELAY_2026-10-08.md`  
Designer commit: 0954664 (DISENELO-eLoDesktopBuddy)

**Verified [VERIFIED]:** `auto_action`, `brain_action`, `water_play`, `weather_request` are NOT consumed in server.py, spine.py, or ambient_engine.py — zero grep hits. Swimming cost keys absent from `_LEGS_TO_COST`. Events are arriving in `unity_events.json` (Designer confirmed); the brain has no consumer.

---

## Ask 1 — New event consumers (own bookmark, like movement charger)

In server.py or spine.py, add a new consumer (own bookmark, NOT the shared cursor) for these `unity_events.json` types:

| type | what to do |
|---|---|
| `auto_action` | Log to WKG: "eLo chose [subject] for himself (reflex, timer-driven)" — so causal chain records his self-chosen behaviour |
| `brain_action` | Log outcome: brain intent [subject] → ok/fail, why. Feed to WKG. |
| `water_play` | Log to WKG: "eLo had fun — [subject]". Flag as positive experience. |
| `weather_request` (subject=`app_open`) | Trigger Builder 3's weather fetch. Publish result to `weather` key in blender_state.json. Schedule refresh every 10–15 min. |

---

## Ask 2 — HP costs: add remaining movement_cost keys

In `ambient/ambient_engine.py` `_LEGS_TO_COST`, add (alongside the swim WO keys from 2026-10-07):

| key | cost | source |
|---|---|---|
| `swimming` | 0.025 per 5s | [SPEC] SOURCE_DESIGNER-WATER-SWIM-BUILD_2026-10-07 §Health |
| `swimming_fast` | 0.04 per 5s | [SPEC] same |
| `pool_hop_out` | 0.02 | [SPEC] same |
| `pool_wall_jump` | 0.02 | [SPEC] same |
| `pool_dive` | 0.02 | [SPEC] same |
| `pool_jump_in` | 0.02 | [SPEC] SOURCE_DESIGNER-FULL-PRESENCE-RELAY_2026-10-08 §3 |
| `rock_stomp` | 0.02 | [SPEC] same — same rate as parkour |
| `hazard_lava` / `hazard_acid` / `hazard_poison` | 0.05 (one-time, instant exit) | [ESTIMATE — pending David L3 confirm. Touching hazard = instant cost, similar to a heavy fall.] |

Also in `_consume_movement_costs` or equivalent: handle `rest_tick` type with subject `floating` as a **refill** (not a drain). Amount: [ESTIMATE 0.01 per 5s — floating in the doughnut ring is gentle rest. Pending David L3 confirm.]

---

## Ask 3 — Movement vocabulary: expose §2 intents to the Executive

The brain's movement vocabulary (wherever `movement_intent` is set for blender_state.json) currently has sitting, rest, explore, climb, etc. Add the full set from Designer §2:

`swim`, `play_water`, `fill_pool`, `deep_water`, `lava`, `acid`, `poison`, `muddy`, `doughnut`, `float`, `ring`, `dive`, `dive_under`, `leap`, `jump_in`, `leave_water`, `get_out`, `drain`, `drain_pool`, `stomp`, `break_rock`, `chimney`, `wall_jumps`, `weather_rain`, `weather_snow`, `weather_fog`, `weather_clear`

The Executive must be able to pick these from drives and context, not just the timers.

---

## File ownership
- `ambient/ambient_engine.py` — [VERIFIED] belongs to Builder 1 (runtime/ambient). Confirm if different.
- `runtime/server.py` · `runtime/spine.py` — Builder 1.

## Done when
1. Swimming cost keys charged in ambient_engine.py.
2. New event types consumed with own bookmark.
3. Weather fetch triggered on `weather_request app_open` → result published to `weather`.
4. Executive movement vocab extended.
Committed. Board reruns test suite.
