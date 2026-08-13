---
chapter: 4
title: "The Sole-Writer Contract, Retrieval & the Memory / Knowledge / World-State Boundary"
volume: VIII
status: READY FOR REVIEW
version: 0.1.0
owner: David Charles
architect: Claude (Lead Architect)
implementation: PARTIAL (physical write chokepoint + reader live; single logical Memory Faculty / candidate submission PENDING)
audit_status: OPEN
dependencies:
  - Volume_VIII/01 (D-F reconciliation), 02 (record shapes), 03 (consolidation writes)
  - Volume_V/03 Memory Architecture (cognitive-layer view — reconciled, not forked)
  - Volume_VI Working Memory (in-turn frames — the boundary above)
  - Volume_XV World State (live world — the boundary beside)
  - Volume_XXIV Knowledge Architecture (durable knowledge — the boundary beside)
  - Volume_XXI Autobiographical Thread (derived view over episodic memory — the boundary above)
  - memory/vault_layer.py (write_memory / recall_context), memory/obsidian_loader.py (sole reader)
---

# Chapter 4: The Sole-Writer Contract, Retrieval & Boundaries

## 4.0 Purpose

Runtime Invariant 7 (**Memory Ownership**) requires *one permanent-memory writer*. Decision
**D-F** names it: the **Memory Faculty owns persistence, retrieval, indexing, forgetting, and
consolidation; no other faculty writes permanent memory directly.** This chapter specifies
that contract, the retrieval path that serves it, and — critically — the **boundaries** that
keep Memory from absorbing (or being absorbed by) Working Memory, World State, Knowledge, and
the Autobiographical Thread. Naming is architecture: if "memory" means five different things,
five divergent stores appear. This chapter draws the lines.

## 4.1 The Sole-Writer Contract (D-F)

**4.1.1 One writer.** All durable memory is written through a single chokepoint. In the live
system that chokepoint is `memory/vault_layer.py::write_memory` — every tiered vault record
(index + summary + deep) is produced there and only there. Consolidation (Ch.3),
session integration (`reflection_faculty.integrate_session`), the journal router
(`journal_router → truth_sync.compress_to_obsidian`), and satellite faculties (e.g.
`faculties/music_memory/storage.py`) all funnel through it. The physical invariant holds:
there is exactly one place bytes become durable memory.

**4.1.2 Everything else submits a Candidate.** Per D-F, no other faculty *decides* what
persists — it submits a **Memory Candidate** and the Memory Faculty decides depth, priority,
weight, and whether to write at all. Today this decision is distributed: `journal_router`
applies significance thresholds and calls the writer directly; consolidation calls it
directly. **GAP (PENDING):** a single logical `MemoryFaculty` that receives all candidates
and is the sole *caller* of `write_memory` does not yet exist — callers invoke the writer
directly rather than submitting to one owner. The *physical* sole-writer holds (§4.1.1); the
*logical* single-owner (candidate-in, decision-out) is the remaining work. Flag for the
owning seat: route all `write_memory` callers through one `MemoryFaculty.submit(candidate)`.

**4.1.3 Anti-fabrication at the write boundary.** A fact that was *inferred*, not observed,
must not be written as memory (Vol V Ch.3 failure mode; Verified Speech / Reality-Before-
Narrative). The vault stores meaning that actually happened — never a plausible invention.

```
Memory Candidate (what any faculty submits — canonical shape)
  source_faculty : str          who observed it
  content        : str          meaning (not raw transcript)
  proposed_type  : episodic|semantic|procedural|emotional
  proposed_weight: 0–9          a REQUEST; Memory Faculty may override
  significance   : SignificanceProfile   (Vol V Ch.5) — the decision input
  verified       : bool         false ⇒ Memory Faculty MUST NOT persist as fact
  → MemoryFaculty decides: {write | reinforce existing | drop}, sets final weight, calls write_memory once.
```

## 4.2 Retrieval — Serving the Turn

Retrieval runs in the **response path** (`PROCESSING`), reading only; durable writes never
happen in the hot loop. The live entry points are `vault_layer.recall_context(query)` and
`lookup(query)`, plus the session `memory_pack` (Ch.2 §2.5) assembled at session start and
handed into the spine (`spine.run(..., memory_pack=...)`).

**Rules (MUST):**

- **4.2.1 Retrieval returns confidence + source + status, never a bare string.**
  `recall_context` returns `{status: live|absent, results:[{memory, confidence 0.0–1.0,
  timestamp, source}]}`. This mirrors the LiveWorldState freshness discipline (Vol XV §1.1.3)
  so eLo can say *"I recorded this on <date>, high confidence"* — never a vague "I think…".
  Confidence is `weight/9`.
- **4.2.2 Meaning, ranked by weight.** Results sort by `weight` descending (structured
  summaries above flat index rows). Semantic (embedding) retrieval via `embedding_store`
  refines ranking when `OPENAI_API_KEY` is present; without it, keyword scoring takes over
  — meaning-retrieval is therefore **best-effort, degraded gracefully** (Ch.2 §2.6), never a
  hard failure.
- **4.2.3 Vault-down is honest.** If the vault is unreachable, `recall_context` returns
  `status: absent` with a message; the turn proceeds on the `memory_pack` and the context is
  flagged stale (Vol V Ch.3 ST-3). eLo degrades to "I can't reach that memory right now" — it
  never fabricates the recall.
- **4.2.4 Retrieval feeds reinforcement.** A record retrieved *and used* should be reinforced
  (Ch.3 §3.4). This is the PENDING edge noted in Ch.3.

## 4.3 The Reader Chokepoint

Symmetric to the sole writer: `memory/obsidian_loader.py` is the **only** module permitted to
read `obsidian_vault/`. No other module imports from or reads the vault directly; the kernel
receives processed `MemoryPack` output and never sees vault paths or markdown. Writer chokepoint
(§4.1) + reader chokepoint together make the vault a sealed store with two doors.

## 4.4 The Boundaries — What Memory Is NOT

This is the anti-duplication core of the chapter. Four neighbours are frequently confused with
Memory; each owns something distinct.

| Neighbour | Owns | Boundary with Memory (this volume) |
|---|---|---|
| **Working Memory** (Vol VI / V Ch.1) | The **in-turn** frames — this session's active context, bounded, per-turn, frozen for the turn. | Working memory = what is live *now*; Memory = what *outlives the session*. Consolidation (Ch.3) is the bridge: pinned working frames graduate into durable records here. Memory never holds the live turn buffer. (Audit gap #3 lives in Vol VI, not here.) |
| **World State** (Vol XV) | The **live external world** this turn — frontmost app, music, weather, presence — assembled once, frozen, perishable (valid for its turn only). | World State is *sensed and disposable*; Memory is *experienced and durable*. A weather reading is World State; "David and I watched the storm roll in" is Memory. Memory may record that an event happened; it never re-serves live sensor data. |
| **Knowledge** (Vol XXIV) | The **durable knowledge graph** — ontology, entities, relationships, concepts, evidence, citation (`knowledge/graph_loader.py`). | Knowledge is *impersonal, structured truth* ("Python is a language"); Memory is *the relationship's lived record* ("David and I debugged the router on the 8th"). Semantic memory (Ch.2 §2.1) can *feed* Knowledge, but Knowledge is not weighted by emotional significance and does not decay on a forgetting curve. They pair (Vol XXIV metadata) but do not merge. |
| **Autobiographical Thread** (Vol XXI) | The **derived, meaning-level self-story** across time — "I am the same eLo who…". | The thread is a *view over* episodic Memory (Vol XXI §1.2: "Not a second memory store… one permanent-memory writer, Volume VIII"). It reads episodic records to compose narrative; it never writes its own store. Memory is the source of record; the thread is the story told from it. |

**Rule (MUST):** none of these four may open its own permanent-memory store. Working Memory
and World State are ephemeral by design; Knowledge has its own durable store but for
*structured knowledge*, not weighted lived episodes; the Autobiographical Thread is strictly
derived. Any new store claiming to "remember" for the relationship is a fork of Vol VIII and
must be reconciled here.

## 4.5 Reconciliation with Volume V Chapter 3 (not a fork)

Vol V Ch.3's six cognitive layers are the **per-turn cognitive view** of memory; Vol VIII is
the **durable-storage model**. They map cleanly, so there is one architecture, not two:

```
V Ch.3 layer          →  owned by
Active Context        →  Working Memory (Vol VI) — in-turn
Working Memory        →  Working Memory (Vol VI) — in-turn
Episodic              →  Vol VIII (this) — durable
Semantic              →  Vol VIII (this) — durable  (may feed Knowledge, Vol XXIV)
Pattern               →  Vol VIII consolidation output (Ch.3 §3.2) → Personality (Vol X)
Identity              →  weight-9 floored records (Ch.3 §3.3) + Personality/Kernel
```

Vol V Ch.3 remains valid as the cognitive-layer sub-view; this volume is the deep spec it
maps onto. Neither is edited to contradict the other (D-F).

## 4.6 Faculty Contract (Memory Faculty — the intended single owner)

```
Faculty:
  name:            MemoryFaculty
  version:         1.0.0
  purpose:         Sole owner of durable memory — receive Memory Candidates, decide what
                   persists, write once, retrieve with confidence, consolidate + forget (timed).
  contributes_to:  CognitiveState (retrieval) + durable vault (writes, timed)
  runs_in:         response-path (retrieval, read-only) + integration-window (writes/consolidation)

Inputs:
  - type: memory_candidate   source: any faculty (§4.1.2)     required: false   (submit-and-decide)
  - type: meaning_query      source: CognitiveState / turn    required: true    (retrieval)
  - type: significance       source: Significance Engine (V Ch.5)  required: true (decides weight)
Outputs:
  - type: memory_context     destination: CognitiveState (confidence+source+status — §4.2.1)
  - type: durable record     destination: vault (via the one writer, §4.1.1)
  - type: personality_delta (proposal)  destination: Vol X / V Ch.7 (validated — Ch.3 §3.5)

Dependencies:
  - module: vault_layer (hard — the one writer + recall), obsidian_loader (hard — the one reader)
  - faculty: SignificanceEngine (hard — decides depth), ConsolidationFaculty (Ch.3), Personality (proposals)

Failure Modes:
  - condition: two faculties race to write        fallback: single-writer chokepoint serialises; last-writer semantics documented.
  - condition: unverified candidate submitted      fallback: MUST NOT persist as fact (§4.1.3 anti-fabrication).
  - condition: vault unreachable on retrieval       fallback: status=absent + memory_pack; flagged stale (§4.2.3).
  - condition: a neighbour opens its own store      fallback: canon violation — reconcile into Vol VIII (§4.4).
```

## 4.7 Acceptance Tests

```
FT-1  One writer            Given any faculty stores memory, Then the bytes were written by vault_layer.write_memory and nowhere else.
FT-2  Candidate decided by owner  Given an unverified candidate, Then it is dropped (not persisted as fact).  (blocked on §4.1.2 single-owner wiring)
FT-3  Confidence on recall   Given a recall, Then each result carries {confidence, timestamp, source, status}; none is a bare string.
FT-4  Meaning not keyword     Given "why does eLo exist?", Then recall returns meaning-ranked results (embedding when keyed; keyword fallback otherwise).
ST-1  Vault-down honest       Given the vault is unreachable, Then status=absent, turn proceeds on memory_pack, recall is not fabricated.
ST-2  No neighbour store      Given Working Memory / World State / Knowledge / Thread, Then none writes a permanent memory record of its own.
IT-1  V Ch.3 mapping holds     Given the six-layer view, Then episodic/semantic map to Vol VIII, active/working to Vol VI, pattern/identity to consolidation+Personality — one architecture.
IT-2  Thread reads, never writes  Given Vol XXI composes the autobiographical thread, Then it only READS episodic records here and writes no store of its own.
```

## 4.8 References
- Code: `memory/vault_layer.py` (`write_memory` = the one writer; `recall_context`/`lookup` = retrieval),
  `memory/obsidian_loader.py` (the one reader), `memory/journal_router.py` +
  `tools/truth_sync.py` (current candidate/write callers), `runtime/reflection_faculty.py`
  (`integrate_session`), `runtime/spine/spine.py` (`memory_pack` into the turn).
- Canon: Vol VIII Ch.1 (D-F reconciliation table), Ch.2 (record shapes), Ch.3 (timed writes);
  Vol V Ch.3 (six layers), Ch.5 (significance); Vol VI (working memory); Vol XV (world state);
  Vol XXIV (knowledge); Vol XXI (autobiographical thread).
- ARCHITECTURAL_PRINCIPLES.md Invariant 7 (Memory Ownership); Decision Log D-F, D-G.

---
**Status: READY FOR REVIEW** — the sole-writer contract (physical chokepoint live; single
logical owner PENDING), the confidence-carrying retrieval path, the reader chokepoint, and
the four boundaries (Working Memory · World State · Knowledge · Autobiographical Thread) that
keep Memory from forking. Reconciles Vol V Ch.3 rather than replacing it. FLAG: candidate-in/
decision-out single owner not yet wired — callers invoke the writer directly.
