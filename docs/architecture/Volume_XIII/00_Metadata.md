---
volume: XIII
title: "Presence & Embodied Spatial Intelligence"
former_title: "Presence Engine"
status: REVIEW
version: 0.1.0
owner: David Charles
architect: Claude (Lead Architect)
source: >
  WO-049 (EPIC, design SATURATED/CLOSED) · WO-094 · David VERBATIM
  _intake/SOURCE_2026-08-10_roam_os_vision.md · _intake/SOURCE_2026-08-10_brain_body_brain_loop.md ·
  _intake/SOURCE_2026-08-10_headaim_mouse_follow.md · AUDIT_INTENT_self_embodiment_2026-08-10.md §1 · live code
implementation: PARTIAL (presence/ + ambient/ live; Spatial Faculty PENDING — nothing yet owns "can I reach that?")
audit_status: OPEN
canonical_path: docs/architecture/Volume_XIII/
tier: FACULTY
dependencies:
  - Volume XII (Perception — supplies the observations this volume reasons over; sibling, no overlap)
  - Volume XV (World State — holds the frozen per-turn world; Spatial Faculty reads it, never re-senses)
  - Volume XI (Motor Cortex — the body contract this volume's decisions travel DOWN through)
  - Volume V/CONTRACTS.md (envelope, lifecycle, base faculty contract)
  - Volume V Ch.10 (Agency — supplies the *wanting* that becomes a spatial goal)
  - Volume XXVIII (Adaptive Learning — Movement Faculty is RL domain #1)
  - ADR-Exec-001 (Verified Speech) · ADR-Exec-003 (Embodied Truth) · ADR-Exec-004 (Situated Self) ·
    ADR-Exec-005 (Learning Through Verified Consequences)
priority: "Audit P1 — the volume David's entire spatial-embodiment vision routes into, previously unwritten"
last_review: 2026-08-11
next_review: TBD
---

# Volume XIII — Presence & Embodied Spatial Intelligence

## What this volume is (and why the title changed, not the number)

Volume XIII was **"Presence Engine"** — idle, silence, ambient, withdrawal. That half is **live in code**
(`presence/`, `ambient/`). WO-049 ratified (2026-08-04, Chief Architect cross-check) that the Spatial
Faculty's canonical home is **the evolution of this volume**, not a new one:

> "⚠ Volume XIII already exists = the Presence Engine (idle / silence / ambient). A second Vol XIII would
> be exactly the numbering-drift / duplicate-authority we prevent. The concept's home is to **EVOLVE the
> existing Volume XIII → 'Presence & Embodied Spatial Intelligence.'** … No new number, no duplicate
> volume. This is where One Brain becomes fully embodied." — WO-049

So: **same number, widened title.** Presence is *being somewhere without demanding attention*. Spatial
intelligence is *knowing where that somewhere is, what it affords, and how to get to the next one*. They
are one faculty of mind — situated being — not two.

## The problem this volume closes

`AUDIT_INTENT_self_embodiment_2026-08-10.md` §1 recorded the failure plainly: **no volume owned "can I
reach that?", "how do I get there?", or noticing a screen event.** Volume XIII had one file
(`14_presence_faculty.md`, five lines, "STATUS: PENDING") and `CANON_BUILD_PROGRAM.md` filed it under
"already live — verify only," so nothing in the programme would ever cause it to be written. Eight canon
docs, WO-049, WO-094 and David's own words all pointed *here*, at an empty room.

## Scope (authoritative)

Presence as a cognitive state · idle · silence · withdrawal and return · **the Spatial Faculty**
(desktop world map · surface graph · affordances · body schema · reachability · route planning · movement
cost · safe landing) · noticing screen events and choosing what to do about them · spatial learning
(remembered routes, accrued favourites, verified confidence) · one spatial model across desktop, game and
robot.

**Out of scope (owned elsewhere, referenced not duplicated):**
- *Sensing* windows, screen, mouse, voice → **Volume XII (Perception)**. This volume never re-senses.
- *Holding* the per-turn world snapshot → **Volume XV (World State)**. This volume reads it frozen.
- *Executing* a decided motion + the ACK contract → **Volume XI (Motor Cortex)**.
- *Wanting* to go somewhere → **Volume V Ch.10 (Agency)**. This volume answers "how", not "why".
- *Policy training* on movement → **Volume XXVIII**. This volume defines the capture the policy learns from.

## Anchors in the live system (verified 2026-08-11)

| Anchor | Path | State |
|---|---|---|
| Presence as cognitive state | `presence/presence_state.py` (7 `PresenceMode` values + `MODE_FEEL`) | **LIVE** |
| Presence derivation (stateless) | `presence/presence_engine.py` `derive()` | **LIVE** |
| Presence scheduling | `presence/presence_scheduler.py` | **LIVE** |
| Idle repertoire + wander + meditation | `ambient/ambient_engine.py` (`_IDLE_THRESHOLD=30s`, `_ANIM_MIN/MAX=3–8 min`, `_decide_idle_behaviour`) | **LIVE** |
| Withdrawal / return | `leave_command` / `return_command` (`blender_bridge/state_writer.py`) · WO-045 | **LIVE** |
| Window geometry + eLo position | `desktop/spatial_state.py` (`WindowBounds`, `EloSpatial`, `elo_spatial.json`) | **LIVE (as a sensor)** |
| Game world graph | `world/world_state.py` (memory → node graph, eLo Planet) | **LIVE (different world — see §Ruling)** |
| Desktop route execution | Unity `EloDesktopNav` (`_route`, descent pathfinder, wall-jump chimneys) | **LIVE (currently decides — must not)** |
| **Spatial Faculty** | *(none — `faculties/spatial/` does not exist)* | **PENDING** |
| **Window-event perception** | *(none — the sensor does not diff frame-to-frame)* | **PENDING (WO-094 §A)** |

## Chapter Build Queue

| ID | Chapter | Title | Status |
|----|---------|-------|--------|
| ELO-V13-CH01 | Chapter 1 | Presence & Situated Being — the live half | READY FOR REVIEW |
| ELO-V13-CH02 | Chapter 2 | **The Spatial Faculty** — the load-bearing chapter | READY FOR REVIEW |
| ELO-V13-CH03 | Chapter 3 | Noticing & Choosing in Space | READY FOR REVIEW |
| ELO-V13-CH04 | Chapter 4 | Spatial Learning & Favourites | READY FOR REVIEW |
| ELO-V13-CH05 | Chapter 5 | One Spatial Model, Many Bodies | READY FOR REVIEW |

**Chapter set rationale (no padding):** Ch.1 canonises what is already live and states the presence law
that governs *when* spatial behaviour is allowed to happen at all. Ch.2 is the missing organ — it owns
every question the audit found ownerless, and issues the ruling on the three competing planners. Ch.3 is
the input side (events perceived → brain chooses), which Ch.2 has no meaning without. Ch.4 is how the
faculty gets better without ever touching identity. Ch.5 is the cross-embodiment guarantee that makes this
one spatial model rather than a desktop hack. Five chapters, no overlap.

## Invariants this volume must never break

1. **Movement is visible spatial reasoning, never a random clip.** Every traversal act must be explainable
   as this continuous mind pursuing a goal in a perceived world. If it can't, it doesn't ship. (WO-049,
   governing principle; David verbatim: *"If a move can't be explained as 'he wanted to get somewhere and
   worked out how,' it doesn't belong."*)
2. **brain > body > brain — the body NEVER decides.** The brain decides and drives DOWN; the body only
   senses, acts, and reports UP; the brain reads that back and decides again. *"No local script may choose
   a behaviour."* (David verbatim, `SOURCE_2026-08-10_brain_body_brain_loop.md`.) This is the invariant the
   Unity navigator currently breaches — see the Ruling below.
3. **The desktop is a world eLo inhabits, not a canvas he floats on.** Windows are terrain with depth;
   *behind* is a place you can go, not a z-layer. (WO-049 build rule 2.)
4. **Affordance before action.** eLo perceives what a surface *invites*, then chooses an action that
   satisfies his intention within his verified capabilities. He never selects an animation directly.
   (`ARCHITECTURAL_PRINCIPLES.md`.)
5. **Embodied Truth.** He believes — and may only say — that he moved once the body ACKs it.
   Goal → aim → route → execute → **confirm**. (ADR-Exec-003; David verbatim.)
6. **Presence over engagement.** Spatial capability never becomes a reason to be seen. David working →
   stay peripheral. Silence and stillness are first-class outputs of this volume, not gaps between
   behaviours. (D-PRESENCE; Protect Wonder.)
7. **eLo has NO EYES.** Attention and gaze are expressed by **head/body orientation, posture and glow**,
   plus the single curved mouth — never eyes, never an eye-target. (`CO_WORKING_GUIDE.md`: *"Character
   constants (immutable): eLo has NO EYES"*.) Any "look at it" output of this volume is an orientation
   command, not a gaze-of-the-eyes.
8. **One spatial model, many bodies.** The same cognition serves desktop now and robot later. A
   desktop-only planner that fakes awareness is the forbidden path. (WO-049 CA cross-check.)
9. **Learning improves how well he moves — never who he is.** ADR-Exec-005 boundary is absolute inside
   this volume (Ch.4).

## ⚖ RULING D-XIII-1 (PROPOSED — requires Chief Architect cross-check + David L3)

**One owner of spatial reasoning. The other two are a supplier and an executor.**

| Component | Ruling | Keeps | Loses |
|---|---|---|---|
| **`faculties/spatial/` — the Spatial Faculty** (Vol XIII Ch.2, **PENDING, to be built**) | **SOLE OWNER of spatial reasoning.** The only component that may answer *"can I reach that?"* and *"how do I get there?"* | surface graph · affordances · body schema · reachability · route selection · movement cost · safe-landing choice | — |
| **`desktop/spatial_state.py`** | **SUPPLIER (sensor + geometry).** Feeds Perception (Vol XII) → World State (Vol XV) → the Spatial Faculty. | window bounds via `osascript`; `EloSpatial` read from `elo_spatial.json`; pure distance/geometry helpers (`distance_to`, `nearest_windows`, `find_window`) | **its route-planning role.** Its docstring claim *"plans routes"* is retired; that logic moves into the Spatial Faculty. It reports geometry; it never picks a destination. |
| **Unity `EloDesktopNav`** | **EXECUTOR + bounded reflex.** Receives an ordered route DOWN and performs it. | leg execution (walk/run/jump/wall-jump/slide legs) · landing physics · collision · **the survival re-attach safety net when eLo's own surface is destroyed (WO-094 §A: must not regress)** | **`_route` as a decision.** Selecting *where to go* and *which route to take* is the brain's. Unity may no longer choose a traversal locally. |
| **`world/world_state.py`** | **NOT a desktop planner — different world.** It is the **eLo Planet game world graph** (memory snapshots → node graph). It supplies the Spatial Faculty only in the **game** embodiment (Ch.5). | its game-world role, unchanged | nothing — but the canon description of it must be corrected (see below). |

**Plain statement, as the audit requires (C-5):** *the Unity navigator deciding routes locally violates
brain > body > brain and must become a supplier/executor.* `EloDesktopNav._route` currently selects the
traversal. That is the body deciding. WO-086 closed mouse-idle into the loop; David explicitly asked for
the same audit of *other* local drivers, and the navigator — a far larger local driver than mouse-idle —
was never included. This ruling includes it.

**Bounded-reflex carve-out (the one legal exception).** A reflex is not a choice. Unity may act locally
**only** to keep the body safe when the brain cannot be consulted in time — falling must land, and a
destroyed surface must be re-attached (the live `DesktopBuddy.cs` survival path). Every such reflex MUST
be reported UP as an event so the brain re-plans from the real position. A reflex that is never reported
is indistinguishable from the body deciding, and is forbidden.

**Canon correction this ruling forces:** `Volume_XV/01_Unified_World_State.md` §1.2 describes
`world/world_state.py` as *"the spatial node graph Unity uses for navigation and presence movement."*
The file's own header says it converts memory snapshots into an eLo Planet world graph. Vol XV §1.2 is
**stale and must be corrected** — it currently institutionalises the wrong split (audit C-5). Flagged for
the Vol XV owner; **not** edited from here.

## Definition of Done

- [x] Volume created at the ratified number with the ratified evolved title (no new volume)
- [x] Five deep chapters authored (presence · Spatial Faculty · noticing/choosing · learning · many bodies)
- [x] Each: contract + lifecycle + envelope + acceptance tests + open questions
- [x] Grounded in named live anchors and in David's verbatim sources (referenced, never paraphrased into replacement)
- [x] The three-planner conflict RULED on, with the brain>body>brain breach stated plainly
- [ ] Chief Architect cross-check of Ruling D-XIII-1 and the flagged open questions (Ch.2 ×5, Ch.3 ×3, Ch.4 ×3, Ch.5 ×3)
- [ ] **David L3** on Ruling D-XIII-1 (it retires live Unity behaviour — a body/authority decision, not a refactor)
- [ ] `Volume_XV` §1.2 correction accepted by its owner
- [ ] `CANON_BUILD_PROGRAM.md` line 44: remove XIII from the "already live — verify only" list; raise **WO-CANON-XIII**
- [ ] `00_CANON_INDEX.md`: one home for the Spatial Faculty (here); delete the "Volume-V faculty chapter" alternative
- [ ] Audit can mark COMPLETE (blocked on the above + 049-B1 build)

**Status: REVIEW** — scope locked; five chapters READY FOR REVIEW; one ruling awaiting L3.
