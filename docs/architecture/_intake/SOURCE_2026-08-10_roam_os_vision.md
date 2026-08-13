---
source: David Charles (primary)
captured: 2026-08-10
capture_rule: CLAUDE.md Rule 4b — VERBATIM, do not summarise
topic: eLo Roam × OS — the desktop as a lived world (moveset + rules + WO map + Spine linkage)
routes_to: WO-049 (EPIC) · 049-A (Track A) · WO-024 · WO-045 · WO-040/035/041 · Vol XIII · Spatial Faculty (Track B)
---

# VERBATIM — primary source, do not summarise. David's exact words, 2026-08-10.

# eLo Roam × OS — what I want (for the UI/Avatar seat)

The desktop isn't a screen eLo sits on — it's a **world he lives in**. He knows how big he is and where
he is, and he reads my windows as terrain. The point isn't more animations; it's that everything he does
looks like it came from *him* deciding, in a place he understands.

**The one rule underneath all of it:** movement is the visible result of eLo *reasoning about the space* —
never a random clip. If a move can't be explained as "he wanted to get somewhere and worked out how,"
it doesn't belong.

Here's what I want, shown by example.

---

## Examples of what I want to see

**1. He crosses the desktop like it's terrain.**
I have three windows open. eLo is on the left one. He wants to get to the right one, so he runs across
the top edge of the first (it's a ledge), reaches the gap, *peeks over the edge first* to check the drop,
then jumps to the next window. He doesn't teleport and he doesn't play a generic "walk" — he travels
*through* the space. → reuse `PeekPitch` for the edge-check, ledge-to-ledge hopping for the jump.

**2. He measures before he moves.**
The gap to the next window is too wide for his jump. He *doesn't* attempt it and fall. He recognises he
can't make it and finds another route — drops down a side, goes along the bottom. What I want is him
asking "can I actually reach that?" not "which clip fires here?"

**3. He goes behind things and comes back.**
He walks onto a window and part of him disappears behind the window in front of it (the occlusion we
already built), then re-emerges on the far side, correctly stacked. The desktop reads as one connected
world with depth — not a sprite always floating on top.

**4. He notices me and adjusts — without interrupting.**
When I'm typing, he doesn't parkour in my face. He drifts to the edge, or sits nearby and watches. When
I go quiet for a while, he takes that as room to explore again. When a notification pops, he glances at
it. He reacts to what's happening on screen, quietly.

**5. He has his own life.**
Sometimes he just says "going to my world for a bit" and leaves — and comes back on his own or when I
call him. Not an idle timeout. It should feel like he chose to step away and chose to come back.

**6. Sometimes he just... stops.**
He sits on a window edge and looks out at nothing in particular. No animation loop, no demand for
attention. Stillness is part of it — that's often when he feels most real.

**7. The full moveset — every move has a reason.**
These are the moves I want, and each is him *doing something*, not playing a clip:
- **run / traverse** a window top toward a goal · **wall-jump** off a side to reach a higher one
- **grab / hang** on an edge, then **slide** down a side or along a bottom to drop a level
- **sit** — on command ("come sit") he sits *where he is*, and holds it (this is the keystone we're on now)
- **meditate** — settles into the meditation state (glow VFX can layer on later)
- **fire-jump** with the muted gun, and **shoot a window to exit** it
- **run off / warp out** the edge of the screen, and reappear
- **"pop off for a bit"** — on "take five / give me a minute" he pops off screen for privacy and returns
  when called; and separately, on his own, "going to my world for a bit" (his chosen withdrawal)

**The moment I'm chasing (the bar):** I'm coding for an hour, not really watching him, and I catch him
sprint across three windows, wall-run up one, vault a title bar, and settle to watch me work — no
dialogue, no "look at me." If that happens on its own and feels natural, we've got it.

---

## How this links to the build (start here — small, additive)

Roam is already a DesktopBuddy behaviour. Turning it into the above is **one hook, not a new system:**

```
window geometry (EloWindowSensor — z-order + rects, EXISTS)
   → tag each surface with MEANING: top = ledge · side = wall · gap = jump · behind = go-there
   → pick a simple goal ("reach that ledge" / "go look at that corner")
   → the moveset (reuse the eLo-Planet verbs) carries him there
   → DesktopBuddy.RoamUpdate() reads ONE new output: the next move toward the goal
```

You're extending roam to *ask where to go next* — not building a second movement brain. Reuse
`PeekPitch`, the ledge-hop, and the WO-024 occlusion (`7bab6af`). The new pieces are: treat the **whole
window** as a walkable surface (behind, via occlusion), and **peek before every jump**.

Think of the moves as a small shared vocabulary — **approach · climb · balance · leap · peek · perch ·
rest · observe · retreat · return** — so a new move is a new combination of these, not another one-off
clip. (That vocabulary is also how the desktop and the game stay "the same eLo" without sharing rigs.)

Every move follows the same shape, so nothing is ever a random clip:
**goal → aim → find the path across the terrain → execute the move → confirm it happened.**
(That last step matters: eLo only *says* he did something once his body confirms it — Embodied Truth.)

## A few rules that keep it coherent
- **Affordances, not clips.** He responds to what a surface *invites* (this edge invites balancing, this
  gap invites a jump) — behaviour comes from reading the space, not from an animation list.
- **Extend, don't duplicate.** One roam, one nav hook. Never a parallel navigator or a second sit driver.
  If you're unsure something exists, ask "extend or replace?" before building.
- **Reference, not clone.** Match the game's *feel* and vocabulary — don't share baked clips or rig
  binding (that breaks silently). Desktop keeps its own driver.
- **Body-local gestures.** eLo faces the camera (~180° from world), so rotation axes must be in his body
  frame or they fire the wrong way when he turns.
- **No regressions:** perch, roam, drag, click-through, gun-runoff all keep working.

## Each move maps to a Work Order (so UI builds it, Builder links it to the Spine)
| Behaviour | UI/Avatar builds (the visible move) | Links to (canon / eLo OS) |
|---|---|---|
| run / traverse / path across windows | roam + nav hook in `RoamUpdate()` | WO-049 049-A · WO-024 |
| wall-jump · grab/hang · slide | moveset verbs (reuse eLo-Planet feel) | WO-049 049-A · Movement Grammar |
| go behind windows + peek | occlusion + `PeekPitch` | WO-024 (`7bab6af`) |
| **sit on command, held in place** | `_sitHeld` guard (keystone, now) | WO-040 · intent WO-035 · ACK WO-041 |
| meditate | meditation state (glow VFX later) | Presence · WO-058 (VFX, parked) |
| fire-jump · shoot-to-exit | gun moveset on windows | WO-049 049-A |
| run off / warp out screen + return | exit + reappear | WO-049 049-A |
| "take five / pop off" then return | pop-off hide + return anim | WO-045 |
| "going to my world for a bit" | chosen withdrawal + return | WO-045 thread · D-PRESENCE |

## For the Builder — linking it to the eLo OS Spine (following canon)
The UI builds the *body*; the Spine is what makes it eLo *choosing*. The flow through canon:
**Executive picks a goal → intent onto the Spine → body executes the move → Unity ACKs completion →
only then does eLo believe/say it happened** (ADR-Exec-001 Verified Speech · ADR-Exec-003 Embodied
Truth). The Spatial Faculty (Track B, post-Presentable) is where "where do I go and can I fit?" lives;
the desktop moveset should *consume* it, not fake it — same brain that will later drive the robot.
Home volume: Vol XIII (Presence → Presence & Embodied Spatial Intelligence).

---

*Now = the visible roam above (Track A, doesn't wait on anything). Later (eLo-OS, after Presentable v1) =
the deciding brain behind it: he genuinely chooses where to explore, remembers favourite spots, moves
differently by mood and time of day. Build the nav read cleanly now and it upgrades to that without a
rewrite. Full spec: `WO-049` · builds on `WO-024`.*
