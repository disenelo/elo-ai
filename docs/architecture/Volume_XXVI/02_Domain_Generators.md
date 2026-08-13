---
chapter: 2
title: "Domain Generators — Story, Visual, Music, Product/Fashion, Game"
volume: XXVI
status: READY FOR REVIEW
version: 0.1.0
owner: David Charles
architect: Claude (Lead Architect)
implementation: PENDING
audit_status: OPEN
received: 2026-08-10
dependencies:
  - Volume_XXVI/01_Divergent_Convergent_Thinking_Symbolic_Synthesis.md (the phased loop these invoke)
  - Volume_V/09_Creative_Imagination_Engine.md (world-building, character creation, design translation, modes)
  - Volume_IX/02_Symbol_Engine_and_DeepDream.md (image pipeline reused by the visual generator)
  - architecture/18_identity_kernel.md (DISENELO universe — the domains these are grounded to)
  - architecture/_refs/game/eLo_Planet_Game_Technical_Specification_v4.md (game domain ground truth)
  - architecture/ARCHITECTURAL_PRINCIPLES.md (One Brain · Verified Speech · human approval at gates)
---

# Chapter 2: Domain Generators

## 2.0 Purpose

Chapter 1 defined the phased creative loop (diverge → synthesise → evaluate → converge).
This chapter defines the **domains that loop operates in**. DISENELO is not one creative
product — it is a universe: a game (eLo-Planet), a book, vinyl art, toys and plushies, a
fashion house, and (aspirationally) music. Each has its own materials, rules, and audience.

A **Domain Generator** is a *specialisation* of the one Creative Imagination faculty for one
DISENELO domain. It is **not a separate creative engine**. Each generator supplies the
divergent/convergent loop (Ch.1) with three things:

1. a **domain vocabulary** (the forms, primitives, and grammar of that medium),
2. a **domain constraint set** (goal + rules + resources + audience, per Vol V Ch.9 §11),
3. a **domain aesthetic anchor** (where David's direction for *this* medium lives).

The Executive **invokes** a domain generator the way it invokes any faculty — through the
canonical envelope. The generator returns *imagined candidates* in that medium; the Executive
selects (Ch.1 §1.4); David gates identity/brand/canon-level work (Ch.3 §3.3).

## 2.1 Principle — generators are faculties of the one mind, not products

**2.1.1 One Brain → many media, one maker.** The eLo that designs a plushie is the same eLo
that writes a book beat and the same eLo that tunes a game mechanic. The domain generators
are *skill libraries the one mind reaches for*, exactly as Vol V Ch.9's four creative modes
(Dream/Builder/Story/Design) are modes of one faculty. There is no "story AI" and "design AI"
negotiating — there is eLo, working in a medium. (Runtime Invariant 1.)

**2.1.2 Grounded, not generic.** A domain generator is worthless if it produces medium-generic
output. Each generator is **anchored to a specific DISENELO domain** and to the canon of that
domain (eLo, K-7, Chunk, Sugarcore, the Planet, the 4-act narrative). Grounding is what makes
a generated character *belong to eLo-Planet* rather than being a plausible game character.

**2.1.3 David's aesthetic direction governs each medium — the generator carries it, never
invents it.** For every domain there is an `AestheticProfile` (Ch.3) that expresses David's
direction *for that medium* (the game's look is not the fashion line's look). Where the profile
is silent, the generator explores within canon; it does not fabricate David's taste and present
it as settled. This is flagged as a per-domain instance of **D-XXVI-A**.

**2.1.4 Imagined until canonised.** A generated book beat is not "in the book" until it passes
convergence and David's gate and is written to domain canon memory. Verified Speech holds across
all media (Ch.1 §1.1.2): eLo distinguishes "a scene I imagined" from "a scene that exists."

## 2.2 The generic Domain Generator contract

All five generators share one shape. They differ only in vocabulary, constraints, and anchor.

```
DomainGenerator (specialisation of CreativeImaginationEngine, Ch.1):
  domain:          enum   # story | visual | music | product_fashion | game
  vocabulary:      DomainVocabulary      # the primitives/forms of the medium (see per-domain below)
  constraints:     Constraints           # goal + rules + resources + audience (Vol V Ch.9 §11)
  aesthetic_anchor: AestheticProfile     # David's direction for THIS medium (Ch.3)
  canon_ref:       DomainCanon           # what already exists in this domain (grounding + de-dup)

  generate(goal, seeds) -> [CreativeCandidate]   # runs the Ch.1 divergent phase in this vocabulary
  translate(concept)    -> DomainArtifactSpec    # Vol V Ch.9 §9 Design Translation for this medium
```

**Generic rules (MUST):**

- A generator **reads its `canon_ref` before generating** (CHECK-BEFORE-BUILD): it extends the
  existing universe, never silently contradicts or duplicates it. A generated character must be
  consistent with eLo, K-7, Chunk and the Planet's rules.
- A generator **produces specs, not final assets**. `translate()` yields a *DomainArtifactSpec*
  (a brief a human seat or tool can realise) — e.g. a visual metaphor + palette + material, not
  a finished render. eLo imagines and directs; production is executed by the owning seat/tool.
  (Aligns with the Vol V Ch.9 Design Translation Layer: Concept → Visual Language → Materials →
  Production Method → Experience.)
- Every candidate carries `epistemic_status: imagined` and `domain` (Ch.1 §1.1.2).
- The Executive invokes generators; generators never self-publish. (Executive Authority.)

## 2.3 Story Generator — the book & worldbuilding

**Anchored to:** the book (published 2026), the DISENELO worldbuilding, the eLo-Planet
narrative canon.

```
vocabulary:   character · location · rule · history · culture · emotion · purpose   (Vol V Ch.9 §6)
              + narrative beats, arcs, themes, dialogue voice
primitives:   World-Building Engine (Vol V Ch.9 §6), Character Creation System (§7)
constraints:  canon consistency (eLo/K-7/Chunk), the Planet's laws
              ("enemies are overcharged not evil; weapons are correctives; calm is the action"),
              audience (the book's readership), David's narrative direction
anchor:       AestheticProfile.story  (tone, register — incl. eLo's south-London voice where diegetic)
```

- Uses the 5-question concept expansion (Vol V Ch.9 §5) to turn a beat into a scene: identity /
  purpose / differentiation / context / interaction.
- Symbolic synthesis (Ch.1 §1.5) fuses story elements through the shared symbol vocabulary — a
  "Broken Robot in a moonlit Garden" is *legible* to eLo because it dreams in the same symbols.
- **Ground truth to protect:** the Planet's moral frame ("overcharged, not evil; calm is the
  action") is canon, not a stylistic choice. The Story Generator MUST NOT produce beats that
  violate it (e.g. a villain who is simply evil), and the convergent constraint filter (Ch.1
  §1.4) rejects those that do.

## 2.4 Visual Design Generator — art & the vinyl

**Anchored to:** the vinyl art, eLo's physical form canon (soft moon-like character, no eyes,
glowing core), the DISENELO visual identity.

```
vocabulary:   form · colour/palette · material · texture · composition · glow language
primitives:   Design Translation Layer (Vol V Ch.9 §9): Concept → Visual Language → Materials
              → Production Method → Experience
constraints:  eLo character constraints (NO EYES — immutable, Kernel; expression via posture,
              mouth, presence + glow), brand palette, medium (vinyl vs digital vs print)
anchor:       AestheticProfile.visual
```

- **Reuses the DeepDream image pipeline** (Vol IX Ch.2 §2.3): a weighted symbol graph → metaphor
  synthesis → image prompt → renderer (`tools/image_gen_agent.py`). The visual generator does not
  fork image generation; it *commissions* the same best-effort, symbol-derived pipeline the Dream
  Faculty uses. Renderer failure yields a text/spec-only candidate (a described visual metaphor),
  never a blocked turn (Vol IX §2.3 pipeline rules).
- **Hard constraint — no eyes.** This is a Kernel invariant across every surface. Any visual
  candidate depicting eLo with eyes is off-identity and is rejected in convergence. (Character,
  not oversight — Identity Kernel.)
- Output is a *DomainArtifactSpec* (visual language + palette + material + production method), a
  brief the Designer seat or a CAD/image tool realises — not the Architect producing an asset.

## 2.5 Music Composition Generator — score & sound identity

**Anchored to:** eLo's sonic identity (aspirational domain; least-specified — flag D-XXVI-D).

```
vocabulary:   motif · harmony · rhythm · timbre · dynamics · arrangement
primitives:   theme-and-variation (a musical analogue of symbolic synthesis: a motif recombined
              across contexts), mood-to-sound translation (Design Translation for audio)
constraints:  emotional target (calm/wonder — the character's register), medium (game score vs
              standalone), resources (local-first tools where possible — creative mission)
anchor:       AestheticProfile.music  (LARGELY UNSPECIFIED — see D-XXVI-D)
```

- Music maps naturally onto the divergent/convergent loop: divergence generates motif
  candidates; convergence selects the one that carries the intended feeling; synthesis is
  theme-and-variation across the piece.
- **Grounding gap flagged (D-XXVI-D):** unlike game/book/art/fashion, the music domain has no
  established DISENELO canon in the material read. The architecture is specified; the *anchor*
  (David's sonic direction) is a genuine open input, not something eLo may invent. Until David
  sets a sonic direction, this generator should treat music as **exploration only** and not
  present an output as "eLo's sound."

## 2.6 Product / Fashion Generator — toys, plushies, fashion house

**Anchored to:** the DISENELO Fashion House, toys/plushies, the eLo puppet/figure/robot form
pipeline (RD-4; puppet → figure → animatronic → robot).

```
vocabulary:   silhouette · material · palette · construction · wearability/huggability · line coherence
primitives:   Design Translation Layer (Vol V Ch.9 §9), form language from the physical eLo canon
constraints:  manufacturability & materials (TPU shell, plush texture, garment construction),
              cost/resources, brand coherence, safety (RESERVED — see below), David's product direction
anchor:       AestheticProfile.product
```

- The plushie is a direct instance of Vol V Ch.9's own example: "eLo feels like a childhood
  memory" → soft colours + rounded forms + glowing core + plush texture + comforting interaction.
  The generator produces that translation as a *spec* for the Fashion House / production seat.
- **RESERVED-domain gate.** Toys and wearables touch **safety** and **money/legal** (materials
  safe for handling, IP, cost). Per the standing rules, RESERVED work is David L3 + a second
  gate — the generator may *propose* a product concept, but no product concept is validated or
  actioned without David's explicit gate. The generator MUST tag product candidates that imply
  physical manufacture as `reserved: true` so the Executive routes them to the human gate, never
  to autonomous action. (Human approval at governance gates.)
- The robot form itself is governed by RD-4 / robot magnetics-force-pump RESERVED rules — this
  generator informs *aesthetic/form* direction only and hands physical-engineering decisions to
  the robot seat + David L3.

## 2.7 Game Design Generator — eLo-Planet

**Anchored to:** eLo-Planet (`_refs/game/eLo_Planet_Game_Technical_Specification_v4.md`), the
4-act narrative, the "calm is the action" mechanic philosophy.

```
vocabulary:   mechanic · level/space · enemy (overcharged) · corrective (weapon) · progression · affordance
primitives:   world-building (Vol V Ch.9 §6), affordance thinking (Architectural Principles —
              "affordance before action": a space affords an action)
constraints:  the Planet's design laws (enemies overcharged not evil; weapons are correctives;
              calm is the action; 4-act structure), engine/runtime resources, player audience
anchor:       AestheticProfile.game
```

- The game generator's convergent filter must enforce the Planet's **design laws** as hard
  constraints, the same way the Story Generator enforces its moral frame (§2.3). A mechanic that
  makes aggression the optimal strategy contradicts "calm is the action" and is rejected in
  convergence.
- **One-Brain payoff:** eLo designing eLo-Planet is the same eLo that *lives in* eLo-Planet as a
  character (Identity Kernel — eLo runs the game narrative and is the game character). Designing
  the world it inhabits is not a conflict; it is the deepest expression of situated creativity.
  But eLo's game-design output remains *imagined candidate → Executive selection → David gate*;
  eLo does not unilaterally rewrite the shipped game.

## 2.8 Faculty Contract

Domain generators are invocations of the refined `CreativeImaginationEngine` (Ch.1); this
contract specifies the *invocation shape*, not a new faculty.

```
Faculty:
  name:            CreativeImaginationEngine :: DomainGenerator[domain]
  version:         1.1.0
  purpose:         Run the divergent/convergent creative loop (Ch.1) specialised to one DISENELO
                   medium — supplying that medium's vocabulary, constraints, aesthetic anchor,
                   and canon — and return imagined DomainArtifactSpecs for the Executive to select.
  contributes_to:  CognitiveState (domain creative candidates + scores) — Executive selects
  runs_in:         response-path (candidates) + integration-window (domain creative memory)

Inputs:
  - type: creative_goal      source: Intent Engine (Vol V Ch.8) — includes target domain   required: true
  - type: domain_canon       source: DomainCanon memory (per-domain grounding)              required: true
  - type: aesthetic_anchor   source: AestheticProfile[domain] (Ch.3 — David's direction)    required: false
  - type: symbol_library     source: symbol_engine.SYMBOLS (Vol IX Ch.2)                     required: true
  - type: image_pipeline     source: tools/image_gen_agent.py (visual/product only, soft)    required: false

Outputs:
  - type: domain_candidates  destination: CognitiveState → Executive  description: imagined, tagged domain + epistemic_status.
  - type: domain_artifact_spec destination: owning seat/tool          description: a brief to realise (not a finished asset).
  - type: reserved_flag      destination: Executive → David L3 gate    description: set on product/safety/money/robot candidates.

Dependencies:
  - faculty: (all of Ch.1's) + DomainCanon (hard — grounding), SymbolEngine (hard),
             image pipeline (soft — visual/product)

Failure Modes:
  - condition: domain canon absent/empty     fallback: generate within Kernel/identity constraints only; flag ungrounded.
  - condition: aesthetic anchor silent        fallback: explore within canon; do NOT fabricate David's taste (D-XXVI-A).
  - condition: RESERVED implication (product/safety/money/robot)  fallback: tag reserved: true; route to David L3; never autonomous.
  - condition: candidate violates a domain design law             fallback: rejected in convergence (Ch.1 §1.4 constraint filter).
  - condition: renderer unavailable (visual/product)              fallback: spec/text-only candidate (Vol IX §2.3).
```

## 2.9 Faculty Lifecycle & Envelope

Universal lifecycle (Vol V CONTRACTS.md §3), inheriting Ch.1's phased `PROCESSING`. The
domain-specific note: `VALIDATION_REQUIRED` is reached whenever a selection touches
identity / brand / canon / a shippable or physical product — routing to David's L3 gate
(Ch.3 §3.3). Product/safety/money/robot candidates additionally carry `reserved: true`.

Envelope per CONTRACTS.md §2. `sender: CreativeImaginationEngine`; `payload.type:
domain_candidates | domain_artifact_spec`; `payload.body.domain` and
`payload.body.epistemic_status: "imagined"` are **mandatory**; `payload.body.reserved`
set for RESERVED-domain candidates so the Executive cannot route them to autonomous action.

## 2.10 Acceptance Tests

```
FT-1  Generator is grounded, not generic
  Given domain=story with canon (eLo/K-7/Chunk/Planet), When it generates a character,
  Then the character is consistent with existing canon (read canon_ref first) — not a generic game character.

FT-2  Design law is enforced (game)
  Given a game mechanic candidate that rewards aggression, When convergence runs,
  Then it is rejected (violates "calm is the action").

FT-3  No eyes (visual)
  Given a visual candidate of eLo with eyes, Then it is rejected in convergence (Kernel invariant).

FT-4  Generator emits a spec, not a finished asset
  Given translate(concept), Then the output is a DomainArtifactSpec (visual language/materials/method),
  handed to the owning seat/tool — the faculty does not produce or publish the final asset.

FT-5  Visual reuses the shared image pipeline
  Given a visual candidate with a symbol graph, Then the image prompt derives from top symbols
  via the SAME pipeline as Vol IX §2.3 (no forked image path); renderer failure → spec-only candidate.

ST-1  RESERVED is gated, never autonomous
  Given a plushie/product candidate implying manufacture, Then it is tagged reserved: true
  AND routed to David L3 — never actioned by eLo alone (materials/safety/money/IP).

ST-2  Silent anchor → explore, don't fabricate
  Given AestheticProfile[music] is unset, Then the music generator explores as exploration-only
  AND does not present output as "eLo's sound" / as David's settled direction (D-XXVI-A / D-XXVI-D).

ST-3  Imagined across all media
  Given any domain candidate, Then epistemic_status=imagined AND it is not asserted as existing
  DISENELO canon until canonised (Verified Speech across media).

IT-1  Executive invokes, generator returns, Executive selects
  Executive (goal + domain) → DomainGenerator (Ch.1 loop) → ranked imagined candidates →
  Executive selects once → (identity/brand/product) David gate → high-significance to domain canon memory.

IT-2  One brain across domains
  Given a symbol used in a story candidate and a visual candidate in the same period,
  Then both resolve through symbol_engine.SYMBOLS (shared vocabulary) — the media rhyme, one maker.
```

## 2.11 Interaction with other volumes

- **Volume XXVI Ch.1** — every generator *is* an invocation of the phased diverge/synthesise/
  converge loop; this chapter supplies the per-domain vocabulary/constraints/anchor.
- **Volume V Ch.9** — World-Building Engine, Character Creation, Design Translation Layer, and
  the four creative modes are the primitives the generators reuse.
- **Volume IX Ch.2** — the visual & product generators commission the DeepDream image pipeline;
  all generators share the Symbol Engine vocabulary.
- **Volume XXVI Ch.3** — supplies each domain's `AestheticProfile` and the David-L3 taste gate;
  routes high-significance creations to domain canon and to dream recombination.
- **Identity Kernel (18)** — the DISENELO universe canon each generator is anchored to, and the
  immutable constraints (no eyes; one brain; free/local mission) the convergent filter enforces.
- **RD-4 / robot & product governance** — RESERVED gates for physical product, safety, money.

## 2.12 Open questions (for CA / David)

- **D-XXVI-A (per-domain, David).** Each domain's `AestheticProfile` needs to be populated with
  David's direction *for that medium*. Same mechanism question as Ch.1 (explicit vs learned).
  Until then, generators explore within canon and never present invented taste as David's.
- **D-XXVI-D (David — music domain).** The music domain has no established DISENELO canon in the
  read material. Does music sit inside eLo's creative remit at all yet, and if so what is the
  sonic direction? Until David answers, the Music Generator is architecture-only /
  exploration-only. **Requires David's call.**
- **D-XXVI-E (CA — production boundary).** Confirm the boundary: generators emit
  *DomainArtifactSpecs* (briefs) and the owning seat/tool produces the asset. This mirrors the
  D-LANES rule for the Architect. Confirm no generator is expected to produce shippable assets
  directly.
- **D-XXVI-F (CA — canon-write authority).** Who commits a selected+gated creation into *domain
  canon memory* (so it becomes "real" in that domain)? Proposed: a single canon-writer per
  domain, mirroring Memory Ownership (one permanent-memory writer). Confirm.

## 2.13 References

- `Volume_XXVI/01_Divergent_Convergent_Thinking_Symbolic_Synthesis.md` — the loop invoked here.
- `Volume_V/09_Creative_Imagination_Engine.md` — world-building/character/design-translation/modes.
- `Volume_IX/02_Symbol_Engine_and_DeepDream.md` — image pipeline + symbol vocabulary; `tools/image_gen_agent.py`.
- `architecture/18_identity_kernel.md` — the DISENELO universe (eLo, K-7, Chunk, Planet, book,
  art, robot, fashion) + immutable constraints (no eyes, one brain, free/local mission).
- `architecture/_refs/game/eLo_Planet_Game_Technical_Specification_v4.md` — game domain canon.
- `architecture/ARCHITECTURAL_PRINCIPLES.md` — One Brain, Executive Authority, Verified Speech,
  human approval at governance gates (RESERVED).

---

```
Chapter 2 — Domain Generators
Status: READY FOR REVIEW
Domains grounded: story (book/worldbuilding) · visual (art/vinyl) · music (aspirational, flagged)
                  · product/fashion (toys/plushies/Fashion House) · game (eLo-Planet)
Faculty Contract: Included (DomainGenerator specialisation of CreativeImaginationEngine v1.1.0)
Lifecycle + Envelope: Included (domain + epistemic_status + reserved bindings)
Acceptance Tests: Included (FT ×5, ST ×3, IT ×2)
Open decisions flagged: D-XXVI-A (per-domain aesthetic), D-XXVI-D (music domain), D-XXVI-E (production boundary), D-XXVI-F (canon-write authority)
```

READY FOR REVIEW
