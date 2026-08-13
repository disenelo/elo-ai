# WO-065 — Designer remaining: runtime integrity (heartbeat · restart-on-launch · sit_ended)

**Owner:** Designer (UI/Avatar — Unity C#). **Priority:** P1. **Status:** OPEN — spec'd 2026-08-07.
Consolidates the Designer-side items that had board notes but no full spec, so the seat can build them
end-to-end without checking back.

## 1. `sit_held` heartbeat (make the HOLD verifiable, not claimed)
`sit_complete` only proves the sit ENGAGED — there's no "still held" signal, so the hold can't be confirmed
from artifacts. **Do:** while `_sitHeld`, write `sit_held: true` to `blender_state.json` (or the state
block); on the linger stand, write `false`. Log at +5s/+10s: "`_sitHeld` true, idle rotation suppressed";
on a stomp, log which system broke it.
- **Test (no David):** inject a commanded sit → `sit_held` goes true and stays true across the settle
  window; after linger lapse → false. The Architect can then confirm the hold from the file.

## 2. `EloOSProcess` restart-on-launch (kill the relaunch gotcha)
The app only spawns a fresh `server.py` "if not running" (probes :5050) → it connects to a STALE backend
and new eLo-OS code doesn't load. **Do:** on launch, if a `server.py`/:5050 is detected, kill it and spawn
fresh (or expose a "force restart" toggle). Removes the manual `kill :5050` step so a relaunch ALWAYS loads
current backend code.
- **Test (no David):** launch with a stale backend present → the app kills it and the fresh one is the one
  connected (log/PID check). Launch clean → normal spawn.

## 3. Emit `sit_ended` UP (pairs with WO-064 BP-5)
When `SitLingerCo` stands eLo on its own, emit `sit_ended` to `unity_events.json` (mirror of `sit_complete`)
so the brain can flip its self-model pose to standing. Builder consumes it (WO-064 BP-5).
- **Test (no David):** trigger the linger stand → `sit_ended` written with a fresh `_ts`.

## Definition of Done
All three shipped, committed, and the running app rebuilt from them so they're live. David L3 = the sit
holds through a conversation and eLo rises on his own after you leave; a relaunch always loads current code.
