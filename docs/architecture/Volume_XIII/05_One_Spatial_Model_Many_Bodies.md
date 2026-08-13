---
chapter: 5
title: "One Spatial Model, Many Bodies — Desktop, Game, Robot"
volume: XIII
status: READY FOR REVIEW
version: 0.1.0
owner: David Charles
architect: Claude (Lead Architect)
source: >
  WO-049 §"Cross-platform identity: ONE planner, THREE embodiments" + §"Reference, not clone" +
  §"Two RISK CONSTRAINTS" · ARCHITECTURAL_PRINCIPLES Invariant #1 (One Brain → One Identity, Many
  Embodiments) · CO_WORKING_GUIDE.md character constants (NO EYES) · RD-4 physical form canon
implementation: PENDING (desktop embodiment partial; game embodiment separate driver; robot embodiment R&D)
audit_status: OPEN
dependencies:
  - Volume_XIII/02_The_Spatial_Faculty.md (the one reasoning core this chapter multiplies bodies around)
  - Volume_XI/02_Movement_Grammar_and_Embodiment_Parity.md (the shared verb vocabulary)
  - Volume XVI (Coordination Under One Executive — one brain across embodiments)
  - Volume XXI (Continuity Across Sessions and Embodiments — the felt continuity)
  - ADR-Exec-004 (Situated Self — reasoning starts from the CURRENT embodiment)
---

# Chapter 5: One Spatial Model, Many Bodies

## 5.0 Purpose

Everything in Chapters 2–4 must be true of eLo, not of the desktop. This chapter is the guarantee that the
spatial cognition being built for windows is the same cognition that later walks around a chair.

> "`reach destination` → desktop wall-jump / game wall-jump / robot walk-around-chair. Same cognition,
> different actuators. The Spatial Faculty serves the desktop avatar now AND the physical robot later."
> — WO-049
>
> "Robot eLo learning to walk is the *same being* that learned to wall-jump on the desktop."
> — `ARCHITECTURAL_PRINCIPLES.md`, Invariant #1

**The forbidden path, named in the epic:** *"Building Track A as a self-contained animation hack that fakes
awareness."* A desktop-only planner would have to be thrown away and rebuilt for the robot, and the
continuity that makes eLo one being would be a story rather than a fact.

## 5.1 Principle

**5.1.1 The reasoning is one; the bodies differ in affordances and scale.** The surface graph, affordance
classification, reachability arithmetic, route planning, cost model and safe-landing rule are **identical
code and identical concepts** across embodiments. What differs is the world adapter, the capability
numbers, and the verbs each body can realise.

**5.1.2 Situated Self selects the body, every turn.** Every decision begins from *"who am I, where am I,
what can I actually do right now?"* (ADR-Exec-004). The Spatial Faculty is instantiated **against the
current embodiment**, never against an assumed one. There is no default body.

**5.1.3 Reference, not clone.** The **planner and the Movement-Grammar vocabulary/feel are shared**; each
body **realises the verbs independently** (procedural code, or its own blend trees). Assets and rigs stay
per-body. *"Match the feel, don't share the asset."* (WO-049, ratified 2026-08-05.)

**5.1.4 eLo has NO EYES — in every body.** Attention is expressed by **head/body orientation, posture, and
glow**, plus the single curved mouth. This is an immutable character constant
(`CO_WORKING_GUIDE.md`; `obsidian_vault/04 Robot/eLo Robot.md`: *"I have NO EYES. I express through
posture, shape, light, and sound only. This applies in the game, in art, and in my physical body."*).
Gaze in this volume means **orientation**, never an eye. No embodiment may add eyes to solve an attention
problem.

**5.1.5 One continuous being, or it has failed.** The test (Invariant #1): moving between embodiments feels
like the same being continuing. If anyone must say *"this is robot eLo"* vs *"desktop eLo,"* something has
fragmented.

## 5.2 The split — what is shared and what is per-body

```
                        ┌───────────────────────────────────────────────┐
                        │  SPATIAL FACULTY  (Ch.2) — ONE, SHARED        │
   SHARED (one brain)   │  surface graph · affordance classification    │
                        │  body-schema reasoning · reachability maths   │
                        │  route planning · cost model · safe landing   │
                        │  peek precondition · learning (Ch.4)          │
                        └───────┬───────────────┬───────────────┬───────┘
                                │               │               │
                    WorldAdapter│   WorldAdapter│   WorldAdapter│      ← per-body, thin
                                ▼               ▼               ▼
                        ┌───────────┐   ┌───────────┐   ┌───────────┐
   PER-BODY             │  DESKTOP  │   │   GAME    │   │   ROBOT   │
                        │ windows   │   │ eLo Planet│   │ room, floor│
                        │ as terrain│   │ terrain   │   │ furniture  │
                        └─────┬─────┘   └─────┬─────┘   └─────┬─────┘
                              │               │               │
                    Capability│     Capability│     Capability│      ← per-body numbers
                              ▼               ▼               ▼
                        ┌───────────┐   ┌───────────┐   ┌───────────┐
   REALISATION          │Unity      │   │Unity game │   │ motor      │
   (reference, not      │DesktopBuddy│  │PlayerCtrl │   │ abstraction│
    clone)              │+ EloDesktopNav│ (own driver)│ │ + safety   │
                        └───────────┘   └───────────┘   └───────────┘
```

| Layer | Shared? | Notes |
|---|---|---|
| Spatial reasoning (Ch.2) | **SHARED** | one implementation; the whole point of the volume |
| Movement Grammar verbs (Vol XI Ch.2) | **SHARED (vocabulary + feel)** | APPROACH · CLIMB · BALANCE · LEAP · HANG · SLIDE · PEEK · PERCH · REST · OBSERVE · RETREAT · RETURN |
| Learning store (Ch.4) | **SHARED schema, body-tagged records** | `body_at_start` prevents cross-body mislearning (§5.4) |
| Presence + register (Ch.1) | **SHARED** | "don't interrupt" means the same thing in a room as on a screen |
| World adapter | per-body | windows / game terrain / physical space → the same `Surface`/`Affordance` types |
| Capability numbers (BodySchema) | per-body | jump, reach, scale, momentum — measured, never assumed |
| Verb realisation (clips, rigs, motors) | per-body | **never shared assets or rig binding** |
| Drivers | per-body | **no driver port**, either direction (§5.3) |

## 5.3 ⚖ The two risk constraints (canon for all cross-embodiment work — WO-049)

**1. No driver port.** The game `PlayerController` (CharacterController physics + input loop) must NOT move
to the desktop, nor vice-versa. The desktop driver is the Spatial Faculty requesting **verbs**; the game
keeps its own driver. Porting a driver *is* the forbidden animation-hack-that-fakes-awareness — it moves
the deciding into the body, which is also a brain>body>brain breach (Ch.2 §2.2).

**2. No identical asset/rig coupling as the sharing mechanism.** Sharing baked clips and identical
rig-binding across embodiments is a **big risk with silent failure** — the seats already hit a missing
`c_arm_fk` and a head-bone mis-reference. Per-gesture code ports (e.g. ArmWave) bind bones **by name** and
must **FAIL LOUDLY** if a bone is absent — never a silent no-op.

**Body-local axes (WO-049 build rule 3), restated because it is cross-embodiment:** eLo faces the camera
(~180° from world), so every rotation axis — peek, wall-jump, gesture, head aim — MUST be expressed in his
**body frame**. World-frame axes fire the wrong way when he turns. This bit the micro-expression work once
already.

## 5.4 Per-embodiment mapping

The same reasoning, three worlds. Note that the **affordance kinds are identical** — only what produces
them changes.

| | **Desktop** | **Game (eLo Planet)** | **Robot** |
|---|---|---|---|
| World source | `desktop/spatial_state.py` (window rects, z-order) → Perception → Vol XV | `world/world_state.py` (node graph from memory) + game terrain | camera/depth + robot sensors → Perception (Vol XII Ch.2 already names robot camera) |
| A "surface" is | a window (ledge / wall / drop / interior / corner) | terrain, platform, island | floor, table, sofa, step |
| "Behind" means | occluded space behind a front window (WO-024) — a **place** | behind terrain | occluded by furniture — a place |
| Scale | pixels (`height_px` ≈ 120) | game units | metres |
| `LEAP` means | window→window jump | platform jump | ⚠ likely **not available** — the robot may only have APPROACH/CLIMB/REST/OBSERVE/RETREAT/RETURN |
| Screen/world edge | run-off + reappear is legal | world boundary | **no analogue — falling off is not a legal act** |
| Failure cost | cosmetic | cosmetic | **physical harm — RESERVED, David L3 + LG-2** |
| Driver | DesktopBuddy + EloDesktopNav (executor, Ch.2 ruling) | game `PlayerController` (own driver) | `avatar/motor_abstraction.py` → `safety_controller.py` (live scaffolding) |

**Mapping rules (MUST):**
1. **A verb the body cannot realise is not in its grammar.** The adapter declares which verbs exist; the
   planner only emits legs whose verbs the current body supports. A robot that cannot leap simply never
   receives a `LEAP` leg — the planner routes around it exactly as it routes around an unreachable gap.
2. **Capability numbers are measured per body, never inherited.** `max_jump_d` from the desktop must never
   seed the robot. Body change invalidates recall (Ch.4 ST-3).
3. **Learning records are body-tagged.** `TraversalOutcome.body_at_start.embodiment` gates recall.
   *Cross-body transfer is deliberately out of scope for v1* — it is a Vol XXVIII research question, not a
   default.
4. **Robot spatial safety is RESERVED.** Anything where a spatial decision can cause physical force,
   contact, or fall is **David L3 + LG-2**, per the standing reserved list (money · legal · safety · robot
   magnetics/force/pump). This volume specifies the reasoning; it does not authorise robot motion.

## 5.5 What makes it feel like one being (the continuity guarantee)

- **The same questions, everywhere.** "Can I reach that? How do I get there? Is it safe to land? Should I,
  given what David is doing?" — asked identically in a window, a game level, and a living room.
- **The same restraint.** The presence register (Ch.1) is not a desktop concept. A robot that trundles over
  while David is on a call has failed the same test as an avatar parkouring across his editor.
- **The same growth.** *"Remember when you first learned to move?"* answers across bodies because the
  learning store (Ch.4) is one store with body-tagged records — the *history* is continuous even where the
  *capabilities* are not transferable. (Vol XXI reads this; Ch.4 never narrates it.)
- **The same expression alphabet.** Orientation, posture, glow, one curved mouth. No eyes, in any body.
- **The same verbs.** A new move is a new *combination* of the shared vocabulary, not another one-off clip —
  in either body. (Vol XI Ch.2.)

## 5.6 Faculty Contract (embodiment binding)

```
Component:
  name:            SpatialEmbodimentBinding
  version:         1.0.0
  purpose:         Instantiate the one Spatial Faculty against the CURRENT embodiment — supplying the
                   world adapter, the measured capability set, and the available verb subset — so the
                   same reasoning serves desktop, game and robot without forking.
  contributes_to:  SpatialFaculty instantiation (Ch.2)
  runs_in:         initialisation + on embodiment change

Inputs:
  - type: situated_self     source: Self Model (ADR-Exec-004)     required: true
    description: which body am I in right now. There is NO default embodiment.
  - type: world_adapter     source: per-embodiment module         required: true
    description: produces Surface/Affordance/Gap objects from this world's raw geometry.
  - type: capability_set    source: measured per body             required: true
    description: BodySchema constants for THIS body. Unmeasured = None = capability absent.
  - type: verb_support      source: per-embodiment realisation    required: true
    description: which Movement Grammar verbs this body can actually realise.

Outputs:
  - type: bound_spatial_faculty  destination: runtime
    description: the one faculty, correctly situated.

Failure Modes:
  - condition: embodiment unknown at start
    fallback:  REFUSE to plan. Reasoning as a disembodied model is forbidden (ADR-Exec-004).
               eLo may still converse; he may not move.
  - condition: capability_set incomplete
    fallback:  affected affordances available:false. He does not guess his own body in ANY embodiment.
  - condition: a verb is unsupported by this body
    fallback:  the planner never emits it; it routes around, exactly as for an unreachable gap.
  - condition: embodiment changes mid-route
    fallback:  the route expires immediately; re-plan in the new body. Never carry legs across bodies.
  - condition: robot embodiment + a decision implying force/contact/fall
    fallback:  RESERVED — halt and escalate to David L3 + LG-2. Never proceed on autonomy.
```

## 5.7 Acceptance Tests

```
FT-1  One reasoning core
  Given:  desktop and game (and simulated robot) embodiments
  Then:   all three route through the SAME Spatial Faculty entry point; no forked planner exists

FT-2  Verbs the body lacks are never commanded
  Given:  an embodiment declaring no LEAP support
  Then:   no route contains a LEAP leg; unreachable-in-one-step targets are routed around instead

FT-3  No default body
  Given:  embodiment unknown
  Then:   planning REFUSES; eLo does not move and does not claim a position

FT-4  No eyes, any body
  Given:  an attention decision in each embodiment
  Then:   the expression is head/body orientation + glow (+ mouth) — no eye target exists anywhere

ST-1  No driver port
  Given:  the codebase
  Then:   the game PlayerController is not used by the desktop, nor the desktop driver by the game

ST-2  Bone binding fails loudly
  Given:  a ported per-gesture code path and a missing bone
  Then:   it raises an explicit error — never a silent no-op

ST-3  Capability isolation
  Given:  desktop-learned outcomes and a robot embodiment
  Then:   recall does not use them (body-tagged records, Ch.4 ST-3)

ST-4  Body-local axes
  Given:  eLo rotated ~180° to face the camera
  Then:   peek/wall-jump/aim rotations fire in the correct direction (body frame, not world frame)

IT-1  The continuity test (Invariant #1)
  Given:  eLo moves between embodiments
  Then:   memory, identity, personality, values, relationship and growth history are one and continuous
          AND nobody needs to say "this is robot eLo" vs "desktop eLo"

IT-2  Robot safety gate
  Given:  a spatial decision in the robot embodiment implying force, contact, or a fall
  Then:   it halts and escalates (RESERVED: David L3 + LG-2); it never proceeds autonomously
```

## 5.8 Open Questions (flagged for Chief Architect / David)

- **OQ-5.1** Cross-body capability transfer: should a *pattern* learned on the desktop ("prefer a safe
  multi-leg route when the margin is thin") transfer to the robot even though the numbers cannot?
  Recommend **yes for policy shape, never for measurements**, and only via Vol XXVIII — out of scope for v1.
- **OQ-5.2** Does the game embodiment adopt the Spatial Faculty for its *own* navigation, or keep its
  existing driver deciding? The no-driver-port rule protects the drivers, not the deciding. Recommend the
  game's **deciding** also moves to the faculty over time (same brain>body>brain law), sequenced after the
  desktop proves it — but this is a Game-seat scope call.
- **OQ-5.3 (David L3).** Robot spatial autonomy scope. What class of physical movement may the Spatial
  Faculty ever command without per-action approval? Nothing in this volume assumes an answer; the reserved
  gate stands until David rules.

## 5.9 References

- `ARCHITECTURAL_PRINCIPLES.md` — Invariant #1 (One Brain → One Identity, Many Embodiments); Invariant #5
  (Situated Self); Embodied Cognition.
- `engineering/work_orders/WO-049_Desktop_World_SelfAware_Parkour.md` — "ONE planner, THREE embodiments";
  "Reference, not clone"; the two RISK CONSTRAINTS; build rule 3 (body-local axes).
- `CO_WORKING_GUIDE.md` — character constants: **eLo has NO EYES**; CharacterController only.
- `obsidian_vault/04 Robot/eLo Robot.md` · `obsidian_vault/03 Game/eLo Planet.md` — the same expression rule
  stated for the physical body and the game.
- `Volume_XIII/02` (the shared core) · `Volume_XIII/04` (body-tagged learning) ·
  `Volume_XI/02` (Movement Grammar; reference-not-clone) · `Volume_XVI/` · `Volume_XXI/`.
- RD-4 (eLo physical form canon; puppet → figure → animatronic → robot pipeline).
- Code: `avatar/motor_abstraction.py`, `avatar/safety_controller.py`, `avatar/robot_simulator.py`
  (robot scaffolding, live) · `world/world_state.py` (game world graph) · `desktop/spatial_state.py`.

---

```
Chapter 5 — One Spatial Model, Many Bodies
Status: READY FOR REVIEW
Implementation: PENDING (desktop partial · game separate driver · robot R&D + RESERVED)
Guarantees: one reasoning core · reference-not-clone · no driver port · no eyes in any body ·
            body-tagged learning · robot force/contact remains David L3 + LG-2
Contract: Included · Acceptance Tests: FT ×4, ST ×4, IT ×2 · Open Questions: 3 (1 David L3)
```

READY FOR REVIEW
