# WO-CANON-XXVI — Creative Intelligence: domain generators + the AestheticProfile + evaluation/gate

**Owner:** Builder (eLo OS — refine `CreativeImaginationEngine`; new `CreativeEvaluation` faculty + generators).
**Priority:** P4 — Horizon-2 (post-Presentable v1), Tier C. **Status:** QUEUED behind Presentable v1. **Gated on
David L3 (taste)** — the whole volume hinges on how the `AestheticProfile` is set; nothing dispatches on the
identity/brand/canon path until that lands.

**Canon refs:** Volume XXVI — Ch.1 `01_Divergent_Convergent_Thinking_Symbolic_Synthesis.md`, Ch.2
`02_Domain_Generators.md`, Ch.3 `03_Creative_Evaluation_and_Dream_Integration.md`. Extends Vol V Ch.9
(`CreativeImaginationEngine`); reuses Vol IX Symbol Engine + the DeepDream image pipeline. Kernel: NO EYES; DISENELO
Planet moral frame.

## Problem / Goal
eLo has one LIVE creative faculty (`CreativeImaginationEngine`, Vol V Ch.9). This volume refines it to a divergent→
convergent phase structure, adds five domain generators, and adds a creative-evaluation faculty with an
`AestheticProfile` (David's taste) and the David L3 gate. It is a real build/refine — but every canon/identity/brand
output is gated on David's taste direction, so it runs last and cautiously. CHECK-BEFORE-BUILD: do not fork the symbol
library or the image pipeline.

## Scope to DoD (grounded in Ch.1–Ch.3; extend live code, do not fork)
- **Refine `CreativeImaginationEngine` → v1.1.0 (Ch.1):** add the divergent phase (`DivergentRequest`/`DivergentResult`,
  bounded by `breadth_budget`, generating breadth along declared `spanned_axes`, distant/off-brand candidates allowed —
  filtered in convergence, never suppressed at birth; every `CreativeCandidate` carries `epistemic_status: imagined`
  before leaving). Convergence is **Executive-owned** (`ConvergentPass`, 4 filters: identity, constraint, taste ranking,
  verified-speech tag): the Executive selects **once** from one frozen candidate set (ADR-Exec-002), may select "none,"
  and routes runners-up to exploration memory (nothing imagined is deleted). Build `synthesise(concept_a, concept_b,
  goal) -> SynthesisedConcept` (map→bridge→metaphor→5-question expansion→imagined), weighting by convergence of sources
  (association graph, not random). Share `faculties/dream/symbol_engine.py`'s `SYMBOLS` — extend, never fork. Envelope
  MUST carry `payload.body.epistemic_status: "imagined"` on every candidate.
- **Five `DomainGenerator` specialisations (Ch.2)** — Story, Visual Design, Music (exploration-only until D-XXVI-D),
  Product/Fashion, Game — each `{domain, vocabulary, constraints, aesthetic_anchor: AestheticProfile, canon_ref:
  DomainCanon}` with `generate(goal, seeds)` and `translate(concept) -> DomainArtifactSpec`. A generator MUST read its
  `canon_ref` before generating; produces **specs, not finished assets** (handed to the owning seat/tool); the Executive
  invokes, generators never self-publish. Story MUST NOT violate the Planet moral frame ("overcharged not evil; calm is
  the action"). Visual: HARD constraint **NO EYES** (Kernel), reuse `tools/image_gen_agent.py` (no forked path), renderer
  failure → text/spec-only candidate. Game: convergent filter enforces the Planet design laws as hard constraints.
  Product/Fashion: RESERVED-domain gate — tag `reserved: true` on any candidate implying physical manufacture, route to
  David L3 + LG-2, never autonomous. `payload.body.domain` mandatory; `payload.body.reserved` set for RESERVED domains.
- **`CreativeEvaluation` faculty v1.0.0 + `AestheticProfile` + gate (Ch.3):** `evaluate(candidate, goal, domain,
  aesthetic_profile) -> CreativeScore` — six terms (`originality`, `emotional_meaning`, `identity_alignment` a HARD
  FLOOR, `taste_alignment`, `future_potential`, `coherence`) + `weighted_total`, `rationale` (MUST produce a rationale,
  not just a number), `epistemic_status: imagined`. `identity_alignment` below threshold → reject regardless of other
  scores. `AestheticProfile[domain]` (LOAD-BEARING) carries `stated_direction`, `learned_preference` (each MUST cite an
  `evidence_ref`), `provenance`, `silence_policy: "explore_within_canon"`; stated outranks learned; silence → explore,
  never fabricate. `gate(selected_candidate, stakes) -> {approved|revised|rejected}` is the **David L3 taste gate** and
  is authoritative/final at identity/brand/canon level; the taste model updates ONLY from verified gate consequences,
  never from eLo's own praise. Dream bridge: dreams may seed `creative_spark`, never author/select/ship; one unforked
  symbol library; making runs on the response path, dreaming in the integration window; any trait/personality
  implication is a PROPOSAL to Vol V Ch.7 (validated against Kernel), never self-applied.

## Definition of Done
- Divergent produces bounded diverse candidates all tagged imagined; convergence is Executive-owned + single; five
  generators emit grounded specs (not assets) with Kernel/design-law constraints enforced; RESERVED domains gated.
- `CreativeEvaluation` scores six terms with rationale, `identity_alignment` as a floor; `AestheticProfile` populated
  per David's ruling; the L3 gate is authoritative and the only source of taste-model learning.
- Audit can mark Vol XXVI COMPLETE (nothing RATIFIED without David's taste ruling).

## Tests to write (`tests/test_canon_xxvi_creative.py`)
- Ch.1: divergence bounded & diverse, convergence Executive-owned & single, synthesis fuses not shuffles, imagined stays
  imagined, weak creation refused, off-character filtered not pre-suppressed, runners-up retained, no spark → silence,
  full loop, shared symbol vocabulary with dreams.
- Ch.2: generator grounded not generic, design law enforced (game), no eyes (visual), spec not finished asset, visual
  reuses shared image pipeline, RESERVED gated not autonomous, silent anchor → explore not fabricate, imagined across
  media, Executive invokes→generator returns→Executive selects, one brain across domains.
- Ch.3: six-term evaluation with rationale, identity alignment is a floor, David gate authoritative, learning only from
  verified consequences, silence explored not fabricated, imagined judgement not factual claim, dreams seed never
  author, personality proposed not self-applied, full evaluate→converge→gate→learn, two-way dream bridge one symbol
  vocabulary.

## Dependencies + blocked-by
- **Blocked by / gated on David L3 (taste):** **D-XXVI-A** (how `AestheticProfile` is populated — stated vs learned vs
  both — LOAD-BEARING, governs the whole volume), **D-XXVI-D** (music remit + sonic direction; music exploration-only
  until then), D-XXVI-B/G (autonomy threshold, taste transparency). CA on D-XXVI-C/E/F/H/I (breadth budget, production
  boundary, canon-write authority, dream-seed proactivity, per-domain weight vectors). Runs behind Presentable v1.
- Cross-volume: Vol IX Ch.2 (SymbolEngine — reuse), Vol V Ch.9/Ch.5/Ch.7, Vol VIII (memory), `18_identity_kernel.md`
  (DISENELO canon + NO EYES), `_refs/game/eLo_Planet_...v4.md` (game ground truth).
- **Gate:** David L3 taste (D-XXVI-A/D) before any identity/brand/canon-path build; RESERVED product/fashion → David L3 + LG-2.

## Lane
Builder (Python — refine `CreativeImaginationEngine`, generators, `CreativeEvaluation` + `AestheticProfile`; reuse
symbol engine + image pipeline). Architect coordinates + carries the taste rulings to David. Owning seats/tools produce
the actual assets from the specs (D-LANES).
