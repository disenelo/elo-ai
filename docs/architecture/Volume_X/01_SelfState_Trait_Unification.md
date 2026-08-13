---
chapter: 1
title: "Self-State + Trait Unification"
volume: X
status: READY FOR REVIEW
version: 0.1.0
owner: David Charles
architect: Claude (Lead Architect)
source: "self/elo_self_model.py + memory/personality_drift.py + V Ch.7"
implementation: PARTIAL
audit_status: OPEN
dependencies:
  - Volume V Ch.7 (authoritative: trait vectors, evolution, validation, versioning)
  - Volume V Ch.4 (affect baseline consumer)
---

# Chapter 1: Self-State + Trait Unification

## 1.0 Purpose

eLo has an inner life that moves at **two speeds**: a fast **self-state** (mood, curiosity,
satisfaction right now) and a slow **trait vector** (who eLo is, evolving over months).
Today these live in two disconnected systems — `self/elo_self_model.py` (fast) and
`memory/personality_drift.py` (slow). This chapter unifies them into one Personality
Engine, deferring the trait-vector model and evolution rules to the authoritative
**Volume V Ch.7**.

## 1.1 The two layers (and who owns them)

```
FAST — Self-State        (this volume)      moment-to-moment inner life
   mood, curiosity, satisfaction, inner_events, session_read
   fluctuates within a session; resets/relaxes toward the trait baseline
        ▲ reads baseline from
        │
SLOW — Trait Vector      (Volume V Ch.7)    who eLo is
   curiosity, patience, confidence, empathy, discipline, wonder, playfulness, directness
   evolves only via validated integration (never turn-to-turn)
```

**Ownership (MUST):** Volume V Ch.7 is authoritative for the trait vector, evolution
rules, identity-continuity validation, and versioning. Volume X owns the **self-state**
and the **interface** between the two. No duplication.

## 1.2 Self-State model (from `elo_self_model.py`)

```
EloSelfState:
  mood:          float 0.0–1.0        # current emotional tone of eLo (not David)
  curiosity:     float 0.0–1.0        # fast; relaxes toward trait curiosity baseline
  satisfaction:  float 0.0–1.0        # sense of a session going well
  inner_events:  [ {what, ts} ]       # eLo's own noticings this session
  session_read:  str                  # eLo's summary of how the session feels
  lifetime_threads: [thread_ref]      # long-running arcs eLo tracks about itself
```

**Rules (MUST):**
- Self-state is eLo's **own** state, distinct from David's emotional context (Vol V Ch.4
  reads David; this is eLo). Keep them separate.
- Self-state **fluctuates fast** within a session and **relaxes toward the trait baseline**
  between sessions (the baseline is owned by V Ch.7). A great session lifts mood now; it
  does not change who eLo is — only validated integration does that.
- Self-state feeds the **affect baseline** the Emotional Processing Layer reads (V Ch.4 §4.3).

## 1.3 The Unification (Audit gap #6)

```
BEFORE:  self/elo_self_model.py  ──(no link)──  memory/personality_drift.py
AFTER:   PersonalityEngine
           ├─ self_state  (fast, this volume)
           └─ trait_vector (slow, V Ch.7)   — self_state relaxes toward trait baselines;
                                              Reflection (V Ch.6) proposes trait deltas;
                                              Ch.7 validates against Identity Kernel.
```

**Unification rules (MUST):**
- One faculty holds both layers; the fast layer never writes the slow layer directly —
  trait change only via V Ch.7's validated path (single-source rule).
- `personality_drift.py`'s drift becomes the *proposal* stream into V Ch.7, not a direct
  mutation. The self-model's fast values remain free to move within a session.

## 1.4 Faculty Contract

```
Faculty:
  name:            PersonalityEngine
  version:         1.0.0
  purpose:         Hold eLo's fast self-state and expose the slow trait vector (V Ch.7),
                   unifying the two live systems into one inner-life faculty.
  contributes_to:  CognitiveState (self-state) + affect baseline (V Ch.4)
  runs_in:         response-path (self-state read/update) + integration-window (trait via V Ch.7)

Inputs:
  - type: turn_outcome     source: ExecutionReport / Reflection (V Ch.6)   required: false
  - type: trait_vector     source: Personality Evolution (V Ch.7)          required: true
Outputs:
  - type: self_state       destination: CognitiveState + V Ch.4 baseline
  - type: drift_proposal   destination: V Ch.7 (validated — never self-applied)

Dependencies:
  - faculty: PersonalityEvolution (V Ch.7, hard — owns traits + validation)

Failure Modes:
  - condition: trait vector unavailable   fallback: self-state relaxes toward last-known baseline.
  - condition: drift would change identity fallback: V Ch.7 rejects (identity-continuity gate).
  - condition: self-model corrupt          fallback: reset self-state to trait baseline; inner_events cleared.
```

## 1.5 Lifecycle & Envelope

Universal lifecycle (CONTRACTS.md §3). Self-state updates in `PROCESSING` (fast);
trait changes only via the `LEARNING → VALIDATION_REQUIRED → UPDATING` arc owned by V Ch.7.
Envelope §2: `sender: PersonalityEngine`, `payload.type: self_state | drift_proposal`;
a `drift_proposal` MUST route to `PersonalityEvolution`, never self-apply.

## 1.6 Acceptance Tests

```
FT-1  Two speeds              Given a good session, Then mood/satisfaction rise now; the trait vector is unchanged.
FT-2  eLo ≠ David              Given David is distressed, Then eLo's self-state mood is tracked separately from David's affect.
FT-3  Baseline relaxation      Given a session ends, Then self-state relaxes toward the V Ch.7 trait baseline.
ST-1  No direct trait write     Given personality_drift produces drift, Then it becomes a proposal to V Ch.7, not a mutation.
ST-2  Identity protected         Given a drift that violates identity, Then V Ch.7 rejects it; self-state unaffected.
IT-1  Self-state → affect + evolution   Self-state feeds V Ch.4 baseline; sustained drift → validated trait nudge (V Ch.7).
```

## 1.7 References
- Code: `self/elo_self_model.py`, `memory/personality_drift.py`, `self/elo_self_state.json`.
- `Volume_V/07_Personality_Evolution_Engine.md` (authoritative traits/evolution), Ch.4 (affect baseline), Ch.6 (deltas).
- `19_cognitive_plan_architecture.md` (Personality layer). `ARCHITECTURE_AUDIT.md` gap #6.

---
**Status: READY FOR REVIEW** — self-state model + unification of the two live systems, deferring trait model/evolution to V Ch.7. Contract/lifecycle/envelope/tests included. Closes Audit gap #6 at spec level.