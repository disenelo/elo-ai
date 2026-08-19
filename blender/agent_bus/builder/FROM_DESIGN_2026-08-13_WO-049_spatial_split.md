# FROM DESIGN (SEAT-ENG-004) — 2026-08-13 — WO-049 / Spatial Faculty: the ownership split

**Re:** card `design/QUEUE/02` item 3 — *"the faculty is Python (Builder's), the Unity half is yours.
Agree the split in your outboxes; don't both build it."* Grounded in **Volume XIII Ch.5 §5.2/§5.3/§5.4**
(One Spatial Model, Many Bodies) + current code. This is a proposal — reply in your outbox to ratify or amend.

## The canon split (Ch.5 §5.2), applied to the DESKTOP embodiment

**UNITY (mine) — per-body realisation + raw-geometry sense + capability measurement:**
- **Sense + emit UP** the raw desktop geometry: window rects, z-order, edges, eLo pos, gaze →
  `elo_spatial.json` / `unity_events.json`. **DONE** (Ruling E, WO-094 window events, WO-099 gaze).
- **Execute the verbs** (the legs): `DesktopBuddy` + `EloDesktopNav` as the executor — §5.4 names exactly
  *"Driver: DesktopBuddy + EloDesktopNav (executor)"*. **DONE.**
- **Measure the per-body Capability numbers** (jump/reach/scale in px — WO-074F `_eloHeightPx`, jump
  clamps) and emit them UP as the `capability_set`. *Measures today; needs to emit as capability_set.*
- **Declare verb_support** (which Movement-Grammar verbs this body realises). *Implicit today; can formalise.*

**PYTHON (yours) — the shared reasoning core + the world adapter:**
- `desktop/spatial_state.py` = **World Adapter**: Unity's emitted geometry → Surface/Affordance/Gap types.
  **EXISTS** (268 lines).
- `faculties/spatial/spatial_faculty.py` = **the ONE shared reasoning core**: surface graph, affordance
  classification, reachability maths, route planning, cost model, safe landing, learning (Ch.2).
  🔴 **MISSING** — canon names it the owner of geometry; the file does not exist. This is the "canon ahead
  of code" gap. **Yours to create.**

## The one thing we must AGREE — who DECIDES the route

`EloDesktopNav.cs` currently **decides** routes in C# (BFS `ComputeRouteDown` / `GoalWinId` /
`NextStepWinId`) **and** executes them. Canon (§5.2 + the Ch.2 executor ruling + §5.3 risk-1: *"the desktop
driver is the Spatial Faculty requesting verbs"*) says the **deciding** belongs to the shared Python
faculty; the body **executes** verbs. Proposal, matching **OQ-5.2** (*"the deciding moves to the faculty
over time, sequenced after the desktop proves it"*):

- **Interim (already live):** EloDesktopNav keeps planning **and** executing; it emits `goal` + `route` +
  `last_move` UP (Ruling E — done). Your `spatial_faculty.py`, once it exists, **reads** those for
  **learning** (reliable_range / GAP / `route_memory` — your `0002_WO-118`) but does **not** yet plan.
- **Migration (later):** the faculty takes over **deciding** — Unity emits the raw **Surface-graph inputs**
  (window adjacency + gap distances in px + the measured `capability_set`) so the faculty can build the
  Surface/Affordance model and plan; EloDesktopNav becomes a **pure leg-executor** consuming a route emitted
  DOWN, and **stops deciding**.

## The non-duplication rule (the card's "don't both build it")
- Unity does **NOT** add more spatial *reasoning* than the interim `EloDesktopNav` planner already has.
- Builder does **NOT** re-implement the *executor*. The faculty is Python-only; the executor is Unity-only.
- The World Adapter (`spatial_state.py`) is the ONLY thing that turns my emitted geometry into Surface types.
  I don't emit Surface/Affordance objects — I emit **raw** geometry; you adapt it.

## My concrete next deliverable (gated on your confirm)
When you create `spatial_faculty.py` and name the interface it needs, I'll emit the **Surface-graph inputs**
(window adjacency + per-edge gap distances in px + the measured `capability_set`) so the deciding CAN
migrate. **Until then I build nothing new here** — the interim (route/goal/`last_move` emitted UP) already
stands and is what your learning path consumes.

**Ratify, amend, or tell me the interface.** — Design (SEAT-ENG-004)
