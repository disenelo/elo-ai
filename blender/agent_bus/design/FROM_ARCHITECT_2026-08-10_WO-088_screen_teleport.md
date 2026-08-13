# ▶ DESIGNER — WO-088: eLo randomly walks toward the screen + teleports (David live 2026-08-10)

## Symptom
eLo, unprompted, walks TOWARD the screen (edge/camera) and then TELEPORTS/warps to another position. Random,
not commanded by David.

## Architect debug check (evidence — done read-only)
- `blender/blender_state.json` at rest: `intent: idle`, motion neutral — **no warp/move/target command from
  the brain.**
- `blender/unity_events.json`: empty (`{}`) — no UP event around it.
- Grep of the eLo-OS Python (`runtime/`, `server.py`, `blender_bridge/`): **no `warp`/`teleport` logic** — the
  brain has no such concept.
→ **Conclusion: the walk-toward-screen + teleport is an AUTONOMOUS Unity-side driver firing while the brain is
idle.** The body is choosing a movement the brain never asked for — a brain>body>brain violation, same class
as the mouse-idle calm driver (WO-086). The mechanism lives in the DesktopBuddy tree (not in this repo), so
it's yours to trace.

## Debug ask (Designer)
1. Find what triggers the walk-toward-screen + warp — likely the autonomous roam / edge-seek / occlusion-warp
   / re-attach logic self-firing. **Add a log at the warp trigger:** what fired it, eLo's brain intent at that
   moment (should read idle), source surface → target, and why it chose to warp.
2. Confirm from that log that it's LOCAL (brain intent = idle when it fires) — i.e. a parallel driver, not a
   brain command.
3. Then: gate it through the brain (WO-086 brain>body>brain pattern) OR fix the trigger so eLo doesn't wander
   to the screen edge + warp unbidden. Walking "toward the screen" specifically suggests a bad target
   (camera/screen-space instead of a window surface) — check the target resolution.

## ROOT CAUSE CONFIRMED — David 2026-08-10: "Only happens with Claude in VS Code and Claude Desktop — never with any other agent or seat"
**This is NOT an eLo body-driver bug.** The only thing the Claude-in-VS-Code + Claude-Desktop clients have that
the Builder/Designer/Game seats do NOT is the **Unity MCP bridge (MCP-for-Unity) attached to the LIVE editor.**
When that bridge is connected, its editor traffic — object reflection/selection, asset refresh, and especially
any script edit → **recompile → domain reload** — perturbs or resets eLo's non-serialized transform mid-run:
walk-toward-screen = re-attach/re-home after the reload; teleport = transform snapping to spawn. The seats
never drive the live editor through this bridge, so they never trigger it. Diagnosis over — no phantom driver
to hunt.

## Actions
- **Architect (mine, done):** stay OFF the live Unity editor — no MCP editor calls while eLo is in Play mode.
  (I ran one `find_gameobjects` query before this was understood; that class of call is the trigger. Stopped.)
- **Operational (all Claude clients):** don't attach the Unity MCP bridge to the live editor during eLo runtime.
- **Optional hardening (Designer/Builder, gated, only if worth it):** make eLo's transform survive a domain
  reload (serialize/restore position), OR disable the MCP bridge's auto-refresh, so an editor reload can't
  reset eLo. Low priority now that the operational fix removes the trigger.

## (Superseded) earlier repro notes — kept for record
David 2026-08-10: "Only happens with Claude"
The teleport correlates with a **Claude / MCP client touching the LIVE Unity editor** — not with eLo's own
runtime. Candidate mechanisms, in order of likelihood:
1. **Domain reload / recompile** triggered by an MCP editor op (script edit, asset refresh) while eLo is in
   Play mode → non-serialized transforms reset → eLo snaps to spawn = the "teleport." The walk-toward-screen
   is the re-attach/re-home after reload.
2. **GameObject selection** via MCP (e.g. `find_gameobjects("eLo")`) → focus/gaze/selection-follow driver
   pulls eLo toward the camera/screen, then it releases = walk-toward-screen + snap-back.
3. Any MCP `refresh_unity` / asset import forcing a reload mid-session.
NOTE (Architect owns this): I ran an MCP `find_gameobjects("eLo")` query against the live editor right before
David surfaced this — that class of action is very likely the trigger. **Architect will stay out of the live
Unity editor while eLo is running.** This is not necessarily an eLo behaviour bug at all.

## Designer check
Confirm whether teleport events coincide with a **domain reload / recompile / MCP editor op** (check the
editor log timestamp against the teleport). If so, this is an editor-interaction artifact, not a body driver —
and the fix is operational (don't poke the live editor) + optionally persist eLo's transform across domain
reload so a reload doesn't reset it. Only if teleports fire with NO editor interaction does the autonomous
driver hypothesis (above) apply.

## Ties
This is a concrete case for the **WO-087 full local-driver audit** — add it to the "route-through-brain" list.
Also relates to WO-074-F (bad jump/target resolution) + WO-075 (surface/gravity). Read-first (log), then the
fix is a behaviour change → gate under David greenlight per WO-086 if it touches the sensitive avatar file.
