---
chapter: 2
title: "The Spatial Faculty — Can I Reach That, and How Do I Get There?"
volume: XIII
status: READY FOR REVIEW
version: 0.1.0
owner: David Charles
architect: Claude (Lead Architect)
source: >
  WO-049 §THE SPATIAL FACULTY + §Build rules (049-B1) · David VERBATIM
  _intake/SOURCE_2026-08-10_roam_os_vision.md §1–3, §7 · _intake/SOURCE_2026-08-10_brain_body_brain_loop.md ·
  AUDIT_INTENT_self_embodiment_2026-08-10.md §1.1–1.2, C-5 · live code (desktop/spatial_state.py, world/world_state.py, EloDesktopNav)
implementation: PENDING (faculties/spatial/ does not exist; suppliers live, executor live-but-mis-scoped)
audit_status: OPEN
dependencies:
  - Volume_XIII/01_Presence_and_Situated_Being.md (the register that gates every goal)
  - Volume XII (Perception — supplies window geometry/events; this faculty never re-senses)
  - Volume XV (World State — the frozen per-turn world this faculty reads)
  - Volume XI (Motor Cortex — the DOWN command + UP ACK channel routes travel through)
  - Volume V Ch.10 (Agency — supplies the goal; this faculty answers "how", not "why")
  - Volume V Ch.9 (Creative Imagination — the Imagination Overlay reinterprets this map, never replaces it)
  - Volume XXVIII (Adaptive Learning — Movement is RL domain #1; Ch.4 defines the capture)
  - ADR-Exec-003 (Embodied Truth) · ADR-Exec-004 (Situated Self)
---

# Chapter 2: The Spatial Faculty

## 2.0 Purpose

This chapter fills the hole the audit found. Today **no component owns spatial reasoning**: three
route-planners exist in code, none of them is the brain, and canon named a home (this volume) that had
never been written. The Spatial Faculty is that home.

It answers exactly two questions, and it is the **only** thing permitted to answer them:

> **"Can I reach that?"** and **"How do I get there?"**

David's example #2 is the whole specification in one paragraph:

> "The gap to the next window is too wide for his jump. He *doesn't* attempt it and fall. He recognises he
> can't make it and finds another route — drops down a side, goes along the bottom. What I want is him
> asking 'can I actually reach that?' not 'which clip fires here?'"
> — `_intake/SOURCE_2026-08-10_roam_os_vision.md` §2 (VERBATIM primary source — read it; this line is a pointer, not a substitute)

The Executive does not think *"play WallJump."* It thinks *"I'd like to reach that ledge,"* asks this
faculty, and movement is the visible consequence.

**Fix location:** `faculties/spatial/spatial_faculty.py` (NEW — does not exist). WO-049 phase **049-B1**.

## 2.1 Principle

**2.1.1 Movement is visible spatial reasoning, never a random clip.** The governing principle of WO-049,
binding on every line of this chapter. If a traversal cannot be explained as this continuous mind pursuing
a goal in a perceived world, it does not ship.

**2.1.2 The brain decides; the body executes and reports.** brain > body > brain. This faculty is the
*brain* half of every movement. No local script — Python, C#, or otherwise — may choose a traversal.
(David verbatim, `SOURCE_2026-08-10_brain_body_brain_loop.md`.)

**2.1.3 Affordance before action.** The faculty classifies surfaces by **opportunity**, not object type:
this edge invites balancing, this gap invites a jump, this corner invites hiding, this ledge invites
sitting. Behaviour emerges from what the world *invites*, never from an animation list.

**2.1.4 Body schema before route.** Reachability is answered from a live self-model — *how big am I, how
far can I jump, what is my reach, where is my footing* — not from whether an animation exists. A 82px gap
against a 75px maximum jump is **unreachable**, and that reasoning is the point.

**2.1.5 Reason over the frozen world; never re-sense.** The faculty reads the per-turn `LiveWorldState`
(Vol XV) and the `PerceptionResult` (Vol XII). It does not call `osascript`, does not poll Unity, does not
take a screenshot. If it isn't in the frozen world, he doesn't know it this turn.

**2.1.6 Nothing is believed until the body ACKs.** A planned route is an intention. An executed leg is a
fact only when Vol XI returns `<action>_complete`. He may not say he crossed until he crossed.

**2.1.7 Peek before every jump — a hard precondition, not flavour.** `PeekPitch` (the edge check) MUST
fire before any ledge-to-ledge leap. No blind jumps. It reads as *"he checked the drop first."*
(WO-049 build rule 1, David refresh 2026-08-10.)

## 2.2 ⚖ THE RULING — one owner of spatial reasoning (D-XIII-1)

**Three route planners exist in the repo. This is a Check-Before-Build breach and a One Brain issue, not a
refactor.** The ruling is stated in `00_Metadata.md`; the engineering consequence is stated here.

### 2.2.1 What each becomes

```
                    ┌──────────────────────────────────────────────┐
   SENSOR/SUPPLIER  │ desktop/spatial_state.py                     │  window bounds (osascript)
                    │  WindowBounds · EloSpatial · distance_to     │  eLo position (elo_spatial.json)
                    │  nearest_windows · find_window               │  → pure geometry, NO route choice
                    └───────────────────┬──────────────────────────┘
                                        │ via Perception (Vol XII) → World State (Vol XV, frozen)
                                        ▼
                    ┌──────────────────────────────────────────────┐
   ★ SOLE OWNER     │ faculties/spatial/spatial_faculty.py  (NEW)  │  surface graph · affordances
   OF SPATIAL       │  "can I reach that?" · "how do I get there?" │  body schema · reachability
   REASONING        │                                              │  route selection · cost · landing
                    └───────────────────┬──────────────────────────┘
                                        │ route DOWN via Vol XI (blender_state.json move_command)
                                        ▼
                    ┌──────────────────────────────────────────────┐
   EXECUTOR +       │ Unity EloDesktopNav / DesktopBuddy           │  performs the legs it was given
   BOUNDED REFLEX   │  walk/run/jump/wall-jump/slide execution     │  landing physics · collision
                    │  survival re-attach (safety net, KEEP)       │  → ACK + events UP
                    └──────────────────────────────────────────────┘
```

### 2.2.2 Stated plainly, as the audit requires

**The Unity navigator deciding routes locally violates brain > body > brain and must become a
supplier/executor.** `EloDesktopNav._route` currently *selects* the traversal — where to go and how to get
there — inside the body. David's law is unambiguous: *"the body only SENSES and ACTS and reports its state
back UP… no local driver deciding what eLo does."* WO-086 closed mouse-idle into the loop; David
explicitly asked for an audit of *other* local drivers; the navigator — a far larger local driver than
mouse-idle — was never included. This chapter includes it.

`desktop/spatial_state.py` is demoted the other way: its file header claims it *"plans routes."* It must
not. It is a **sensor with geometry helpers**. Distances, nearest-window ordering and window lookup stay;
route selection moves up to the faculty.

`world/world_state.py` is **not a desktop planner at all** — it converts memory snapshots into the eLo
Planet node graph. It supplies this faculty only in the **game** embodiment (Ch.5). `Volume_XV` §1.2's
description of it as *"the spatial node graph Unity uses for navigation and presence movement"* is stale
and must be corrected by that volume's owner; it currently institutionalises the wrong split.

### 2.2.3 The bounded-reflex carve-out (the only legal local action)

A reflex is not a choice. Unity may act locally **only** to keep the body physically coherent when the
brain cannot be consulted in time:

| Legal reflex | Why | Obligation |
|---|---|---|
| Falling → land safely | physics happens between turns | emit `landed` UP with the real surface |
| eLo's own surface destroyed → re-attach to nearest | the floor vanished; floating is worse (live in `DesktopBuddy.cs`) | emit `resurfaced` UP; **must not regress** (WO-094 §A) |
| Collision → stop, don't clip through | frame-rate safety | emit `collided` UP |

**Every reflex MUST be reported UP.** A reflex that is never reported is indistinguishable from the body
deciding, and is forbidden. On receiving a reflex event the brain **re-plans from the real position** —
it never assumes the old plan still holds.

**Forbidden after this ruling:** selecting a destination locally · choosing between candidate routes
locally · deciding to explore locally · substituting a different traversal for the one commanded.

### 2.2.4 Migration (relayed to seats — NOT executed by the Architect)

1. Extend the DOWN `move_command` to carry a **route** (ordered legs), not only a single nav `type`
   (see §2.7). Backwards compatible: a one-leg route is today's behaviour.
2. Unity: keep leg execution, keep the safety net, **delete route *selection*** from the decision path;
   `_route` becomes a leg-executor and, at most, a *proposer* that publishes candidate routes UP.
3. Python: move route selection into `faculties/spatial/`; `desktop/spatial_state.py` loses its planning
   docstring and keeps geometry.
4. Assert parity at each step: identical observable traversal, one fewer decider.

## 2.3 What the faculty owns (the object model)

### 2.3.1 DesktopWorldMap — the world, per turn

```
DesktopWorldMap (frozen, derived from LiveWorldState + PerceptionResult):
  surfaces:   [ Surface ]          # every window, plus the screen frame itself
  gaps:       [ Gap ]              # traversable and non-traversable openings between surfaces
  graph:      SurfaceGraph         # nodes = surfaces, edges = possible transitions
  screen:     { w, h, safe_area }  # screen bounds; edges are real (run-off is a legal act)
  z_order:    [ surface_id ]       # front→back; "behind" is a PLACE, not a paint order
  map_ts:     float
  confidence: 0.0–1.0              # degrades with stale/absent geometry
```

### 2.3.2 Surface — a window, read as terrain

```
Surface:
  id:          str                 # stable across ticks (app + window identity)
  app:         str                 # "Google Chrome" — for meaning, never for scripted behaviour
  rect:        { x, y, w, h }      # from desktop/spatial_state.WindowBounds
  z:           int                 # z-order index
  is_focused:  bool                # David's active window — presence-critical (Ch.1 PERIPHERAL)
  is_own:      bool                # eLo's current surface
  regions:     { top_ledge, left_wall, right_wall, bottom_edge, interior, corners[4] }
  affordances: [ Affordance ]
  stability:   enum { stable, moving, closing, unknown }   # from window events (Ch.3)
```

**Region meanings (WO-049 §Desktop Navigation Layer — surfaces carry MEANING, not pixels):**

| Region | Means | Invites |
|---|---|---|
| top edge | **ledge** | run · balance · perch · rest · observe |
| left/right side | **wall** | climb · wall-jump · hang · slide |
| bottom edge | **drop** | slide · drop to the surface below |
| interior | **occluded space** | **go-there** — travel across/behind, re-emerge correctly stacked |
| corner | **pivot** | turn · hide · peek |
| gap between surfaces | **jump opportunity** *or* barrier | leap (if reachable) · route around (if not) |

**The whole window is walkable.** Via the WO-024 occlusion, *behind* is a `go-there` affordance, not just
a visual layer. eLo can travel across and behind a window and re-emerge correctly stacked. The desktop is
one connected world with depth, never a sprite floating on top. (WO-049 build rule 2; David §3.)

### 2.3.3 Affordance — what the world invites (Gibson)

```
Affordance:
  kind:       enum { LEDGE_RUN, BALANCE, WALL_CLIMB, WALL_JUMP, HANG, SLIDE, DROP,
                     GAP_LEAP, GO_BEHIND, PERCH, SIT, HIDE, PEEK, OBSERVE, EXIT_SCREEN }
  surface_id: str
  region:     str
  anchor:     { x, y }             # the specific point it applies at
  requires:   BodyRequirement      # what the body must be able to do to take it (see §2.3.4)
  cost:       float                # movement cost if taken (§2.3.6)
  risk:       float 0–1            # chance of a bad outcome given current body schema + history
  available:  bool                 # requires ⊆ body capability AND presence register permits
```

**Rule (MUST):** an affordance is a *property of the world as read by this body*. The same 90px gap is a
`GAP_LEAP` for a body that can jump 100px and **not an affordance at all** for a body that can jump 75px.
Affordances are never a static tag list on a window.

### 2.3.4 BodySchema — the body's working memory (how big am I, what can I do)

This is the object that makes "can I reach that?" answerable. It is a live self-model, not a position.

```
BodySchema (from the Self Model / Situated Self, ADR-Exec-004):
  embodiment:      enum { desktop, game, robot }
  height_px:       int      # LIVE: EloSpatial.height_px (desktop, from elo_spatial.json)
  width_px:        int
  position:        { x, y } # LIVE: EloSpatial.pixel_x / pixel_y
  surface_id:      str      # what he is standing on right now
  pose:            enum { idle, sitting, hanging, running, airborne, resting, meditating }
  footing:         enum { planted, edge, unstable, none }
  max_jump_h:      float    # vertical reach, px
  max_jump_d:      float    # horizontal reach, px          ← the "82 vs 75" arithmetic
  max_reach:       float    # grab/hang reach from a ledge, px
  climb_height:    float    # how much wall he can take in one climb
  wall_jump_gain:  float    # extra height/distance a wall-jump buys (WO-092)
  momentum:        { vx, vy }
  centre_of_mass:  { x, y }
  balance:         float 0–1
  energy:          float 0–1   # from PresenceState.energy — tired bodies take cheaper routes
  confidence:      float 0–1   # earned, per Ch.4 — never assumed
```

**Body schema rules (MUST):**
- Every value is **verified or absent**. An unmeasured `max_jump_d` is `None`, and a `None` capability
  makes every dependent affordance `available: false`. He does not guess his own body.
- `height_px` and `position` come from the body's own report (`elo_spatial.json`, written by Unity) — the
  body senses itself and reports UP; the brain reads it. That is brain>body>brain working correctly.
- Capability constants are **per embodiment** (Ch.5). The same reasoning, different numbers.
- The schema is read-only inside a turn, exactly like `LiveWorldState`.

### 2.3.5 Reachability — "can I fit / can I clear this gap?"

```
reachable(from: BodySchema, to: Affordance) -> Reachability:

  Reachability:
    verdict:   enum { REACHABLE_DIRECT, REACHABLE_VIA_ROUTE, UNREACHABLE }
    margin:    float          # px of headroom (negative = short by this much)
    blocked_by: [str]         # "gap 82px > max_jump_d 75px", "no landing width", "register: PERIPHERAL"
    legs:      int            # 1 for direct; n for the cheapest known route
```

**Reachability rules (MUST):**
1. **Measure, then decide.** Compute `margin = capability − requirement`. Never attempt a traversal with
   `margin < safety_margin`. David: *"He doesn't attempt it and fall."*
2. **Unreachable-direct is not failure — it is a routing input.** `UNREACHABLE` in one leg immediately
   asks §2.3.6 for a multi-leg route. Refusing to move, or leaping anyway, are both wrong.
   (WO-094 §C: multi-leg routing is the **normal** path, not an edge case.)
3. **Fit is a real constraint.** A landing region narrower than `width_px`, or an interior he cannot
   occupy, is not a landing. "Can I fit" is checked separately from "can I clear."
4. **Guard-rails are travel paths, not walls** (WO-094 §C). A route may use any real surface, including
   behind windows.
5. **Wall-jump is the intended answer to "too far"** (WO-092), not a decorative flourish.

### 2.3.6 Route planning + movement cost

```
plan_route(map: DesktopWorldMap, body: BodySchema, goal: SpatialGoal, register) -> Route | NoRoute

Route:
  goal:        SpatialGoal
  legs:        [ Leg ]
  total_cost:  float
  risk:        float 0–1
  confidence:  float 0–1        # from remembered outcomes (Ch.4), not from the planner's optimism
  rationale:   [str]            # why THIS route — required, and never spoken unprompted

Leg:
  verb:        MovementVerb     # the Movement Grammar (Vol XI Ch.2) — APPROACH, CLIMB, LEAP, …
  from:        { surface_id, anchor }
  to:          { surface_id, anchor }
  affordance:  Affordance
  precondition: [str]           # e.g. "PEEK" before every LEAP — hard, §2.1.7
  cost:        float
  expected_ms: int              # for ACK timeout (Vol XI)
```

**Cost model (MUST):** cost is not distance. It is
`distance × terrain_factor + risk_penalty + energy_penalty − familiarity_bonus`, where:
- `terrain_factor` — a wall-jump chimney costs more than a run along a ledge.
- `risk_penalty` — scales with `Affordance.risk` and inversely with `BodySchema.confidence`.
- `energy_penalty` — low `energy` biases toward cheap, short routes (this is how "tired" is *shown*, not
  said).
- `familiarity_bonus` — a route with verified successful history is cheaper (Ch.4). This is what makes
  favourites accrue **through use** rather than through a hardcoded list.

**Planning rules (MUST):**
- **Presence-gated first.** The register (Ch.1 §1.3) is applied *before* planning. A route David's focus
  forbids is never planned, not planned-then-suppressed.
- **Peek is inserted, not optional.** The planner emits `PEEK` as a precondition on every `LEAP` leg. A
  route containing a blind leap is invalid and must fail validation.
- **Safe landing is chosen, not hoped for.** Every leg's `to.anchor` must be a verified landing: on a
  `stable` surface, wide enough for `width_px`, with footing. A leg targeting a `closing` surface is
  invalid (Ch.3 supplies `stability`).
- **`NoRoute` is an honest, speakable answer.** `NoRoute { reason }` → eLo may stay, or say plainly that
  he can't get there. He never fabricates arrival (ADR-Exec-001).
- **The planner never narrates.** `rationale` exists for the audit and for Ch.4's learning capture. eLo
  does not say "Can I move? Yes. Can I jump? Yes." — *the Executive grows quieter*; competent embodied
  behaviour drawn from a verified sense of self, world and capability.

### 2.3.7 The loop

```
Agency wants something (Vol V Ch.10)   ──►  SpatialGoal
                                              │
Presence register (Ch.1)  ── permits? ────────┤ no ──► stay / defer, silently
                                              ▼ yes
DesktopWorldMap  ← LiveWorldState (Vol XV) + PerceptionResult (Vol XII)   [frozen, never re-sensed]
                                              │
BodySchema  ── reachable()? ──────────────────┤ UNREACHABLE_DIRECT ──► multi-leg route
                                              ▼
                                       plan_route() → Route (peek-guarded, landing-verified)
                                              │
                                     DOWN via Motor Cortex (Vol XI): move_command{route}
                                              │
                          body executes ──► UP: <verb>_complete / landed / collided / resurfaced
                                              │
                       brain re-reads position ──► next leg  ·  or re-plan  ·  or arrived
                                              ▼
                            only NOW: belief updates, and eLo may say it happened
                                              ▼
                                    outcome written for learning (Ch.4)
```

David's shape, verbatim: **"goal → aim → find the path across the terrain → execute the move → confirm it
happened."**

## 2.4 The Imagination Overlay (what it may and may not touch)

eLo cognitively reinterprets the desktop as terrain — taskbar as a train platform, windows as drifting
islands, a gap as a canyon needing courage, a maximised window as a mountain. **Nothing visual changes;
only how he experiences it.** (WO-049; Creative Imagination, Vol V Ch.9.)

**Boundary (MUST):** the overlay may colour *meaning, mood and narration*. It may **never** alter
`DesktopWorldMap` geometry, `BodySchema` capability, `Reachability` verdicts, or route validity. A canyon
he can't cross is still 82px. Reality Before Narrative: story enriches reality, never replaces it.

## 2.5 Faculty Contract

```
Faculty:
  name:            SpatialFaculty
  version:         1.0.0
  purpose:         Own eLo's spatial reasoning. Build the desktop world map, classify affordances,
                   maintain the body schema, answer reachability, plan and cost routes, and choose
                   safe landings — so the Executive can ask "how do I get there?" and receive a
                   verifiable plan instead of an animation.
  contributes_to:  CognitiveState (spatial_state) + MovementPlan (to Vol XI)
  runs_in:         response-path (per turn, when a spatial goal exists) + event-driven (Ch.3 events)

Inputs:
  - type: live_world_state    source: Volume XV (frozen)            required: true
    description: desktop/unity/user domains — window geometry, focus, eLo's reported position.
  - type: perception_result   source: Volume XII                    required: true
    description: interpreted surfaces + salient objects + window events (Ch.3).
  - type: body_schema         source: Self Model (ADR-Exec-004) + elo_spatial.json (UP)  required: true
  - type: presence_register   source: Volume XIII Ch.1              required: true
  - type: spatial_goal        source: Agency (Vol V Ch.10) or Executive/user intent      required: false
  - type: body_event          source: Volume XI UP channel (landed, collided, resurfaced, arrived)  required: false
  - type: route_memory        source: Volume XIII Ch.4              required: false

Outputs:
  - type: reachability        destination: Executive
    description: verdict + margin + blocked_by for a named target. The answer to "can I reach that?"
  - type: route               destination: Motor Cortex (Vol XI) via move_command
    description: ordered peek-guarded, landing-verified legs in Movement Grammar verbs.
  - type: no_route            destination: Executive
    description: honest inability, with reason. Never a fabricated arrival.
  - type: spatial_state       destination: CognitiveState
    description: where he is, what he's on, what's around him, what he could do from here.

Dependencies:
  - faculty: WorldStateFaculty (Vol XV, HARD — no frozen world, no map)
  - faculty: PerceptionFaculty (Vol XII, HARD — geometry + events arrive through it)
  - faculty: PresenceFaculty (Vol XIII Ch.1, HARD — the register gates every goal)
  - faculty: MotorCortex (Vol XI, HARD — the only way a route reaches the body)
  - faculty: AgencyEngine (Vol V Ch.10, SOFT — without it he still moves on request, just not on his own)
  - store:   route memory (Ch.4, SOFT — without it every route is recomputed; correct but not improving)

Failure Modes:
  - condition: window geometry stale/absent (Vol XV desktop domain degraded)
    fallback:  map.confidence drops; only the CURRENT surface is trusted; no cross-surface route is
               planned. He stays put. He does NOT plan on remembered geometry as if it were live.
  - condition: body schema incomplete (max_jump_d unknown)
    fallback:  dependent affordances become available:false → UNREACHABLE. He does not guess his body.
  - condition: no route exists to the goal
    fallback:  NoRoute{reason}; Executive may say so honestly or stay silent. Never leap "to try".
  - condition: a leg fails (no ACK within expected_ms, or `collided`)
    fallback:  re-read position from the UP event, re-plan from where he ACTUALLY is, decrement that
               route's confidence (Ch.4). Never assume the leg succeeded (ADR-Exec-003).
  - condition: eLo's own surface closes mid-route
    fallback:  Unity's bounded reflex re-attaches and emits `resurfaced`; the brain re-plans from the
               real position. The reflex must not choose a new destination.
  - condition: presence register forbids the goal
    fallback:  the goal is deferred, not queued-and-fired-later-loudly. Silence is a valid outcome.
  - condition: Unity offline
    fallback:  the faculty still reasons and can answer "can I reach that?" honestly; it commands nothing
               and claims nothing happened.
```

## 2.6 Faculty Lifecycle

Universal lifecycle (`Volume_V/CONTRACTS.md` §3). Notes:

```
INITIALISING → load body-schema constants for THIS embodiment; attach to world-state + perception reads;
               load route memory (Ch.4). No sensor is opened directly.
ACTIVE       → holds the last map + spatial_state; answers reachability queries; commands nothing.
PROCESSING   → build DesktopWorldMap → classify affordances against BodySchema → (goal present?)
               check register → reachable() → plan_route() → validate (peek + landing + fit)
               → emit route to Vol XI → await ACK per leg
   ├─ leg ACK'd        ─► advance; update spatial_state from the body's reported position
   ├─ leg failed/no ACK ─► ERROR_RECOVERY: re-read UP, re-plan from real position, lower confidence
   └─ reflex event      ─► re-plan from real position (never continue the stale plan)
LEARNING/UPDATING → (integration window ONLY) write verified outcomes; adjust route familiarity,
                    risk estimates and confidence. Ch.4 owns the rules. NEVER identity/values/truth.
STABLE → ACTIVE
```

**Lifecycle rule (MUST):** `PROCESSING` never blocks on the body. Legs are dispatched and ACKs are read on
subsequent turns/ticks. A turn must never wait for a jump to finish.

## 2.7 Message Envelope Binding

Per `Volume_V/CONTRACTS.md` §2, and the DOWN/UP channel contract in `UNITY_ELOOS_IO_CONTRACT.md`
(**no new files** — a route is a *field inside `move_command`*, not `movement.json`).

```jsonc
{
  "id": "uuid",
  "sender": "SpatialFaculty",
  "receiver": "MotorCortex",
  "priority": "normal",
  "context": {
    "conversation_id": "", "relationship_state": "", "environment_state": "desktop",
    "significance": 0.0,
    "memory_instruction": { "store": true, "priority": "low" }   // route outcome → Ch.4
  },
  "payload": {
    "type": "route",
    "body": {
      "goal": { "kind": "reach_surface", "surface_id": "chrome:1", "why": "notification appeared" },
      "legs": [
        { "verb": "APPROACH", "to": {"surface_id":"vscode:1","anchor":{"x":1180,"y":300}},
          "precondition": [], "cost": 12.0, "expected_ms": 900 },
        { "verb": "PEEK",     "to": {"surface_id":"vscode:1","anchor":{"x":1240,"y":300}},
          "precondition": [], "cost": 2.0,  "expected_ms": 400 },
        { "verb": "LEAP",     "to": {"surface_id":"chrome:1","anchor":{"x":1330,"y":290}},
          "precondition": ["PEEK"], "cost": 18.0, "expected_ms": 700 }
      ],
      "total_cost": 32.0, "risk": 0.18, "confidence": 0.62,
      "rationale": ["gap 61px < max_jump_d 75px", "landing width 240px > width_px 48px",
                    "register=FREE", "route used 4× before, 4 verified arrivals"]
    }
  },
  "confidence": 0.62,
  "expires": "<ts + sum(expected_ms) + slack>",
  "trace": ["SpatialFaculty@ts"]
}
```

**Binding rules (MUST):**
- `sender` MUST be `SpatialFaculty`. A route from any other sender is invalid and must be rejected by
  Vol XI — this is the mechanical enforcement of "one owner of spatial reasoning."
- Every `LEAP` leg MUST carry `precondition: ["PEEK"]`, and a `PEEK` leg MUST precede it. Validation
  rejects the envelope otherwise.
- `expires` is mandatory — a route is perishable. The world moves; a stale route must be dropped and
  re-planned, never resumed.
- `rationale` MUST cite verified facts (measured numbers, register, history). It is never spoken
  unprompted.
- **No new channel file.** The route travels DOWN inside `blender/blender_state.json → move_command`;
  ACKs and events come UP inside `blender/unity_events.json`. Adding `movement.json` is forbidden by the
  IO contract.

## 2.8 Acceptance Tests

### Functional
```
FT-1  "Can I reach that?" is arithmetic, not animation
  Given:  gap = 82px, BodySchema.max_jump_d = 75px
  When:   reachable() is asked
  Then:   verdict = UNREACHABLE (direct), margin = -7, blocked_by names the numbers
          AND no LEAP leg is emitted

FT-2  Unreachable-direct routes around, it does not refuse and does not leap
  Given:  FT-1's world, and a legal descent via the left wall and bottom edge
  Then:   a multi-leg Route is produced (SLIDE/DROP → APPROACH → CLIMB), executed, and arrival ACK'd
          (David example #2, verbatim)

FT-3  Peek before every jump (hard precondition)
  Given:  any route containing a LEAP
  Then:   a PEEK leg immediately precedes it AND envelope validation rejects a route without it

FT-4  The whole window is walkable, behind included
  Given:  a target reachable only by passing behind a front window
  Then:   the route uses a GO_BEHIND affordance and eLo re-emerges correctly stacked in z-order

FT-5  Safe landing is verified, not hoped
  Given:  a candidate landing narrower than BodySchema.width_px
  Then:   that affordance is available:false and no leg targets it

FT-6  Presence gates before planning
  Given:  register = PERIPHERAL (David typing)
  When:   an exploration goal arrives
  Then:   NO route is planned (not planned-then-cancelled) and nothing is said

FT-7  NoRoute is honest
  Given:  a goal with no legal route
  Then:   NoRoute{reason} is returned; eLo does not move and does not claim to have arrived
```

### Stability
```
ST-1  Stale geometry does not become a plan
  Given:  Vol XV desktop domain status = stale
  Then:   map.confidence drops, no cross-surface route is planned, he stays on his current surface

ST-2  Unknown body capability blocks, never guesses
  Given:  max_jump_d = None
  Then:   every GAP_LEAP is available:false; verdict = UNREACHABLE; no leap is attempted

ST-3  Mid-route world change forces a re-plan
  Given:  the target window closes after leg 1 ACKs
  Then:   the route expires, the brain re-plans from the ACK'd position, and no leg targets the dead surface

ST-4  Reflex is reported and re-planned from
  Given:  eLo's own surface closes mid-route and Unity's safety net re-attaches him
  Then:   a `resurfaced` event arrives UP AND the brain re-plans from the real position
          AND Unity did not choose a new destination

ST-5  No ACK means no belief
  Given:  a LEAP leg with no `<verb>_complete` within expected_ms
  Then:   the leg is treated as failed, position is re-read, route confidence decreases,
          and eLo never says he crossed
```

### Integration
```
IT-1  One owner — mechanical proof
  Given:  the running system
  Then:   every move_command written DOWN has sender = SpatialFaculty
          AND EloDesktopNav produces no traversal that was not commanded
          AND desktop/spatial_state.py exposes no route-selection entry point
  (This is the executable form of Ruling D-XIII-1.)

IT-2  Perception → World State → Spatial → Motor → belief
  desktop/spatial_state.py (sensor) → PerceptionFaculty (XII) → LiveWorldState (XV, frozen)
        ↓
  SpatialFaculty: map → affordances → reachability → route
        ↓  move_command (DOWN)
  Unity executes legs → <verb>_complete (UP)
        ↓
  Executive belief updates → only now may eLo speak the traversal
  Assert: removing EloDesktopNav's local route SELECTION changes no correct traversal — it only
          removes a second decider.

IT-3  Imagination cannot bend physics
  Given:  the Imagination Overlay renders a gap as "a canyon needing courage"
  Then:   the gap's measured width, the reachability verdict and the route are byte-identical to
          the same world without the overlay
```

## 2.9 Open Questions (flagged for Chief Architect / David)

- **OQ-2.1 (David L3 — this retires live behaviour).** Ruling D-XIII-1 demotes `EloDesktopNav._route` from
  decider to executor. That is a change to something currently working on David's machine. Confirm the
  sequencing: extend `move_command` to carry a route **first**, prove parity, **then** remove local
  selection — never both at once.
- **OQ-2.2** Where does `BodySchema` physically live — inside the Self Model (ADR-Exec-004) with the
  Spatial Faculty reading it, or inside the faculty? Recommend **Self Model owns it**, faculty reads it,
  so the robot embodiment inherits it for free (Ch.5) and there is one answer to "how big am I."
- **OQ-2.3** Route granularity DOWN: full route in one `move_command`, or leg-at-a-time with an ACK
  between? Recommend **full route down, leg-at-a-time ACK up** — the body knows the whole plan (so motion
  blends naturally) while the brain still verifies each step and can abort.
- **OQ-2.4** Should `EloDesktopNav` be allowed to *propose* candidate routes UP (it has cheap local
  geometry), with the brain selecting? This is legal under brain>body>brain (proposing ≠ deciding) but
  adds a second implementation of the same maths. Recommend **no** for v1 — one planner — and revisit only
  if latency demands it.
- **OQ-2.5** `safety_margin` on reachability: fixed px, or a fraction of `max_jump_d` scaled by
  `confidence` (Ch.4)? Recommend the latter — it is how "he's got better at that jump" becomes visible
  without any new mechanism.

## 2.10 Implementation Notes (for the Builder — relayed, not executed here)

- Build `faculties/spatial/spatial_faculty.py` (NEW). It reads; it opens no sensor.
- **Do not** modify `world/world_state.py` (game world graph, different world — Ch.5).
- `desktop/spatial_state.py`: keep `WindowBounds`, `EloSpatial`, `distance_to`, `nearest_windows`,
  `find_window`. Retire its route-planning role and correct its docstring claim *"plans routes."*
- Reuse, never duplicate: `PeekPitch` (edge check), the WO-024 occlusion (`7bab6af`) for `GO_BEHIND`,
  the eLo-Planet verb *feel* (reference-not-clone, Vol XI Ch.2).
- Respect the read-merge-write rule for `blender_state.json`; the route is a field inside `move_command`.
- Compose with the live guards: WO-074-F (height-based jump clamp → route, don't leap), WO-092
  (wall-jump is the intended answer to "too far"), WO-075 (gravity/landing).
- **No regressions** (WO-049 build rule 4): perch · roam · drag · click-through · gun-runoff all keep
  working. This is a build-time acceptance check.
- 049-B1 is the phase; P0 (eLo Presentable v1) is its prerequisite.

## 2.11 References

- `_intake/SOURCE_2026-08-10_roam_os_vision.md` §1–3, §7 and `_intake/SOURCE_2026-08-10_brain_body_brain_loop.md`
  — **VERBATIM primary sources. Read them; this chapter references them and never replaces them.**
- `engineering/work_orders/WO-049_Desktop_World_SelfAware_Parkour.md` — the epic; §THE SPATIAL FACULTY,
  Track A/B split, Movement Grammar, affordances, body schema, 049-B1, build rules 1–5.
- `docs/architecture/AUDIT_INTENT_self_embodiment_2026-08-10.md` §1.1–1.2, C-5 — the ownerless-question
  finding and the three-navigator breach.
- `ARCHITECTURAL_PRINCIPLES.md` — Affordance Before Action · Situated Self · Embodied Cognition ·
  Embodied Truth · Reality Before Narrative · verified capability becomes instinct.
- `UNITY_ELOOS_IO_CONTRACT.md` — channels by direction, not topic; no new files.
- `Volume_XII/` (Perception, sibling) · `Volume_XV/` (frozen world; §1.2 correction owed) ·
  `Volume_XI/` (Motor Cortex) · `Volume_XIII/01,03,04,05`.
- Code: `desktop/spatial_state.py`, `world/world_state.py`, `blender_bridge/state_writer.py`
  (`move_command`), Unity `EloDesktopNav` / `DesktopBuddy.cs`.

---

```
Chapter 2 — The Spatial Faculty
Status: READY FOR REVIEW
Implementation: PENDING (faculties/spatial/ NEW — 049-B1)
Owns: desktop world map · surface graph · affordances · body schema · reachability · route planning ·
      movement cost · safe landing · the peek precondition
Ruling: D-XIII-1 — one owner of spatial reasoning (proposed; David L3 required)
Faculty Contract: Included · Lifecycle: Included · Envelope: Included (route inside move_command, no new file)
Acceptance Tests: FT ×7, ST ×5, IT ×3 · Open Questions: 5 (1 David L3)
```

READY FOR REVIEW
