---
volume: XI
title: "Motor Cortex"
status: REVIEW
version: 0.1.0
owner: David Charles
architect: Claude (Lead Architect)
source: >
  UNITY_ELOOS_IO_CONTRACT.md (David L3, 2026-08-06) · WO-035 · WO-040 · WO-041 · WO-054 · WO-063 ·
  WO-086 · _intake/SOURCE_2026-08-10_brain_body_brain_loop.md (VERBATIM) ·
  _intake/SOURCE_2026-08-10_roam_os_vision.md §7 · WO-049 §Movement Grammar · live code (avatar/, blender_bridge/)
implementation: PARTIAL (avatar/ + blender_bridge/ live; command/ACK loop live for sit·move·leave·return; grammar not generalised)
audit_status: OPEN
canonical_path: docs/architecture/Volume_XI/
tier: FACULTY
dependencies:
  - Volume XIII (Presence & Embodied Spatial Intelligence — the deciding brain this volume serves)
  - Volume XVI (Coordination Under One Executive — one plan per turn)
  - Volume V/CONTRACTS.md (envelope, lifecycle, base contract)
  - ADR-Exec-001 (Verified Speech) · ADR-Exec-002 (Single Cognitive Truth) · ADR-Exec-003 (Embodied Truth)
priority: "Audit P1 — the body layer of brain>body>brain had zero canon contract"
last_review: 2026-08-11
next_review: TBD
---

# Volume XI — Motor Cortex

## What this volume is

The Motor Cortex is **how a decided action becomes motion, and how motion becomes belief**. It is the
narrow, verifiable channel between the brain and every body eLo has.

It is deliberately small. It does not decide anything. Volume XIII decides *whether* and *where*; this
volume owns *the command going down, the body doing it, and the confirmation coming back up* — and the
rule that eLo believes nothing until that confirmation arrives.

## The problem this volume closes

`AUDIT_INTENT_self_embodiment_2026-08-10.md`:

> "**XI Motor Cortex — NO. DOES NOT EXIST.** No `Volume_XI/` directory. No metadata, no chapter, no
> contract. Canon Index calls it '✅ Live — `avatar/` (code).' … **The body layer of brain>body>brain has
> zero canon contract.** The entire down/up motor contract (command → body → ACK → belief) lives only in
> WOs (035/040/041/063/086), never in canon. **NO WO EXISTS** — `CANON_BUILD_PROGRAM.md` line 44 lists XI
> under 'no build WO — verify-only.'"

The contract was real and working in code and in `UNITY_ELOOS_IO_CONTRACT.md`; it simply had no home in the
canon, so nothing bound future work to it. Five WOs each restated a piece of it. This volume is the piece
they were all pointing at.

## Scope (authoritative)

The DOWN command channel · the UP ACK/event channel · commanded state owning the body · ACK before belief ·
timeout honesty · the Movement Grammar verb vocabulary · embodiment parity (reference-not-clone) ·
body-local axes · the "no local driver decides" law and how it is audited.

**Out of scope (owned elsewhere):**
- *Deciding* to move, and where → **Volume XIII** (Presence & Embodied Spatial Intelligence).
- *Sensing* the world → **Volume XII** (Perception).
- *Holding* the world → **Volume XV** (World State).
- *Speaking* about what happened → the Executive, gated by this volume's ACK (ADR-Exec-001/003).
- *Emotional light / glow authoring* → `11_emotional_light_engine.md` (this volume only carries it DOWN).

## Anchors in the live system (verified 2026-08-11)

| Anchor | Path | State |
|---|---|---|
| DOWN channel (render + command) | `blender/blender_state.json` via `blender_bridge/state_writer.py` | **LIVE** |
| Command emission | `state_writer.write()` / `write_with_presence()` → `sit_command`, `move_command{type}`, `leave_command`, `return_command` | **LIVE** |
| UP channel (events + ACKs) | `blender/unity_events.json` | **LIVE** |
| ACK gating of speech | `server.py` — `sit_complete` / `move_complete` / `exit_complete` with `_ts > since` guard | **LIVE** |
| Channel law | `docs/architecture/UNITY_ELOOS_IO_CONTRACT.md` (David L3, 2026-08-06) | **LIVE, ratified** |
| Signal bridge (schema-normalised) | `avatar/unity_bridge.py`, `avatar/animation_router.py` | **LIVE** |
| Robot motor path | `avatar/motor_abstraction.py` (`build_command_packet` / `apply_commands`), `avatar/safety_controller.py`, `avatar/robot_simulator.py` | **LIVE (scaffolding)** |
| Movement Grammar as a real vocabulary | *(none — verbs exist in WO-049 prose, not in the channel)* | **PENDING** |
| Route (multi-leg) in `move_command` | *(none — `move_command` carries a single nav `type`)* | **PENDING (Vol XIII Ch.2 §2.2.4)** |

## Chapter Build Queue

| ID | Chapter | Title | Status |
|----|---------|-------|--------|
| ELO-V11-CH01 | Chapter 1 | The Motor Cortex & the Body Contract | READY FOR REVIEW |
| ELO-V11-CH02 | Chapter 2 | Movement Grammar & Embodiment Parity | READY FOR REVIEW |

**Chapter set rationale (no padding):** Ch.1 is the *channel* — how a decision becomes motion and returns as
verified fact. Ch.2 is the *vocabulary* that travels through it, and the rule that keeps it the same eLo in
every body. Two chapters, because the volume is a contract, not a cognition — padding it would be the
opposite of the point.

## Invariants this volume must never break

1. **The body NEVER decides.** *"the brain decides + drives the body (DOWN), the body only SENSES and ACTS
   and reports its state back UP… no local script may choose a behaviour."* (David verbatim,
   `_intake/SOURCE_2026-08-10_brain_body_brain_loop.md`.) This volume's job is to make that mechanically
   true, and auditable.
2. **ACK before belief.** No `<action>_complete`, no belief, no speech. *"eLo only says he did something
   once his body confirms it."* (ADR-Exec-003 Embodied Truth; David §7.)
3. **Commanded state owns the body.** While a command is in flight, autonomous behaviour may not overwrite
   it (WO-035/WO-040 `_sitHeld`). One authority at a time.
4. **Channels are defined by DIRECTION and DELIVERY TYPE, never by topic.** New concerns are **fields in an
   existing channel**, never new files. `emotions.json` / `movement.json` are forbidden.
   (`UNITY_ELOOS_IO_CONTRACT.md`, David L3.)
5. **Timestamp guard + consume.** An ACK counts only if `_ts > pending.since`, and is cleared after read.
   A stale event may never false-trigger.
6. **Honest failure.** No ACK within timeout → say so plainly ("I tried to X but couldn't"), never claim
   success, never go quiet as if it worked.
7. **Autonomous and commanded are one capability.** What eLo does on his own must be drivable by the
   Executive through the *same* underlying capability — never two divergent paths.
   (`ARCHITECTURAL_PRINCIPLES.md`.)
8. **Reference, not clone.** Share the verb vocabulary and the feel across bodies; never baked clips or
   rig binding. Bone-bound code fails **loudly**.
9. **Body-local axes.** eLo faces the camera ~180° from world; every rotation axis is expressed in his body
   frame.
10. **No eyes.** Expression is orientation, posture, glow, and the single curved mouth. This volume carries
    no eye channel, and none may be added.

## Relationship to Volume XIII (the clean boundary)

```
Volume XIII — decides           Volume XI — delivers and confirms
──────────────────────          ────────────────────────────────
"should I?"  (presence)         command DOWN
"can I reach it?" (spatial)     body executes
"how do I get there?" (route)   ACK/event UP
"was it worth it?" (learning)   belief updates → only now may the Executive speak
```

Volume XIII produces intentions. Volume XI turns them into facts. Neither may do the other's job: a Motor
Cortex that chooses a route has become a second brain (the exact breach Ruling D-XIII-1 corrects), and a
Spatial Faculty that writes animation directly has bypassed verification.

## Definition of Done

- [x] Volume created; the down/up motor contract lifted out of five WOs into canon
- [x] Two deep chapters authored (body contract · movement grammar + parity)
- [x] Each: contract + lifecycle + envelope + acceptance tests + open questions
- [x] Grounded in the ratified `UNITY_ELOOS_IO_CONTRACT.md` and in live code paths
- [x] "No local driver decides" stated as a law with an explicit audit rule (Ch.1 §1.7)
- [ ] Chief Architect cross-check of the open questions (Ch.1 ×4, Ch.2 ×3)
- [ ] **David L3** on the generalised verb channel (it changes a working DOWN contract he signed)
- [ ] `CANON_BUILD_PROGRAM.md` line 44: remove XI from the "already live — verify only" list; raise **WO-CANON-XI**
- [ ] `00_CANON_INDEX.md`: XI is no longer "✅ Live — `avatar/` (code)"; it is canon + partial implementation
- [ ] Audit can mark COMPLETE

**Status: REVIEW** — scope locked; two chapters READY FOR REVIEW.
