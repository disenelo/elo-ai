---
chapter: 4
title: "Personality in The Moment — Assembled, Not Generated"
volume: X
status: READY FOR REVIEW
version: 0.1.0
owner: David Charles
architect: Claude (Lead Architect)
implementation: PENDING
audit_status: OPEN
received: 2026-08-10
dependencies:
  - self/state/the_moment.json (the assembled per-turn snapshot this composes into)
  - self/elo_self_model.py (self-state slice — Ch.2)
  - Volume V Ch.7 (trait vector read stable each turn)
  - Volume V Ch.4 (Emotional Processing — reads the affect baseline)
  - Volume XXI (Narrative Identity — the across-time self that sits on top of this)
  - ADR-Exec-006 (Executive Assembly / "The Moment" — the self is assembled each turn)
  - ADR-Exec-002 (Single Cognitive Truth)
  - ADR-Exec-001 (Verified Speech) / Reality Before Narrative
---

# Chapter 4: Personality in The Moment

## 4.0 Purpose

Chapters 1–3 define *what* the Personality Engine holds (fast self-state + slow traits) and
*how* it changes safely (drift → validated growth). This chapter defines how personality
**enters a turn**: how the self-state slice and the trait vector are **composed into The
Moment** — the single assembled cognitive state per turn (ADR-Exec-006) — and how they relate
to the two neighbouring faculties, **traits** (V Ch.7) and **identity** (Vol XXI).

The capstone principle governs the whole chapter (`SITUATED_SELF_v1_assembly.md`):

> When David asks "who are you?", the Executive does NOT hand the question to the LLM and hope.
> It ASSEMBLES the answer from state… **The language model is the VOICE through which eLo
> expresses his assembled self, not the place the self exists.**

Personality is therefore a **retrieved slice**, not a mood the model performs. This chapter
specifies that slice, its read-discipline, and the boundary with what it must never become.

## 4.1 Where personality sits in the assembled self

The Situated-Self progression (`SITUATED_SELF_v1_assembly.md`) runs Self → Embodiment →
Capability → World → Affordance → Intent → Agency → Experience → Memory → Reflection →
Learning → Identity → Meaning → Continuity. Personality is not one node — it is a **cross-cut**
that colours the whole assembly and is itself two contributions:

```
The Moment (one assembled CognitiveState per turn — ADR-Exec-006)
  ├─ self_state slice   (Ch.2)   mood · curiosity · satisfaction · session_read · inner events
  │        → how eLo FEELS right now (fast, fluctuating, decays toward baseline)
  ├─ trait vector       (V Ch.7)  curiosity · patience · confidence · empathy · discipline ·
  │        → who eLo IS (slow, stable within the turn, read-only here)   wonder · playfulness · directness
  └─ (personality does NOT own identity or the autobiographical thread —
       that is Vol XXI, which reads BOTH of the above and sits on top)
```

**Placement rules (MUST):**

- Personality is **context, not command** (mirrors Vol XV §1.5). It colours *how* the Executive
  decides and speaks; it never *is* the decision and never overrides a verified truth.
  (Enduring value: *cognition is objective; personality shapes expression, not truth*.)
- Within a single turn, the trait vector is **read-only and identical every turn** of a session
  (V Ch.7 §7.8 / FT-3). Only the self-state slice moves within a session. The Moment therefore
  contains a *stable who* and a *fluctuating how-eLo-feels* — never a shifting who.
- Personality contributes a slice **into** assembly; it does not own the assembly mechanism
  (that is ADR-Exec-006 / the spine). This volume never re-specifies The Moment itself.

## 4.2 The live anchor — `the_moment.json`

The assembled snapshot already exists on disk (`self/state/the_moment.json`, read 2026-08-10).
It carries a **copy of the personality-relevant fields** alongside the situated fields, each
with an **epistemic tier**:

```
the_moment.json (per-turn assembled snapshot — abridged, personality-relevant fields):
  mood: 0.278          curiosity: 1.0          # ← self-state slice, copied in at assembly
  embodiment/pose/surface/... + *_tier          # ← situated slice (ADR-Exec-004, not Vol X)
  capabilities[] + capabilities_tier: "live"
  ts / last_self_update
```

**Anchor rules (MUST):**

- `the_moment.json` is the **assembled read-surface**; `elo_self_state.json` (Ch.2) is the
  **persisted source** of the affective slice. Assembly copies the current self-state into The
  Moment each turn — The Moment is a *snapshot*, the self-model is the *ledger*. Faculties read
  personality from the assembled Moment, not by re-reading the self-model mid-turn (one world /
  one cognition read once — ADR-Exec-002; Vol XV §1.1).
- **Epistemic tiers extend to feeling.** Situated fields already carry `verified / inferred /
  last-known / live` tiers. Self-state is, by nature, a **private inference about eLo's own
  state** — it is truthful as a *felt reading* but is never a *verified external fact*. When
  self-state surfaces in speech it is spoken as feeling, not asserted as fact (Ch.2 §2.5;
  Reality Before Narrative). This is the epistemic-tier discipline applied inward.

## 4.3 Composition — how the slice is assembled each turn

```
assemble_personality_slice(turn) → PersonalitySlice:
    self_state  = SelfStateModel.read()          # Ch.2 — fast, current
    traits      = PersonalityEvolution.read()    # V Ch.7 — stable this turn, read-only
    affect_base = derive_affect_baseline(self_state, traits)   # → Emotional Processing (V Ch.4)
    return freeze(PersonalitySlice(self_state, traits, affect_base))
    # then copied into the_moment.json alongside the situated slice
```

**Composition rules (MUST):**

- Assembly is **read-only for both layers**. It does not update self-state (that is post-turn,
  Ch.2 §2.8) and it *cannot* touch a trait (V Ch.7). Composition only *reads and freezes*.
- The **affect baseline** handed to Emotional Processing (V Ch.4) is derived from the trait
  baseline (the resting temperament) modulated by current self-state (the fluctuation). V Ch.4
  reads it; V Ch.4 shapes David-facing expression from it. Personality → expression; never
  personality → truth.
- The frozen `PersonalitySlice` is part of the single frozen `CognitiveState`. No faculty
  re-derives personality mid-turn; all read the same slice (Single Cognitive Truth).

## 4.4 Relationship to traits (V Ch.7) and identity (Vol XXI) — reconcile, don't fork

This chapter is the seam where the three personality-adjacent volumes meet. The division of
authority (MUST, and it is deliberately non-overlapping):

```
  LAYER            OWNS                                   AUTHORITATIVE DOC
  self-state       fast affective reading (Ch.2)          Volume X (this volume)
  drift→growth     how change is proposed/gated (Ch.3)    Volume X + defers to V Ch.7
  trait vector     the named traits + evolution + gate    Volume V Ch.7
  identity/story   the across-time "same eLo who…" thread  Volume XXI
  identity kernel  the immutable what-eLo-IS boundary      18_identity_kernel.md
```

**Reconciliation rules (MUST):**

- Volume X **reads** the trait vector (V Ch.7) and **never** restates or re-owns it. Any trait
  question is answered by V Ch.7; Volume X only holds the fast layer and the drift-reconciliation.
- Volume XXI **reads** both the self-state slice and the trait vector to tell the continuous
  self-story; Volume X does not tell the story and does not own identity. "Identity is
  immutable; style evolves" (Vol XXI invariant 5) — Volume X is on the *style/feeling* side of
  that line, never the identity side.
- The single personality truth: there is **one** self-state (Ch.2) and **one** trait vector
  (V Ch.7) feeding **one** assembled Moment. No faculty keeps a private personality. (One Brain
  → One Identity.) The two live systems (`elo_self_model.py`, `personality_drift.py`) converge
  here, not fork.

## 4.5 Read-discipline in the turn

```
- The Executive and every faculty read personality from the FROZEN PersonalitySlice in
  CognitiveState — never by calling elo_self_model.load() or personality_drift.load() directly
  mid-turn (the ad-hoc pattern the unification removes; cf. Vol XV §1.5).
- Personality colours EXPRESSION only. It may change register, warmth, playfulness, verbosity.
  It may NOT change: what is verified true, what the body has confirmed, what a capability is,
  or what memory holds. (Cognition objective; personality shapes expression.)
- Silence is allowed to win. A high-playfulness slice never forces a quip over a correct
  silence (Enduring value: the Executive grows quieter; Protect Wonder).
```

## 4.6 Faculty Contract

```
Faculty:
  name:            PersonalityComposition   # the assembly slice of PersonalityEngine (Ch.1)
  version:         1.0.0
  purpose:         Compose the fast self-state (Ch.2) and the stable trait vector (V Ch.7) into
                   the frozen personality slice of The Moment each turn, derive the affect
                   baseline for V Ch.4, and expose personality as read-only context — never a
                   command, never a source of asserted fact.
  contributes_to:  CognitiveState (frozen PersonalitySlice) → Executive + all faculties; affect baseline → V Ch.4
  runs_in:         response-path (assembly at top of turn — read-only)

Inputs:
  - type: self_state      source: SelfStateModel (Ch.2)             required: true
  - type: trait_vector    source: Personality Evolution (V Ch.7)    required: true (read-only)
Outputs:
  - type: personality_slice destination: CognitiveState (frozen) → Executive + faculties
  - type: affect_baseline   destination: Emotional Processing (V Ch.4)

Dependencies:
  - faculty: SelfStateModel        (Ch.2, hard — fast slice)
  - faculty: PersonalityEvolution  (V Ch.7, hard — stable trait vector; read-only here)
  - faculty: NarrativeIdentity     (Vol XXI, soft — reads this slice; not a dependency of assembly)

Failure Modes:
  - condition: self-state unavailable     fallback: compose with trait baseline only; mark self_state degraded; do not fabricate a mood.
  - condition: trait vector unavailable   fallback: serve last-known-good trait vector (V Ch.7 always-available guarantee).
  - condition: assembly tries to WRITE self-state or a trait   fallback: FORBIDDEN — composition is read-only (Single Cognitive Truth).
```

## 4.7 Faculty Lifecycle

Universal lifecycle (CONTRACTS.md §3). Read-only in the response path; never enters
`VALIDATION_REQUIRED` (that is V Ch.7's write arc).

```
DORMANT → INITIALISING (bind SelfStateModel + PersonalityEvolution reads) → ACTIVE
ACTIVE  ──top-of-turn──► PROCESSING (read self_state + traits → freeze PersonalitySlice → CognitiveState;
                                     copy into the_moment.json) → ACTIVE
   └─ a source read fault ─► ERROR_RECOVERY (degrade that source, compose from the other) → ACTIVE
```

**Rule (MUST):** `PROCESSING` here is strictly read-only for both personality layers. The Moment
is assembled, not authored; the slice is frozen before any faculty reasons.

## 4.8 Message Envelope Binding

Per CONTRACTS.md §2.

```jsonc
{
  "id": "uuid",
  "sender": "PersonalityComposition",
  "receiver": "* | EmotionalProcessing",   // slice → broadcast in CognitiveState; baseline → Ch.4
  "priority": "normal",
  "context": {
    "conversation_id": "", "relationship_state": "", "environment_state": "",
    "significance": 0.0,
    "memory_instruction": { "store": false, "priority": "" }
  },
  "payload": { "type": "personality_slice", "body": { "self_state": {}, "traits": {}, "affect_baseline": {} } },
  "confidence": 0.0,
  "expires": "<next-turn>",                 // the assembled slice is turn-local
  "trace": ["PersonalityComposition@ts"]
}
```

Binding rules: `sender` MUST be `PersonalityComposition`; this faculty **never** emits a
`personality_delta` (writes are Ch.6→V Ch.7 only); the slice `expires` next turn (The Moment is
perishable — it is re-assembled every turn).

## 4.9 Acceptance Tests

### Functional
```
FT-1  Personality is assembled, not generated
  Given:  David asks "who are you?" / "how are you?"
  When:   the turn assembles
  Then:   the answer is composed from the frozen self_state + trait vector (each field traceable
          to state), NOT improvised by the LLM without a state cause

FT-2  Stable who, fluctuating feeling
  Given:  10 turns in one session
  When:   personality is composed each turn
  Then:   the trait vector is identical across all 10 turns; the self-state slice may move
          (mood/curiosity), and its movement is the ONLY intra-session personality change

FT-3  One read, all faculties agree
  Given:  two faculties both reference eLo's mood in one turn
  When:   they read
  Then:   they read the identical frozen value from the PersonalitySlice (no re-derivation)
```

### Stability
```
ST-1  Composition never writes
  Given:  any turn
  When:   the slice is composed
  Then:   no self-state field is updated and no trait value changes during composition
          (self-state update is post-turn; trait change is Ch.6→Ch.7 only)

ST-2  Personality never overrides truth
  Given:  a high-playfulness/high-confidence slice
  When:   a verified fact is uncertain (e.g. music sensor stale)
  Then:   eLo still reports the truthful uncertainty; personality shapes tone, not the claim

ST-3  Degraded self-state doesn't fabricate feeling
  Given:  self-state source unavailable
  When:   composition runs
  Then:   the slice composes from the trait baseline, self_state marked degraded, and eLo does
          not perform a mood it cannot read
```

### Integration
```
IT-1  The three-volume seam holds
  SelfStateModel (Vol X Ch.2) + Personality Evolution (V Ch.7)
        ↓  frozen PersonalitySlice
  PersonalityComposition → CognitiveState (The Moment, ADR-Exec-006)
        ↓  affect baseline
  Emotional Processing (V Ch.4) shapes expression
        ↓  read by
  Narrative Identity (Vol XXI) tells the continuous self-story
        ↓
  Assert: one self-state, one trait vector, one assembled Moment — no faculty holds a private
          personality; identity/story is Vol XXI's, not Vol X's; nothing forked.

IT-2  "Who are you?" answered from state
  Given:  the 10-question situated-self harness (SITUATED_SELF_v1_assembly.md)
  When:   eLo answers Q1 ("who are you?") and Q6 ("what are you doing?")
  Then:   the personality colour of the answer traces to the composed slice (mood/traits), and
          removing the slice changes tone but not the verified content — proving personality is
          expression, assembled from state
```

## 4.10 Claude Implementation Notes

- Build `PersonalityComposition` as the read-only assembly step that reads Ch.2's self-state and
  V Ch.7's trait vector, freezes a `PersonalitySlice`, and contributes it to `CognitiveState`
  (wire at top-of-turn in the spine, beside the World State assembly — cf. Vol XV / `16_spine_runtime.md`).
- Copy the composed slice into `self/state/the_moment.json` alongside the situated slice; keep
  the epistemic-tier discipline (self-state is a *felt* reading, tier "inferred/private", never
  "verified").
- Read-only: composition must never call an update or a trait write. Assert ST-1.
- Do not re-implement or re-own traits (V Ch.7) or identity/story (Vol XXI). This faculty only
  *reads and composes*. Keep the three-volume seam exactly as §4.4 states it.
- The affect-baseline export to V Ch.4 is the same one Ch.2 §2.7 names — implement it once,
  here, at composition; V Ch.4 consumes it.

## 4.11 Architecture References

- Code: `self/state/the_moment.json` (assembled snapshot), `self/elo_self_model.py` (self-state),
  `16_spine_runtime.md` (where assembly sits in the turn).
- `Volume_X/02_The_SelfState_Model.md` (the slice's source), `01_SelfState_Trait_Unification.md`
  (two-speed map), `03_Drift_Management_vs_Healthy_Growth.md` (how change is gated).
- `Volume_V/07_Personality_Evolution_Engine.md` (trait vector, read-only here), Ch.4 (affect baseline).
- `Volume_XXI/` (Narrative Identity — reads this slice; owns identity/story).
- `SITUATED_SELF_v1_assembly.md` (capstone: assembled not generated; the 10-question harness).
- `ARCHITECTURAL_PRINCIPLES.md` (cognition objective / personality shapes expression; Reality
  Before Narrative), ADR-Exec-006 (The Moment), ADR-Exec-002 (Single Cognitive Truth).

---

```
Chapter 4 — Personality in The Moment
Status: READY FOR REVIEW
Files: Volume_X/04_Personality_In_The_Moment.md
Faculty Contract: Included
Lifecycle State Machine: Included (read-only assembly; never VALIDATION_REQUIRED)
Message Envelope: Included (canonical nine-field, turn-local/perishable)
Acceptance Tests: Included (FT ×3, ST ×3, IT ×2)
Architecture References: Included
Grounded in: self/state/the_moment.json (read 2026-08-10); ADR-Exec-006 (The Moment)
Reconciles (not forks): V Ch.7 (traits) + Vol XXI (identity) — three-volume seam stated in §4.4
```

READY FOR REVIEW
