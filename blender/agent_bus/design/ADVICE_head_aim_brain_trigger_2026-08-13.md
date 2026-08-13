# ▶ ARCHITECT — ADVICE: make the head-aim BRAIN-TRIGGERED (gaze brain>body>brain)

From **design (SEAT-ENG-004)** · 2026-08-13 · David: *"the brain will need to trigger this soon — advise how to make it read that way."*

## Where it is now (built + working)
- **Head-aim MECHANISM is done + tuned** (`HeadLook.cs`, commit `5180b0f`): decoupled yaw/pitch (LookRotation of a target direction — fixes the up/down-scramble-at-large-yaw), body-local axes derived empirically from a `[BASIS]` dump, looks at nearby cursors (`aimResponse 0.10`), chest **trails** the head (`chestSmooth < lookSmooth`, ≤20°, off while walking/seated), sit-aware (full track seated, chest off), plus a self-verifying log (face `fwd.x` vs cursor `curDx`).
- Today it's a **BODY REFLEX**: `forceCursorTrack=true` → the head always aims at the mouse cursor.
- **The brain's EXISTING cue conflicts.** `HeadCueActive/HeadYawCue/HeadPitchCue` (from `blender_state.json` `gaze`) is a blunt on/off. It was getting **stuck ON with ~0 yaw**, and because the old code gave it priority (`forceCursorTrack && !eloDrivingHead`), the head followed the brain's *nothing* instead of the cursor → **he stopped following while seated and after standing up.** Stopgap shipped: cursor-follow is now **primary** (ignores the stale cue). Consequence: **the brain currently canNOT drive the head** while the reflex is on.

## The ask
The **brain** should TRIGGER/choose the look (when + where eLo looks), not the body doing it blindly — and the body should report what he's looking at UP so the brain decides with awareness. Right now the brain cue is a blunt switch that *fights* the reflex instead of *steering* it.

## Recommended shape — gaze as brain>body>brain (same as WO-086 / WO-094)

**DOWN (brain → body): a gaze INTENT, replacing the blunt on/off** — extend the existing `gaze` object in `blender_state.json`:
```json
"gaze": { "mode": "follow_cursor" | "look_at_window" | "look_at" | "rest" | "free",
          "win_id": <int?>, "point": {"x":,"y":}?, "weight": 0.0-1.0, "hold_secs": <float?> }
```
- `follow_cursor` → track the mouse (today's reflex, now brain-CHOSEN not assumed).
- `look_at_window(win_id)` → aim at that window's rect (reuse `EloWindowSensor`; ties WO-094).
- `look_at(point)` → aim at a screen point (a notification; the night-light later, WO-091).
- `rest`/`free` → settle / autonomous glances.
- `weight` → blend in/out (brain can half-look); `hold_secs` → the "sometimes" duty the BRAIN owns.

**BODY (`HeadLook`): consume the intent — SAME aim mechanism, brain-chosen target.** Swap the target from "always cursor" to "the brain's gaze target." When the brain is **silent**, fall back to the local reflex (cursor-follow, or the eventual "sometimes" glance) so it degrades gracefully and never freezes. This **dissolves the conflict**: the brain stops fighting the follow and instead SELECTS it (`follow_cursor`) or overrides it (`look_at_window`).

**UP (body → brain): gaze awareness** (the emit I already relayed to the board): publish what he's actually looking at — cursor viewport pos + whether a window is under that gaze (id/owner/rect via `IsTopmostAt`) — on the existing `unity_events.json`/`elo_spatial.json` channel. So the brain DECIDES with awareness ("he's already looking at that window") and the loop closes.

## Migration (don't break what works)
1. **Now:** keep the `forceCursorTrack` reflex (works; David's happy).
2. **Designer:** add the gaze-awareness emit UP (relayed) + teach `HeadLook` to read a gaze INTENT target (mode/win/point/weight), defaulting to the cursor reflex when the field is absent.
3. **Builder:** extend eLo OS to DECIDE the gaze from context (David working → peripheral; window opened → glance; idle → follow cursor — per WO-086/094), emit the intent DOWN, consume the awareness UP.
4. **Retire** the blunt `HeadCueActive` on/off in favour of the gaze mode, so it can never block the reflex again.

## Why this "reads that way"
Head-aim = the body's **HOW** (built). Brain owns the **WHAT + WHEN** (target + the "sometimes"). Body reports back so the brain is **aware**. Identical three-part shape to WO-086 (idle) and WO-094 (windows) — one consistent brain>body>brain for **attention/gaze**.

**Requesting:** a WO for this (Designer: intent-consume + awareness-emit; Builder: decide + drive), the channel decision (extend `gaze` in `blender_state.json` DOWN, `unity_events`/`elo_spatial` UP), and sequencing (both halves land together, WO-086 rule).

— design (SEAT-ENG-004)
