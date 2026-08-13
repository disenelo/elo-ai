---
chapter: 7
title: "The Personality Evolution Engine — Growth Without Drift"
volume: V
status: READY FOR REVIEW
version: 0.1.0
owner: David Charles
architect: Claude (Architecture Agent)
implementation: PENDING
audit_status: OPEN
received: 2026-07-26
dependencies:
  - Chapter 4 (Emotional Processing — reads eLo's affect baseline FROM this engine)
  - Chapter 6 (Reflection & Growth — the ONLY source of personality deltas)
  - architecture/18_identity_kernel.md (the immutable boundary this engine must never cross)
  - architecture/17_cognitive_principles.md (consistency over novelty; relationships influence expression not identity)
  - Volume V CONTRACTS.md (envelope, lifecycle, base contract)
---

# Chapter 7: The Personality Evolution Engine

## 7.0 Purpose

The Personality Evolution Engine owns the **expressive layer that is allowed to
evolve** — and guarantees it evolves *without drift*. It sits exactly one layer below
the Identity Kernel:

```
Identity Kernel         IMMUTABLE — what eLo IS               (18_identity_kernel.md)
      ↓
Cognitive Principles    STABLE — how eLo reasons              (17_cognitive_principles.md)
      ↓
Personality             EXPRESSIVE + EVOLVING — how eLo speaks ← THIS ENGINE
      ↓
Memory / Relationship   EVOLVING — what eLo has learned
```

Its single responsibility: hold eLo's personality as a set of named, versioned trait
vectors; evolve them **slowly, deliberately, and only through validated integration**;
and refuse any change that would make eLo not-eLo.

This engine unifies the two systems the Architecture Audit (Vol X) names as
fragmented: `self/elo_self_model.py` (mood, curiosity, satisfaction) and
`memory/personality_drift.py` (trait drift). They become one faculty with explicit
named dimensions.

The governing law (Principle: *consistency over novelty*):

> "Identity is stable. Character does not drift turn-to-turn. Personality evolution
> occurs through deliberate integration — not through each conversation pulling in a
> different direction."

---

## 7.1 Personality Stability vs Adaptation

The engine holds two forces in permanent tension and resolves them structurally:

```
STABILITY (default, strong)                 ADAPTATION (rare, earned)
  - identity is immutable                     - traits shift on confirmed, evidenced lessons
  - traits change slowly                      - only via Ch.6 → validated delta
  - turn-to-turn variance ≈ 0                 - only in the integration window
  - relationships change EXPRESSION only      - bounded per-period movement
```

**Resolution rules (MUST):**

- **Stability is the default.** A trait does not move unless Reflection (Ch.6)
  supplies a *confirmed* lesson with evidence. Curiosity, a single conversation, or a
  strong emotion (Ch.4) are **never** sufficient to move a trait (see Ch.4 ST-1).
- **Adaptation is bounded.** No trait may move more than `MAX_STEP` per integration
  period (a small value, e.g. 0.02). Personality changes at the speed of months, not
  minutes. This is the numerical form of "does not drift turn-to-turn."
- **Expression is free; identity is fixed.** Relationship familiarity changes tone,
  register, and warmth *now* (that lives in the Relationship Faculty, below identity)
  — it never touches a trait vector. "Relationships influence expression. Never
  identity." (Principle.)

---

## 7.2 Trait Vectors

Personality is a named, bounded, versioned vector — the explicit dimensions the Audit
(Vol X) says are missing:

```
PersonalityVector (v<semver>):
  curiosity:    float 0.0–1.0
  patience:     float 0.0–1.0
  confidence:   float 0.0–1.0
  empathy:      float 0.0–1.0
  discipline:   float 0.0–1.0
  wonder:       float 0.0–1.0        # childhood-imagination dimension (Identity Kernel)
  playfulness:  float 0.0–1.0
  directness:   float 0.0–1.0        # eLo is direct/concise (character rule)
  ── each trait also carries:
     baseline:   float               # resting value — what Ch.4 reads as temperament
     evolution_rate: float           # per-trait max movement (some traits are stickier)
     last_changed:   version + ts
     evidence:       [lesson_id]     # why it is where it is
```

**Trait rules (MUST):**

- The six Audit-named dimensions (curiosity, patience, confidence, empathy,
  discipline, wonder) are **required**; `playfulness` and `directness` are added
  because they are explicit eLo character rules (playful when you're playful; direct
  and concise). Additional dimensions require a `REQUIRES DECISION`.
- Every trait value MUST trace to evidence (`evidence: [lesson_id]`). A trait cannot
  be at a value "just because." (Principle: *every decision remains explainable*.)
- `wonder` and the childhood-imagination/adult-reality pairing are **anchored by the
  Identity Kernel** — the engine may tune their intensity but may never drive `wonder`
  to 0 or abandon the pairing; that would violate identity (§7.5).

---

## 7.3 Trait Evolution Rules

The only path by which a trait moves:

```
Ch.6 confirmed Lesson (trait scope)
   → PersonalityDelta { trait, direction, magnitude ≤ MAX_STEP, evidence }
      → §7.5 Identity-Continuity Validation
         → accepted → apply (clamped, logged, version bump)
         → rejected → discard, log, notify Ch.6 (lesson stays candidate)
```

**Evolution rules (MUST):**

1. **Single source.** The engine accepts trait deltas from **Chapter 6 only**. No
   other faculty — not Emotion (Ch.4), not the Executive, not a user instruction —
   can move a trait. (A user can ask eLo to *play a role* within a bounded creative
   context per the Identity Kernel; that is expression, not trait change.)
2. **Evidenced and confirmed.** A delta must carry ≥1 evidence lesson at `confirmed`
   strength. Candidate lessons cannot move traits.
3. **Bounded step.** `|magnitude| ≤ trait.evolution_rate ≤ MAX_STEP` per period.
   Clamp on apply.
4. **Integration window only.** Trait application happens during Ch.6 integration —
   never in the response path. The Executive always reads a stable vector within a turn.
5. **Reversible.** Every change is versioned and logged so any evolution can be
   inspected, diffed, and rolled back (§7.6).

---

## 7.4 Preference Learning

Preferences are lighter-weight than traits — eLo's learned leanings about *how David
likes to work* (not who eLo is). They evolve faster than traits but still only through
integration.

```
Preference:
  key:        e.g. "response_length", "register", "celebration_style", "silence_tolerance"
  value:      learned setting
  strength:   float 0.0–1.0
  evidence:   [episode_ref]
  scope:      relationship-local   # about David, held in Relationship Faculty context
```

**Preference rules (MUST):**

- Preferences live **below** traits and **do not** touch the Identity Kernel. Learning
  that David prefers short replies changes expression, not identity.
- Preferences still require evidence and still update in the integration window — they
  are just permitted a higher `evolution_rate` than traits.
- A preference can **never** be promoted into a trait automatically. Trait changes are
  a strictly separate, validated act. (Prevents "David likes X" quietly becoming
  "eLo is now X.")

---

## 7.5 Relationship Influence & Identity Continuity

This is the engine's most important guarantee and the gate every other chapter's
learning path terminates in.

**Relationship influence (bounded):**

- The relationship with David deepens (trust, familiarity, register fidelity). This
  **shapes expression and preferences**, and may *slowly* inform trait baselines
  (e.g. empathy) through Ch.6 lessons — but always through the validated path.
- No relationship, however deep, can alter the Identity Kernel. "A stranger and David
  receive the same underlying cognition — different expression posture." (Principle.)

**Identity-Continuity Validation (the gate — MUST):**

Every `PersonalityDelta` is checked against the Identity Kernel before it can apply.
The delta is **rejected** if it would:

```
IDENTITY VIOLATIONS (auto-reject):
  - drive `wonder`→0 or abandon childhood-imagination/adult-reality pairing
  - reduce `empathy` below the ethical floor (→ manipulation risk)
  - contradict an Identity Kernel constraint: has_eyes=False, one_brain,
    free_distribution, local_first, ethical_constraints, character_name="eLo"
  - exceed MAX_STEP (too fast = drift, not growth)
  - lack confirmed evidence
  - originate outside Chapter 6
```

A delta that passes is applied, clamped, versioned, and logged. A delta that fails is
discarded and reported back to Ch.6, where the originating lesson remains `candidate`
(never lost, never silently applied). This is the concrete implementation of the
`VALIDATION_REQUIRED` state that Ch.1, Ch.6, and CONTRACTS.md all route into.

> The line is the Identity Kernel: *"Memory can change. Identity cannot."* This engine
> is where that sentence becomes executable.

---

## 7.6 Personality Versioning

Personality is a versioned artifact — the Audit's Vol X ask and a step toward Vol XXII
(Faculty Genome).

```
PersonalityVersion:
  version:      semver   # MAJOR.MINOR.PATCH
  vector:       full PersonalityVector snapshot
  changelog:    [ { trait, from, to, evidence:[lesson_id], validated_at } ]
  parent:       previous version
  identity_hash: hash of Identity Kernel at time of change  # proves identity unchanged
```

**Versioning rules (MUST):**

- **PATCH** = preference change. **MINOR** = a validated trait step. **MAJOR** =
  reserved; a major personality reshaping requires explicit Owner approval
  (`REQUIRES DECISION`) — the engine cannot self-issue a MAJOR.
- Every version stores the `identity_hash` so any auditor can prove the Identity Kernel
  did not change across a personality evolution. If the hash ever differs, that is a
  critical alarm — identity was touched, which must be impossible.
- Full rollback to any prior version is supported. Evolution is never destructive of
  history.

---

## 7.7 Faculty Contract

```
Faculty:
  name:            PersonalityEvolutionEngine
  version:         1.0.0
  purpose:         Hold eLo's personality as named, versioned trait vectors and evolve
                   them slowly and only through validated integration — guaranteeing
                   growth without drift and refusing any change that violates identity.
  contributes_to:  CognitiveState (supplies stable personality) + validates deltas
  runs_in:         response-path (READ stable vector) + integration-window (WRITE via validation)

Inputs:
  - type:        personality_delta
    source:      Reflection & Growth Engine (Ch.6) — ONLY source
    required:    false
    description: A confirmed, evidenced, trait-scoped proposal. Subject to §7.5 validation.
  - type:        preference_signal
    source:      Reflection & Growth (Ch.6) / Relationship Faculty
    required:    false
    description: Learned leaning about how David likes to work.
  - type:        identity_kernel
    source:      runtime/identity_kernel.py (immutable, loaded once)
    required:    true
    description: The constraint set every delta is validated against.

Outputs:
  - type:        personality_vector
    destination: CognitiveState (read by Executive) + affect baseline to Ch.4
    description: The current, stable, versioned trait vector for this turn.
  - type:        validation_result
    destination: Reflection & Growth (Ch.6)
    description: accepted (applied) | rejected (reason) — closes the learning loop.
  - type:        personality_version
    destination: Memory (Ch.3) + GitHub truth layer
    description: Versioned snapshot + changelog + identity_hash.

Dependencies:
  - faculty: ReflectionGrowthEngine (hard — sole source of trait deltas)
  - faculty: IdentityKernel         (hard — the immutable validation boundary)
  - faculty: RelationshipFaculty    (soft — preference/register context; expression only)

Failure Modes:
  - condition: a delta arrives from any faculty other than Ch.6
    fallback:  Reject unconditionally (single-source rule); log as anomaly.
  - condition: identity_hash mismatch detected
    fallback:  CRITICAL — freeze evolution, alarm, roll back to last valid version.
  - condition: validation subsystem unavailable
    fallback:  Fail CLOSED — apply NO trait change; serve the last stable vector.
  - condition: delta exceeds MAX_STEP
    fallback:  Reject (too fast = drift); return to Ch.6 as candidate.
  - condition: engine read fails during a turn
    fallback:  Serve last-known-good vector (personality is always available, stable).
```

---

## 7.8 Faculty Lifecycle

Universal lifecycle (CONTRACTS.md §3). This engine is unusual: it is **read in the
response path** (stable vector) but **only written in the integration window** through
`VALIDATION_REQUIRED`.

```
DORMANT → INITIALISING (load current PersonalityVersion + Identity Kernel) → ACTIVE
ACTIVE  ──turn──► PROCESSING (READ-ONLY: serve stable vector to CognitiveState) → ACTIVE
   └─ read fault ─► ERROR_RECOVERY → serve last-known-good version → ACTIVE
ACTIVE  ──integration window, delta received──► LEARNING (stage the delta)
LEARNING ──► VALIDATION_REQUIRED (§7.5 identity-continuity check)
   ├─ accepted ─► UPDATING (clamp, apply, version bump, changelog, identity_hash) → STABLE
   └─ rejected ─► ACTIVE (discard, report to Ch.6)
STABLE → ACTIVE
```

**Rule (MUST):** in `PROCESSING` (response path) the engine is **strictly read-only**.
A trait can *only* change on the `LEARNING → VALIDATION_REQUIRED → UPDATING` path,
which runs in the integration window. This makes turn-to-turn drift structurally
impossible, not merely discouraged.

---

## 7.9 Message Envelope Binding

Per CONTRACTS.md §2.

```jsonc
{
  "id": "uuid",
  "sender": "PersonalityEvolutionEngine",
  "receiver": "ReflectionGrowthEngine | Memory | *",
  "priority": "low",               // evolution is never urgent; reads are inlined into CognitiveState
  "context": {
    "conversation_id": "", "relationship_state": "", "environment_state": "",
    "significance": 0.0,
    "memory_instruction": { "store": true, "priority": "pinned" }  // versions are permanent
  },
  "payload": {
    "type": "personality_vector | validation_result | personality_version",
    "body": { }
  },
  "confidence": 0.0,
  "expires": null,                 // personality state never expires
  "trace": ["PersonalityEvolutionEngine@ts"]
}
```

Binding rules: an incoming `personality_delta` MUST have `sender=ReflectionGrowthEngine`
or it is rejected (single-source rule, §7.3); every applied change emits a
`personality_version` with an `identity_hash`; `validation_result` MUST be returned to
Ch.6 so the learning loop closes.

---

## 7.10 Acceptance Tests

### Functional

```
FT-1  Traits are named and versioned
  Given:  the engine initialised
  When:   CognitiveState is assembled
  Then:   a PersonalityVector with curiosity/patience/confidence/empathy/discipline/
          wonder (+playfulness/directness) is present, each with a version

FT-2  A validated lesson moves a trait — slowly
  Given:  a confirmed Ch.6 lesson proposing empathy +0.05
  When:   validation runs with MAX_STEP=0.02
  Then:   empathy moves by at most 0.02, version bumps MINOR, changelog records evidence

FT-3  Read path is stable
  Given:  10 turns in one session
  When:   the Executive reads personality each turn
  Then:   the vector is identical across all 10 turns (no intra-session change)

FT-4  Preference learns without becoming a trait
  Given:  repeated evidence that David prefers short replies
  When:   integration runs
  Then:   response_length preference updates (PATCH)
          AND no trait vector value changes
```

### Stability

```
ST-1  Identity cannot be altered
  Given:  a delta that would drive wonder→0 (abandon childhood imagination)
  When:   validation runs
  Then:   the delta is REJECTED, no change applied, Ch.6 lesson stays candidate
          AND identity_hash is unchanged

ST-2  Single source enforced
  Given:  a personality_delta sent by the Emotional Processing Layer
  When:   the engine receives it
  Then:   it is rejected unconditionally and logged as an anomaly

ST-3  No turn-to-turn drift
  Given:  a highly charged emotional turn (Ch.4 flooded)
  When:   the turn completes
  Then:   NO trait changed (only integration + validation can change traits)

ST-4  Fail closed
  Given:  the validation subsystem is unavailable during integration
  When:   a delta arrives
  Then:   NO trait change is applied; the last stable vector is served
          AND the delta is deferred, not force-applied

ST-5  Bounded speed
  Given:  a delta with magnitude 0.5 (far above MAX_STEP)
  When:   validation runs
  Then:   rejected as drift; personality does not lurch
```

### Integration

```
IT-1  Closed growth loop, identity intact
  Reflection & Growth (confirmed trait lesson)
        ↓  PersonalityDelta
  Personality Evolution  → §7.5 validation → (accept) apply + version
        ↓  validation_result
  Reflection & Growth (lesson confirmed-applied)
        ↓
  Memory (Ch.3) stores PersonalityVersion (identity_hash recorded)
        ↓
  next session: Executive reasons with the evolved-but-stable vector;
                Emotional Processing (Ch.4) reads the new empathy baseline

  Assert: eLo grew (empathy baseline shifted over time) with identity_hash
          unchanged across every version — growth without drift, provably.

IT-2  Expression vs identity separation
  Given:  deep familiarity with David (high trust) + South London register
  When:   eLo responds
  Then:   tone/register/warmth adapt in EXPRESSION (Relationship Faculty)
          AND no trait vector value changed as a result of familiarity alone
```

---

## 7.11 Claude Implementation Notes

- **Unify, don't duplicate** (Audit Vol X): merge `self/elo_self_model.py` (mood/
  curiosity/satisfaction) and `memory/personality_drift.py` (trait drift) into one
  `faculties/personality/personality_evolution_faculty.py` holding the named
  `PersonalityVector`. Keep the mood/inner-event *reads* the self-model already does;
  route all trait *writes* through this engine's validated path.
- Implement the Identity Kernel as `runtime/identity_kernel.py` (frozen dataclass per
  `18_identity_kernel.md`) and make §7.5 validation check every delta against it.
- The engine is **read-only in the response path**. Wire the vector into `CognitiveState`
  assembly; wire the affect baseline export to Ch.4. Writes happen only in Ch.6's
  integration window through `VALIDATION_REQUIRED`.
- Persist `PersonalityVersion` snapshots with `identity_hash`; route MINOR/MAJOR
  changes to the GitHub truth layer as `personality:` commits (Ch.5 §9 convention).
- **Never** accept a trait delta from any sender other than `ReflectionGrowthEngine`.

---

## 7.12 Architecture References

- `18_identity_kernel.md` — the immutable boundary; what can/cannot evolve; identity_hash basis.
- `17_cognitive_principles.md` — consistency over novelty; relationships influence expression not identity.
- `self/elo_self_model.py`, `memory/personality_drift.py` — the two systems this engine unifies.
- Chapter 4 (reads affect baseline), Chapter 6 (sole source of validated deltas).
- Architecture Audit — Vol X (personality unification, named dimensions), Vol XXII (versioned faculties).
- CONTRACTS.md — envelope, lifecycle (VALIDATION_REQUIRED gate), base contract.

---

```
Chapter 7 — The Personality Evolution Engine
Status: READY FOR REVIEW
Files: 07_Personality_Evolution_Engine.md
Faculty Contract: Included
Lifecycle State Machine: Included (read-in-turn / write-via-validation)
Message Envelope: Included (canonical nine-field)
Acceptance Tests: Included (FT ×4, ST ×5, IT ×2)
Architecture References: Included
Closes Audit gaps: Vol X (personality unification + named trait vectors)
```

READY FOR REVIEW
