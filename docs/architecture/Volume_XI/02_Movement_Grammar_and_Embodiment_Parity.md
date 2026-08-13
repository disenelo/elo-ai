---
chapter: 2
title: "Movement Grammar & Embodiment Parity — A Vocabulary, Not a Clip Library"
volume: XI
status: READY FOR REVIEW
version: 0.1.0
owner: David Charles
architect: Claude (Lead Architect)
source: >
  WO-049 §Movement Grammar + §"Reference, not clone" (ratified 2026-08-05) + §"Two RISK CONSTRAINTS" +
  build rule 3 (body-local axes) · _intake/SOURCE_2026-08-10_roam_os_vision.md §7 + "A few rules that keep
  it coherent" (VERBATIM) · _intake/SOURCE_2026-08-10_headaim_mouse_follow.md · CO_WORKING_GUIDE.md (NO EYES)
implementation: PENDING (verbs exist as WO prose and as per-body moves; not yet a channel-level vocabulary)
audit_status: OPEN
dependencies:
  - Volume_XI/01_Motor_Cortex_and_the_Body_Contract.md (the channel these verbs travel on)
  - Volume_XIII/02_The_Spatial_Faculty.md (the planner that composes routes out of these verbs)
  - Volume_XIII/05_One_Spatial_Model_Many_Bodies.md (the cross-embodiment guarantee)
  - Volume XVI (Coordination Under One Executive)
---

# Chapter 2: Movement Grammar & Embodiment Parity

## 2.0 Purpose

Chapter 1 defined the channel. This chapter defines **what travels on it** — and why a new move should be a
new *sentence*, not a new *clip*.

> "Think of the moves as a small shared vocabulary — **approach · climb · balance · leap · peek · perch ·
> rest · observe · retreat · return** — so a new move is a new combination of these, not another one-off
> clip. (That vocabulary is also how the desktop and the game stay 'the same eLo' without sharing rigs.)"
> — David, `_intake/SOURCE_2026-08-10_roam_os_vision.md` (VERBATIM primary source — read it)

WO-049 states the same thing as the architectural rule: *"Movement Grammar = a small vocabulary of
CONCEPTS… Every animation is choreography over these verbs, giving new moves a common language instead of
one-off clips."*

Without this, "spatial embodiment" degenerates into a clip list with a planner bolted on — which is the
failure the whole programme is built to avoid.

## 2.1 Principle

**2.1.1 Verbs are concepts, not animations.** `LEAP` is *"cross a gap to a landing"* — not a named
animation asset. Each body realises it however it can. The planner (Vol XIII Ch.2) composes routes out of
verbs and never names a clip.

**2.1.2 The vocabulary is closed and small.** Twelve verbs. New behaviour comes from **combination and
parameterisation**, not from extending the list. Growing the vocabulary is a canon change requiring review —
otherwise it silently becomes the clip library it replaced.

**2.1.3 Reference, not clone.** The **planner and the vocabulary/feel are shared**; each body **realises the
verbs independently** (procedural code, or its own blend trees). Assets and rigs stay per-body.
*"Match the feel, don't share the asset."* (WO-049, ratified 2026-08-05, correcting the earlier
"shared moveset/rig" wording.)

**2.1.4 Body-local axes.** eLo faces the camera (~180° from world), so **every** rotation axis — peek,
wall-jump, gesture, head aim — is expressed in his **body frame**. World-frame axes fire the wrong way when
he turns. (WO-049 build rule 3; the same class as the earlier micro-expression axis fixes.)

**2.1.5 No eyes, ever.** `OBSERVE`, `PEEK` and any attention verb are realised as **head/body orientation +
posture + glow**, plus the single curved mouth. No embodiment may add an eye channel to express attention.
(`CO_WORKING_GUIDE.md`: *"Character constants (immutable): eLo has NO EYES."*)

## 2.2 The vocabulary (twelve verbs)

| Verb | Concept (what it *means*) | Typical affordance (Vol XIII Ch.2) | Notes |
|---|---|---|---|
| **APPROACH** | close distance toward a target along a traversable surface | LEDGE_RUN | covers walk→jog→run as a continuum, never instant clip swaps |
| **CLIMB** | gain height against a vertical surface | WALL_CLIMB | bounded by `BodySchema.climb_height` |
| **BALANCE** | hold or traverse a narrow footing | BALANCE | expresses `footing = edge`; a state as much as a move |
| **LEAP** | cross a gap to a verified landing | GAP_LEAP | **requires a preceding PEEK — hard precondition** (§2.4) |
| **HANG** | hold on an edge below the standing plane | HANG | precedes SLIDE or a climb back up |
| **SLIDE** | descend a wall or run a bottom edge under control | SLIDE / DROP | the cheap way down; often the answer to an unreachable leap |
| **PEEK** | check what is beyond an edge before committing | PEEK | the `PeekPitch` behaviour; **mandatory before LEAP** |
| **PERCH** | settle on a high vantage and stay | PERCH | a destination verb, not a transit verb |
| **REST** | settle where he is, low energy, no intent to move | SIT / PERCH | pairs with `PresenceMode.RESTING` |
| **OBSERVE** | attend to something without moving to it | OBSERVE | head/body orientation + glow. **No eyes.** |
| **RETREAT** | withdraw from a position, keeping the world in view | — | not the same as leaving; he is still present |
| **RETURN** | come back to a prior position or to David | — | pairs with `return_command`; the other half of withdrawal |

**Vocabulary rules (MUST):**
- Every route leg carries exactly one verb (Vol XIII Ch.2 §2.3.6).
- **A body declares which verbs it supports** (Vol XIII Ch.5 §5.4). The planner never emits an unsupported
  verb; it routes around it. A robot with no `LEAP` simply never receives one.
- Verbs are **parameterised, not multiplied**: `APPROACH` at speed 0.3 vs 1.0 is the same verb, not
  `WALK`/`RUN`. Micro-intent, momentum and move-type continuity are *parameters*, which is why "walk →
  jog → run → leap → recover" reads as one body and not as clip swapping.
- Composite named moves (fire-jump, shoot-to-exit, wall-jump chimney) are **compositions** —
  `APPROACH + LEAP` with a body-specific realisation — never a thirteenth verb.

## 2.3 How a verb becomes motion (realisation, per body)

```
Vol XIII Ch.2 plans:      [ APPROACH, PEEK, LEAP ]        ← concepts. No asset named anywhere.
        │
Vol XI Ch.1 sends DOWN:   move_command.route[]            ← the channel. Still concepts.
        │
Per-body realisation:
   desktop  → DesktopBuddy verb handlers (roam nav hook, PeekPitch, ledge-hop, WO-024 occlusion)
   game     → eLo Planet blend trees + its OWN driver (PlayerController stays put)
   robot    → avatar/motor_abstraction.build_command_packet() → safety_controller → actuators
```

**Realisation rules (MUST):**
- **The realisation layer chooses the asset; the brain never does.** If a verb realisation needs a
  different clip on a slope than on a flat ledge, that is the body's business.
- **Realisation is not decision.** Picking *how* to render a commanded `LEAP` is legal. Deciding *whether*
  to leap, or leaping somewhere else, is a §1.7 violation.
- **The feel is shared, the assets are not.** The desktop and the game should look like the same creature
  moving; they must not share baked clips or rig binding.

## 2.4 The PEEK precondition (channel-enforced)

David's build rule 1, promoted from flavour to a contract:

> "**Peek before EVERY jump — hard precondition.** Not just 'peeks over edges' as flavour: `PeekPitch` (the
> edge-check) MUST fire before any ledge-to-ledge leap. No blind jumps. Reads as 'he checked the drop
> first.'" — WO-049, David refresh 2026-08-10

**Enforcement is at three layers, deliberately redundant:**
1. **Planner** (Vol XIII Ch.2 §2.3.6) — emits `PEEK` as a precondition on every `LEAP` leg.
2. **Channel** (Vol XI Ch.1 §1.4) — rejects a `move_command.route` containing a `LEAP` without a preceding
   `PEEK`; emits a rejection event UP; executes nothing.
3. **Realisation** — the body's `LEAP` handler asserts the peek occurred; failing loudly, never silently.

A rule that only lives in the planner would be lost the first time anything else issued a route. It is
cheaper to enforce it three times than to debug one blind jump in front of David.

## 2.5 The two risk constraints (canon for all cross-embodiment work)

Restated here because they are *movement* constraints, and this is the movement chapter (WO-049):

**1. No driver port.** The game `PlayerController` (CharacterController physics + input loop) must NOT move
to the desktop, nor vice-versa. The desktop driver is the Spatial Faculty requesting **verbs**; the game
keeps its own driver. *"Porting it = the forbidden 'animation hack that fakes awareness.'"*

**2. No identical asset/rig coupling as the sharing mechanism.** Sharing baked clips and identical
rig-binding is a **big risk with silent failure** — the seats already hit a missing `c_arm_fk` and a
head-bone mis-reference. Per-gesture code ports (e.g. ArmWave) bind bones **by name** and **MUST FAIL
LOUDLY** if a bone is absent — never a silent no-op.

**Corollary (the aim rig).** The HeadAim work — a Multi Aim Constraint with the **head bone** as constraint
object, ~±100° rotation limits, ~0.305 source-follow, plus a lighter-weight chest/shoulder aim so the torso
rotates a little with the head, and an optional Two Bone IK for the arm
(`_intake/SOURCE_2026-08-10_headaim_mouse_follow.md`, VERBATIM) — is a **realisation of `OBSERVE`/`PEEK`
weighting**, not a decider. The brain says *attend to that*; the rig makes it smooth. Its axes are
body-local (§2.1.4), and it targets **no eyes** (§2.1.5).

## 2.6 Contract

```
Component:
  name:            MovementGrammar
  version:         1.0.0
  purpose:         Define the closed, shared verb vocabulary that spatial decisions are expressed in and
                   that every body realises independently — so a new move is a new combination, and so
                   desktop, game and robot read as the same creature without sharing assets.
  contributes_to:  Volume XI Ch.1 command channel · Volume XIII Ch.2 route legs
  runs_in:         planning (composition) + realisation (per body)

Inputs:
  - type: route_leg      source: Volume XIII Ch.2         required: true
    description: one verb + from/to anchors + preconditions + expected_ms.
  - type: verb_support   source: per-embodiment declaration   required: true
    description: which verbs THIS body can realise (Vol XIII Ch.5 §5.4).
  - type: expression_params source: Presence (Vol XIII Ch.1) + Emotional Light Engine   required: false
    description: speed/intensity/mood — how the verb is coloured, never which verb is chosen.

Outputs:
  - type: realised_motion  destination: the body's animation/motor layer
  - type: leg_ack          destination: Volume XI Ch.1 UP channel (<verb>_complete + actual position)

Failure Modes:
  - condition: unsupported verb commanded
    fallback:  REJECT at the channel and emit UP. The planner should never have emitted it (Vol XIII Ch.5
               FT-2); a rejection means the verb-support declaration is wrong — fail loudly, don't substitute.
  - condition: LEAP without a preceding PEEK
    fallback:  REJECT the whole route; execute nothing (§2.4).
  - condition: a bone/rig element the realisation needs is absent
    fallback:  RAISE explicitly. Never a silent no-op (risk constraint 2).
  - condition: world-frame axis used for a rotation
    fallback:  treated as a defect — rotations fire the wrong way when eLo turns (§2.1.4).
  - condition: a realisation wants a verb outside the twelve
    fallback:  compose from existing verbs, or raise a canon change. Do NOT extend the vocabulary in code.
```

## 2.7 Acceptance Tests

### Functional
```
FT-1  Routes are verbs, never assets
  Given:  any route emitted by Vol XIII Ch.2
  Then:   every leg names one of the twelve verbs AND no animation/clip name appears anywhere in the
          command payload

FT-2  PEEK precondition holds at every layer
  Given:  a LEAP with no preceding PEEK, injected at the planner, at the channel, and at the realisation
  Then:   each layer independently refuses it

FT-3  Composite moves are compositions
  Given:  fire-jump / shoot-to-exit / wall-jump chimney
  Then:   each decomposes into existing verbs with a body-specific realisation; no thirteenth verb exists

FT-4  Parameterisation, not multiplication
  Given:  a slow APPROACH and a fast APPROACH
  Then:   the same verb is emitted with different parameters; there is no separate WALK/RUN verb
          AND the transition reads as continuous (no instant clip swap)

FT-5  Unsupported verbs are never commanded
  Given:  a body declaring no LEAP
  Then:   no LEAP leg is ever emitted to it; the planner routed around instead (Vol XIII Ch.5 FT-2)

FT-6  OBSERVE has no eyes
  Given:  an OBSERVE or PEEK leg in any embodiment
  Then:   realisation is head/chest orientation + posture + glow, in body-local axes; no eye target exists
```

### Stability
```
ST-1  Missing bone fails loudly
  Given:  a per-gesture code path and an absent bone
  Then:   an explicit error is raised — never a silent no-op (risk constraint 2)

ST-2  No driver port
  Given:  the codebase
  Then:   the game PlayerController is not used by the desktop, nor the desktop driver by the game

ST-3  Body-local axes under rotation
  Given:  eLo rotated ~180° to face the camera
  Then:   peek pitch, wall-jump direction and head aim all fire in the correct direction

ST-4  Closed vocabulary
  Given:  the codebase
  Then:   the set of verbs accepted by the channel is exactly the twelve; adding one requires a canon change
```

### Integration
```
IT-1  Same creature, different bodies
  Given:  the same route concept executed on desktop and in the game
  Then:   the motion reads as the same creature (shared feel + vocabulary)
          AND no baked clip or rig binding is shared between them

IT-2  Grammar survives the round trip
  Vol XIII composes verbs → Vol XI Ch.1 carries them DOWN → body realises → <verb>_complete UP with
  the ACTUAL position → Vol XIII Ch.4 records the outcome against the verb
  Assert: learning is per-verb-and-affordance, which is what lets Vol XXVIII train on it unchanged.

IT-3  No regressions (WO-049 build rule 4)
  Given:  the grammar is introduced
  Then:   perch · roam · drag · click-through · gun-runoff all still work
```

## 2.8 Open Questions (flagged for Chief Architect / David)

- **OQ-2.1** Are twelve the right verbs? WO-049 lists eleven (APPROACH · CLIMB · BALANCE · LEAP · HANG ·
  SLIDE · PEEK · PERCH · REST · OBSERVE · RETREAT · RETURN — twelve as written); David's roam source lists
  ten (omitting HANG and SLIDE, which appear in his moveset paragraph instead). This chapter takes the
  **union** and treats it as closed at twelve. Confirm — and confirm that closing it is the right call,
  since the whole value is in it staying small.
- **OQ-2.2** Where does the verb-support declaration physically live — with the realisation layer, or with
  the embodiment binding (Vol XIII Ch.5)? Recommend the **binding**, so the planner has one place to ask
  and the body cannot silently disagree with what it claimed to support.
- **OQ-2.3 (David L3-adjacent).** `EXIT_SCREEN` / run-off-and-reappear and the muted-gun moves are legal
  desktop acts but have no robot analogue and are cosmetic in the game. Should they be a **thirteenth verb**
  or a **composition + a body-specific affordance**? Recommend composition (`RETREAT` toward an
  `EXIT_SCREEN` affordance), which keeps the vocabulary closed.

## 2.9 References

- `_intake/SOURCE_2026-08-10_roam_os_vision.md` §7 and "A few rules that keep it coherent" —
  **VERBATIM primary source; referenced, never replaced.**
- `_intake/SOURCE_2026-08-10_headaim_mouse_follow.md` — **VERBATIM** (Multi Aim Constraint on the head bone,
  chest/shoulder follow, Two Bone IK arm option).
- `engineering/work_orders/WO-049_Desktop_World_SelfAware_Parkour.md` — Movement Grammar; "Reference, not
  clone" (ratified 2026-08-05); the two RISK CONSTRAINTS; build rules 1–4; the per-move → WO map.
- `CO_WORKING_GUIDE.md` — character constants: **eLo has NO EYES**; CharacterController only.
- `Volume_XI/01` (the channel) · `Volume_XIII/02` (the planner that composes verbs) ·
  `Volume_XIII/05` (verb support per body) · `Volume_XXVIII/` (training on per-verb outcomes).
- WO-024 (occlusion, `7bab6af`) · WO-074-F (jump reach clamp) · WO-092 (wall-jump) · WO-075 (gravity/landing)
  · WO-090 (HeadAim).

---

```
Chapter 2 — Movement Grammar & Embodiment Parity
Status: READY FOR REVIEW
Implementation: PENDING (verbs live as per-body moves; not yet a channel-level closed vocabulary)
Vocabulary: 12 verbs, closed — APPROACH · CLIMB · BALANCE · LEAP · HANG · SLIDE · PEEK · PERCH · REST ·
            OBSERVE · RETREAT · RETURN
Rules: reference-not-clone · no driver port · bone binding fails loudly · body-local axes · no eyes ·
       PEEK enforced at three layers
Contract: Included · Acceptance Tests: FT ×6, ST ×4, IT ×3 · Open Questions: 3
```

READY FOR REVIEW
