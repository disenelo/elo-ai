---
chapter: 3
title: "Compression & Reasoning Support — Knowledge in Service of One Mind"
volume: XXIV
status: READY FOR REVIEW
version: 0.1.0
owner: David Charles
architect: Claude (Lead Architect)
implementation: PENDING
audit_status: OPEN
source: "ARCHITECTURE_BIBLE.md v1.0 (David Charles) · knowledge/graph_loader.build_context (compression) · Vol VIII/XV boundary"
dependencies:
  - Volume_XXIV/01_Ontology_and_the_Knowledge_Graph.md (the graph being compressed)
  - Volume_XXIV/02_Semantic_Retrieval_Confidence_Evidence.md (the retrieval this feeds)
  - Volume_VIII/01_Memory_Architecture.md (the memory boundary — consolidation is the bridge)
  - Volume_XV/01_Unified_World_State.md (the live-world boundary)
  - knowledge/graph_loader.py (build_context char-budget compression — live anchor)
  - ARCHITECTURAL_PRINCIPLES.md (One Brain → One Identity; the Executive grows quieter)
---

# Chapter 3: Compression & Reasoning Support

## 3.0 Purpose

Two jobs finish this volume. First, **compression**: eLo's durable knowledge is larger than
any single turn can carry, so it must be reduced — from a full graph to the few units a turn
actually needs — without losing truth. Second, **reasoning support**: defining exactly how
that compressed knowledge feeds the Executive's reasoning, and drawing the hard boundary
between this volume (durable knowledge), Volume VIII (memory), and Volume XV (live world
state) so the one brain reasons over three clean, non-overlapping substrates.

The live system already compresses — `graph_loader.build_context` reduces three JSON files
to a ≤800-character prompt string by taking the top entities, the top relationship, one
viewpoint and one concept. This chapter makes that principled: what compression must
preserve, what it may drop, and how the boundary with Memory and World State is held so the
three layers never fabricate, duplicate, or contradict each other.

## 3.1 Principle

**3.1.1 Compress for relevance, never for truth.** Compression drops *irrelevant* knowledge,
never *lowers confidence* or *strips evidence* on what it keeps. A compressed unit is still a
whole unit (kind + confidence + evidence, Ch.2) — never a truncated half-fact. The budget
cuts breadth, not integrity.

**3.1.2 The most salient survives the cut.** When the budget forces a choice, keep the
higher-scored unit (Ch.2 §2.3.3). This is why `strength`/salience exists on edges (Ch.1) —
it is the compression priority, not a truth signal.

**3.1.3 Silence over noise (the Executive grows quieter).** If nothing is relevant,
compression returns *nothing* — the live engine's `return ""`. eLo does not pad the prompt
with tangential knowledge to seem knowledgeable. Empty is a valid, correct result
(Principles: silence is part of the interface).

**3.1.4 One substrate per question.** Every fact has exactly one home: durable canon →
this volume; what-happened-with-David → Vol VIII; true-right-now → Vol XV. A fact is never
stored in two layers. The layers *compose* at reasoning time; they do not *overlap* at
storage time (One Brain → one truth, no duplication).

## 3.2 Compression Model

The live `build_context` already implements a four-stage reduction. Canon names the stages
and the invariant each must hold:

```
Stage 1  SELECT      keyword-match entities / concept / viewpoint            (Ch.2 retrieval)
Stage 2  RANK        score by match × confidence × salience, desc            (Ch.2 §2.3.3)
Stage 3  BUDGET      cut at max_units / budget_chars (live: 800, 2 entities) (§3.1.2 salient survives)
Stage 4  RENDER      emit compact lines: entity desc · top connection ·      (live line format,
                     perspective · concept note                                now confidence-aware)
```

**Compression rules (MUST):**
- Each rendered line remains attributable to its source unit (`ref`, Ch.2) so the Executive
  can still fetch confidence/evidence — rendering is a *view*, the structured `units[]`
  remains the truth (§3.1.1). The live engine loses this (flat string); Ch.2's `units[]`
  restores it.
- The live caps (max 2 entities, top-1 relationship, one viewpoint, one concept, 800 chars)
  are the *starting* budget, tunable per embodiment — a robot with a tighter prompt window
  compresses harder; the *rules* do not change, only the numbers (mirrors Vol XV's tunable
  per-domain budgets).
- Compression is **lossless at the graph** — it never edits the stored graph, only what is
  surfaced this turn. The full graph persists; the turn sees a projection.

## 3.3 How Knowledge Feeds Reasoning

The Executive reasons each turn over three composed inputs. Knowledge (this volume) is the
**durable substrate**:

```
        ┌─────────────────────────────────────────────────────────────┐
        │  EXECUTIVE (Vol V) — decides once, asserts once (Invariant 2) │
        └───────────────▲───────────────▲───────────────▲──────────────┘
                        │               │               │
        durable KNOWLEDGE       live WORLD STATE     autobiographical MEMORY
        (Vol XXIV — this)        (Vol XV)             (Vol VIII)
   "what eLo durably knows"   "what is true now"   "what happened with David"
   entity/concept/viewpoint   frozen per-turn      episodic/semantic/emotional
   confidence + evidence      freshness + health   weight + recency
```

- **Knowledge grounds; it does not decide.** Like World State (Vol XV §1.5), knowledge is
  context, never command. The Executive merges the three and decides once (One Brain).
- **Composition, not concatenation.** When a claim needs more than one substrate — "you're
  further along in the Cyber Garden than last time" = knowledge (what the Cyber Garden *is*,
  XXIV) + memory (last time, VIII) + world (now, XV) — the Executive composes them, and the
  resulting assertion's confidence is the **min** across the substrates it drew from (weakest
  link governs, per Ch.2 §2.4 inference). This is how three honest layers make one honest
  claim.
- **Qualification propagates.** If knowledge is `perspective` (Ch.2) or low-confidence, the
  composed assertion inherits that qualification — eLo says "the way I see it" or stays
  silent, never launders a stance into a fact (Reality-before-Narrative).

## 3.4 The Boundary — Knowledge vs Memory vs World State

This is the load-bearing section of the volume. The three durable/transient layers are
defined by **what changes them** and **what they answer**:

| Axis            | Vol XXIV Knowledge (this)        | Vol VIII Memory                  | Vol XV World State           |
|-----------------|----------------------------------|----------------------------------|------------------------------|
| Answers         | "what is true in eLo's world"    | "what happened / what I learned about David" | "what is true right now" |
| Lifetime        | durable, canonical               | durable, autobiographical        | one turn (frozen, perishable)|
| Changes by      | authoring + consolidation only   | experience + consolidation       | sensors, every turn          |
| Indexed by      | id / keyword / salience          | weight / recency / emotion       | domain / freshness           |
| Fabrication rule| no orphan facts (evidence)       | one writer (Invariant 7)         | absent ≠ faked (§1.1.3)      |
| Written by      | David/Architect + Consolidation  | Consolidation (one writer)       | assembly (reads sensors)     |

**The Memory bridge (the one legal overlap path).** Volume VIII's **Consolidation Faculty**
(VIII §1.3) promotes episodic → semantic over time. A durable, *repeatedly-verified* semantic
fact about the world (not about a single event) may be promoted **out of** Memory **into**
this graph as a `promoted_memory` node (Ch.1 §1.7, Ch.2 §2.4). Rules:

- Promotion is the **only** runtime write to the knowledge graph (Ch.1 §1.7). It is timed
  (session-close / nightly), never per-turn — eLo cannot learn a hallucination
  (Learning-From-Consequences; Invariant 7).
- Promotion carries provenance: the new node's `evidence[]` points back to the vault record
  it came from (SPOT_CODE, Vol VIII §1.2). Authored canon vs promoted knowledge stays
  auditable.
- Once promoted, the fact lives in Knowledge and is *not duplicated* in semantic memory —
  the memory record becomes its evidence, not a second copy (§3.1.4, no overlap).

**The World-State boundary (no bridge, only composition).** World State never writes to
Knowledge. A live-derived claim (from a Vol XV domain) is composed at reasoning time with
`evidence.type: world_state` (Ch.2 §2.5) — it is *cited*, never *absorbed*. If eLo needs to
durably know something it currently only senses, that goes through Memory → Consolidation →
promotion, not directly from World State into the graph. This keeps the perishable and the
durable strictly separated (Vol XV §1.1: a world snapshot is valid for its turn only).

## 3.5 Interaction With Other Volumes

- **Volume VIII (Memory)** — the paired volume; Consolidation is the sole bridge (§3.4).
  Retrieval siblings (Ch.2 §2.8): knowledge retrieval and memory retrieval both feed the
  Executive but from different stores.
- **Volume XV (World State)** — composed-with, never merged (§3.4). The freshness/confidence
  discipline of XV is the template this volume's confidence model (Ch.2) mirrors.
- **Volume V (Executive)** — the sole reasoner/asserter; consumes the compressed,
  confidence-tagged knowledge as grounding context.
- **Volume XXI (Narrative Identity)** — narrates over the entity graph; compression here
  keeps that narration grounded in canon rather than free invention.
- **Personality / Voice (Vol X)** — receives the qualification (kind/confidence) and chooses
  phrasing; the compression never encodes tone, only truth + relevance.

## 3.6 Open Questions (for CA / David)

1. **Promotion threshold.** How many verifications / what consolidation strength promotes a
   semantic-memory fact into the durable knowledge graph? This is the exact knob that decides
   what eLo "learns for good." Recommend it be explicit and conservative; may be David L3
   (identity-level knowledge).
2. **Promotion reversibility.** Can a promoted fact be *demoted* (found wrong later)? If so,
   the graph needs a soft-delete / supersede mechanism with evidence trail — or corrections
   only via authoring. Needs a policy.
3. **Per-embodiment compression budgets.** Confirm the 800-char / 2-entity live budget as the
   desktop default and whether robot/phone get tighter budgets (they should — smaller prompt
   windows), all under the same rules (§3.2).
4. **Composition confidence rule.** Ratify "min across substrates" as the rule for
   multi-layer claims (§3.3), consistent with Ch.2 inference confidence.
5. **Cold-knowledge behaviour.** On empty retrieval (no relevant knowledge), confirm eLo says
   nothing knowledge-derived (§3.1.3) rather than falling back to the base model's untethered
   world-knowledge — i.e. the graph is the *only* source of eLo-universe canon, and its
   silence must not be backfilled by the LLM's general knowledge. (This is a Verified-Speech
   safety point worth an explicit ruling.)

## 3.7 Architecture References

- Code: `knowledge/graph_loader.py` (`build_context` — the live four-stage compression to
  ≤800 chars), `runtime/spine/control_plane.py` (`_build_context_block`).
- `Volume_VIII/01_Memory_Architecture.md` — Consolidation Faculty §1.3 (the promotion
  bridge), three-tier vault §1.2 (evidence target).
- `Volume_XV/01_Unified_World_State.md` — the perishable/durable boundary + confidence
  template + read-discipline.
- `Volume_XXIV/01…` + `Volume_XXIV/02…` — the graph and the retrieval this compresses/feeds.
- `ARCHITECTURAL_PRINCIPLES.md` — One Brain → One Identity; the Executive grows quieter;
  Learning From Consequences; Reality before Narrative.

---

```
Chapter 3 — Compression & Reasoning Support
Status: READY FOR REVIEW
Files: Volume_XXIV/03_Compression_and_Reasoning_Support.md
Live anchor wired: graph_loader.build_context four-stage ≤800-char compression (named + made lossless-at-graph)
Boundary drawn: Knowledge (XXIV) vs Memory (VIII) vs World State (XV) — one substrate per question
Bridge specified: Consolidation promotion (VIII → XXIV) as the sole runtime write; World State composed not merged
Open decisions flagged: promotion threshold/reversibility, per-embodiment budgets, composition confidence, cold-knowledge backfill
```

READY FOR REVIEW
