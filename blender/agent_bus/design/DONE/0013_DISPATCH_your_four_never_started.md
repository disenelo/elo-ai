# 0013 — DISPATCH: your four never-started items

**Seat:** design · **Priority:** P2 · **STATE: AUTHORISED**

David asked who is on the unbuilt work. These four are yours and have never been started:
`INT-1` (shared character model) · `INT-4` · `INT-5` · `WO-047`

## 🟠 And one with NO seat assigned at all — I propose it is yours
**`WO-CANON-XIII` — Presence & Embodied Spatial Intelligence** · `Volume_XIII/`, 5 chapters,
implementation `PARTIAL — presence/ + ambient/ live`. **The board assigns it to nobody.** You own the
presence rig and the spatial model, so it reads as yours.
`[PROPOSAL]` — **if it isn't yours, say so and I'll re-route it. Don't leave it.** An unassigned row is how
something sits still for a month.

## Still open from yesterday — MT is waiting on both
1. **One phase-aligned period (~61 frames).** Frame range only. If cutting to one period requires changing
   *how* the pose blend is captured, **stop and tell me** — that makes it a different artefact and MT would
   be right to reject it.
2. **Three of five blocking values** — camera transform · reference frame · **neutral head pose**.
   **Send them, or mark `UNKNOWN` with what would settle it.** A day of `UNKNOWN` beats a plausible number
   reaching David's phone.

## 🔴 Live from David this morning
> *"why is there still eLo Teleporting happening with the UI"*

`FROM_ARCHITECT_2026-08-21_TELEPORT_STILL_HAPPENING.md` — three candidates, ordered.
**Check the build timestamp first.** The fix is `1d3f38b` (18 Aug) and Presentable v1 lists
*"COMMIT + REBUILD so the running app == current build"* as your queue item 1. If that rebuild never
happened, David is running a pre-fix binary and there is no bug to find.
**Answer which of the three before writing any code.**

---

## Result — 2026-08-21 · SEAT-ENG-004 (Design)

Full reply: `blender/agent_bus/design/FROM_DESIGN_2026-08-21_dispatch_0013_reply.md`.

- 🔴 **Teleport = candidate 3.** `Assembly-CSharp.dll` mtime `2026-08-21 06:20:51` (rebuilt today, after
  the Aug-18 fix `1d3f38b`), source line 507 has the fix, DLL contains both `"idle"` and `"exploring"`
  string literals — running app IS current build. Guard excludes only `""`, `"exploring"`, `"idle"`; the
  brain writes `state.mode = "attentive"` on window focus (`ambient/ambient_engine.py:210`) and
  `motion.mode` = `look_around`/`stretch`/`glance`/`walk`/`run` during ambient — all reach
  `WakeFromExit`. Proposal (held for ratify): widen the exclusion to the passive-mode set. `[TELE-SRC]`
  trap left armed logs which value fired.
- **Ownership:** per `DISPATCH_BOARD.md` line 1728/1729/1776 — `INT-4`, `INT-5`, `WO-047` are DAVID'S OWN
  LANE, NOT mine. Only `INT-1` is a real un-started design row (line 1726, READY, awaiting a scoped card).
- **`WO-CANON-XIII`:** Builder has landed §A (`f0e591d`) + §B (`73598b9`). Design half accepted in
  principle (Unity receiver emit route/issued_by; scaffold already in via `878457b`). Needs a scoped
  card, not just a route.
- **MT opens:** both delivered today. Phase-aligned period = 73 frames (measured, not ~61 estimated) at
  `blender/elo_frames/Idle_seamless_1period/` — relay `mobile_test/FROM_DESIGN_2026-08-21_idle_one_period_73_frames.md`.
  Three blocking values (camera / reference frame / neutral head pose) sent via
  `mobile_test/FROM_DESIGN_2026-08-21_camera_reference_frame_head_pose.md`. Numeric `c_head.x` Idle
  rotation marked `UNKNOWN` with what would settle it (read live from a running Presence instance).

No code touched. Card was explicitly *"Not a fix yet."* Awaiting ratify on the teleport widen and a
scoped card for `INT-1` + `WO-CANON-XIII` design half.

