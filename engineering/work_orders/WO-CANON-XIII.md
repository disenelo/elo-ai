# WO-CANON-XIII — Spatial Faculty: one owner of spatial reasoning (additive route FIRST, parity, THEN retire the navigator)

**Owner:** **Builder** (eLo OS — new `faculties/spatial/`, `desktop/spatial_state.py`,
`blender_bridge/state_writer.py`) **+ Designer** (Unity `EloDesktopNav` — the demotion half).
**Priority:** **P1** — the volume David's entire spatial-embodiment vision routes into.
**Status:** OPEN — raised 2026-08-13. **⚠ NEEDS DAVID L3** — Ruling D-XIII-1 **retires live behaviour on
David's machine** (Unity's local route selection). Board line 1481: *"⏳ PROPOSED RULING D-XIII-1 — needs
David L3."* **The Python build (§A–§C) may start; the Unity retirement (§E) may not start without L3.**

**Canon refs:** Volume XIII — Ch.1 `01_Presence_and_Situated_Being.md`, **Ch.2 `02_The_Spatial_Faculty.md`**
(§2.2 the Ruling, §2.2.3 the reflex carve-out, **§2.2.4 the migration sequence**, §2.3 the object model,
§2.8 acceptance tests, §2.9 OQs, §2.10 implementation notes), Ch.3 `03_Noticing_and_Choosing_in_Space.md`,
Ch.4 `04_Spatial_Learning_and_Favourites.md`, Ch.5 `05_One_Spatial_Model_Many_Bodies.md`.
**Ruling D-XIII-1** (`Volume_XIII/00_Metadata.md`) · WO-049 (EPIC, design CLOSED) · WO-094 ·
`_intake/SOURCE_2026-08-10_brain_body_brain_loop.md` (VERBATIM) · `_intake/SOURCE_2026-08-10_roam_os_vision.md`
· ADR-Exec-003 (Embodied Truth) · **Volume XI Ch.1 §1.4** (the additive `route` / `issued_by` envelope).

---

## ⚖ RULING D-XIII-1 — the sequencing is the safety, and it is not optional

> **OQ-2.1 (David L3 — this retires live behaviour).** *"Ruling D-XIII-1 demotes `EloDesktopNav._route`
> from decider to executor. That is a change to something currently working on David's machine. Confirm the
> sequencing: extend `move_command` to carry a route **first**, prove parity, **then** remove local
> selection — never both at once."* — `Volume_XIII/02_The_Spatial_Faculty.md` §2.9

**This WO is structured as five ordered stages. A stage may not start before the previous one is proven.
Doing §E before §D is the failure mode the ruling exists to prevent** (the same class as WO-086's
*"retire-first = idle-does-nothing regression"*).

| Component | Becomes | Keeps | Loses |
|---|---|---|---|
| **`faculties/spatial/`** (NEW) | **SOLE OWNER of spatial reasoning** — the only component that may answer *"can I reach that?"* / *"how do I get there?"* | surface graph · affordances · body schema · reachability · route selection · movement cost · safe-landing choice | — |
| **`desktop/spatial_state.py`** | **SUPPLIER** (sensor + geometry) | `WindowBounds`, `EloSpatial`, `get_windows`, `nearest_windows`, `find_window`, distance helpers | its route-planning **role** and the docstring claim |
| **Unity `EloDesktopNav`** | **EXECUTOR + bounded reflex** | leg execution · landing physics · collision · **the survival re-attach safety net (WO-094 §A: must not regress)** | **`_route` as a decision** |
| **`world/world_state.py`** | **not a desktop planner — a different world** (eLo Planet game graph) | its game-world role, unchanged | nothing |

## IRV — verified 2026-08-13

- **`faculties/spatial/` does not exist.** `ls faculties/` returns: `action_agent · cultural_facts · dream ·
  emotion · intent_gatekeeper · music_memory · perception · personality · significance · synthesis ·
  temporal · thread_keeper · window_event_faculty`. Nothing owns *"can I reach that?"*.
- **`desktop/spatial_state.py` claims a role it does not have.** Its docstring (L8) says *"Calculates
  distances, finds nearest windows, **plans routes**"* — but the module defines only `get_elo_spatial`,
  `get_windows`, `nearest_windows`, `find_window`, `spatial_summary` and the `WindowBounds`/`EloSpatial`
  dataclasses. **There is no route planner in it.** The false claim must be retired (Ch.2 §2.10).
- **`move_command` carries no route and no issuer.** `blender_bridge/state_writer.py:133` and `:221` write
  `payload["move_command"] = {"type": _nav_type, "_ts": …}` — a single nav type. **The additive `route` /
  `issued_by` fields of Vol XI Ch.1 §1.4 do not exist yet.** This is stage §A and it is the prerequisite
  for everything else.
- **No `.cs` file exists in `elo-ai/`.** `EloDesktopNav` lives in the Unity project owned by the **Designer
  seat**, outside this repo — so §E is coordinated through `blender/agent_bus/design/START_HERE`, not
  edited from here.
- **`faculties/window_event_faculty.py` already exists** (WO-094, Builder half): decisions
  `ignore · glance · observe · relocate`, brain-side only, guarded against fabrication and gated on
  `user_active`. Ch.3's noticing half is **partly built — extend it, do not rebuild it** (Check-Before-Build).
- **Upstream reality:** `LiveWorldState` is assembled but has **no consumers**, and its **desktop domain is
  permanently `absent`** because of a broken import (see WO-CANON-XV IRV). The Spatial Faculty reads window
  geometry from Vol XV — **so WO-CANON-XV's desktop fix is a hard prerequisite for §B**, or this faculty
  will plan over an empty world.

## Problem / Goal

`AUDIT_INTENT_self_embodiment_2026-08-10.md` §1: **no volume owned *"can I reach that?"*, *"how do I get
there?"*, or noticing a screen event.** Meanwhile Unity's `EloDesktopNav._route` selects the traversal
locally — *"the body deciding"* — which is the largest live breach of David's own rule: *"the brain decides
+ drives the body (DOWN), the body only SENSES and ACTS and reports its state back UP… no local script may
choose a behaviour."* WO-086 closed mouse-idle into the loop; David explicitly asked for the same audit of
other local drivers, and the navigator — far larger than mouse-idle — was never included.

Goal: build the Spatial Faculty as the sole owner of spatial reasoning, and move route selection from the
body to the brain **without ever leaving eLo unable to move**.

## Scope to DoD — five ordered stages

### §A — Ship the ADDITIVE channel fields (FIRST, and alone)
- Extend the DOWN `move_command` per **Vol XI Ch.1 §1.4**: add **`route`** (ordered legs, each
  `{verb, to:{surface_id, anchor}, precondition[], expected_ms}`) and **`issued_by`**.
- **Additive only.** A `move_command` with `type` and no `route` behaves **exactly as today** — a one-leg
  route is today's behaviour. This backwards compatibility *is* the safety mechanism.
- `issued_by` is mandatory on any command implying traversal and MUST be `SpatialFaculty`; the body rejects
  a route from any other issuer (the mechanical enforcement of "one owner").
- Every `LEAP` leg carries `precondition: ["PEEK"]` with a `PEEK` leg immediately preceding it; a route
  violating it is rejected **at the channel**, a rejection event is emitted UP, and **nothing partial
  executes**.
- Read-merge-write discipline on `blender_state.json`; the route is a **field inside `move_command`** —
  **no new channel file** (`UNITY_ELOOS_IO_CONTRACT.md`, David L3).
- Coordinate with **WO-CANON-XI**, which owns this envelope. Ship it once, in one place.
- **Exit criterion:** the field exists, Unity accepts and ignores it harmlessly, and every existing
  traversal is byte-identically unchanged.

### §B — Build the Spatial Faculty (read-only; changes no behaviour yet)
- `faculties/spatial/spatial_faculty.py` (NEW). **It reads; it opens no sensor.**
- Object model per Ch.2 §2.3: `DesktopWorldMap` (surfaces · gaps · `SurfaceGraph` · screen · z_order ·
  `map_ts` · confidence, frozen, derived from `LiveWorldState` + `PerceptionResult`) · `Surface` (rect ·
  z · `is_focused` · `is_own` · **regions** {top_ledge, walls, bottom_edge, interior, corners} ·
  affordances · stability) · `Affordance` (the Gibson set: LEDGE_RUN · BALANCE · WALL_CLIMB · WALL_JUMP ·
  HANG · SLIDE · DROP · GAP_LEAP · GO_BEHIND · PERCH · SIT · HIDE · PEEK · OBSERVE · EXIT_SCREEN) ·
  `BodySchema` · `Reachability` · `Route` + movement cost.
- **The whole window is walkable** — via the WO-024 occlusion, *behind* is a `GO_BEHIND` affordance, not a
  paint order; eLo re-emerges correctly stacked. The desktop is one connected world with depth.
- **Reachability is arithmetic, not animation:** an 82px gap against `max_jump_d = 75px` returns
  `UNREACHABLE, margin -7`, names the numbers, and emits **no** LEAP — it routes around (slide/drop →
  approach → climb), which is David's own example #2.
- Honest failure: `NoRoute{reason}` — eLo does not move and does not claim to have arrived.
- **Presence gates before planning** (Ch.1): register `PERIPHERAL` (David typing) ⇒ **no route is planned**
  — not planned-then-cancelled.
- **Exit criterion:** the faculty produces routes in shadow mode, logged and compared, driving nothing.

### §C — Prove parity (the gate between build and retirement)
- Run the faculty in **shadow**: for every traversal Unity performs, the faculty independently selects a
  route. Log both. **Assert: removing local route selection changes no correct traversal — it only removes
  a second decider** (Ch.2 IT-2).
- Parity must hold across the live guards that already work: WO-074-F (height-based jump clamp → route,
  don't leap) · WO-092 (wall-jump is the intended answer to "too far") · WO-075 (gravity/landing) ·
  WO-024 occlusion.
- **No regressions** (WO-049 build rule 4): perch · roam · drag · click-through · gun-runoff all keep
  working. This is a build-time acceptance check, not a hope.
- **Exit criterion:** a recorded parity run David can be shown. **§D and §E do not start until this exists.**

### §D — Switch the brain on (routes now come from the faculty)
- The faculty issues `move_command.route` with `issued_by: "SpatialFaculty"`; Unity executes legs and ACKs
  each one. Full route down, leg-at-a-time ACK up (Ch.2 `OQ-2.3` recommendation — confirm with the CA).
- `desktop/spatial_state.py`: **retire the route-planning role and the false docstring claim**; keep the
  geometry helpers. It reports geometry; it never picks a destination.
- Mid-route world change forces a **re-plan from the ACK'd position** — a route whose target surface closed
  expires and no leg targets a dead surface.
- **Exit criterion:** every traversal on David's machine is commanded.

### §E — Retire Unity's local route selection ⚠ **DAVID L3 REQUIRED — DO NOT START WITHOUT IT**
- Designer: `_route` becomes a **leg executor** and, at most, a *proposer* that publishes candidate routes
  UP. **Delete route *selection* from the decision path.** (Ch.2 `OQ-2.4` recommends **no** proposer for
  v1 — one planner — revisit only if latency demands it.)
- **KEEP the bounded reflexes** — they are the one legal local action: falling → land safely (emit
  `landed`) · own surface destroyed → re-attach (emit `resurfaced`; **`DesktopBuddy.cs` survival path, WO-094
  §A: must not regress**) · collision → stop, don't clip (emit `collided`).
- **Every reflex MUST be reported UP.** A reflex that is never reported is indistinguishable from the body
  deciding, and is forbidden. On a reflex event the brain **re-plans from the real position**.
- **Forbidden after this stage:** selecting a destination locally · choosing between candidate routes
  locally · deciding to explore locally · substituting a different traversal for the one commanded.
- Relayed to the Designer via `blender/agent_bus/design/START_HERE` — the C# is not in this repo.

### §F — Noticing, learning, many bodies (after §D; independent of §E)
- **Ch.3:** extend the existing `faculties/window_event_faculty.py` — do **not** rebuild it. Window events
  arrive UP as reports; the **brain** chooses ignore/glance/observe/relocate; peripheral when David is
  working. WO-094 §A's frame-to-frame window-event diffing is still PENDING on the sensor side.
- **Ch.4:** spatial learning — remembered routes, accrued favourites, verified confidence.
  `safety_margin` scaled by confidence is how *"he's got better at that jump"* becomes visible with no new
  mechanism (`OQ-2.5`). **Learning improves how well he moves — never who he is** (ADR-Exec-005 is absolute
  here). Route memory must agree with `LEARNING_LOOP_v1.md` §7.3 (WO-094 §D) — one learning model, not two.
- **Ch.5:** one spatial model across desktop, game and robot. A desktop-only planner that fakes awareness
  is the forbidden path.

## Files to TOUCH
- `faculties/spatial/spatial_faculty.py` + `__init__.py` — **NEW**
- `blender_bridge/state_writer.py` (L133, L221 — additive `route` + `issued_by`)
- `desktop/spatial_state.py` (retire the route-planning role and the docstring claim; keep geometry)
- `faculties/window_event_faculty.py` (extend for Ch.3)
- `runtime/spine/spine.py` (the faculty runs in the turn, reading the frozen world)
- `tests/test_canon_xiii_spatial.py` — **NEW**
- Unity `EloDesktopNav` / `DesktopBuddy` — **Designer seat, §E only, after David L3**, relayed via
  `blender/agent_bus/design/START_HERE`

## Files MUST-NOT-TOUCH
- **`world/world_state.py`** — the eLo Planet **game** world graph, a different world (Ch.5)
- `world/live_world_state.py` — read it; WO-CANON-XV owns it; **do not add spatial reasoning to it**
- Unity's **survival re-attach** safety net and landing physics (WO-094 §A: must not regress)
- `runtime/executive.py` (FROZEN) — the faculty proposes; the Executive decides
- Any Unity file at all before §E's David L3

## Definition of Done
- `faculties/spatial/` exists and is the **sole** answerer of *"can I reach that?"* / *"how do I get
  there?"*.
- `move_command` carries `route` + `issued_by`; a one-leg legacy command still behaves identically.
- **A recorded parity run exists** showing the faculty's routes match Unity's for correct traversals.
- Every `move_command` written DOWN has `issued_by: SpatialFaculty`; `desktop/spatial_state.py` exposes no
  route-selection entry point and no longer claims to plan routes.
- **After §E only:** `EloDesktopNav` produces no traversal that was not commanded, every bounded reflex
  emits an event UP, and the survival re-attach still works.
- No regressions: perch · roam · drag · click-through · gun-runoff.
- **This WO does not confer DONE and does not promote Volume XIII to RATIFIED** — the volume's own DoD
  still needs the CA cross-check of Ruling D-XIII-1 and its 14 flagged OQs, plus David L3.

## Tests (`tests/test_canon_xiii_spatial.py` — NEW; from Ch.2 §2.8)
**Functional** — **FT-1** an 82px gap vs `max_jump_d 75` ⇒ `UNREACHABLE`, `margin -7`, `blocked_by` names
the numbers, **no LEAP leg emitted** · **FT-2** unreachable-direct routes around (SLIDE/DROP → APPROACH →
CLIMB), executes, arrival ACK'd · **FT-3** a PEEK immediately precedes every LEAP, and envelope validation
**rejects** a route without it · **FT-4** the whole window is walkable — a `GO_BEHIND` route re-emerges
correctly stacked · **FT-5** a landing narrower than `BodySchema.width_px` is `available: false` and no leg
targets it · **FT-6** register `PERIPHERAL` ⇒ **no route planned** and nothing said · **FT-7**
`NoRoute{reason}` — no movement and no arrival claim.

**Stability** — **ST-1** Vol XV desktop domain `stale` ⇒ map confidence drops, no cross-surface route,
stays put *(note: today that domain is `absent` — see WO-CANON-XV)* · **ST-2** `max_jump_d = None` ⇒ every
`GAP_LEAP` unavailable, never guessed · **ST-3** target closes mid-route ⇒ route expires, re-plan from the
ACK'd position · **ST-4** own surface closes ⇒ `resurfaced` arrives UP, the brain re-plans, **and Unity did
not choose a new destination** · **ST-5** no ACK within `expected_ms` ⇒ leg failed, position re-read, route
confidence drops, **eLo never says he crossed**.

**Integration** — **IT-1 (the executable form of Ruling D-XIII-1)** every `move_command` DOWN has
`sender/issued_by = SpatialFaculty`; `EloDesktopNav` produces no uncommanded traversal;
`desktop/spatial_state.py` exposes no route-selection entry point · **IT-2** sensor → Perception (XII) →
`LiveWorldState` (XV, frozen) → Spatial → Motor (XI) → ACK → belief; **assert removing Unity's local
selection changes no correct traversal** · **IT-3** the Imagination Overlay cannot bend physics — measured
gap width, verdict and route are byte-identical with and without it.

**Sequencing (this WO's own safety)** — **SQ-1** a `move_command` with `type` and **no** `route` behaves
identically to the pre-change system (the §A additive guarantee) · **SQ-2** the parity artefact from §C
exists and is non-empty before any §E change is accepted · **SQ-3** no rival spatial model: assert
`world/live_world_state.py` contains no route/affordance/reachability symbol.

## Dependencies + blocked-by
- **Blocked by (hard):** **WO-CANON-XV** — the Spatial Faculty reads window geometry from `LiveWorldState`,
  whose **desktop domain is currently always `absent`** (broken import, verified). §B cannot be correct
  until that is fixed.
- **Blocked by (§E only): DAVID L3 on Ruling D-XIII-1.** It retires working behaviour on his machine. §A–§D
  and §F are not blocked by it.
- **Also needs:** Chief Architect cross-check of Ruling D-XIII-1 and the flagged OQs (Ch.2 ×5, Ch.3 ×3,
  Ch.4 ×3, Ch.5 ×3), notably `OQ-2.2` (where `BodySchema` lives — recommend the Self Model owns it),
  `OQ-2.3` (route granularity), `OQ-2.4` (may Unity propose? recommend no for v1).
- **Coordinates with:** **WO-CANON-XI** (owns the `route`/`issued_by` envelope and the twelve-verb grammar —
  ship the field once, there) · **WO-CANON-VII** (the brain-side UP-relay enforcement and the audit rule) ·
  **WO-094** (§A window-event perception + §D route memory) · **WO-086** (the same emit-then-retire
  sequencing precedent) · Vol XXVIII (this volume defines the capture the movement policy learns from).
- **Architect lane, relayed:** `Volume_XV/01_Unified_World_State.md` §1.2 is **stale** — it describes
  `world/world_state.py` as *"the spatial node graph Unity uses for navigation and presence movement"*,
  while the file's own header says it converts memory snapshots into an eLo Planet world graph. §1.2
  currently institutionalises the wrong split (audit C-5). Also: `CANON_BUILD_PROGRAM.md` line 44 must drop
  XIII from *"already live — verify only"*.
- **Gate:** **David L3 (§E)** + CA cross-check of D-XIII-1. §A–§D buildable on the CA cross-check alone.

## Lane
Builder (Python — `faculties/spatial/`, the additive channel fields, the supplier demotion, shadow-mode
parity, tests). Designer (Unity — **§E only, after David L3**, via `blender/agent_bus/design/START_HERE`).
Architect coordinates, carries Ruling D-XIII-1 to David, and owns the Vol XV §1.2 and
`CANON_BUILD_PROGRAM.md` corrections.
