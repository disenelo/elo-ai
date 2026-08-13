---
id: ADR-Exec-002
aliases: [ADR-Executive-002]
title: "Single Cognitive Truth — one authoritative state, all modalities derive from it"
status: ACCEPTED · CANON · LAW
date: 2026-08-10                 # date this ADR document was written
ratified: 2026-08-03             # Chief Architect (SEAT-EXE-003), relayed + endorsed by David (L3)
owner: David Charles
author: Claude (Lead Architect)
supersedes: []
related: [ADR-Exec-001, ADR-Exec-006, ADR-0001]
canon_home: DECISION_LOG.md §"ADR-Executive-002"
---

# ADR-Exec-002 — Single Cognitive Truth

> **Formalisation note (2026-08-10).** Already present as a full narrative section in
> `DECISION_LOG.md` (spelled `ADR-Executive-002`) plus a summary row. This document is the single
> addressable home. **No new policy.**

## Context

Live bugs showed faculties reporting conflicting realities in the same moment — Memory said "yes",
the Executive said "no", the Tool said "maybe"; the weather faculty gave three temperatures inside
one exchange. Different modalities were narrating different states. That is cognitive
inconsistency, and it breaks the **One Brain Principle** at runtime.

ADR-Exec-001 forbids speaking past verified state. That is useless if there are five candidate
states to verify against. **002 guarantees there is exactly one.**

## Decision

**At any point in time there shall be exactly ONE authoritative cognitive state, from which ALL
externally visible behaviour is derived.**

**Laws (MUST):**

1. Every faculty **PUBLISHES** its state (to the health registry / Faculty Bus — WO-042).
2. The Executive **ASSEMBLES** the unified cognitive state and **FREEZES** it for the turn
   (Vol V Ch.1: one decision per turn, frozen after assembly; feeds the World Model, Vol XV).
3. Every outward expression — response text, avatar posture, eye movement, speech timing, orb
   brightness, robot action — references the **SAME frozen state snapshot**.
4. **No modality may invent private state after Executive arbitration.**

## Consequences

**Forbids**
- Any modality (voice, avatar, orb, robot, panel) computing its own view of "how eLo is" at render
  time.
- Two faculties resolving the same question differently within one turn without Executive
  arbitration.
- Re-probing the world mid-turn to answer a question the frozen snapshot already answers.

**Enables**
- When David asks *"How are you?"*, the words, the posture, the speech timing and the orb
  brightness all originate from ONE executive snapshot — not five interpretations.
- Conflicting readings (memory yes / executive no) become structurally impossible: the Executive
  resolves them into a single truth **before** anything is expressed.
- Replayability and debuggability — a turn can be reconstructed from one object.

## How it is enforced

| Mechanism | Where |
|---|---|
| Faculties publish state to a registry rather than being queried ad hoc | **WO-042** · `runtime/faculty_health.py` |
| One frozen `CognitiveState` per turn | Vol V Ch.1; the spine (`16_spine_runtime.md`) |
| One world object with confidence/source/freshness | Vol XV · `world/live_world_state.py` |
| One snapshot file read by avatar / voice / orb | `blender/brain_state.json` |
| Assembly named and ordered before the decision | **ADR-Exec-006** + Ruling C (2026-08-10) |
| Conflict-resolution order across embodiments | `Volume_XVI/04_Conflict_Resolution_and_One_Brain_Across_Embodiments.md` |

## Relationship

ADR-Exec-001 (Verified Authority) + ADR-Exec-002 (Single Truth) = **the runtime embodiment of the
One Brain Principle.** ADR-Exec-006 later *names* the assembly step that 002 requires and fixes its
position in the loop (before the decision, not after).

## Citations (representative — 29 references repo-wide)

- `ARCHITECTURAL_PRINCIPLES.md` — Runtime Invariant #4.
- `Volume_XVI/02_Executive_Assembly_One_Plan.md`; `Volume_XVI/04_*` (immutable inputs).
- `Volume_X/04_Personality_In_The_Moment.md` (personality shapes expression, never truth).
- `DECISION_LOG.md` thematic index — "Executive cognition".
