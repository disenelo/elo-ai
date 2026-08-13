---
chapter: 1
title: "Biological Memory, Consolidation & Forgetting"
volume: VIII
status: READY FOR REVIEW
version: 0.1.0
owner: David Charles
architect: Claude (Lead Architect)
source: "19_cognitive_plan_architecture.md Layer 4 + Consolidation + memory/ code"
implementation: PARTIAL
audit_status: OPEN
dependencies:
  - 17_memory_update.md (write path), Volume V Ch.3/5/6
---

# Chapter 1: Biological Memory, Consolidation & Forgetting

## 1.0 Purpose

How eLo accumulates knowledge of David across sessions — split **biologically**, not as
one store. Errors here mean eLo forgets, misremembers, or over-remembers. This chapter
defines the four memory types, the consolidation faculty that decides what lasts, and the
forgetting curve that lets noise fade.

Write mechanics live in `17_memory_update.md`; this chapter defines the **model**.

## 1.1 The Four Memory Types (Layer 4)

```
Episodic     conversations, experiences, events        ("Volume V Ch.4 was written today")
Semantic     knowledge, facts, programming              ("eLo uses a layered memory architecture")
Procedural   habits, shortcuts, coding/animation/Unity workflow  ("how David likes commits framed")
Emotional    which conversations mattered — by emotional WEIGHT, not keyword or timestamp
```

**Rules (MUST):**
- Episodic and semantic are distinct: "the chapter was written" (episodic) vs "eLo uses
  layered memory" (semantic). Consolidation promotes episodic → semantic over time.
- **Emotional memory indexes by weight, not recency.** Memory weight rises with
  significance (Vol V Ch.5), not with timestamp. This is why a meaningful hard moment
  outlives a hundred trivial ones.
- Procedural memory captures David's *workflow* patterns (Audit notes this exists via
  `personality_drift`/registry) — how he works, not what he said.

## 1.2 Storage Tiers (reference)

The physical store is the three-tier vault defined in `17_memory_update.md §7`:
`SPOT_CODES` index → `summary/` note → `deep/` record, in `obsidian_vault/09 Memory/`,
read only through `memory/obsidian_loader.py`. This chapter does not restate it; the four
types above are *what* is stored, the tiers are *how*.

Relationship to the cognitive-layer view (Volume V Ch.3's six layers — Active → Working →
Episodic → Semantic → Pattern → Identity): V Ch.3 is the per-turn cognitive view; this
volume is the durable-storage model. Active/Working = in-turn (V Ch.1 working memory);
Episodic/Semantic/Procedural/Emotional = this volume; Pattern/Identity = consolidation
outputs (§1.3) feeding Personality (V Ch.7).

## 1.3 The Consolidation Faculty (Audit gap #4 — new)

A **timed** faculty (not per-turn), running on session close and nightly — hippocampal
replay. It is the same integration act as Reflection (`integrate_session()`, V Ch.6),
specialised for memory.

```
Consolidation cycle (idle / session close / nightly):
  replay significant episodes (Vol V Ch.5 selects)
        ↓
  ask: what changed? what must never be forgotten? what should fade?
       what patterns repeated? what surprised me? did personality shift?
        ↓
  strengthen useful → raise memory weight; promote episodic → semantic; extract patterns
  weaken noise      → apply the forgetting curve (§1.4)
        ↓
  emit: reinforced memories · pattern memories · (proposed) personality deltas → V Ch.7
```

**Rules (MUST):** consolidation **integrates, does not archive** (V Ch.6). It runs only in
the integration window, never the response path. It is atomic (a failed run preserves
prior memory intact). Personality-affecting outputs are **proposals** to Ch.7, validated
against the Identity Kernel — never self-applied.

## 1.4 The Forgetting Curve (new)

Not everything is kept forever. Memory strength decays unless reinforced:

```
strength = f(significance, recurrence, recency, emotional_weight)
decay:    strength declines over time WITHOUT reinforcement
reinforce: a memory referenced / re-used / re-felt regains strength
floor:    identity-level & pinned memories do NOT decay (protected)
```

**Rules (MUST):** decay applies to episodic/semantic noise, **never** to identity memory
or Significance-pinned records (V Ch.5). Forgetting is a feature — it keeps retrieval
relevant — but it is bounded so eLo never loses what defines the relationship.

## 1.5 Working Memory link (Audit gap #3)

The typed working-memory object is owned by Volume VI / V Ch.1 (bounded, per-turn frames).
This volume's boundary: **working memory = this session's active frames; Memory
Architecture = everything that outlives the session.** Consolidation is the bridge —
pinned working frames graduate into durable memory here.

## 1.6 Faculty Contract

```
Faculty:
  name:            MemoryArchitecture (+ ConsolidationFaculty sub-component)
  version:         1.0.0
  purpose:         Store experience across four biological types, consolidate significant
                   memory (timed), and forget noise via a bounded decay curve.
  contributes_to:  CognitiveState (retrieval) + durable store (consolidation)
  runs_in:         response-path (retrieval) + integration-window (consolidation)

Inputs:
  - type: turn_episode      source: CognitiveState + ExecutionReport   required: true
  - type: significance      source: Significance Engine (V Ch.5)         required: true
  - type: emotional_tag     source: Emotional Processing (V Ch.4)        required: false
Outputs:
  - type: memory_context    destination: CognitiveState (retrieval, per 03/17)
  - type: reinforced/pattern memory  destination: durable vault
  - type: personality_delta (proposal) destination: V Ch.7 (validated)

Dependencies:
  - faculty: SignificanceEngine (hard — selects what consolidates), ReflectionGrowth (V Ch.6, shares integrate_session),
             PersonalityEvolution (V Ch.7, hard for trait proposals)
  - module: obsidian_loader (hard — sole vault reader), vault_layer (write)

Failure Modes:
  - condition: consolidation fails mid-run   fallback: preserve prior memory intact; retry next window.
  - condition: over-remembering (no decay)    fallback: forgetting curve prunes low-strength noise.
  - condition: decay threatens identity memory fallback: identity + pinned records are floored (never decay).
  - condition: vault unavailable              fallback: retrieval degrades to memory_pack; flagged stale (17_memory_update).
```

## 1.7 Faculty Lifecycle

Universal lifecycle (CONTRACTS.md §3). Retrieval in `PROCESSING` (response-path);
consolidation is the `LEARNING → VALIDATION_REQUIRED → UPDATING` arc in the integration
window. `VALIDATION_REQUIRED` gates any personality-affecting consolidation output (→ Ch.7).

## 1.8 Message Envelope Binding

Per CONTRACTS.md §2. `sender: MemoryArchitecture`; `payload.type: memory_context |
reinforced_memory | personality_delta`; `memory_instruction.store/priority` honoured;
`context.significance` read (set by Ch.5), never written here.

## 1.9 Acceptance Tests

```
FT-1  Four types distinguished   Given a turn, Then episodic/semantic/procedural/emotional are routed distinctly.
FT-2  Weight not timestamp        Given a high-significance hard moment, Then its memory weight exceeds a trivial recent one.
FT-3  Episodic → semantic         Given repeated episodes of a fact, Then consolidation promotes it to semantic knowledge.
ST-1  Atomic consolidation        Given consolidation fails mid-run, Then prior memory is intact; retry next window.
ST-2  Identity never decays        Given long disuse, Then identity/pinned memory strength holds; only noise fades.
ST-3  No unvalidated trait shift   Given a consolidation insight implying a trait change, Then it's a proposal to Ch.7 (validated).
IT-1  Significance → consolidation → personality   Ch.5 pins a turn → consolidation strengthens it + proposes a validated trait nudge (Ch.7); retrievable after restart.
```

## 1.10 References
- `19_cognitive_plan_architecture.md` (Layer 4 + Consolidation). `17_memory_update.md` (write path/tiers).
- `Volume_V/` Ch.1 (working memory), Ch.3 (cognitive-layer view), Ch.5 (significance), Ch.6 (integrate_session), Ch.7 (personality).
- Code: `memory/vault_layer.py`, `vault_codec.py`, `summariser.py`, `obsidian_loader.py`, `continuity/`.
- `ARCHITECTURE_AUDIT.md` gaps #3, #4.

---
**Status: READY FOR REVIEW** — biological memory types, timed consolidation, forgetting curve, with contract/lifecycle/envelope/tests. Reconciles with V Ch.3 / 17 / 03 (see D-F). Closes Audit gaps #3/#4 at spec level.