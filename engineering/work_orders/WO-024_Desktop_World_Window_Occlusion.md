---
id: WO-024
title: "Desktop-as-world — eLo walks BEHIND windows (z-order occlusion); windows are platforms AND occluders"
owner_seat: SEAT-ENG-004 (UI/Avatar, Unity) + SEAT-ENG-001 (Builder, native window plugin)
occupant: UI/Avatar + Builder — cross-lane (R&D spike first)
priority: P2
reason: "David 2026-08-01: when eLo walks the desktop and a window is in front of where he is, he should pass BEHIND it and disappear behind it (and behind the next one if stacked). Connect the platforms so the desktop functions like one coherent world — windows are both surfaces he stands on AND occluders he can go behind."
review_required: L1 → L3 (David visual sign-off) — needs a SPIKE + approach decision first
risk: medium (touches the topmost-overlay window model; must not break click-through, perch, or drag)
status: READY — spike first
created: 2026-08-01
depends_on: WO-023 (screen-position) — sibling Presence work
---

# WO-024 — Desktop world: eLo occluded by windows (walk behind), windows as platforms + occluders

**David's words:** *"When walking around desktop, if a window is behind a window he moves behind the
window and disappears behind the window; if it's behind another one [too] — connecting the platforms to
function like a world."*

## The gap
Today eLo's overlay is a **single transparent topmost window** (`UniWindowController`, per-pixel hit
test) — so he renders **in front of everything** and can never be behind an app window. Meanwhile
`EloWindowSensor` (CGWindowList — list + **z-order** + rects, no permission) already knows every window's
position and stacking, and eLo already **perches/hops on window top/bottom bars** (windows-as-platforms).
The missing half is **depth**: give eLo a place in the z-order and let windows in front of him occlude him.

## Desired behaviour
1. eLo has a **world depth** (which windows are "in front of" vs "behind" him).
2. When he walks under/behind a window that sits **in front** of his depth, the covered part of him is
   **hidden** — he disappears behind it, cleanly (no half-ghosting), and reappears on the far side.
3. Stacked windows compose correctly — behind window A but in front of window B reads right.
4. **Platforms + occluders unify:** the top bar he stands on and the window body he passes behind are the
   same object — the desktop reads as one coherent world.
5. Must **not** break: click-through on transparent pixels, perch/roam/hop, drag-to-place, the gun run-off
   choreography, or "always see eLo when he's meant to be foreground" (e.g. active chat).

## Approach — SPIKE required (Builder + UI/Avatar), David picks after
Two viable routes on macOS; the spike compares feasibility/robustness, then David approves one:

- **(A) Sprite masking / clip** — keep the single topmost overlay; each frame, from `EloWindowSensor`'s
  z-ordered rects, compute the union of windows that should be *in front* of eLo's current depth and
  **clip those pixels** out of his sprite (stencil/mask in URP). Fully controllable per-pixel; no OS
  restacking. Likely the safer route.
- **(B) Window-level restacking** — dynamically insert eLo's native window into the OS z-order between
  specific app windows (`EloWindowManager` / window level + ordering via ObjC). True OS occlusion, but
  ordering an overlay relative to arbitrary app windows is fragile and can fight click-through/topmost.

Grounded components to build on: `EloWindowSensor` (z-order + rects), `WindowController` /
`EloWindowPlugin.bundle` (native list), `EloWindowManager` (window level/collection behaviour),
`UniWindowController` (overlay/hit-test), `DesktopBuddy` (perch/roam/jump), URP for masking.

## Acceptance
1. eLo walks behind a window and the covered portion is hidden; he re-emerges on the far side.
2. Correct with **stacked** windows (behind A, in front of B).
3. Standing on a window's top bar (platform) and passing behind its body (occluder) both work on the same
   window — the world is coherent.
4. No regression: click-through, perch/hop, drag, gun run-off, foreground-when-intended all intact.
5. Handback: spike memo (A vs B recommendation) → after David's pick, the implementation diff + a short
   screen recording of walk-behind + stacked-window occlusion.

## Notes
- **Spike memo comes back to David as a decision (which approach)** before the full build — reserved gate.
- Sequences after / alongside WO-023 (both are the Presence "eLo in the real desktop world" strand).
- Canon tie-in: this is the embodiment/Perception "desktop world" surface — fold the ratified approach
  into the DesktopBuddy spec + Perception (Vol XII) on completion.
