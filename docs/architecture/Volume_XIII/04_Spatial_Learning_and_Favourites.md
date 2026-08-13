---
chapter: 4
title: "Spatial Learning & Favourites — Routes Remembered, Confidence Earned"
volume: XIII
status: READY FOR REVIEW
version: 0.1.0
owner: David Charles
architect: Claude (Lead Architect)
source: >
  WO-049 §049-B2 (continuity wiring) · WO-094 §D (LEARNING IS PART OF DONE) ·
  Volume XXVIII §"Movement Faculty ⭐ — RL domain #1" · ADR-Exec-005 (Learning Through Verified Consequences)
implementation: PENDING (no traversal outcome is recorded today; routes are recomputed every time)
audit_status: OPEN
dependencies:
  - Volume_XIII/02_The_Spatial_Faculty.md (produces the routes and the outcomes learned from)
  - Volume_XIII/03_Noticing_and_Choosing_in_Space.md (decisions are outcomes too)
  - Volume XI (Motor Cortex — the ACK is the ONLY admissible evidence an outcome occurred)
  - Volume VIII (Memory Architecture — storage shapes; Memory Ownership invariant applies)
  - Volume V Ch.5 (Significance Engine — the reward signal; do NOT invent a scalar)
  - Volume V Ch.6/7 (Reflection & Growth — where preference formation belongs)
  - Volume XXVIII (Adaptive Learning — the policy layer this capture upgrades into)
  - ADR-Exec-003 (Embodied Truth) · ADR-Exec-005 (hard boundary)
---

# Chapter 4: Spatial Learning & Favourites

## 4.0 Purpose

A being that solves the same route from scratch every time is a solver, not an inhabitant. This chapter is
how eLo comes to **know his own desktop** — how a corner becomes *his* corner, how a jump he has landed
thirty times stops costing him deliberation, and how a route that keeps failing quietly stops being
offered.

WO-049 states it as the emergent principle, and it is deliberately not a feature list:

> "History creates preference; routes are remembered not recomputed; confidence grows from experience.
> **EMERGENT — favourites accrue, never coded.**" (049-B2)

WO-094 §D makes it non-optional: *"A seat may NOT close this WO with the movement built and the learning
missing."*

And Volume XXVIII names this the **first** RL domain — *"Movement Faculty ⭐ — instead of scripting parkour,
eLo learns traversal… This is 'run around because he WANTS to.'"* This chapter defines the **capture and
recall loop** that is buildable today and that the policy layer later upgrades **without a rewrite**.

## 4.1 Principle

**4.1.1 Learn only from verified outcomes.** The body's ACK is the sole admissible evidence that something
happened (ADR-Exec-003). A route is not "successful" because it was planned, dispatched, or plausible — only
because `<verb>_complete` / `arrived` came back UP. eLo can never learn a hallucinated traversal.

**4.1.2 Routes are remembered, not recomputed.** A path that worked to a given surface is **recalled before
the planner re-solves from scratch**. This is the mechanism behind the principle *"verified capability
becomes instinct through repetition"* — instinct never bypasses verification; it **reduces planning cost**
as a route proves reliable, exactly like a person who no longer thinks about the stairs.

**4.1.3 Favourites accrue through USE.** There is no favourite-places list, ever. A surface becomes a
favourite because he keeps ending up there and it keeps going well. If a reviewer can find a hardcoded
favourite, the chapter has been implemented wrongly.

**4.1.4 Confidence is earned, and it is spatial — not personal.** `BodySchema.confidence` and per-route
confidence rise from repeated verified success and fall from verified failure. It is confidence *in this
jump*, not self-esteem. Nothing here touches personality.

**4.1.5 Reward is Significance, not a new number.** Vol XXVIII is explicit: *"Reuse
`memory/significance_engine.py` — do NOT invent a reward scalar."* Optimise toward what matters — safety,
curiosity, efficiency, not-interrupting-David — evaluated through the existing significance path.

## 4.2 ⚖ THE HARD BOUNDARY (ADR-Exec-005)

> **Learning here may improve *how well he moves*. It may NEVER touch identity · values · personality ·
> memory truth · Executive authority · speech correctness.**
> *"Constitution defines who; Executive decides what; RL improves how well."*

| May be written by this chapter | May NEVER be written by this chapter |
|---|---|
| route familiarity / recall index | identity kernel, values, constitution |
| per-route success rate + confidence | personality traits or drift dimensions (Vol X) |
| affordance risk estimates | permanent autobiographical memory (Vol VIII owns the writer) |
| movement cost weights, safety margins | Executive decision policy or authority |
| surface preference (accrued) | what eLo believes is true, or what he may say |
| salience weights for noticing (Ch.3) | relationship state, emotional truth |

**Enforcement (MUST):** the learning path is confined to the Movement/Spatial faculty and writes only to a
**spatial learning store**. It holds no handle to the identity kernel, the personality store, or the
permanent-memory writer. This must be assertable in a test, not merely stated (AT: "assert nothing in the
learning path can write identity/values/personality" — WO-094 §LEARNING IS PART OF DONE).

## 4.3 What is recorded (WO-094 §D — "record what happened")

Every traversal writes one record, on ACK, whether it succeeded or not. **A failed reach is as valuable as
a success.**

```
TraversalOutcome (written ONLY on a verified body ACK or a verified failure):
  goal:          { kind, surface_id, why }        # what he was trying to do, and why
  route_id:      str                              # stable hash of (from_surface, to_surface, leg verbs)
  legs:          [ { verb, from, to, affordance_kind } ]
  arrived:       bool                             # ACK'd arrival at the intended anchor
  failure:       enum { none, no_ack, collided, fell, surface_gone, aborted_by_register }
  smoothness:    float 0–1                        # from leg timings vs expected_ms + collision count
  duration_ms:   int
  reflexes:      [ str ]                          # any bounded reflex that fired en route (Ch.2 §2.2.3)
  body_at_start: { height_px, max_jump_d, energy, confidence }   # capability at the time
  world_hash:    str                              # coarse world signature (so a route isn't recalled
                                                  #   into a desktop that no longer resembles it)
  register:      PresenceRegister
  ts:            float
```

**Recording rules (MUST):**
1. **On ACK only.** No record for a dispatched-but-unconfirmed leg. `no_ack` is itself a *verified*
   failure (the timeout elapsed) and IS recorded — it is not an assumed success.
2. **Record the capability at the time.** A jump that failed at `max_jump_d = 60` is not evidence about a
   body that can now do 75. Without `body_at_start`, learning would mislearn across body changes — and
   would break outright across embodiments (Ch.5).
3. **Record the register.** A traversal aborted because David started typing is not a route failure and
   must never lower that route's confidence.
4. **Record reflexes.** A route that repeatedly needs the survival net is a *risky* route even if he
   arrives.
5. **Bounded store.** Outcomes age and compact (Vol VIII forgetting curve applies as the model, but Vol
   VIII owns memory decay — this store keeps its own bounded summary and never runs its own memory decay
   on permanent memory).

## 4.4 Recall — routes remembered, not recomputed

```
recall_route(from_surface, to_surface, body, world_hash) -> RememberedRoute | None

RememberedRoute:
  route:       Route            # the legs that worked
  attempts:    int
  arrivals:    int
  confidence:  float 0–1        # from verified outcomes only
  last_used:   float
  still_valid: bool             # do the surfaces still exist, at compatible geometry?
```

**Recall rules (MUST):**
- The Spatial Faculty (Ch.2 `plan_route`) **asks recall first**. A valid remembered route with adequate
  confidence is taken directly; planning cost is skipped. This is instinct.
- **Recall never bypasses verification.** The remembered route is still validated against the *current*
  frozen world (surfaces exist, geometry compatible, landings still wide enough, register permits) and
  still carries the peek precondition. A remembered route that no longer validates is discarded and the
  planner re-solves. Instinct reduces planning; it never skips reality.
- `still_valid = false` (window resized, closed, moved) → re-plan, and do **not** penalise the route's
  confidence. The world changed; he did not fail.
- Below a confidence floor, recall returns `None` and the planner solves fresh — an untested route should
  not feel familiar.

## 4.5 Favourites — accrued, never coded

```
SurfaceAffinity (derived, never authored):
  surface_signature: str     # app + coarse role, so it survives the window being reopened
  visits:            int
  dwell_ms_total:    int     # time spent resting/observing there, not passing through
  outcomes_good:     int     # arrived, smooth, uninterrupted
  significance:      float   # from Vol V Ch.5 — what MATTERED about being there
  affinity:          float   # derived: dwell × outcome quality × significance, aged
```

**Favourite rules (MUST):**
- Affinity is **derived from records**, never set. There is no configuration surface for it.
- Affinity enters Ch.2's cost model as `familiarity_bonus` only — it makes a place *cheaper to choose*, it
  never *forces* a destination. Otherwise eLo would visibly loop to one corner, which is the repetition the
  WO-049 Presence Acceptance test explicitly fails.
- **Novelty must survive.** Curiosity (Vol V Ch.10 Agency) must be able to outbid affinity, or favourites
  become a rut. *"Nothing feels repetitive or random"* is the acceptance bar; affinity without novelty
  fails the first half.
- Dwell counts differently from transit. A ledge he crosses a hundred times is not a favourite; a ledge he
  *sits* on is.

## 4.6 Confidence — how "he's got better at that" becomes visible

```
on verified arrival:  route.confidence ↑ (diminishing, capped)
                      affordance.risk  ↓ for that affordance kind at that body capability
on verified failure:  route.confidence ↓ (faster than it rose — safety is asymmetric)
                      prefer the safer multi-leg route next time (WO-094 §D)
on register abort:    no change (§4.3 rule 3)
on world change:      no change (§4.4)
```

**Visible consequences (this is the *point* — none of it is narrated):**
- A high-confidence route is taken **without hesitation**: fewer preparatory beats, tighter timing.
- A low-confidence route is taken **carefully**: longer peek, slower approach, or the multi-leg alternative
  is preferred outright.
- Repeated failure on a direct leap makes the safe route *cheaper*, so he simply stops trying the leap —
  visibly "he learned that one doesn't work," with no dialogue.
- `safety_margin` may scale with confidence (Ch.2 OQ-2.5), which is how growth shows in the body rather
  than in speech.

**Rule (MUST):** eLo does **not** say "I've got better at this." If growth needs narrating, that is
Narrative Identity (Vol XXI) reading this store — never this chapter speaking. *The Executive grows quieter.*

## 4.7 Faculty Contract

```
Faculty:
  name:            SpatialLearningFaculty      # the learning half of Vol XIII; sits under Spatial
  version:         1.0.0
  purpose:         Capture verified traversal outcomes, recall proven routes before re-planning,
                   accrue surface affinity through use, and grow movement confidence from experience —
                   improving HOW WELL eLo moves and nothing else.
  contributes_to:  SpatialFaculty (recall + cost weights) · CognitiveState (spatial confidence)
  runs_in:         post-action (on ACK) + integration window (compaction, weight updates)

Inputs:
  - type: route            source: Volume XIII Ch.2                     required: true
  - type: body_ack         source: Volume XI UP channel                 required: true
    description: <verb>_complete / arrived / collided / landed / resurfaced — the ONLY evidence admitted.
  - type: notice_decision  source: Volume XIII Ch.3                     required: false
  - type: significance     source: Volume V Ch.5                        required: false
    description: what mattered about this traversal. NOT a new reward scalar.
  - type: presence_register source: Volume XIII Ch.1                    required: true
    description: needed to exclude register-aborted traversals from failure statistics.

Outputs:
  - type: remembered_route destination: Volume XIII Ch.2 (plan_route asks recall first)
  - type: cost_weights     destination: Volume XIII Ch.2 (familiarity_bonus, risk, safety_margin)
  - type: surface_affinity destination: Volume XIII Ch.2 + Vol V Ch.6/7 (preference formation)
  - type: movement_confidence destination: BodySchema (spatial confidence ONLY)

Dependencies:
  - faculty: SpatialFaculty (Vol XIII Ch.2, HARD)
  - faculty: MotorCortex (Vol XI, HARD — no ACK, no learning, full stop)
  - faculty: SignificanceEngine (Vol V Ch.5, SOFT — without it, outcomes are recorded but unweighted)
  - store:   spatial learning store (bounded, faculty-local)
  - FORBIDDEN handles: identity kernel · personality store · permanent-memory writer · Executive policy

Failure Modes:
  - condition: no ACK returned
    fallback:  record failure=no_ack. NEVER record success. (ADR-Exec-003)
  - condition: learning store corrupt/missing
    fallback:  recall returns None; the planner solves fresh every time. Movement still works, just
               without improvement. Degradation must be invisible to David except as lost familiarity.
  - condition: world changed since the route was learned
    fallback:  still_valid=false → re-plan, no confidence penalty.
  - condition: register aborted the traversal
    fallback:  excluded from statistics entirely.
  - condition: body capability changed (embodiment switch, scale change)
    fallback:  records with an incompatible body_at_start are not used for recall (Ch.5 §5.4).
  - condition: any write attempted outside the permitted set (§4.2)
    fallback:  REJECT and raise. This is a constitutional violation, not a bug to be tolerated.
```

## 4.8 Faculty Lifecycle

```
INITIALISING → open the bounded spatial learning store; verify no forbidden handles are held
ACTIVE       → serving recall + cost weights to Ch.2; writing nothing
PROCESSING   → on ACK/failure: assemble TraversalOutcome → append → update route + affinity + confidence
   └─ ACK absent/ambiguous ─► record verified failure; never infer success
LEARNING/UPDATING → integration window ONLY: compact outcomes, age affinity, recompute weights.
                    Scope-checked against §4.2 on every write.
STABLE → ACTIVE
```

**Lifecycle rule (MUST):** learning sits **after** verification in the cycle
`Execute → Verify → Outcome → Reflect → Learn → Memory` (`ARCHITECTURAL_PRINCIPLES.md`). It never runs
inline in the decision path — a turn must never wait on learning.

## 4.9 Message Envelope Binding

```jsonc
{
  "id": "uuid",
  "sender": "SpatialLearningFaculty",
  "receiver": "SpatialFaculty",
  "priority": "low",
  "context": {
    "conversation_id": "", "relationship_state": "", "environment_state": "desktop",
    "significance": 0.31,
    "memory_instruction": { "store": true, "priority": "low" }
  },
  "payload": {
    "type": "traversal_outcome",
    "body": {
      "route_id": "vscode:1→chrome:1/APPROACH,PEEK,LEAP",
      "arrived": true, "failure": "none", "smoothness": 0.82, "duration_ms": 2010,
      "reflexes": [], "register": "FREE",
      "body_at_start": { "height_px": 120, "max_jump_d": 75, "energy": 0.7, "confidence": 0.58 },
      "world_hash": "3w:2560x1440:z[vscode,chrome,finder]",
      "evidence": ["move_complete@1754812347.9", "arrived@1754812348.4"]
    }
  },
  "confidence": 1.0,
  "expires": null,
  "trace": ["SpatialFaculty@ts", "MotorCortex@ts", "SpatialLearningFaculty@ts"]
}
```

**Binding rules (MUST):** `evidence[]` is **mandatory and must name the actual ACK events with their
timestamps** — an outcome without evidence is inadmissible and must be rejected. `expires: null` (outcomes
are durable, unlike routes and world snapshots). `significance` comes from Vol V Ch.5; this faculty never
computes its own reward number.

## 4.10 Acceptance Tests

### Functional
```
FT-1  Outcomes are written only on verified ACK
  Given:  a route is dispatched and no <verb>_complete arrives within expected_ms
  Then:   an outcome is written with failure=no_ack AND arrived=false
          AND no success is recorded anywhere

FT-2  Routes are RECALLED, not re-solved
  Given:  N successful verified traversals to the same target in a compatible world
  When:   the same goal recurs
  Then:   recall returns the remembered route AND the planner does not re-solve from scratch
          AND the route is still validated against the CURRENT world before dispatch

FT-3  Repeated failure changes behaviour
  Given:  a direct LEAP route that has failed repeatedly (verified)
  Then:   its confidence is below the safer multi-leg route's, the multi-leg route is chosen,
          and the leap stops being attempted — with no dialogue about it

FT-4  Favourites accrue, never coded
  Given:  a fresh install and a week of use
  Then:   surface affinity exists and is non-uniform AND no hardcoded favourite list exists in the codebase

FT-5  Register aborts are not failures
  Given:  a traversal aborted because David started typing
  Then:   the route's confidence is unchanged

FT-6  World change is not failure
  Given:  a remembered route whose target window has been resized beyond compatibility
  Then:   still_valid=false, the planner re-solves, and confidence is unchanged
```

### Stability
```
ST-1  ⚖ Constitutional containment (the test WO-094 demands)
  Given:  the learning path
  Then:   it holds NO handle to the identity kernel, personality store, or permanent-memory writer
          AND any attempted write to identity/values/personality/memory-truth is REJECTED and raised

ST-2  Store loss degrades, never breaks
  Given:  the learning store is deleted
  Then:   recall returns None; routes are planned fresh; movement still works; nothing is fabricated
          about remembered places

ST-3  Body change invalidates stale learning
  Given:  outcomes recorded at max_jump_d = 60 and a body now at 75 (or a different embodiment)
  Then:   incompatible records are not used for recall

ST-4  Bounded growth
  Given:  months of traversals
  Then:   the store stays bounded (compaction in the integration window), recall latency stays flat
```

### Integration
```
IT-1  Verified consequence chain
  Ch.2 plans → Vol XI dispatches → body ACKs → Ch.4 records → Ch.2's next plan is cheaper/safer
  Assert: removing the ACK removes the learning entirely (no ACK, no record) — learning cannot
          exist without embodied verification.

IT-2  Upgrade path to Vol XXVIII without rewrite
  Given:  the TraversalOutcome record set
  Then:   it is sufficient as an RL episode log (state = world+body, action = leg verbs,
          outcome = arrival/smoothness, reward = Significance) — Vol XXVIII's policy layer consumes
          it directly, and no schema change is required to start training.

IT-3  Growth is shown, never narrated
  Given:  a route whose confidence has risen substantially
  Then:   the observable change is in movement (fewer preparatory beats, tighter timing, direct route
          preferred) AND eLo says nothing about having improved
```

## 4.11 Open Questions (flagged for Chief Architect / David)

- **OQ-4.1** Where does the spatial learning store physically live — a faculty-local JSONL, or inside the
  Vol VIII memory system? Recommend **faculty-local and bounded**, precisely because §4.2 forbids it a
  handle to the permanent-memory writer (Memory Ownership invariant). Vol XXI may *read* it for narrative.
- **OQ-4.2** Confidence asymmetry: how much faster should confidence fall than rise? This is a felt-quality
  call ("cautious" vs "timid"). Recommend a modest asymmetry and tune from David's observation, not from
  theory.
- **OQ-4.3 (David L3-adjacent).** Does accrued affinity ever get **surfaced in speech** — "I like it up
  here"? That crosses from spatial preference into stated self-description. Recommend: private cognitive
  state, expressible through *where he goes and how long he stays*, and only narratable through Vol XXI
  with verified history behind it (Reality Before Narrative).

## 4.12 References

- `engineering/work_orders/WO-094_Window_Events_Noticing_And_Choosing.md` §D + §LEARNING IS PART OF DONE.
- `engineering/work_orders/WO-049_Desktop_World_SelfAware_Parkour.md` §049-B2 (continuity wiring;
  "EMERGENT — favourites accrue, never coded").
- `Volume_XXVIII/00_Adaptive_Learning_Reinforcement.md` — Movement Faculty as RL domain #1; "reuse
  `memory/significance_engine.py` — do NOT invent a reward scalar."
- `ARCHITECTURAL_PRINCIPLES.md` — Learning From Consequences (ADR-Exec-005); verified capability becomes
  instinct through repetition; The Executive grows quieter.
- `Volume_XIII/02` (the planner that asks recall) · `Volume_XI/` (the ACK that is the only evidence) ·
  `Volume_VIII/` (memory ownership) · `Volume_V/` Ch.5 (Significance), Ch.6/7 (Reflection & Growth) ·
  `Volume_XXI/` (narrating growth, if ever).
- Code: `memory/significance_engine.py` (reuse), `blender/unity_events.json` (ACK source).

---

```
Chapter 4 — Spatial Learning & Favourites
Status: READY FOR REVIEW
Implementation: PENDING (no traversal outcome recorded today)
Hard boundary: ADR-Exec-005 — improves HOW WELL he moves; never identity/values/truth (ST-1 enforces it)
Faculty Contract: Included · Lifecycle: Included · Envelope: Included (evidence[] mandatory)
Acceptance Tests: FT ×6, ST ×4, IT ×3 · Open Questions: 3
```

READY FOR REVIEW
