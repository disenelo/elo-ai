---
chapter: 2
title: "Semantic Retrieval, Confidence & Evidence — Knowledge That Can Be Trusted"
volume: XXIV
status: READY FOR REVIEW
version: 0.1.0
owner: David Charles
architect: Claude (Lead Architect)
implementation: PENDING
audit_status: OPEN
source: "ARCHITECTURE_BIBLE.md v1.0 (David Charles) · knowledge/graph_loader.py retrieval path · ADR-Exec-001"
dependencies:
  - Volume_XXIV/01_Ontology_and_the_Knowledge_Graph.md (the node/edge schema this retrieves over)
  - knowledge/graph_loader.py (build_context / _find_* — the live retrieval path)
  - runtime/spine/control_plane.py (_build_context_block — where knowledge enters the prompt)
  - ARCHITECTURAL_PRINCIPLES.md (Verified Speech · Truth before fluency · Reality before Narrative)
  - Volume_VIII/01_Memory_Architecture.md (semantic memory retrieval — sibling)
---

# Chapter 2: Semantic Retrieval, Confidence & Evidence

## 2.0 Purpose

Chapter 1 defined *what eLo knows*. This chapter defines *how eLo finds it, how sure it is,
and what backs the claim* — so that knowledge obeys **Verified Speech** (ADR-Exec-001):
knowledge carries confidence and evidence; eLo cites or qualifies rather than asserting
unverified claims. "Truth before fluency" is not a slogan the personality layer applies at
the end — it is a property the knowledge layer must *carry* from retrieval onward.

The live Connection Engine (`knowledge/graph_loader.build_context`) retrieves by naive
substring keyword match, returns the *first* concept/viewpoint hit and the *top* relationship
as a flat ≤800-char string, and attaches **no confidence and no evidence** to anything. That
is adequate enrichment but it cannot support Verified Speech: eLo currently cannot tell the
Executive "I'm fairly sure of this and here's why" versus "this is my opinion" versus "I
don't actually know." This chapter specifies the retrieval contract that closes that gap.

## 2.1 Principle

**2.1.1 Every retrieved unit carries confidence.** No knowledge reaches the Executive as a
bare claim. Each retrieved node/edge carries a `confidence ∈ [0.0, 1.0]` and an epistemic
`kind` (fact · perspective · inference · promoted-memory). This is the exact analogue of
Volume XV §1.1.3 ("every field carries its freshness") applied to knowledge instead of world
state.

**2.1.2 Confidence ≠ salience.** `strength` on an edge (Ch.1 §1.1.3) is centrality, not
certainty. Confidence is a separate axis with a separate field. Retrieval MUST NOT read
`strength` as confidence. (Enforced: they are different keys.)

**2.1.3 Evidence or qualification — never bare assertion.** A `fact`-kind claim carries
`evidence[]` (its provenance: authored canon, or the memory record it was promoted from). A
`perspective`-kind claim (a viewpoint) is tagged as opinion and spoken as "the way I see it,"
never as external truth. A claim with no evidence and low confidence is surfaced as *not
known*, not asserted — this is Reality-before-Narrative applied to knowledge.

**2.1.4 Retrieval is ranked and bounded, not first-match.** Retrieval returns a *ranked* set
under a budget, with the ranking legible, replacing the live "first hit wins" heuristic.
Determinism: same query + same graph → same result (no hidden ordering by dict insertion).

## 2.2 What this is NOT

- Not a vector store. The live engine is lexical (keyword substring). This chapter specifies
  the *contract* (confidence, evidence, ranking, kinds) independent of the matcher; §2.7
  flags embedding retrieval as a future option, not a requirement.
- Not the personality layer. Retrieval reports confidence and kind *objectively*; the
  personality/voice layer decides how to phrase the qualification ("I think…", "I'm sure…").
  Cognition objective; expression shaped (Principles).
- Not memory retrieval. Volume VIII retrieves autobiographical records by weight/recency;
  this retrieves durable canon. Sibling, not same (boundary in Ch.3).

## 2.3 The Retrieval Contract

### 2.3.1 Input

```jsonc
KnowledgeQuery {
  "text":        "how do chunk and sugarcore relate?",   // the turn's user/Executive text
  "budget_chars": 800,                                    // live default (build_context max_chars)
  "max_units":    6,                                      // ranked cap (replaces top-1 heuristic)
  "kinds":        ["fact","perspective","inference"]      // optional filter (Executive may ask facts-only)
}
```

### 2.3.2 Output — a ranked, annotated result (replaces the flat string)

```jsonc
KnowledgeContext {
  "units": [
    {
      "ref":        "rel:chunk→sugarcore",   // stable pointer into the graph (Ch.1 ids)
      "kind":       "fact",                  // fact | perspective | inference | promoted_memory
      "text":       "Chunk forms after Sugarcore breaks things apart — two phases of one process.",
      "salience":   0.75,                    // from edge.strength (centrality) — NOT confidence
      "confidence": 0.95,                    // NEW: epistemic certainty (§2.4)
      "evidence": [                          // NEW: provenance (§2.5) — empty allowed only for perspective
        { "type": "authored_canon", "source": "relationships/world_graph.json#chunk→sugarcore" }
      ]
    },
    {
      "ref":        "viewpoint:identity",
      "kind":       "perspective",           // opinion — spoken qualified, never as external fact
      "text":       "Identity is not fixed — it's maintained.",
      "salience":   null,
      "confidence": null,                    // perspective has no truth-confidence; it is a stance
      "evidence":   []                       // perspectives need no evidence, but MUST carry kind=perspective
    }
  ],
  "query":      "how do chunk and sugarcore relate?",
  "coverage":   "partial",                   // full | partial | none — did retrieval find enough?
  "rendered":   "…≤ budget_chars string…"    // back-compat: the compact prompt string (build_context shape)
}
```

`rendered` preserves the current `build_context` contract so the prompt builder keeps
working during migration; `units[]` is the new structured surface the Executive reasons over.

### 2.3.3 Ranking (replaces `_find_*` first-match)

Rank retrieved units by a legible score, highest first, cut at `max_units` / `budget_chars`:

```
score(unit) = keyword_match_quality      # how many / how specific the keyword hits (0..1)
            × confidence                  # certain knowledge ranks above uncertain
            × (0.5 + 0.5 × salience)      # salient edges preferred, but salience alone never wins
```

Rules: perspective units are ranked in a **separate lane** and only included after the top
facts, so eLo leads with what it knows and adds stance second. Ties broken by `ref`
(deterministic — §2.1.4). Direction of edges may become a retrieval filter here (Ch.1 notes
the live loader ignores direction).

## 2.4 Confidence Model

Confidence is assigned per unit, per kind:

| kind             | confidence source                                                            |
|------------------|------------------------------------------------------------------------------|
| `fact`           | authored canon → high (default 0.95); lowered only if flagged provisional    |
| `promoted_memory`| inherited from Volume VIII consolidation strength × verification count        |
| `inference`      | derived (min of the confidences of the edges/nodes it was inferred from)     |
| `perspective`    | `null` — a viewpoint is a stance, not a truth-claim; it carries no confidence |

**Bands (for the Executive / voice, not stored):** `≥0.9` assert plainly · `0.6–0.9` assert
with light qualification · `0.3–0.6` hedge explicitly ("I think…") · `<0.3` or absent → treat
as **not known**, do not assert (Truth-before-fluency). These bands are consumed by the
Executive; the knowledge layer only supplies the number and the kind.

## 2.5 Evidence & Citation Model (ties Verified Speech)

Every `fact`/`promoted_memory` unit carries `evidence[]`. An evidence item:

```jsonc
Evidence {
  "type":   "authored_canon" | "promoted_memory" | "world_state" | "inference_trace",
  "source": "relationships/world_graph.json#chunk→sugarcore"   // stable, checkable pointer
             // promoted_memory → SPOT_CODE / vault ref (Vol VIII §1.2 three-tier)
             // world_state     → LiveWorldState domain (Vol XV) if the knowledge was world-derived
}
```

**Rules (MUST):**
- A `fact` with empty `evidence[]` is a canon error — either it is authored (evidence =
  its graph location) or promoted (evidence = the memory record). No orphan facts.
- `perspective` needs no evidence but MUST be tagged `kind: perspective` so it is never
  laundered into a factual assertion (the "I sense calm so I know I'm meditating" failure,
  Reality-before-Narrative).
- Citation is *available*, not always *spoken*. The Executive/voice decide when to surface a
  citation ("in the eLo world, Chunk transforms rather than restores"); the knowledge layer
  guarantees one *exists* to surface. This is what makes eLo able to cite/qualify on demand.

## 2.6 Reasoning Support

Knowledge feeds reasoning in three ways (developed further in Chapter 3):

1. **Grounding** — the Executive starts each turn from *what eLo durably knows* (this graph)
   plus *what is true now* (Vol XV) plus *what happened before* (Vol VIII). Knowledge is the
   stable substrate under the transient ones.
2. **Connection (the live engine's namesake)** — relationship and concept edges let eLo
   answer "how do these relate?" (`_find_relationships`, concept `related`/`opposites`).
   Multi-hop traversal (Chunk → Sugarcore → Orb) is an `inference`-kind unit whose confidence
   is the min along the path (§2.4) and whose evidence is the `inference_trace`.
3. **Qualification** — because every unit is confidence- and kind-tagged, the Executive can
   reason *about its own certainty* and choose to assert, hedge, or stay silent. This is the
   mechanism by which Verified Speech is enforced at the knowledge boundary, not patched on
   afterward.

## 2.7 Migration From the Live Engine (no behaviour break)

The change is additive and incremental, matching the Vol XV migration discipline:

1. Add `confidence`, `kind`, `evidence[]` as new fields (default `fact`/authored/`0.95`); the
   old string still renders via `rendered`. No consumer breaks.
2. Replace `_find_concept`/`_find_viewpoint` first-match with the ranked scorer (§2.3.3),
   asserting the top result is unchanged for existing single-hit queries.
3. Have the prompt builder read `units[]` (with confidence/kind) instead of the flat string,
   so the Executive can qualify. Assert parity, then retire the string dependence.
4. (Optional, flagged) Add embedding retrieval behind the same contract if lexical recall
   proves insufficient — the contract does not change, only the matcher.

## 2.8 Interaction With Other Volumes

- **Executive (Vol V)** — sole consumer for assertion; reads confidence bands (§2.4) to
  assert / hedge / stay silent. Knowledge is context, not command.
- **Voice / Personality (Vol X)** — phrases the qualification; never alters confidence or
  kind (objective cognition, shaped expression).
- **Memory (Vol VIII)** — `promoted_memory` units inherit confidence from consolidation;
  evidence points back into the vault (SPOT_CODE). Sibling retrieval path.
- **World State (Vol XV)** — `world_state`-typed evidence lets a knowledge claim cite a live
  domain when knowledge and world combine (e.g. "you're in the Cyber Garden stage" +
  live progress). Confidence then also inherits the domain's freshness/confidence.
- **Verified Speech (ADR-Exec-001)** — this chapter is the knowledge-layer implementation of
  that ADR; the confidence+evidence contract here is what lets speech remain a sensor.

## 2.9 Open Questions (for CA / David)

1. **Where is confidence authored?** Do entity/concept nodes get an explicit `confidence`
   field in the JSON (author-set), or is `fact` confidence a fixed default (0.95) with only
   `promoted_memory` carrying a computed value? Recommend: default for authored, computed for
   promoted, explicit override allowed.
2. **Perspective vs fact adjudication.** A viewpoint ("identity is maintained") can *sound*
   factual. Who decides a node is `perspective` vs `fact` — is it structural (viewpoints.json
   ⇒ perspective, world_graph ⇒ fact) or per-node tagged? Recommend structural-by-default,
   overridable.
3. **Citation surfacing policy.** When *should* eLo actually voice a citation vs silently
   rely on it? Needs a voice-layer rule (D-PRESENCE: the Executive grows quieter — don't
   narrate every source).
4. **Inference confidence floor.** Is min-along-path the right rule for multi-hop inference,
   or should chain length also decay confidence? Recommend min × length-decay; confirm.
5. **Embedding retrieval (§2.7.4).** In-scope for v1, or explicitly deferred to keep the
   layer lexical and auditable for now?

## 2.10 Architecture References

- Code: `knowledge/graph_loader.py` (`build_context`, `_find_entities`,
  `_find_relationships`, `_find_concept`, `_find_viewpoint`), `runtime/spine/control_plane.py`
  (`_build_context_block`), `server.py` (`graph_context` import).
- `ARCHITECTURAL_PRINCIPLES.md` — Verified Speech (ADR-Exec-001), Truth before fluency,
  Reality before Narrative.
- `Volume_XXIV/01_Ontology_and_the_Knowledge_Graph.md` — the node/edge schema retrieved here.
- `Volume_VIII/01_Memory_Architecture.md` — consolidation strength (promoted-memory confidence).
- `Volume_XV/01_Unified_World_State.md` — the freshness/confidence pattern this mirrors.

---

```
Chapter 2 — Semantic Retrieval, Confidence & Evidence
Status: READY FOR REVIEW
Files: Volume_XXIV/02_Semantic_Retrieval_Confidence_Evidence.md
Live anchor wired: graph_loader.build_context + _find_* retrieval path (naive keyword → ranked+scored)
Contract: Included (KnowledgeQuery / KnowledgeContext with confidence + kind + evidence)
Verified Speech tie: confidence bands + evidence/citation model + perspective tagging
Open decisions flagged: confidence authoring, perspective/fact adjudication, citation policy, embeddings
```

READY FOR REVIEW
