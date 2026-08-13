# WO-094 — eLo NOTICES window events and CHOOSES to act ("I saw that window close — let me jump across")

**Owner:** Designer (emit window events UP) + Builder (brain notices + decides). **Priority:** P2.
**Status:** OPEN — spec'd 2026-08-10 from David live. **Not gated** (Presentable done, gate open).
**Canon:** WO-049 §"notification → glance; big window opens → climb it; David working → stay peripheral;
idle → come closer" · 049-B1 Spatial Faculty (Track B) · Vol XIII Presence & Embodied Spatial Intelligence ·
brain > body > brain (WO-086 pattern) · Movement is visible spatial reasoning, never a random clip.

## David (live 2026-08-10)
> "Where are we with eLo know more of I see a window close, let me jump across, and then the gravity is
> enabled so if he can't jump far enough he finds patterns and finds ways to move around the guardrails or
> travel paths — this gives him more free form"

## What ALREADY EXISTS (Architect audit — do not rebuild)
- **Survival recovery on window close IS built** (`DesktopBuddy.cs`): `:1109` *"window closed → release"* ·
  `:1438` *"his window closed → re-settle"* · `:1775` *"window closed → re-evaluate"* · `:1809` *"attach to
  the nearest window at ANY distance — he runs/leaps to it, never floats."*
- **Route-finding IS built** — `EloDesktopNav` descent pathfinder (`_route` → walk/run/jump legs, wall-jump
  chimneys), and `:187` already forces gaps beyond reach to ROUTE instead of leap.
- **Gravity/landing** — WO-075, in progress.

## THE GAP — reflex, not intent
There is **no window EVENT perception**. The sensor does not diff frame-to-frame and publish "window closed" /
"window opened" / "window moved". So today it is *"my floor vanished, recover"* — never *"I saw that happen,
I'm going over there."* That distinction is the whole ask.

## Scope

### A. DESIGNER — emit window events UP (body senses, does not decide)
- Diff the window set each sensor tick → publish to `unity_events.json`:
  `{type:'window_closed'|'window_opened'|'window_moved', rect, id, _ts}` (+ whether it was **eLo's own**
  surface). **Extend the existing presence/window emitter — no parallel contract** (same rule as WO-086).
- Keep the existing survival re-attach exactly as is. It is the safety net and must not regress.
- **Do NOT decide** what eLo does about the event. Emit and stop.

### B. BUILDER — the brain notices and chooses
- Ambient/Spatial path consumes the events and DECIDES: ignore it · glance at it · go look · relocate to the
  new window · climb a big one that just opened. Decision considers what eLo's doing, whether David is
  working (stay peripheral), mood/energy — it is a real choice, not a reflex.
- Sends the goal DOWN through the SAME action path as sit/move ("go to that surface"), ACK'd per WO-041.
- **Never fabricate:** he only claims he saw something if the event actually arrived (ADR-Exec-001).

### C. FREE-FORM ROUTING (the "finds patterns / ways around" half)
- When the goal is unreachable in one jump, the **pathfinder finds a multi-leg route** — drop a side, run a
  bottom, wall-jump a chimney — instead of refusing or leaping. This is the existing planner; this WO makes it
  the *normal* path rather than an edge case.
- Composes with **WO-074-F** (height-based jump clamp: too far → route, don't leap) and **WO-092** (wall-jump
  is the intended answer to "too far"), and **WO-075** gravity so failure falls and lands rather than floating.
- **Guard-rails are travel paths, not walls** — the route may use any real surface, including behind windows
  (whole-window-walkable, WO-049).

### D. LEARNING — the brain gets better at this over time (David 2026-08-10: "the brain to think more, learn")
**This is canon, not an extra.** Vol XXVIII names **Movement Faculty as RL domain #1** — *"instead of
scripting parkour, eLo learns traversal (state = window geometry · speed · jump height · ledges · momentum;
actions = walk/run/jump/wall-jump/climb/slide/drop/hide; reward = smooth · no collisions · interesting ·
natural pauses · safe landing). This is 'run around because he WANTS to.'"* And **049-B2**: *"History creates
preference; routes are remembered not recomputed; confidence grows from experience. **EMERGENT — favourites
accrue, never coded.**"*

So this WO must **write the outcome of every traversal**, not just execute it:
- **Record what happened:** goal · route taken · legs used · did he arrive · did he fall/miss · how smooth ·
  how long. A failed reach is as valuable as a success.
- **Routes are remembered, not recomputed** — a path that worked to a given surface is recalled next time
  before the planner re-solves from scratch.
- **Favourites accrue** — surfaces/routes he uses repeatedly gain preference through USE, never a hardcoded
  favourite list.
- **Confidence grows from experience** — a route he's landed many times is taken more readily than an untested
  one; repeated failure makes him prefer the safer multi-leg route.
- **Reward = Vol V Ch.5 Significance, NOT a new scalar.** Vol XXVIII §: *"Reuse `memory/significance_engine.py`
  — do NOT invent a reward scalar."* Optimise toward what matters (safety · curiosity · efficiency), not a number.

**⚖ HARD BOUNDARY — ADR-Exec-005 (Learning Through Verified Consequences):** learning may improve **how well
he moves**. It may **NEVER** touch identity · values · personality · memory truth · Executive authority ·
speech correctness. *"Constitution defines who; Executive decides what; RL improves how well."* Learning here
is confined to the Movement/Spatial faculty. It learns only from **verified outcomes** — the body's ACK that
he actually arrived (ADR-Exec-003 Embodied Truth), never from an assumed success.

**Scope now vs later:** this WO builds the **capture + recall + preference** loop (memory of routes,
outcomes, growing confidence) — that is buildable today and is what makes him visibly get better. Full RL
policy training is **Vol XXVIII / WO-CANON-XXVIII**, sequenced after; build the capture cleanly now and it
upgrades without a rewrite.

## Test (without David)
Designer: close/open a window → assert the correct event is emitted with the rect, and that eLo's own-surface
case still re-attaches. Builder: inject `window_opened` → assert a decision is produced (and that it can
legitimately decide to ignore it); inject with David actively typing → assert it stays peripheral.
Routing: place a goal beyond jump reach → assert a multi-leg route is produced and executed, no leap, no float.

## LEARNING IS PART OF DONE (Architect fix 2026-08-10 — §D was in neither the tests nor Done-when)
**Test §D explicitly:** after N traversals to the same target, assert the route is RECALLED (not re-solved
from scratch) · assert a repeatedly-failed route loses preference and the safer multi-leg route is chosen ·
assert outcomes are written ONLY on a verified body ACK (never an assumed success) · assert nothing in the
learning path can write identity/values/personality (ADR-Exec-005).
**A seat may NOT close this WO with the movement built and the learning missing.**

## Done when
both halves land together (Designer emit + Builder decide — same sequencing rule as WO-086), tests green,
committed. **David's bar:** he sees eLo notice a window close and choose to travel there — routing around the
gap rather than leaping or freezing.

## Result
- commit: bf5a545 (Designer §A — emit)
- window_opened/closed/moved published on unity_events.json (same WO-086 contract), own-surface flagged, seeded at launch, single-slot one-per-poll priority closed>opened>moved
- Builder half (§B decide / §C route / §D learn) relayed: builder/FROM_DESIGN_2026-08-13_WO-094_window_events_half_B.md
- NOTE: WO not fully closed until Builder half lands (same sequencing rule as WO-086)
