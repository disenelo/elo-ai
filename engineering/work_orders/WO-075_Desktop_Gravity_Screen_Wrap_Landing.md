# WO-075 — Desktop gravity + screen-wrap landing (eLo always lands on a platform)

**Owner:** Designer (UI/Avatar — Unity nav/physics). **Priority:** P2 — desktop-world "feels alive" behaviour;
behind Presentable, but David wants it. **Status:** OPEN — spec'd 2026-08-07 (David live intent).
**Canon:** desktop-as-a-world eLo inhabits (WO-049 / 049-A · Situated Cognition) · never lost off-screen
(Embodied Truth — his position is always real + on a surface). Ties the existing `drop` move + `EloWindowSensor`
+ `EloDesktopNav`.

## Current (wrong) behaviour — David live 2026-08-07
Drag-to-place (WO-024) currently leaves eLo **floating exactly where he's dropped** on empty desktop — he
does NOT fall/land on anything. He just hangs there, and only after an idle time-period does he wander off.
That breaks grounding (Embodied Truth: he should always be ON a real surface, never floating in space). The
fix is gravity on release: he falls immediately, he doesn't hover-then-wander.

## The behaviour (David's words, 2026-08-07)
"If I drop eLo off a window he should fall — **straight down, in line with where he was dropped.** He lands
on the first window directly below that drop point. If there's no window in that vertical line, he falls
through the bottom of the screen and reappears at the TOP **in the same column**, keeps falling, and lands
on the first window down that line." Gravity is VERTICAL along the drop x — NOT a sideways drift to some
nearest window off to the side. eLo always ends up on a platform, in line with where he fell.

## Scope
1. **Vertical gravity along the drop x — TWO triggers:** (a) **DRAG/RELEASE (the original intent, David
   "said in passing", was never written down):** when David picks up / drags eLo and RELEASES him
   (drag-to-place already exists — WO-024) over empty desktop, gravity applies — he falls straight down from
   the release point; (b) **step/fall off an edge.** Either way he falls STRAIGHT DOWN — no horizontal drift.
   The landing target is the first window whose horizontal span contains the drop/release x-coordinate,
   beneath him.
2. **Landing:** land on that first in-column window; play the existing land/settle so it reads as a real
   landing (not a snap), attach to its surface. (Do NOT veer to a closer window that isn't under the drop x.)
3. **Screen-wrap in the SAME column:** if no window sits below him in that vertical line, he falls through
   the bottom edge and re-enters from the TOP at the **same x**, continuing straight down until he reaches
   the first window in that column, and lands on it.
4. **Floor guarantee (edge case):** if there is NO window anywhere in that column, he lands on the desktop
   floor / taskbar at that x (the existing `desktop_floor` affordance) — NEVER an infinite fall, NEVER lost
   off-screen. (If a "nearest window in another column" behaviour is ever wanted, that's a separate, later
   decision — the default is strictly vertical.)
5. Reads off the SAME window sensor + nav everything else uses (Check-Before-Build — extend `EloDesktopNav` /
   `EloWindowSensor`, no parallel physics system).

## Definition of Done
Drop eLo with a window below → he falls + lands on it. Drop with a window off to the side (none directly
below) → he falls to the nearest one. Drop with no window beneath at all → he wraps through the bottom,
reappears at top, lands on a window. No windows at all → lands on the floor/taskbar. He is ALWAYS on a real
surface afterward (self-model pose/surface updated via the UP channel).

## Test / verify
Designer inject/log-verified where possible (drop from various positions → assert final surface = a window /
floor, never off-screen); David L3 = the visual feel (drop him around, he always finds a platform).

## Lane / relationship
Designer (Unity). Extends 049-A desktop nav + the `drop` move (FREEFORM_MOVESET_CONTRACT). Pairs with WO-063
(a command wakes/re-attaches a dormant body) — both keep eLo grounded on a real surface. Post-Presentable.
