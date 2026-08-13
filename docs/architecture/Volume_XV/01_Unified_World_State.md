---
chapter: 1
title: "The Unified World State — One World, Read Once"
volume: XV
status: READY FOR REVIEW
version: 0.1.0
owner: David Charles
architect: Claude (Architecture Agent)
implementation: PENDING
audit_status: OPEN
received: 2026-07-27
dependencies:
  - architecture/16_runtime_contracts.md (CognitiveState — what World State contributes to)
  - Volume_V/CONTRACTS.md (envelope, lifecycle, base contract)
  - Volume_XII (Perception System — supplies the raw observations, sibling)
---

# Chapter 1: The Unified World State

## 1.0 Purpose

Every faculty needs to know *what is true in David's world right now* — what app is
focused, what's playing, what time it is, what the weather is, whether he's present.
Today each faculty finds that out its own way, at its own time, from its own source.
The result is that two faculties in the same turn can believe different things about
the world.

The **Unified World State** ends that. It is one typed object, `LiveWorldState`,
**assembled once per turn from all sensors and frozen**, that every faculty reads. One
world, read once.

This is **Architecture Audit gap #2**. The fix named there is `world/live_world_state.py`.

## 1.1 Principle

Three rules govern the world model. They are constraints on every faculty.

**1.1.1 One world per turn.** The world is sampled once, at the top of the turn, into a
single object. No faculty re-queries a sensor mid-turn. If it isn't in `LiveWorldState`,
the faculty does not know it this turn. (This is what removes the race conditions and
stale-data drift the Audit flags.)

**1.1.2 Frozen after assembly.** Like `CognitiveState` (`16_runtime_contracts.md`), the
`LiveWorldState` is immutable once assembled. Faculties read; none writes. The world
does not change *underneath* a turn.

**1.1.3 Every field carries its freshness.** The world is sensed asynchronously (a
weather poll is minutes old; the frontmost app is milliseconds old). So every domain
carries a timestamp and a confidence. A faculty reasoning on stale data must be able to
*know* it is stale. Absence of a signal is represented explicitly, never faked.

## 1.2 What this is NOT

> ⚠️ **CORRECTION NOTE — 2026-08-10.** The paragraph below (retained verbatim as the
> as-written text) is **stale on two counts**, both found by the 2026-08-10 audits
> (`AUDIT_MASTER_2026-08-10.md` §3; `AUDIT_INTENT_self_embodiment_2026-08-10.md`). It
> mis-describes `world/world_state.py`, **and** — more seriously — by excluding geometry from
> the World Model with no faculty named as geometry's owner, it **institutionalised the split
> that lets the Unity navigator decide routes locally.** §1.2.1 and §1.2.2 correct both. The
> exclusion itself is *kept* — it was the right call — but it is no longer an exclusion into
> nowhere.

**As written (retained, then corrected below):**

> `world/world_state.py` already exists — it is the **spatial** node graph Unity uses for
> navigation and presence movement. That is a different object with a different consumer.
> This chapter defines the **cognitive** world state (`world/live_world_state.py`, new).
> Do not merge them; do not overload the name "World State" across both (Cognitive
> Principle: naming is architecture).

### 1.2.1 Correction 1 — `world/world_state.py` is the eLo Planet game world graph

It is **not** "the spatial node graph Unity uses for navigation and presence movement" and it
is **not a desktop planner at all.** Read plainly (Verify-Before-Claim, 2026-08-10): its own
header says *"eLo Planet persistent world state — converts memory snapshots into a spatial node
graph for eLo Planet."* Its node types are `universe_entity` (eLo, Chunk, K-7, Core,
Sugarcore), `concept`, `project`, `interaction`; its inputs are `core/memory_engine.py` and
`core/visual_memory.py`. It is a **memory→landmark graph for the game embodiment**, not a
desktop-navigation structure.

The practical consequence: the sentence above was read as *"desktop geometry already has an
owner, elsewhere"* — and it does not. **Vol XIII Ch.2 §2.2.2 names this description stale and
asks this volume's owner to correct it. This is that correction.**

Everything else in the as-written paragraph stands: **do not merge the two objects**, and do
not overload the name "World State" across both. `LiveWorldState` (cognitive, per-turn, frozen)
and the eLo Planet graph (game, persistent, memory-derived) remain distinct.

### 1.2.2 Correction 2 — geometry is EXCLUDED from this object but OWNED by Volume XIII

**The Spatial Faculty (`Volume_XIII/02_The_Spatial_Faculty.md`) owns spatial reasoning.** It is
the single answerer of *"can I reach that?"* and *"how do I get there?"*, and it is the only
component permitted to answer them (Vol XIII Ch.2 §2.2, D-XIII-1). Its home is
`faculties/spatial/spatial_faculty.py` (NEW — WO-049 phase 049-B1).

**The relationship, stated — this is what §1.2 previously left blank:**

```
   PERCEPTION (Vol XII)            ← senses window geometry, events; never reasons
        │
        ▼
   WORLD STATE (this volume)       ← holds LIVE WORLD FACTS, frozen once per turn:
   LiveWorldState                    what app is frontmost, its window bounds, what's playing,
        │                            who is present, what time it is, freshness of each.
        │                            It is a READING of the world. It plans nothing.
        ▼
   SPATIAL FACULTY (Vol XIII Ch.2) ← REASONS OVER GEOMETRY against the frozen world:
        │                            surface graph · affordances · body schema · reachability
        │                            · route selection · cost · landing. It decides the route.
        ▼
   MOTOR CORTEX (Vol XI)           ← carries the chosen legs DOWN; carries ACK/events UP
        ▼
   BODY (Unity EloDesktopNav)      ← EXECUTES the legs it was given + bounded reflexes only.
                                     It does NOT choose the traversal. (brain > body > brain)
```

**The rule (MUST):**

- **World State holds live world facts; the Spatial Faculty reasons over geometry.** The split
  is *facts vs. reasoning*, **not** *world vs. space*. Space is emphatically part of eLo's
  world; what this object excludes is the **route planning over it**, because planning is
  reasoning and this object does no reasoning about anything (§1.5: "context, not command").
- The Spatial Faculty **reads the frozen `LiveWorldState`** and the `PerceptionResult`; it MUST
  NOT re-sense (Vol XIII §2.1.5 — no `osascript`, no Unity poll, no screenshot). So geometry
  that the faculty needs must reach it **through** this object's `desktop` / `environment`
  slices and through Vol XII — never by the faculty going around it.
- **No local script may choose a traversal** (David, verbatim: *"the body only SENSES and ACTS
  and reports its state back UP… no local driver deciding what eLo does"*).
  `EloDesktopNav._route` currently selects traversals inside the body; Vol XIII Ch.2 §2.2.2
  rules that it becomes an executor. **This volume must not be cited as the licence for that
  local decision** — which is exactly how the uncorrected §1.2 was functioning.
- `desktop/spatial_state.py` is a **sensor with geometry helpers** (distances, nearest-window
  ordering, window lookup) feeding this object via Perception. Its file header's claim that it
  *"plans routes"* is wrong; route selection lives in the faculty (Vol XIII §2.2.1).

**Open — for the owning seat + CA (not decided here):** whether the desktop **window-bounds
geometry** the Spatial Faculty needs should be carried as fields on the existing `desktop`
slice, or as a twelfth typed domain slice. Either satisfies the rule above; the choice is a
schema decision for Ch.2's owner, and it is **not** a licence to re-introduce route *planning*
into this object under either shape.

## 1.3 The LiveWorldState Object

`LiveWorldState` is a container of eleven typed **domain slices** (schematised in Ch.2)
plus assembly metadata. It contributes to `CognitiveState` and is read by the Executive
and every faculty.

```
LiveWorldState (frozen):
  # --- the eleven Bible domains (each a typed slice — see Chapter 2) ---
  desktop:      DesktopState      # frontmost app, window title, active surface
  user:         UserState         # present/away, register, focus/idle, attention target
  unity:        UnityState        # avatar surface status, presence.json (present/away)
  browser:      BrowserState      # active tab domain/title, visibility
  files:        FilesState        # recent/open files, active project dir
  internet:     InternetState     # connectivity, reachable services
  music:        MusicState        # Spotify: track, artist, playing (blender_state.json.spotify)
  calendar:     CalendarState     # next event, in-meeting, free/busy
  environment:  EnvironmentState  # OS, machine, screen-record perm, vision.active
  time:         TimeState         # now, local tz, part-of-day, day-of-week
  weather:      WeatherState      # condition, temp, location (AccuWeather)

  # --- assembly metadata ---
  assembled_ts:  float            # when this snapshot was taken
  turn_id:       string
  domain_health: { domain: {fresh_ts, confidence, source, status} }   # per-domain freshness
  degraded:      [domain]         # domains that fell back to default this turn
```

**Object rules (MUST):**

- Each domain slice is independently typed and independently degradable. One domain
  failing (weather API down) never blocks the others or the turn.
- `domain_health` is mandatory: every domain reports `fresh_ts`, `confidence 0.0–1.0`,
  its `source`, and `status ∈ {live, cached, stale, absent}`. This is how §1.1.3 is
  enforced.
- A domain that cannot be sensed is `status: absent` with a neutral default value —
  **never a fabricated value** (aligns with the anti-fabrication discipline in
  `17_memory_update.md` / `runtime/prompt_builder.py`).

## 1.4 Assembly — Once Per Turn

```
assemble_world_state(turn_id) -> LiveWorldState (frozen):
    for each domain:
        read from its sensor/cache (never block > budget_ms)
        stamp fresh_ts, confidence, source, status
        on timeout/error → default value, status=absent|stale, add to degraded[]
    return freeze(LiveWorldState(...))
```

**Assembly rules (MUST):**

- Assembly runs **once, at the top of the turn**, before faculties reason — in the
  spine this is a `CognitiveState` contributor (see `16_spine_runtime.md` §6 assembly).
- Assembly is **bounded**: each domain read has a time budget. A slow sensor yields its
  last cached value with `status: stale`, never delays the turn. Fast sensors (time,
  frontmost app) are read live; slow sensors (weather) are read from their background
  poll's cache (see Ch.2 for per-domain cadence).
- Assembly **reads, never triggers**: it does not kick off a screenshot or a network
  call inline. It consumes what the background loops and Perception Faculty (Vol XII)
  have already produced. (The vision loop, spotify poll, etc. run as their own daemons —
  `CO_WORKING_GUIDE.md` §6.)
- Absent/stale domains are collected in `degraded[]` so any faculty (and the Audit) can
  see the world was partially sensed this turn.

## 1.5 Read Discipline

- Faculties read `LiveWorldState` from the frozen `CognitiveState`. They **must not**
  call `desktop/window_state.py`, `spotify_agent`, weather, etc. directly — that is the
  exact ad-hoc pattern this volume removes.
- A faculty that needs a freshness guarantee checks `domain_health[domain].status`
  before relying on a value (e.g. don't reference "now playing" if music is `stale`).
- The Executive treats `LiveWorldState` as **context, not command**: the world informs
  the decision; it never *is* the decision (One Brain — the Executive still decides once).

## 1.6 Faculty Contract

```
Faculty:
  name:            WorldStateFaculty
  version:         1.0.0
  purpose:         Assemble one frozen LiveWorldState per turn from all sensors and
                   contribute it to CognitiveState, so every faculty reasons over an
                   identical, freshness-annotated world.
  contributes_to:  CognitiveState
  runs_in:         response-path (assembly at top of turn)

Inputs:
  - type:        sensor_read (per domain)
    source:      desktop/window_state.py, blender_state.json[vision|spotify],
                 tools/accuweather_agent, calendar agents, browser/visibility,
                 desktop/file_drop_handler, presence.json (Unity), os/time
    required:    false (each individually — the set degrades gracefully)
    description: The latest available reading for each of the eleven domains.
  - type:        perception_result
    source:      Perception Faculty (Volume XII)
    required:    false
    description: Transformed observations (e.g. what's on screen) feeding desktop/user/browser.

Outputs:
  - type:        live_world_state
    destination: CognitiveState (frozen) → Executive + all faculties
    description: Eleven typed domain slices + per-domain freshness/health.

Dependencies:
  - faculty: PerceptionFaculty (soft — Vol XII; without it, vision-derived domains degrade)
  - background loops (soft): vision_loop, spotify poll, weather poll, project_knowledge

Failure Modes:
  - condition: a domain sensor times out or errors
    fallback:  last cached value with status=stale, or neutral default with status=absent;
               add to degraded[]; never block the turn.
  - condition: all sensors unavailable (cold start)
    fallback:  minimal world (time from OS clock; everything else absent); turn proceeds.
  - condition: a faculty tries to read an absent domain
    fallback:  it receives the neutral default + status=absent, and must not fabricate.
  - condition: assembly exceeds total budget
    fallback:  freeze with whatever is ready; remaining domains marked stale/absent.
```

## 1.7 Faculty Lifecycle

Universal lifecycle (Volume_V/CONTRACTS.md §3). Notes:

```
INITIALISING → register the eleven domain readers; attach to background-loop caches
ACTIVE       → idle, subscribed; caches updated by daemons out-of-band
PROCESSING   → assemble_world_state() at top of turn → freeze → contribute to CognitiveState
   └─ domain fault ─► ERROR_RECOVERY (that domain only) → default/stale → continue
LEARNING/UPDATING → (integration window) tune per-domain freshness budgets / cadence
STABLE → ACTIVE
```

The faculty **has no personality-affecting learning**; its only `UPDATING` is tuning
sensor budgets/cadence. It never proposes a personality delta.

## 1.8 Message Envelope Binding

Per CONTRACTS.md §2.

```jsonc
{
  "id": "uuid",
  "sender": "WorldStateFaculty",
  "receiver": "*",                 // world is part of CognitiveState → broadcast
  "priority": "normal",
  "context": {
    "conversation_id": "", "relationship_state": "", "environment_state": "",
    "significance": 0.0,
    "memory_instruction": { "store": false, "priority": "" }
  },
  "payload": { "type": "live_world_state", "body": { /* LiveWorldState */ } },
  "confidence": 0.0,               // overall assembly confidence (min across live domains)
  "expires": "<assembled_ts + turn_ttl>",   // a world snapshot is valid for its turn only
  "trace": ["WorldStateFaculty@ts"]
}
```

Binding rules: `sender` MUST be `WorldStateFaculty`; `expires` MUST be set (a world
snapshot is inherently perishable — a stale one must be dropped, never reused across
turns); per-domain freshness lives in `payload.body.domain_health`, not the envelope.

## 1.9 Acceptance Tests

### Functional

```
FT-1  One assembly per turn
  Given:  a turn begins
  When:   faculties reason
  Then:   exactly one LiveWorldState was assembled and frozen before any faculty ran
          AND no faculty called a sensor module directly

FT-2  Freshness is carried
  Given:  weather last polled 8 minutes ago, frontmost app read this turn
  When:   LiveWorldState assembles
  Then:   domain_health.weather.status ∈ {cached, stale}, desktop.status = live
          AND both carry fresh_ts + confidence

FT-3  Absent domain is explicit, not faked
  Given:  no music is playing / Spotify creds absent
  When:   assembly runs
  Then:   music.status = absent with a neutral default
          AND no fabricated track/artist appears anywhere downstream

FT-4  All faculties see the same world
  Given:  two faculties both read the frontmost app in one turn
  When:   they reason
  Then:   they read the identical value from the frozen LiveWorldState
```

### Stability

```
ST-1  One domain down never blocks the turn
  Given:  the weather API times out
  When:   assembly runs
  Then:   weather → stale/absent, added to degraded[], all other domains present,
          turn completes within budget

ST-2  Cold start
  Given:  first turn after boot, no background poll has run yet
  When:   assembly runs
  Then:   time is live (OS clock), all other domains absent, turn proceeds

ST-3  No mid-turn mutation
  Given:  a background poll updates a cache mid-turn
  When:   a faculty reads the world
  Then:   it still sees the frozen snapshot from top-of-turn (update applies next turn)

ST-4  Perishability
  Given:  a LiveWorldState from a previous turn
  When:   a new turn begins
  Then:   the prior snapshot is expired (envelope.expires) and not reused
```

### Integration

```
IT-1  Sensors → World State → Cognition
  Perception Faculty (Vol XII) + background loops
        ↓  domain readings
  WorldStateFaculty  → LiveWorldState (frozen)
        ↓  in CognitiveState
  Executive + faculties reason on one world
        ↓
  Assert: removing a faculty's direct sensor call and routing it through LiveWorldState
          changes no correct output (only removes drift).

IT-2  Degraded-world honesty
  Given:  vision offline + calendar offline
  When:   the turn runs
  Then:   degraded=[unity?, environment.vision, calendar]; eLo does not claim to see
          the screen or know the schedule; anti-fabrication holds.
```

## 1.10 Claude Implementation Notes

- Build `world/live_world_state.py` as a frozen dataclass of the eleven slices +
  `domain_health`. **Do not** modify `world/world_state.py` (the **eLo Planet game** graph —
  §1.2.1; it is not a desktop planner).
  > **Note 2026-08-10 (audit):** `WO-CANON-XV` orders this file built "(NEW)" — **it already
  > exists (379 lines).** Extend it; do not fork a second one (CHECK-BEFORE-BUILD).
  > (`AUDIT_MASTER_2026-08-10.md`.)
- **Do not add route planning to this object.** Geometry may be *carried* here as world fact;
  reasoning over it belongs to the Spatial Faculty (Vol XIII Ch.2) — §1.2.2.
- Assembly is a `CognitiveState` contributor wired at top-of-turn in
  `runtime/spine/spine.py` (see `16_spine_runtime.md` §6). It **reads caches**, it does
  not trigger sensors — the vision loop / spotify poll / weather poll already populate
  those (`CO_WORKING_GUIDE.md` §6).
- Move each faculty's direct sensor call to read from `LiveWorldState` incrementally
  (one domain at a time), asserting behaviour parity (FT-4 / IT-1) at each step.
- Respect the read-merge-write rule for `blender_state.json` when sourcing the `vision`
  and `spotify` blocks — read only; never write from here.
- Per-domain schemas, sources, and cadences are in Chapter 2.

## 1.11 Architecture References

- `architecture/ARCHITECTURE_AUDIT.md` — gap #2 (Unified World State).
- `16_runtime_contracts.md` — CognitiveState (frozen, one cognition).
- `16_spine_runtime.md` — where world assembly sits in the turn.
- `Volume_XII` — Perception System (supplies raw observations; sibling).
- `Volume_XIII/02_The_Spatial_Faculty.md` — **owner of spatial reasoning** ("can I reach that?"
  / "how do I get there?"). This volume holds live world facts; that faculty reasons over
  geometry. See §1.2.2. (Added 2026-08-10.)
- `Volume_XI` — Motor Cortex (the DOWN command + UP ACK channel routes travel through).
- `Volume_V/CONTRACTS.md` — envelope, lifecycle, base contract.
- Code: `world/world_state.py` (**eLo Planet game graph** — do not touch, and note §1.2.1: it
  is not a desktop planner), `desktop/spatial_state.py` (sensor + geometry helpers, not a
  route planner), `desktop/window_state.py`,
  `blender/blender_state.json` (vision/spotify blocks), `tools/accuweather_agent.py`,
  calendar agents, `CO_WORKING_GUIDE.md` §6 (background loops).

---

```
Chapter 1 — The Unified World State
Status: READY FOR REVIEW
Files: Volume_XV/01_Unified_World_State.md
Faculty Contract: Included
Lifecycle State Machine: Included
Message Envelope: Included (canonical nine-field, perishable)
Acceptance Tests: Included (FT ×4, ST ×4, IT ×2)
Architecture References: Included
Closes Audit gap: #2 (Unified World State)
CORRECTED 2026-08-10 (§1.2): world/world_state.py is the eLo Planet GAME graph, not a desktop
  navigation planner — the old description was stale. Geometry stays excluded from this object,
  but is now OWNED by the Volume XIII Spatial Faculty rather than excluded into nowhere:
  World State holds live world facts; the Spatial Faculty reasons over geometry.
  Removes this volume's role in institutionalising the Unity-navigator-decides-locally split.
```

READY FOR REVIEW
