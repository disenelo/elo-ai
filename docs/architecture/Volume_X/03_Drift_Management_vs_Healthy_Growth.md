---
chapter: 3
title: "Drift Management vs Healthy Growth — Change Without Losing eLo"
volume: X
status: READY FOR REVIEW
version: 0.1.0
owner: David Charles
architect: Claude (Lead Architect)
implementation: PENDING
audit_status: OPEN
received: 2026-08-10
dependencies:
  - memory/personality_drift.py (the live drift system this chapter reconciles)
  - self/elo_self_model.py (fast self-state — the other input to the unification)
  - Volume V Ch.7 (AUTHORITATIVE: validated trait evolution, identity-continuity gate, versioning)
  - Volume V Ch.6 (Reflection & Growth — the ONLY legitimate source of trait deltas)
  - Volume XXI Ch.3 (Narrative Coherence — drift-vs-growth at the identity/story layer)
  - ADR-Exec-005 (Learning From Consequences — adaptation sits AFTER verification)
---

# Chapter 3: Drift Management vs Healthy Growth

## 3.0 Purpose

eLo must be able to **change** — a companion that is identical in month six to day one is dead,
not stable. But change has two faces, and the difference between them is the whole safety
question of the Personality Engine:

- **Healthy growth** — eLo becomes more himself over time, through *validated* lessons, in
  small bounded steps, provably without touching identity. (Owned by V Ch.7.)
- **Drift** — eLo slides somewhere he never chose to go, because each conversation pulled him a
  little, and nothing checked it against who he is. (The failure this chapter guards against.)

The governing law, from V Ch.7 (Principle: *consistency over novelty*):

> "Identity is stable. Character does not drift turn-to-turn. Personality evolution occurs
> through deliberate integration — not through each conversation pulling in a different
> direction."

This chapter reconciles the **live drift system** (`memory/personality_drift.py`) with that
law. It does **not** restate V Ch.7's trait model, evolution rules, or validation gate — V
Ch.7 is authoritative for those. This chapter owns: (a) an honest account of what the live
drift code does today; (b) the definition that separates drift from growth; (c) the contract
that turns drift from a *self-applied mutation* into a *validated proposal*.

## 3.1 What the live drift system does today (honest account)

`memory/personality_drift.py` is live and running. Read plainly (Verify-Before-Claim):

```
It holds a SEPARATE personality model from V Ch.7's PersonalityVector:
    tone_profile:      { calm, expressive, grounded }
    interaction_bias:  { simplify_tendency, emotional_reflection, technical_focus }
It drifts these per SESSION from David's emotional history + session text:
    ±0.01–0.05 per value, capped by drift_rate (default 0.02)
    clamped to [0.2, 0.9]
    stability_lock: if instability detected, drift_rate → 0.01 and out-of-band values
                    are restored to baseline
It SELF-APPLIES the result: update() → save() to memory/personality_state.json.
```

**Three facts this creates — each a reconciliation item, not a criticism of the code:**

1. **It self-applies.** Drift is written straight to disk with **no identity-continuity
   validation** and **no Reflection gate**. Under V Ch.7's law this is exactly the pattern
   forbidden: a change that reaches the personality store without passing the validation gate
   or originating from Ch.6. It is *safe by construction* (bounded + clamped + stability-lock),
   but it is *architecturally unvalidated*. **This is the core of Audit gap #6.**
2. **It uses a different trait model.** `tone_profile` / `interaction_bias` are **not** the
   canonical `PersonalityVector` (curiosity/patience/confidence/empathy/discipline/wonder/
   playfulness/directness) that V Ch.7 owns. Two personality models exist in the running system.
3. **It drifts from David's inputs.** The signal is David's tone and words — i.e. change driven
   by *conversation*, which is precisely what "does not drift turn-to-turn / not each
   conversation pulling a different direction" warns against. It is per-session not per-turn (a
   mitigation), but the *source* is conversational pressure, not verified consequence.

## 3.2 Drift vs Growth — the definition

The line, made testable:

```
                        HEALTHY GROWTH                 DRIFT
  source                Ch.6 confirmed lesson          conversational pressure / raw signal
                        (verified consequence)         (tone counts, keyword hits)
  gate                  §7.5 identity-continuity        none (self-applied)
                        validation
  cadence               integration window only         per-session (or worse, per-turn)
  bound                 ≤ MAX_STEP, versioned           clamped band only, unversioned
  reversible            yes (versioned, identity_hash)   only by luck (last_update overwrite)
  explains itself       evidence: [lesson_id]            no cause trace
  can touch identity    NO (auto-rejected)               NO guarantee it won't
```

**The definition (MUST):** a change is **growth** iff it (1) originates from a Ch.6 confirmed,
evidenced lesson, (2) passes the V Ch.7 identity-continuity gate, (3) is bounded by `MAX_STEP`,
and (4) is versioned with an `identity_hash`. **Any change lacking any one of these is drift**
and must not reach the personality store directly. Bounded-and-clamped is *necessary but not
sufficient* — the live drift system is bounded but ungated, so it is still drift.

## 3.3 The reconciliation — drift becomes a proposal, never a mutation

Chapter 1 §1.3 states the target: *"`personality_drift.py`'s drift becomes the proposal stream
into V Ch.7, not a direct mutation."* This chapter specifies that migration.

```
TODAY:
  session signals → personality_drift.update() → save(personality_state.json)   [self-applied — drift]

TARGET (unified):
  session signals → drift analysis → DriftObservation (a candidate signal, NOT a write)
        → Reflection & Growth (V Ch.6): is there a CONFIRMED, evidenced lesson here?
              → if yes: PersonalityDelta → V Ch.7 §7.5 validation → (accept) apply + version
              → if no:  observation is logged as a candidate, applied to NOTHING
```

**Reconciliation rules (MUST):**

1. **No self-apply.** The drift analyser MUST NOT write the personality store. It emits a
   `DriftObservation` and stops. (This is the one behavioural change gap #6 requires; the math
   and clamps can stay — they just feed a proposal, not a `save()`.)
2. **Route through Ch.6, not around it.** A drift signal is a *hypothesis* about a lesson, not
   a lesson. Only Reflection & Growth may promote it to a `PersonalityDelta`, and only from a
   *confirmed* lesson with evidence (V Ch.7 §7.3 rule 2). Conversational pressure alone never
   moves a trait (Ch.4 ST-1; V Ch.7 §7.1).
3. **One trait model wins.** ✅ **DECIDED — David L3, Ruling D, 2026-08-10 (§3.6.A).**
   `tone_profile` / `interaction_bias` MUST be **reconciled onto the canonical
   `PersonalityVector` (Volume V Ch.7's model) — not kept alongside it.** The parallel model does
   not survive. The two routes previously offered — (a) map the drift dimensions onto existing
   traits + preferences (calm→patience baseline; simplify_tendency/technical_focus→**preferences**
   per V Ch.7 §7.4), or (b) deprecate the drift dimensions once Reflection produces canonical
   deltas — are now **implementation routes to the same ruled end state**, chosen by the owning
   seat + CA, not by this document. Do not invent the dimension mapping here; do not ship two
   models.
4. **Adaptation sits after verification.** Per ADR-Exec-005, eLo adapts from *verified
   consequences*, never from having generated or heard language. A drift signal derived purely
   from conversation text is, at most, a candidate for Reflection to weigh against verified
   outcomes — never a direct adaptation. This keeps eLo from "learning" a hallucinated or merely
   spoken pattern.

## 3.4 Drift *detection* — the safety monitor (distinct from applying change)

Separately from *proposing* change, the Personality Engine must be able to **detect** unhealthy
drift as an alarm — the diagnostic side of "management." This reuses and generalises the live
`_detect_instability()` check.

```
DriftMonitor (read-only, raises alarms — never mutates):
  band check       — any trait/tone value outside its safe band → ALARM
  velocity check   — cumulative movement over a window > threshold → ALARM (too-fast = drift)
  identity check   — identity_hash changed across a version → CRITICAL (must be impossible)
  divergence check — self-state chronically far from trait baseline for many sessions →
                     surfaces to Reflection as a possible genuine growth signal (NOT auto-applied)
```

**Monitor rules (MUST):**

- The monitor **never applies or reverts** on its own beyond the existing stability-lock's
  restore-to-baseline safety (which is a *clamp*, not an evolution). Detection and application
  are separate faculties (detection here; application in V Ch.7).
- An `identity_hash` mismatch is **CRITICAL** — it means identity was touched, which V Ch.7
  §7.6 says must be impossible. Response: freeze evolution, alarm, roll back to last valid
  version (V Ch.7 failure mode).
- A chronic self-state / baseline divergence (fast layer persistently pulling one way over many
  sessions) is the *legitimate* signal that eLo may be genuinely growing. The monitor surfaces
  it **to Reflection**; it does not itself move a baseline. This is how the fast layer's
  accumulated pressure earns a hearing without ever bypassing the gate.

## 3.5 Faculty Contract

```
Faculty:
  name:            DriftManager       # the drift-reconciliation slice of PersonalityEngine (Ch.1)
  version:         1.0.0
  purpose:         Turn conversational/self-state drift signals into validated PROPOSALS (never
                   self-applied mutations), and monitor for unhealthy drift as an alarm —
                   guaranteeing all personality change flows through the V Ch.7 growth path.
  contributes_to:  Reflection & Growth (V Ch.6) via DriftObservation; alarms to governance
  runs_in:         integration-window (analysis + proposal) + always-on (monitor, read-only)

Inputs:
  - type: emotional_history   source: session emotional context (David)         required: false
  - type: session_summaries   source: session store                            required: false
  - type: self_state          source: SelfStateModel (Ch.2)                     required: false
  - type: personality_version source: Personality Evolution (V Ch.7)            required: true (for monitor)
Outputs:
  - type: drift_observation   destination: Reflection & Growth (V Ch.6) — a candidate, applied to nothing
  - type: drift_alarm         destination: governance / logs (band, velocity, identity_hash, divergence)

Dependencies:
  - faculty: ReflectionGrowthEngine (V Ch.6, hard — the ONLY promoter of an observation to a delta)
  - faculty: PersonalityEvolution   (V Ch.7, hard — the ONLY applier of a validated delta; owns versioning)

Failure Modes:
  - condition: drift analyser attempts to write personality_state.json   fallback: FORBIDDEN — emit DriftObservation instead (gap #6 fix).
  - condition: identity_hash mismatch across versions                     fallback: CRITICAL — freeze evolution, alarm, roll back (V Ch.7).
  - condition: value out of safe band                                      fallback: clamp/restore-to-baseline (stability-lock) + alarm; no evolution.
  - condition: Reflection unavailable                                      fallback: log observation as candidate; apply NOTHING (fail closed).
```

## 3.6 Decided rules and remaining RESERVED decisions

### 3.6.A ✅ DECIDED — Ruling D (David L3, 2026-08-10)

`CANON_RULINGS_2026-08-10.md` **Ruling D — DRIFT IS A PROPOSAL, NOT A WRITE**, verbatim:

> Personality drift may **NOT** self-apply to disk. Drift becomes a **validated proposal**
> through a gate. **One trait model wins: Volume V Ch.7's** — the parallel model in
> `memory/personality_drift.py` is reconciled to it, not kept alongside. Rationale: an ungated
> drift path means David's companion's personality can wander with nothing checking it.
> Identity is not allowed to drift unsupervised (ADR-Exec-005).

Two things this settles, both now binding canon rather than proposals of this chapter:

**D-1 — Drift is a validated PROPOSAL, never a direct write. (DECIDED.)** The behaviour §3.3
rule 1 specified as a target is now the ruled rule: the drift analyser MUST NOT write
`memory/personality_state.json` — it emits a `DriftObservation` and stops. Application belongs
to V Ch.7 alone, after the §7.5 identity-continuity gate, from a Ch.6 confirmed evidenced
lesson. **There is no ungated path to the personality store, and none may be added.** Bounded
and clamped is *not* validated (§3.2) — the existing self-apply is drift by this chapter's own
definition and is superseded.

**D-2 — One trait model: Volume V Ch.7's. (DECIDED — this closes D-X3-1.)** The canonical
`PersonalityVector` (curiosity/patience/confidence/empathy/discipline/wonder/playfulness/
directness) is **the** trait model. `tone_profile` / `interaction_bias` are **reconciled onto
it — not kept alongside it.** The two-models-in-one-running-system fact recorded in §3.1 fact 2
is therefore a *migration item*, not a standing state: it ends. Two personality models in one
mind is a One-Brain violation for the same reason two attention drivers were (Ruling B).

**What "reconciled, not kept" means for §3.3 rule 3.** That rule offered David two options —
(a) map the drift dimensions onto traits + preferences, or (b) deprecate them. **The ruling
picks reconciliation over preservation:** the drift dimensions do not survive as a second model.
Whichever mechanical route the seat takes, the end state is one model — V Ch.7's — and the
drift math survives only as a *signal source feeding proposals*, never as a store of record.
The remaining detail (which drift dimension lands on which trait vs. which V Ch.7 §7.4
*preference*) is mechanical mapping for the owning seat + CA, **not** a further David decision.

**Ruling D releases `WO-CANON-X`.**

### 3.6.B Still RESERVED (David L3 / Chief Architect)

These are **not** covered by Ruling D and remain **flagged, not made** (per project rules — do
not invent David's values):

- **D-X3-1 (trait-model unification).** — **✅ DECIDED 2026-08-10 by Ruling D. See §3.6.A/D-2:
  Volume V Ch.7's model wins; the drift model is reconciled to it, not kept.** Residual is the
  dimension-by-dimension mapping, which is the seat's + CA's mechanical work.
- **D-X3-2 (drift-rate reconciliation).** The live `drift_rate` (0.02, stability-lock 0.01) vs
  V Ch.7's `MAX_STEP` (~0.02): are these the same bound, and does the fast-layer clamp band
  `[0.2, 0.9]` stand? V Ch.7 owns `MAX_STEP`; this is a values call. — **STILL RESERVED.**
- **D-X3-3 (conversational-signal legitimacy).** To what degree may David's tone/words *ever*
  seed a trait proposal, given ADR-Exec-005 says adaptation follows *verified consequences*?
  (§3.3 rule 4.) — **STILL RESERVED**; likely: conversation seeds *preferences* freely, *traits*
  only via verified-consequence lessons. (Note: Ruling D settles that a drift signal may not
  *apply*; it does not settle whether such a signal may legitimately *seed a proposal at all*.)

These are the identity-level parts of Audit gap #6's closure. Volume X specifies the mechanism;
the remaining numeric/identity values are David's.

## 3.7 Acceptance Tests

### Functional
```
FT-1  Drift proposes, never applies
  Given:  a session with strong conversational drift signal
  When:   the drift analyser runs
  Then:   a DriftObservation is emitted to Reflection AND personality_state.json is NOT written

FT-2  Unconfirmed signal changes nothing
  Given:  a DriftObservation with no confirmed Ch.6 lesson behind it
  When:   integration runs
  Then:   no PersonalityDelta is produced and no trait/tone value changes

FT-3  Confirmed lesson grows, slowly
  Given:  a DriftObservation that Reflection confirms as an evidenced lesson (empathy)
  When:   it routes through V Ch.7 §7.5
  Then:   empathy moves ≤ MAX_STEP, version bumps, identity_hash unchanged (growth, logged)
```

### Stability
```
ST-1  Bounded-but-ungated is still drift
  Given:  the legacy self-apply path (bounded + clamped) is invoked
  When:   it tries to save() the personality store
  Then:   it is blocked/redirected to a DriftObservation (§3.2: bounded ≠ validated)

ST-2  Identity cannot move under any drift
  Given:  cumulative drift signals over many sessions all pushing wonder down
  When:   they route through the gate
  Then:   wonder never approaches 0; any delta that would is rejected; identity_hash constant

ST-3  Monitor alarms, doesn't act
  Given:  a value drifts out of its safe band
  When:   the DriftMonitor observes it
  Then:   it raises an alarm and the stability-lock clamps to baseline; the monitor applies no
          evolution of its own
```

### Integration
```
IT-1  Drift → Reflection → validated growth (the whole gap-#6 loop)
  DriftManager (session/self-state signal)
        ↓  DriftObservation (candidate — applied to nothing)
  Reflection & Growth (V Ch.6) confirms an evidenced lesson
        ↓  PersonalityDelta
  Personality Evolution (V Ch.7) §7.5 validation → accept → apply + version (identity_hash)
        ↓
  Assert: eLo changed only through the validated path; no self-applied write occurred anywhere;
          identity_hash unchanged across the change — drift became growth.

IT-2  Chronic fast-layer divergence earns a hearing (not a bypass)
  Given:  self-state curiosity sits far above the trait baseline for many sessions
  When:   the monitor surfaces the divergence to Reflection
  Then:   Reflection MAY (if it finds a confirmed lesson) propose a small baseline nudge via
          V Ch.7 — but the divergence alone never moves the baseline
```

## 3.8 Claude Implementation Notes

- Keep the drift math in `memory/personality_drift.py` (band, clamp, drift_rate, stability-lock,
  `_detect_instability`). The **one required change** for gap #6: replace the `save()` self-apply
  with emitting a `DriftObservation` to Reflection (V Ch.6). Assert FT-1 / ST-1.
- Do not build a second evolution path — application stays in V Ch.7 (single applier). This
  chapter's `DriftManager` only *proposes* and *monitors*.
- The `DriftMonitor` reuses `_detect_instability()` generalised to band/velocity/identity_hash/
  divergence checks; it is strictly read-only beyond the existing stability-lock clamp.
- **D-X3-1 is DECIDED (Ruling D, 2026-08-10):** build toward **one** trait model — V Ch.7's
  `PersonalityVector`. `tone_profile` / `interaction_bias` are reconciled onto it and do not
  persist as a second model. The mechanical dimension mapping is the seat's + CA's; the
  *outcome* (one model) is not negotiable.
- Do **not** resolve D-X3-2/3 in code — they are **STILL RESERVED** (§3.6.B). Wire the
  mechanism; leave the numeric bounds and conversational-signal legitimacy as configuration
  awaiting David L3.
- Reconcile with Volume XXI Ch.3, which handles drift-vs-growth at the *narrative/identity*
  layer; this chapter handles it at the *trait/personality* layer. Same principle, two layers —
  keep them consistent, do not duplicate.

## 3.9 Architecture References

- Code: `memory/personality_drift.py` (tone_profile, interaction_bias, drift_rate, clamp,
  stability-lock, `_detect_instability`), `memory/personality_state.json` (the store it writes
  today), `self/elo_self_model.py` (self-state signal source).
- `Volume_V/07_Personality_Evolution_Engine.md` — AUTHORITATIVE trait model, §7.3 evolution
  rules, §7.5 identity-continuity gate, §7.6 versioning + identity_hash; Ch.6 (sole delta source).
- `Volume_X/01_SelfState_Trait_Unification.md` §1.3 (drift → proposal), `02_The_SelfState_Model.md`
  (fast-layer decay).
- `Volume_XXI/03_Narrative_Coherence_and_Verified_Autobiography.md` — drift-vs-growth at the
  identity/story layer (sibling; do not duplicate).
- `ARCHITECTURAL_PRINCIPLES.md` — consistency over novelty; Learning From Consequences (ADR-Exec-005).
- `ARCHITECTURE_AUDIT.md` — gap #6.

---

```
Chapter 3 — Drift Management vs Healthy Growth
Status: READY FOR REVIEW
Files: Volume_X/03_Drift_Management_vs_Healthy_Growth.md
Faculty Contract: Included
Lifecycle: Deferred to V Ch.7 (application) + always-on read-only monitor
Message Envelope: Covered via DriftObservation / drift_alarm (routes to Ch.6 / governance)
Acceptance Tests: Included (FT ×3, ST ×3, IT ×2)
DECIDED 2026-08-10 (David L3, Ruling D): drift is a validated PROPOSAL never a direct write;
  ONE trait model — Volume V Ch.7's — with personality_drift.py's model reconciled to it, not kept.
  Closes D-X3-1. Releases WO-CANON-X.
RESERVED decisions still flagged: D-X3-2 (drift-rate), D-X3-3 (conversational-signal legitimacy)
Grounded in: memory/personality_drift.py (read 2026-08-10)
Closes (at spec level): Audit gap #6 — drift becomes a validated proposal, not a self-applied mutation
```

READY FOR REVIEW
