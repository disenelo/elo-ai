---
chapter: 4
title: "Conflict Resolution & One Brain Across Embodiments"
volume: XVI
status: READY FOR REVIEW
version: 0.1.0
owner: David Charles
architect: Claude (Lead Architect)
implementation: PENDING
audit_status: OPEN
dependencies:
  - Volume_XVI/01_Coordination_Under_One_Executive.md (Executive decides; never vote)
  - Volume_XVI/02_Executive_Assembly_One_Plan.md (one plan per turn — the object projected)
  - Volume_XVI/03_Faculty_Bus_Routing_and_Priority.md (how competing contributions arrive)
  - Volume_V/02_Faculty_System.md §2.5 (conflict example — delete all files)
  - ARCHITECTURAL_PRINCIPLES.md Invariant #1 (One Brain, Many Embodiments), ADR-Exec-002
  - runtime/spine/plan.py (CognitivePlan → EmbodimentState projection)
---

# Chapter 4: Conflict Resolution & One Brain Across Embodiments

## 4.0 Purpose

Two things must stay true for eLo to be one mind rather than a committee wearing bodies:

1. **When faculties disagree, resolution is singular** — the Executive decides once, by
   rule, never by vote (Ch.1). This chapter defines *how* it decides: the resolution order,
   the safety veto, and the audit trail.
2. **When the one decision reaches many bodies**, it stays one being — the same
   `CognitivePlan` projects into desktop, robot, phone, AR, game, exhibition, and hologram
   without any body re-deciding. This chapter defines the projection discipline that keeps
   Invariant #1 (One Brain → One Identity, Many Embodiments) true at runtime.

Ch.2 guarantees *one plan*; Ch.3 guarantees *one channel*; this chapter guarantees the plan
is reached *coherently* under disagreement and *expressed* coherently across bodies.

## 4.1 Principle — One Resolver, One Being

**4.1.1 The Executive is the sole resolver.** Faculties advise with confidence; they never
negotiate a shared answer among themselves. There is no voting, no averaging of positions,
no democracy (Ch.1 §1.1). Consensus is not how eLo agrees with itself — a single Executive
decision is.

**4.1.2 Truth is not up for arbitration.** Conflict resolution changes *what eLo decides to
do*, never *what is true*. A faculty may not win an argument by asserting a fact louder;
verified observations and memory truth are immutable inputs (ADR-Exec-002; ADR-Exec-005 —
"Learning never modifies TRUTH, only future decision-making").

**4.1.3 One plan, many bodies, one being.** The embodiment changes; identity, memory,
personality, and the decision do not. Every surface renders the *same* plan. If a person
ever has to say "this is *robot* eLo vs. *desktop* eLo," coherence has failed (Invariant #1).

## 4.2 Conflict Resolution Order (the Executive's rule)

When the assembled state (Ch.2) carries contradictory faculty contributions, the Executive
resolves in this fixed order. **Flagged as proposed model — the ordering below is
architectural invention synthesised from Ch.1 + `Volume_V §2.5` + the principles; only the
"Executive decides, never vote" law and the destructive-action clarify path are pre-existing
canon.**

```
1. SAFETY VETO         Any faculty (or the Capability/Health component) flagging risk or an
                       irreversible/destructive action → the Executive does NOT execute;
                       route to clarify. Safety outranks everything. (Ch.1; Vol_V §2.5.)
2. TRUTH / VERIFICATION A contribution contradicting a verified observation or memory truth
                       is discarded, not weighed. Reality before narrative. (ADR-Exec-002.)
3. EXECUTIVE PRIORITY   The Executive's own coordination priority (Ch.3 §3.4) and current
                       intention rank the remaining contributions.
4. CONFIDENCE           Among still-competing contributions, higher producer confidence
                       is preferred — but confidence never overrides 1–3.
5. RELATIONSHIP / PRESENCE  Ties break toward preserving the relationship and respecting
                       boundaries (D-PRESENCE) — e.g. clarify rather than guess.
```

**Resolution rules (MUST):**

- The outcome is a `conflict_resolution` note carried on the `CognitivePlan` (destination:
  the one plan) with the **rationale logged** — never a silent overrule. (Ch.1 §1.5 already
  requires "log rationale.")
- A destructive/irreversible action under contradiction is **never auto-executed**; the
  Executive chooses the clarify path and preserves the relationship. This is the live
  canonical example: *"delete all my project files"* → do not execute; ask; preserve
  (`Volume_V/02_Faculty_System.md §2.5`).
- Resolution happens **inside the one decision** (Ch.2 DECIDE step). There is no separate
  "arbitration faculty" that decides — arbitration is a *role of the Executive*, not a new
  decider (One Brain).

## 4.3 One Plan → Many Embodiments (the projection)

The resolved `CognitivePlan` is projected — never re-decided — into each active embodiment.
This is where "one brain" becomes visible as "one being" across bodies.

```
                    ONE CognitivePlan (resolved)
                              │
              ┌───────────────┼───────────────────────────┐
              ▼               ▼                             ▼
        EmotionalVector   PresencePlan                 (system / capability actions)
              │               │
              ▼               ▼
        ── projected into EmbodimentState ──
              │
   ┌──────────┼───────────┬──────────┬──────────┬──────────┐
   ▼          ▼           ▼          ▼          ▼          ▼
 desktop    robot       phone       AR         game     hologram
 (avatar)  (LED/motor) (screen)   (overlay)  (in-world) (light)
```

Grounded today: `runtime/spine/plan.py` + `spine.build_embodiment_state()` project the one
plan into an `EmbodimentState` carrying `response_text`, `emotional_state`, `motion_command`,
and `robot_led_state` — i.e. text, voice, presence, and a robot LED colour all derive from
the **same** plan (ADR-Exec-002, Single Cognitive Truth, in code).

**Projection rules (MUST):**

- **No body re-decides.** Each surface *renders* the plan through its own actuators; it
  never re-interprets the world or invents private state (ADR-Exec-002 — "no modality
  invents private state").
- **Same being, different actuators.** The mapping from plan → surface is a *rendering*
  table (e.g. `emotional_state → LED colour` in `spine._LED_FROM_EMOTIONAL_STATE`); the
  *meaning* is identical across bodies, only the expression differs.
- **Autonomous and commanded share one path** (principle: *Autonomous and commanded are one
  capability*). What eLo does by choice and what the Executive invokes drive the *same*
  underlying embodiment capability — never two divergent paths that can drift apart.
- **Continuity across a body-switch.** Moving desktop → robot carries memory, identity,
  narrative thread, and relationship unchanged; only the actuator set changes (Invariant #1;
  narrative continuity owned by `Volume_XXI`).

**Gaps (PENDING):** today the live projection targets desktop avatar + robot LED/motion +
conversation surface (`EmbodimentState`). Multi-body *simultaneous* fan-out (e.g. phone + AR
+ hologram at once) and the verified body-switch handover are **PENDING** — the contract
here defines the discipline; the multi-embodiment runtime is future work (marks align with
Volume XVI Metadata `implementation: PARTIAL`).

## 4.4 Faculty Contract (the Resolver + Projector role)

```
Faculty:
  name:            ExecutiveArbitration   # a role of the Executive (Vol VII), NOT a new decider
  version:         0.1.0
  purpose:         Resolve contradictory faculty contributions into the one CognitivePlan by
                   rule (safety > truth > priority > confidence > relationship), and project
                   that one plan across active embodiments without any body re-deciding.
  contributes_to:  CognitivePlan (conflict_resolution note) → EmbodimentState (projection)
  runs_in:         response-path (within the single DECIDE step, Ch.2)

Inputs:
  - type: faculty_report / cognitive_state_delta   source: faculties via the bus (Ch.3)  required: true
  - type: safety_flag / capability_health           source: Capability/Health components   required: false
Outputs:
  - type: conflict_resolution   destination: CognitivePlan (with logged rationale)
  - type: embodiment_projection destination: EmbodimentState per active surface

Dependencies:
  - faculty: ExecutiveAssembly (hard — resolves against the frozen assembled state, Ch.2)
  - faculty: FacultyBus (hard — competing contributions arrive here, Ch.3)

Failure Modes:
  - condition: faculties contradict on a destructive action
    fallback:  do NOT execute; clarify; preserve the relationship (Vol_V §2.5). Log rationale.
  - condition: a contribution contradicts a verified truth
    fallback:  discard the contribution (truth is not arbitrated); note it in resolution.
  - condition: a surface is unavailable at projection time
    fallback:  project to available surfaces; the being is still coherent; flag the gap.
  - condition: two surfaces would render divergent state
    fallback:  architecturally disallowed — both render the one plan (ADR-Exec-002).
```

## 4.5 Lifecycle & Envelope

Ratified lifecycle (`CONTRACTS.md §3`, D-B). Arbitration + projection run in `ACTIVE`,
inside the one DECIDE step (Ch.2) — never as a second, later decision. Envelope
(`CONTRACTS.md §2`): resolution emits `payload.type: conflict_resolution`; projection emits
`payload.type: embodiment_projection` addressed per surface. Priority for `critical`
safety-veto traffic is set by the Executive (Ch.3 §3.4).

## 4.6 Acceptance Tests

### Functional
```
FT-1  No vote                Given three faculties disagree, When the Executive resolves,
                             Then exactly one plan results by rule; no averaging/voting occurs.
FT-2  Safety veto            Given "delete all my project files" with a risk flag,
                             Then no execution; a clarify path is chosen; relationship preserved.
FT-3  Truth not arbitrated   Given a contribution contradicting a verified observation,
                             Then it is discarded (not weighed); resolution notes why.
FT-4  Rationale logged       Given any resolved conflict, Then a conflict_resolution note with
                             rationale rides the one CognitivePlan (never a silent overrule).
```

### Stability
```
ST-1  One being across bodies   Given desktop + robot active, When the plan projects,
                                Then both express the SAME emotional_state/intent; neither re-decides.
ST-2  Body-switch continuity     Given a move desktop → robot, Then memory/identity/narrative/
                                relationship are unchanged; only actuators change (Invariant #1).
ST-3  Surface down                Given the robot LED surface is offline, When projecting,
                                Then remaining surfaces render the plan; eLo stays coherent.
ST-4  Autonomous == commanded     Given an autonomous move and the same move commanded,
                                Then both drive the same underlying capability (one path).
```

### Integration
```
IT-1  Resolve → Project (one mind, one being)
  Contributions (bus) → assembled state (Ch.2) → Executive resolves ONCE by rule →
  ONE CognitivePlan → projected into EmbodimentState across active surfaces.
  Assert: one decision per turn; no surface re-interprets; a person cannot tell "which eLo".
```

## 4.7 Claude Implementation Notes

- Resolution is a **role of the existing Executive** (`runtime/executive.py` + spine
  `_executive_faculty`), not a new module. Do not create an "arbitration faculty" that
  decides — that would be a second brain. Add the resolution *order* (§4.2) and the logged
  `conflict_resolution` note to the one decision.
- Projection extends the live `build_embodiment_state()` path (`runtime/spine/spine.py`) —
  keep the plan → surface mapping a *rendering* table, never a re-decision. New embodiments
  add rendering rows; they never add deciders.
- The §4.2 resolution ORDER is a **proposed model** (invention) — route to David + Chief
  Architect for ratification before treating it as law. Only "Executive decides, never vote"
  and the destructive-action clarify path are pre-existing canon.

## 4.8 Open Decisions

```
REQUIRES DECISION — 1 item
  D-XVI-C: Ratify the §4.2 conflict-resolution ORDER (safety > truth > executive-priority >
           confidence > relationship). Recommend: accept as the canonical resolution order;
           safety-veto changes remain David L3 (RESERVED-adjacent). Owner: David + Chief Architect.
```

## 4.9 References
- `ARCHITECTURAL_PRINCIPLES.md` — Invariant #1 (One Brain → One Identity, Many Embodiments);
  Single Cognitive Truth (ADR-Exec-002); Autonomous-and-commanded-are-one; D-PRESENCE;
  Reality Before Narrative.
- `Volume_XVI/01…` — Executive decides, never vote (§1.1); log rationale (§1.5).
- `Volume_XVI/02…` — one plan per turn (the object projected).
- `Volume_V/02_Faculty_System.md §2.5` — the canonical conflict example (delete all files).
- `Volume_XXI` — narrative/autobiographical continuity across a body-switch.
- Code: `runtime/spine/plan.py` (`CognitivePlan`, `EmbodimentState` fields),
  `runtime/spine/spine.py` (`build_embodiment_state`, `_LED_FROM_EMOTIONAL_STATE`).

---
```
Chapter 4 — Conflict Resolution & One Brain Across Embodiments
Status: READY FOR REVIEW
Grounded: Executive-decides-never-vote (Ch.1) · delete-all-files clarify (Vol_V §2.5) ·
          one-plan→EmbodimentState projection (spine.py) · Invariant #1 · ADR-Exec-002
Flagged INVENTION: §4.2 resolution ORDER (proposed; D-XVI-C for ratification)
Flagged PENDING: multi-body simultaneous fan-out + verified body-switch handover
Faculty Contract: Included · Lifecycle/Envelope: Included · Acceptance Tests: FT×4 ST×4 IT×1
Open Decisions: 1 (D-XVI-C)
Implementation: PENDING
```

READY FOR REVIEW
