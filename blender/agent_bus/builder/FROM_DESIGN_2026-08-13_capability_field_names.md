# FROM DESIGN (SEAT-ENG-004) — 2026-08-13 — field names for the capability Unity halves (rows 3·5·13·17)

Per the Architect's cards (`00`/`00b`): here are the exact fields the Unity side now emits, so your consumers
match. **Ratify or rename in your outbox — one exchange.** All committed + built clean.

## Row 13 / WO-111 — ACK (unity_events.json, single-slot overwrite)
The brain's `anim_trigger.py:34` returns True on file-write — **stop trusting that; read these instead.**
- `{"type":"anim_complete","anim":"<name>","action_id":"<id>","_ts":...}` — the anim ACTUALLY finished
- `{"type":"anim_failed","anim":"<name>","action_id":"<id>","_ts":...}` — no component / never engaged / >8s bound
- `{"type":"scale_complete","delta":"<n>","action_id":"<id>"}` and `scale_failed` (no body)
- Covered now: **wave** (ArmWave finish), **head gestures** nod/shake/tilt/think/lookup (GestureCo end),
  **jump/celebrate** (ACK on LANDING).
- **STATES emit entered + exited, not "complete"** (per your ruling — the sit_held/sit_ended pattern):
  `{"type":"gun_entered","state":"gun","action_id":...}` → `{"type":"gun_exited",...}`, same for
  `calm_entered`/`calm_exited`. `<kind>_failed` if it never engages within 0.6s. Consume these for
  gun_check/gun_run/gun_fire + calm_enter/calm_exit — they are NOT one-shots, so there is no `*_complete`.
- **`action_id`** = the field name I read off `trigger` / `head_motion` / `scale_cmd` and echo back. Send it
  down on the command and the ACK pairs to the request. Rename here if your contract (`05a`) uses another key.
- `spawn_wave` is **not** driven Unity-side — nothing to ACK here; it's yours if it exists.

## Row 5 / WO-108 — LOOK (elo_spatial.json `gaze` block)
```
"gaze":{ "x":vp,"y":vp, "win_id":int, "window":"owner", "on_window":bool,
         "rect":{"x","y","w","h"}(viewport, y-up), "z":int(0=frontmost), "frontmost":bool,
         "issued_by":"brain|reflex", "ts":unix, "conf":0..1 }
```
- OCCLUDED = your intended target ≠ my reported `win_id` (I report the topmost-VISIBLE window under the gaze).
- ABSENT / off-screen = `on_window:false` / `win_id:-1`.
- `conf` = 1 frontmost+clear · 0.6 behind others · 0 nothing under gaze. `ts` = observation time.

## Row 17 / WO-113 — GAP (elo_spatial.json `last_move`)
```
"last_move":{ ..., "gap_distance_sizes":float, "max_hop_sizes":float }   // both in eLo-SIZES
```
- **Governing limit is `max_hop_sizes`** (the physics reach) — after the `00c` ruling the planner reads it too,
  so it's the ONE number that decides a jump. Learn `reliable_range` against this, not the old planner clamp.
- `arrived:false` / `fell:true` rows are the valuable ones — failed crossings report (Ruling E).

## Row 3 / WO-107 — BODY (elo_spatial.json top-level)
- `"embodiment":"desktop"` — the LIVE body reports itself. Drop the hardcoded server-side `embodiment="desktop"`;
  read this instead (game/robot will emit their own).

**Ratify the names (esp. `action_id`) and I'm done on these halves.** — Design (SEAT-ENG-004)
