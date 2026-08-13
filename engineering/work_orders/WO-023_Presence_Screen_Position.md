---
id: WO-023
title: "eLo screen-position — top-of-screen bias; stop drifting over the app I'm using / blocking my buttons"
owner_seat: SEAT-ENG-001 (Builder) + SEAT-ENG-004 (UI/Avatar)
occupant: Builder (positioning logic) + UI/Avatar (Unity placement)
priority: P1
reason: "Live use (David 2026-08-01): eLo keeps drifting onto the window I'm working in and covers key buttons I need to click/type. He should sit more toward the TOP of the screen and stay out of the active app's controls."
review_required: L1 → L3
risk: low (placement/behaviour; no cognition change)
status: READY
created: 2026-08-01
---

# WO-023 — Presence screen-position: top bias + don't block the active app

**David's words:** *"eLo doesn't always need to drift to the window I'm working on — it's always better
if he is more on the top of the screen rather than where I'm using the app, he sometimes blocks the key
buttons I need to type."*

## Desired behaviour
1. **Default anchor = upper region of the screen** (e.g. top-centre or a top corner), not centre / not
   over the active window's body.
2. **Do NOT drift to cover the focused app's control surface.** When eLo would overlap the active
   window — especially its lower/toolbar/text-entry region where buttons live — he should **keep clear**
   (bias up and/or to the side), not settle on top of it.
3. Keep it **calm and non-distracting** — no jitter; move only when he'd otherwise be in the way.
4. Preserve intentional behaviours (e.g. explicit "come here" / drag), and the drop-target work (INT-8)
   if/when unparked — this WO changes the **idle/ambient drift**, not summoned placement.

## Where to look (Builder to confirm exact call sites — grounded starting points)
- Presence positioning state: `blender/presence.json` / `blender/presence_state.json` /
  `blender/elo_spatial.json` — what writes the target screen position each tick.
- The **follow/drift-to-active-window** logic (whatever picks the target near the focused app) — that's
  the thing to re-bias upward and add an "avoid active-window control region" exclusion to.
- Unity side: the avatar placement receiver that reads the target position — confirm it honours a
  top-anchored target and a keep-out rect.

## Acceptance
1. On a normal desktop session, eLo **rests toward the top** of the screen by default.
2. When the user is typing/clicking in an app, eLo **does not sit over that app's buttons/toolbar/text
   field** — he stays clear (verify by David actually working in an app).
3. No new jitter; movement only to get out of the way.
4. Handback: the before/after — what sets the target position, the top-bias + keep-out change, file:line.
   Emit a small position trace (target x/y, active-window rect, keep-out applied) so it's observable, per
   the WO-017 / WO-019 trace pattern.

## Notes
- Pairs with the "eLo blocks buttons" strand of the live Presence tests.
- ONE behaviour change, test, David confirms in real use → DONE.
