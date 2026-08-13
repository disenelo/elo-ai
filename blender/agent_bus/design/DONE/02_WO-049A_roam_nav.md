# 02_WO-049A_roam_nav.md

**WO:** 049-A (Track A of WO-049) · **Seat:** design · **Priority:** P1 · **Reserved?** no

## Goal
eLo crosses the desktop like terrain — he reasons about the space instead of playing clips.

## Scope — exactly this (extend roam, ONE nav hook, no second movement brain)
- Tag surfaces with meaning: window top = ledge · side = wall · gap = jump · behind = go-there.
- Pick a simple goal ("reach that ledge"), path to it; `RoamUpdate()` reads ONE new output: next move.
- **Peek before EVERY jump** — `PeekPitch` fires before any ledge-to-ledge leap. No blind jumps.
- **Whole window is walkable** via the WO-024 occlusion — he can go behind and re-emerge correctly stacked.
- **Body-local axes** — he faces the camera (~180°); rotation axes in his BODY frame or they fire wrong.
- Reachability: if a gap is wider than his jump, he does NOT attempt it — he finds another route.

## Files likely touched
`EloDesktopNav` + DesktopBuddy roam. Reuse `PeekPitch`, the ledge-hop, WO-024 occlusion (`7bab6af`).

## Test (without David)
Trigger a cross-window traversal: confirm peek fires before each jump, no blind leap, no floating,
re-emerges stacked correctly. No regressions (perch · roam · drag · click-through · gun-runoff).

## Done when
implemented + verified + committed → append hash, move to DONE/, outbox line, next card.
Spec: `WO-049_Desktop_World_SelfAware_Parkour.md` §"2026-08-10 — Build rules made explicit"
Verbatim source: `docs/architecture/_intake/SOURCE_2026-08-10_roam_os_vision.md`

## Result
- commit:
- test:

## Result
- commit: 0b44a8c (+ prior 4a5109f)
- test: build clean; live-tuned with David (fall/land/wrap/teleport-fix, whole-window walkable)
