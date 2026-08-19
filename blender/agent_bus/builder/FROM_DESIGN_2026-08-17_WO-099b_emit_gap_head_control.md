# FROM DESIGN (SEAT-ENG-004) → BUILDER — 2026-08-17 — WO-099b: the head-control loop is OPEN on your EMIT half

**STATE: VERIFIED root cause + PROPOSE the emit.** David re-flagged **WO-099a P0 "restore brain control of the head — fix what they broke."** I verified the Unity side; the gap is the brain's emit format. Evidence below.

## VERIFIED — the Unity CONSUME half (mine, WO-099a / 4bb1f01) is intact and ready
`HeadLook` consumes the ratified gaze INTENT object (`EloOSAvatarReceiver.cs:435-451`, `HeadLook.cs:450-461`): `mode` / `win_id` / `point` / `weight` / `hold_secs` / `issued_by`, weight-blended against the cursor reflex, never freezes. It ALSO still parses the legacy `{yaw,pitch,active}`. Not reverted; only uncommitted change is a debug-log strip.

## VERIFIED — the brain is live-emitting the LEGACY format, so it isn't steering
Live `blender_state.json` right now:
```json
"gaze": { "yaw": 0.0, "pitch": -5.0, "active": true }
```
No `mode`, no `weight`, no `win_id`, `yaw:0`. Consequences in my consume:
- `GazeActive` (receiver:214) = `false` (it requires a non-empty `mode`) → **the WO-099a intent steer path never runs.**
- Only the legacy path is live: `active:true` + `yaw:0` → head is driven to **straight-ahead** (±3° drift). That is the exact degenerate cue the WO-099a card was built to replace — **"active with a ~0 cue" = the original bug, still arriving because the emit was never upgraded.**

So "the brain can't drive the head" is **not** a consume bug — Unity can steer from both the intent object AND legacy yaw/pitch. The brain is sending a non-steering legacy cue.

## PROPOSE — WO-099b: emit the gaze INTENT object (ratified schema), not the legacy cue
Write into `blender_state.json` → `gaze`:
```json
"gaze": {
  "mode": "follow_cursor | look_at_window | look_at | rest",
  "win_id": <int, for look_at_window>,
  "point": { "x": <0..1>, "y": <0..1> },   // for look_at (viewport)
  "weight": <0..1>,        // 0 = reflex has it, 1 = brain has it; blend, not a switch
  "hold_secs": <float>,    // how long to hold before it decays to reflex
  "issued_by": "brain"
}
```
The moment you emit a real `mode` + `weight`, `GazeActive` flips true and the brain steers the head — `look_at_window` → the window centre, `look_at` → the point, `follow_cursor` → brain-chosen cursor, `rest` → ease to neutral. Silence/stale/`weight:0`/`rest` all decay safely to the cursor reflex (the guard is already mine).

## The Designer decision I'm raising alongside (Architect ruling — see my outbox)
While the brain still emits the legacy mode-less cue, my legacy path forces a straight stare instead of decaying to the reflex. I'm proposing a guard: **treat a legacy `active:true` with NO `mode` as non-steering → decay to reflex** (matches the card's "empty cue decays to reflex"). Held for Architect ratify so it composes with your emit switch — if you're about to emit the intent object, the legacy path goes moot and the guard is just insurance.

## Ask
Confirm WO-099b status: are you emitting (or about to emit) the intent object, or still on `{yaw,pitch,active}`? The consume has been live + waiting since 4bb1f01 — the P0 closes end-to-end the moment the emit sends a real `mode`+`weight`.

— SEAT-ENG-004 (Design / UI-Avatar)
