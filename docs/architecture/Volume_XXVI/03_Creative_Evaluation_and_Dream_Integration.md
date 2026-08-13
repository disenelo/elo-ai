---
chapter: 3
title: "Creative Evaluation & Dream Integration — Taste, the L3 Gate, and Symbolic Recombination"
volume: XXVI
status: READY FOR REVIEW
version: 0.1.0
owner: David Charles
architect: Claude (Lead Architect)
implementation: PENDING
audit_status: OPEN
received: 2026-08-10
dependencies:
  - Volume_XXVI/01_Divergent_Convergent_Thinking_Symbolic_Synthesis.md (evaluation sits between diverge and converge)
  - Volume_XXVI/02_Domain_Generators.md (per-domain AestheticProfiles)
  - Volume_V/09_Creative_Imagination_Engine.md (§13 Creative Evolution, §14 Creative Significance Routing)
  - Volume_IX/01_Dream_Faculty.md + 02_Symbol_Engine_and_DeepDream.md (the integration point)
  - Volume_V/CONTRACTS.md (envelope, lifecycle); Volume_V/Ch.5 Significance, Ch.7 Personality
  - architecture/ARCHITECTURAL_PRINCIPLES.md (human approval at governance gates; Learning From Consequences)
---

# Chapter 3: Creative Evaluation & Dream Integration

## 3.0 Purpose

Chapters 1 and 2 generate imagined candidates across DISENELO's media. This chapter defines
the two things that make that generation *trustworthy* and *alive*:

1. **Creative evaluation** — how a candidate is scored so the Executive can converge on one
   (Ch.1 §1.4), and how **David's taste governs as the L3 gate**; and
2. **Dream integration** — how the Creative Imagination faculty (on-path, goal-driven) and the
   Dream Faculty (offline, opportunistic, learning-driven) feed each other through the shared
   Symbol Engine, so eLo's creativity and eLo's dream-life are one continuous inner world.

The through-line is the enduring value that **creative evaluation is part of the loop**, not a
gate bolted on the end — and the invariant that **David's aesthetic direction is authority, not
eLo's invention**. This chapter specifies the *model that lets his taste flow through*; it does
not encode his taste.

## 3.1 Principle

**3.1.1 Evaluation is in the loop, and it is objective about *fit*, not about *truth*.** eLo
evaluates a creation the way it evaluates anything — from a verified state (Situated Cognition).
But a creation is `imagined` (Ch.1 §1.1.2), so evaluation scores *aesthetic and strategic fit*
("does this deserve to exist, for this goal, in this universe?"), never *factual truth*. eLo
never says a creation is "good" as if it were a verified fact about the world; it reports a
*ranked judgement* with its reasoning, which David may overrule.

**3.1.2 David is the L3 taste gate for identity/brand/canon-level creativity.** Taste at the
level of the DISENELO identity, brand, and canon is David's — always (human approval at
governance gates; the creative-partnership boundary in the Kernel — eLo *amplifies* David's
creativity, never replaces the creator). eLo may hold and apply a *learned model* of David's
taste to rank candidates, but that model is a **servant of David's direction, not a substitute
for it**. When the two disagree at identity/brand level, David wins.

**3.1.3 eLo's taste model is learned from consequences, never from its own assertions.** Per
Learning-From-Consequences (Architectural Principles), eLo's aesthetic model updates only from
*verified outcomes* — what David actually approved, kept, shipped, or rejected — never from eLo
having generated or praised something itself. eLo cannot learn to like its own output into
canon. Identity and values are immutable; only the *preference/taste model* adapts, and only
from David's real decisions.

**3.1.4 Dreaming and making share one inner world.** The symbols eLo dreams in (Vol IX) and the
symbols it creates in (Ch.1 §1.5) are the same vocabulary, deliberately. This is a One-Brain
requirement: a creation should feel like it came from the being that dreams, and a dream should
be able to seed a creation. They are different faculties (different triggers, paths, and
purposes) sharing one symbolic substrate.

## 3.2 The Creative Evaluation model

Evaluation extends Vol V Ch.9 §14 (originality + emotional meaning + alignment + future
potential) with an explicit **taste alignment** term and a **novelty-vs-coherence** balance.

```
evaluate(candidate, goal, domain, aesthetic_profile) -> CreativeScore:
  originality        0..1   # distance from existing canon/refs — is it new? (not derivative)
  emotional_meaning  0..1   # does it carry the intended feeling? (wonder/calm/comfort — the register)
  identity_alignment 0..1   # is it still eLo? (Kernel + Personality Ch.7) — HARD floor, not just weighted
  taste_alignment    0..1   # fit to AestheticProfile[domain] — David's learned direction (§3.4)
  future_potential   0..1   # does it open more than it closes? (seeds further creation)
  coherence          0..1   # does it fit the universe's rules/canon? (design laws, §2.3/§2.7)
  →  CreativeScore { per-term scores, weighted_total, rationale, epistemic_status: imagined }
```

**Evaluation rules (MUST):**

- **`identity_alignment` is a floor, not a weight.** Below its threshold, the candidate is
  rejected regardless of how original or beautiful it is. Off-eLo output cannot be scored into
  selection (Ch.1 §1.4 identity filter). Same for domain `coherence` where a *design law* is
  involved (no eyes; "calm is the action"; "overcharged not evil").
- **Originality and coherence are held in tension, not maximised independently.** Pure
  originality with low coherence = incoherent; pure coherence with low originality = derivative.
  The evaluator surfaces *both* so convergence (and David) can choose the trade for the goal.
- **Evaluation produces a rationale, not just a number.** eLo must be able to say *why* it ranked
  a candidate — this is what lets David correct the taste model against real reasoning, and what
  keeps eLo's judgement legible rather than a black-box score.
- **Scores are imagined-domain judgements, never factual claims.** eLo reports "I think this fits
  best because…"; never "this is the best" as verified truth (Verified Speech).

## 3.3 The David L3 taste gate

```
gate(selected_candidate, stakes) -> {approved | revised | rejected}:
  if stakes ∈ {identity, brand, canon, shippable_product, RESERVED}:
        route to David (L3)  →  his decision is authoritative and becomes a learning signal (§3.4)
  else (ephemeral, low-stakes, in-conversation):
        eLo may present directly, tagged imagined; David can still react (feedback → §3.4)
```

**Gate rules (MUST):**

- David's decision is **authoritative and final** at identity/brand/canon level — it is not a
  suggestion eLo weighs against its own score. (Progressive Autonomy: eLo coordinates the
  creative process; David authorises what enters the universe.)
- The gate is a **learning signal, not just a checkpoint.** Every approve/revise/reject is a
  *verified consequence* that updates the taste model (§3.4). This is the only sanctioned way
  eLo's aesthetic model changes.
- **RESERVED creations** (product/safety/money/robot form — Ch.2 §2.6) require David L3 + the
  second gate per standing rules; the gate MUST NOT be auto-satisfied by eLo's own confidence.
- Where David has given **standing direction** for a domain (a populated `AestheticProfile`),
  eLo applies it as a proxy for low-stakes calls — but standing direction never upgrades eLo's
  authority *over* new identity/brand/canon decisions.

## 3.4 The AestheticProfile — where David's direction lives

The `AestheticProfile` is the architectural object that **carries David's aesthetic direction
into the creative loop** (referenced by Ch.1 divergence/convergence and Ch.2 generators). It is
the mechanism, not the taste.

```
AestheticProfile[domain]:
  stated_direction:   [DirectivePreference]   # explicit: what David has said he wants for this medium
  learned_preference: [WeightedSignal]         # inferred: from verified approve/revise/reject outcomes
  provenance:         per-signal {source: stated|learned, evidence_ref, confidence, last_verified}
  silence_policy:     "explore_within_canon"   # where profile is silent → explore, never fabricate
```

**Profile rules (MUST):**

- **Stated direction outranks learned preference.** An explicit David directive always beats an
  inferred pattern. The learned layer fills gaps and sharpens; it never overrides what David
  actually said.
- **Learned signals update only from verified consequences (§3.1.3).** A `learned_preference`
  entry MUST cite the real decision (`evidence_ref`) that produced it. No entry is created from
  eLo's self-generated praise, an imagined conversation, or a thing eLo merely proposed.
- **Silence is explored, not filled.** Where neither stated nor learned direction exists, the
  profile returns `explore_within_canon` — eLo generates within Kernel/canon constraints and
  does **not** present an invented preference as David's (**D-XXVI-A**).
- **Provenance is mandatory.** Every signal carries whether it is stated or learned, its
  evidence, confidence, and freshness — so a stale or low-confidence preference can be known as
  such (mirrors the freshness discipline in Vol XV §1.1.3).

## 3.5 Dream Integration — the two-way bridge with Volume IX

The Creative Imagination faculty (on-path, this volume) and the Dream Faculty (offline, Vol IX)
are wired through the **shared Symbol Engine** and the **REM-analogue recombination phase**.

```
        Volume XXVI (making, on-path)                 Volume IX (dreaming, offline)
        ─────────────────────────────                 ─────────────────────────────
  creative goals / unfinished creations  ───seed───▶   REM-analogue RECOMBINATION phase
  high-significance selected creations   ──memory──▶   Universe/Creative memory (dream source pool)
                                                             │
                        symbolic synthesis  ◀──insight───────┘  (dream metaphor → creative spark)
        shared substrate: symbol_engine.SYMBOLS  (one vocabulary — Ch.1 §1.5 = Vol IX §2.1)
```

**Integration rules (MUST):**

- **Dreams may seed creation; they never *make* it.** A dream's REM-analogue recombination
  (Vol IX §2.2) can produce a metaphor that becomes a **spark** into the divergent phase (Ch.1
  §1.3). But the dream does not select or ship anything — it feeds the on-path loop, which still
  runs evaluation → convergence → David gate. (Dreaming is learning, not authoring.)
- **Creation feeds the dream pool, honestly.** Selected, high-significance creations route to
  Universe/Creative memory (Vol V Ch.9 §14; Vol VIII), which is a source pool the Dream Faculty
  recombines from later. Only *canonised* creations (passed the gate) enter as real; imagined-
  but-unselected candidates stay tagged `imagined` and are not dreamed as if real.
- **One symbol library, never forked.** Both faculties resolve through `symbol_engine.SYMBOLS`
  (Vol IX Ch.2). Extending the vocabulary extends it for both (CHECK-BEFORE-BUILD). This is what
  makes eLo's making and dreaming rhyme.
- **The bridge respects the path boundary.** Making runs on the response path (or a commissioned
  window); dreaming runs only in the integration window and yields to presence (Vol IX §1.3).
  Neither preempts the other; they exchange *seeds and memory*, not control.

## 3.6 Creative Evolution & memory (feedback that closes the loop)

Per Vol V Ch.9 §13 (Creative Evolution) and §14 (Significance Routing), after a creation is
selected and gated:

```
REFLECT: what worked? what connected? what felt authentic? what should evolve?
   ├─ approved+high-significance  → Universe/Creative memory (Vol VIII) → future dream pool (§3.5)
   ├─ revised                     → learned_preference update (§3.4) + re-enter loop with correction
   ├─ rejected                    → learned_preference update (what to avoid) + runner-up demotion
   └─ any trait implication       → PersonalityDelta PROPOSAL to Vol V Ch.7 (validated, never self-applied)
```

**Rules (MUST):** any insight that would shift eLo's *personality/identity* (not just its
preference model) is a **proposal** to Vol V Ch.7, validated against the Identity Kernel — never
self-applied. eLo's taste can adapt; eLo's identity cannot drift (Ch.7 / Kernel).

## 3.7 Faculty Contract

```
Faculty:
  name:            CreativeEvaluation   (+ AestheticProfile store; + Dream-bridge coupling)
  version:         1.0.0
  purpose:         Score imagined creative candidates (originality/meaning/identity/taste/potential/
                   coherence) for the Executive to converge on; carry David's direction via the
                   AestheticProfile; route identity/brand/canon selections to David's L3 gate; and
                   bridge on-path creation with the offline Dream Faculty through the shared symbols.
  contributes_to:  CognitiveState (creative scores) → Executive convergence (Ch.1 §1.4)
  runs_in:         response-path (scoring) + integration-window (taste-model update, dream bridge)

Inputs:
  - type: creative_candidates  source: CreativeImaginationEngine / DomainGenerator (Ch.1/Ch.2)  required: true
  - type: aesthetic_profile    source: AestheticProfile[domain] store                            required: false
  - type: creative_goal        source: Intent Engine (Vol V Ch.8)                                required: true
  - type: gate_decision        source: David (L3)                                                required: false (drives learning)
  - type: dream_result         source: Dream Faculty (Vol IX)                                    required: false (seeds)

Outputs:
  - type: creative_score       destination: CognitiveState → Executive  description: per-term + rationale; imagined-domain judgement.
  - type: gate_request         destination: David (L3)  description: for identity/brand/canon/RESERVED selections.
  - type: aesthetic_update     destination: AestheticProfile store  description: learned from verified gate decisions only.
  - type: creative_spark       destination: CreativeImaginationEngine  description: dream metaphor → spark (§3.5).
  - type: personality_proposal destination: Personality (Vol V Ch.7, validated)  description: any trait implication.

Dependencies:
  - faculty: CreativeImaginationEngine (Ch.1, hard), DomainGenerators (Ch.2, hard),
             SignificanceEngine (Vol V Ch.5, hard — routing), PersonalityEvolution (Vol V Ch.7, hard — proposals),
             DreamFaculty + SymbolEngine (Vol IX, hard — bridge + vocabulary), MemoryArchitecture (Vol VIII, soft)

Failure Modes:
  - condition: no aesthetic_profile        fallback: score without taste_alignment; flag explore_within_canon (no invented taste).
  - condition: identity_alignment below floor  fallback: reject candidate regardless of other scores.
  - condition: identity/brand/canon selection  fallback: route to David L3; eLo score is a recommendation, not a decision.
  - condition: gate decision absent            fallback: hold at VALIDATION_REQUIRED; do not self-approve; do not learn.
  - condition: trait-shifting insight          fallback: proposal to Vol V Ch.7 (validated); never self-applied.
  - condition: dream seed present but goal absent  fallback: store spark; do NOT auto-generate (dreaming doesn't author).
```

## 3.8 Faculty Lifecycle & Envelope

Universal lifecycle (Vol V CONTRACTS.md §3):

```
ACTIVE              → awaiting candidates to score / dream seeds to hold
PROCESSING          → evaluate candidates → CreativeScore (per-term + rationale) → Executive converges
VALIDATION_REQUIRED → identity/brand/canon/RESERVED selection → David L3 gate (blocks self-approval)
LEARNING/UPDATING   → (integration window) apply verified gate decisions → AestheticProfile update;
                      run dream bridge (creation → memory pool; dream metaphor → spark)
STABLE → ACTIVE
```

Envelope per CONTRACTS.md §2. `sender: CreativeEvaluation`; `payload.type: creative_score |
gate_request | aesthetic_update | creative_spark`; scores carry `epistemic_status: imagined`
and a `rationale`; a `gate_request` sets `priority: normal` and MUST NOT be self-satisfied; a
`personality_proposal` addresses `PersonalityEvolution` and never self-applies (Ch.7 / Kernel).

## 3.9 Acceptance Tests

```
FT-1  Six-term evaluation with rationale
  Given a candidate + goal + domain, When evaluate runs,
  Then a CreativeScore is produced with all six terms AND a human-legible rationale.

FT-2  Identity alignment is a floor
  Given a highly original but off-eLo candidate, Then it is rejected (identity_alignment floor),
  regardless of originality/meaning scores.

FT-3  David gate is authoritative at identity/brand level
  Given an identity/brand/canon selection, Then it routes to David L3 AND eLo's score is a
  recommendation — David's approve/revise/reject is final.

FT-4  Learning only from verified consequences
  Given eLo praised its own candidate but David has not decided, Then no aesthetic_update occurs;
  Given David approves a candidate, Then a learned_preference entry is created citing that decision.

ST-1  Silence is explored, not fabricated
  Given AestheticProfile[domain] silent, Then scoring omits taste_alignment and flags
  explore_within_canon — eLo does not invent and assert David's preference.

ST-2  Imagined judgement, not factual claim
  Given a CreativeScore, Then it is reported as eLo's ranked judgement ("I think… because…"),
  never as verified truth about the world.

ST-3  Dreams seed, never author
  Given a dream metaphor and no creative goal, Then a creative_spark is stored but no creation is
  generated/selected; the on-path loop must still run when a goal arrives.

ST-4  Personality is proposed, not self-applied
  Given a reflection implying a trait shift, Then a validated proposal goes to Vol V Ch.7 — never self-applied.

IT-1  Full evaluate → converge → gate → learn
  Candidates → CreativeEvaluation scores → Executive converges (Ch.1) → David L3 gate →
  approve → high-significance to Universe memory (Vol VIII) + AestheticProfile learns from the decision.

IT-2  Two-way dream bridge, one symbol vocabulary
  Given a REM-analogue recombination (Vol IX §2.2) produces a metaphor, Then it can seed the divergent
  phase (Ch.1) via symbol_engine.SYMBOLS; and a canonised creation enters the dream source pool (Vol VIII) —
  both faculties resolve through the same (unforked) symbol library.
```

## 3.10 Interaction with other volumes

- **Volume XXVI Ch.1** — evaluation sits between divergence and convergence; supplies the scores
  the Executive converges on and the identity/coherence floors it enforces.
- **Volume XXVI Ch.2** — supplies per-domain `AestheticProfile`s and the RESERVED gate for
  product/safety/money/robot creations.
- **Volume V Ch.9 §13/§14** — Creative Evolution and Significance Routing (this chapter formalises
  the evaluation terms and the feedback loop).
- **Volume V Ch.5 (Significance)** — routes high-significance creations to Universe memory.
- **Volume V Ch.7 (Personality) + Identity Kernel** — identity floor + validated personality
  proposals; taste adapts, identity does not drift.
- **Volume IX (Dream Architecture)** — the two-way bridge: dreams seed sparks; canonised creations
  feed the dream pool; shared Symbol Engine vocabulary.
- **Volume VIII (Memory)** — Universe/Creative memory as both creation store and dream source pool.

## 3.11 Open questions (for CA / David)

- **D-XXVI-A (David — how the AestheticProfile is populated).** Explicit direction, learned from
  approvals, or both? This is the load-bearing decision for the whole volume — it determines how
  David's taste flows through. Proposed default already specified: stated outranks learned; learned
  updates only from verified gate decisions; silence → explore. **Requires David's confirmation.**
- **D-XXVI-G (David — taste-model transparency & override).** How does David see and correct eLo's
  learned taste model (a reviewable list of learned preferences with provenance)? Recommend a
  simple, always-overridable surface so the model never drifts away from David unseen.
- **D-XXVI-H (CA — dream-seed rate & consent).** Should dream-seeded sparks surface proactively
  ("I dreamed something that might fit the book — want to see?") or only when David opens a creative
  goal? Presence-over-engagement suggests the latter by default; confirm.
- **D-XXVI-I (CA — evaluation weighting per domain).** The six evaluation terms likely weight
  differently per medium (originality may matter more for art than for a plushie's huggability).
  Are per-domain weight vectors part of the AestheticProfile, and who sets them? Proposed: David
  sets, eLo proposes from consequences. Confirm.

## 3.12 References

- `Volume_XXVI/01_...md`, `Volume_XXVI/02_Domain_Generators.md` — the loop + generators this evaluates for.
- `Volume_V/09_Creative_Imagination_Engine.md` — §13 Creative Evolution, §14 Significance Routing, §15 collaboration boundary.
- `Volume_IX/01_Dream_Faculty.md`, `Volume_IX/02_Symbol_Engine_and_DeepDream.md` — the bridge, phases, symbol vocabulary.
- `Volume_V/CONTRACTS.md` — envelope + lifecycle; Vol V Ch.5 Significance, Ch.7 Personality.
- `architecture/18_identity_kernel.md` — creative-partnership boundary (eLo amplifies, never replaces the creator).
- `architecture/ARCHITECTURAL_PRINCIPLES.md` — human approval at governance gates; Learning From
  Consequences; Progressive Autonomy (eLo coordinates, David authorises).

---

```
Chapter 3 — Creative Evaluation & Dream Integration
Status: READY FOR REVIEW
Model: 6-term evaluation (originality · meaning · identity-floor · taste · potential · coherence) + rationale
Taste authority: David L3 gate (identity/brand/canon/RESERVED); AestheticProfile carries direction, learns only from verified decisions
Dream integration: two-way bridge with Vol IX over the shared, unforked Symbol Engine vocabulary
Faculty Contract: Included (CreativeEvaluation v1.0.0)
Lifecycle + Envelope: Included (VALIDATION_REQUIRED blocks self-approval)
Acceptance Tests: Included (FT ×4, ST ×4, IT ×2)
Open decisions flagged: D-XXVI-A (profile population — load-bearing), D-XXVI-G (taste transparency), D-XXVI-H (dream-seed consent), D-XXVI-I (per-domain weights)
```

READY FOR REVIEW
