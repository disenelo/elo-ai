---
chapter: 2
title: "The Four Memory Types & Their Data Shapes"
volume: VIII
status: READY FOR REVIEW
version: 0.1.0
owner: David Charles
architect: Claude (Lead Architect)
implementation: PARTIAL (tiered vault + facts + embeddings live; procedural/emotional typing implicit)
audit_status: OPEN
dependencies:
  - Volume_VIII/01_Memory_Architecture.md (the model this chapter schematises)
  - Volume_V/03_Memory_Architecture.md (six cognitive layers — reconciled, not forked)
  - Volume_V/05 Significance (weight source), Volume_V/04 Emotional (emotional tag)
  - memory/vault_layer.py, memory/vault_codec.py (tiered store + spot codes)
  - memory/fact_store.py (durable semantic facts), memory/embedding_store.py (meaning retrieval)
---

# Chapter 2: The Four Memory Types & Their Data Shapes

## 2.0 Purpose

Chapter 1 names the four biological memory types and states *that* eLo stores
experience biologically rather than as one flat log. This chapter defines the **exact
data shapes** each type takes in the live system, so the Architecture Agent can extend
storage without inventing a schema. Where Chapter 1 is the model, this is the record
format.

The governing discipline: **the type is *what* is stored; the tier is *how*.** A memory's
biological type (episodic / semantic / procedural / emotional) is orthogonal to its
physical tier (index → summary → deep). Both are recorded on every record.

## 2.1 The Four Types — Concrete Definitions

Restating Ch.1 §1.1 as storable categories, each with the live signal that produces it:

```
Episodic     a dated event / conversation / milestone      "Volume VIII Ch.2 was written today"
Semantic     a durable fact or concept, timeless           "eLo uses a layered memory architecture"
Procedural   a workflow / habit / how-David-works pattern  "David frames commits as WO-<n>: <verb>…"
Emotional    which episodes MATTERED, indexed by weight    a hard moment kept above a hundred trivial ones
```

**Rules (MUST):**

- **2.1.1 Episodic and semantic never collapse.** An event ("the chapter was written") and
  the knowledge it produced ("eLo uses layered memory") are stored as distinct records.
  Consolidation (Ch.3) *promotes* episodic → semantic; it never overwrites the episode with
  the fact.
- **2.1.2 Emotional memory indexes by `weight`, not by `date`.** The 0–9 `weight` field on a
  record IS its emotional/significance index. Recency does not raise weight; significance
  (Vol V Ch.5) and reinforcement (Ch.3) do. This is the mechanism behind Ch.1 §1.1 "a
  meaningful hard moment outlives a hundred trivial ones."
- **2.1.3 Procedural memory captures pattern, not utterance.** How David works — commit
  framing, review cadence, lane discipline — is procedural. The live carrier today is
  `memory/personality_drift.py` + `project_registry.json`; a first-class procedural record
  type is **PENDING** (see §2.6).

## 2.2 The Physical Record — Three Tiers

The store is the three-tier Obsidian vault under `obsidian_vault/09 Memory/`, written
**only** through `memory/vault_layer.py` and read **only** through
`memory/obsidian_loader.py` (Ch.4 §4.4). This is the live anchor Chapter 1 §1.2 defers to.
(Note: Chapter 1 and older docs point at `17_memory_update.md §6/§7` for this — that file is
currently a **stub** (`STATUS: PENDING`). The authoritative live spec is `vault_layer.py`;
this chapter grounds there directly. Flag for reconciliation — §2.6.)

```
09 Memory/
  SPOT_CODES.md         # tier 1 — master scannable index, one row per record
  summary/<code>.md     # tier 2 — one-sentence note + weight + wikilink to deep
  deep/<code>-deep.md   # tier 3 — full compressed memory block (≤2000 chars)
```

**Tier rules (MUST):**

- Every summary and deep note carries YAML frontmatter with `type: memory-summary` /
  `memory-deep` so `obsidian_loader` picks it up automatically. A record without that
  frontmatter is invisible to retrieval — never write one.
- The index row and the two notes are written together in one `write_memory()` call
  (`vault_layer.py`). Partial writes (index without notes) are a corruption; the writer
  must produce all three or none.
- Deep text is compressed to ≤2000 chars, summary to ≤200 chars (`vault_codec.compress_text`).
  The vault stores **meaning, never raw transcript** (aligns with Vol XXI §1.1.1 and the
  anti-fabrication discipline).

## 2.3 The Spot Code — Every Memory's Address

Each record is addressed by a **spot code** encoding project · type · date · weight,
produced by `memory/vault_codec.py::encode`:

```
EO·BL·2607·9
│  │   │    └─ weight 0–9   (9 = core identity; the emotional/significance index — §2.1.2)
│  │   └────── date bits    (DDMM)
│  └────────── type code    BL=build FX=fix DC=decision LN=learn CN=connect DS=design CV=conversation
└───────────── project code EO=elo-os · GM=elo-game · RB=elo-robot · BK=elo-book · DIS=disenelo · DV=david · GN=general
```

**Rules (MUST):**

- The spot code is the memory's stable identity across index, summary, and deep tiers and
  across restart. Retrieval, reinforcement (Ch.3 `reinforce(spot_code)`), and the
  autobiographical thread (Vol XXI) all key on it.
- `weight` is written into the code AND the frontmatter `weight:` field AND the body
  `**Weight:** N/9` line. Consolidation's decay/reinforce updates all display copies
  (`consolidation_faculty._update_weight_in_content`); a divergence between them is a bug.

## 2.4 Summary-Note Schema (canonical, from `vault_layer._write_summary_note`)

```yaml
---
type: memory-summary
domain: memory
spot: EO·BL·2607·9          # address (§2.3)
bits: <encoded bitstring>
project: EO                 # project code
memory-type: BL             # type code (episodic build, etc.)
date: 2026-08-10
weight: 9                   # 0–9 emotional/significance index (§2.1.2)
tags: ["architecture", "memory"]
deep: [[deep/<fname>-deep]] # wikilink to tier 3
---
> <one-sentence summary ≤200 chars>
**Code:** `EO·BL·2607·9`
**Weight:** 9/9 (core identity)
**Date:** 2026-08-10
→ [[deep/<fname>-deep|Load full context]]
```

The deep note mirrors this with `type: memory-deep` and the full ≤2000-char body. **No new
fields may be added to these schemas without a canon update** — retrieval, decay, and the
loader all parse them positionally by frontmatter key.

## 2.5 Two Companion Stores (live, distinct from the vault)

Not all memory is a weighted episodic/semantic vault record. Two live stores sit beside it:

- **Durable semantic facts — `memory/facts.json` via `fact_store.py`.** Key→sentence slots
  (location, current project, stated preferences) that must survive restart and inject into
  the system prompt every turn (`facts_summary()`). These are **semantic** memory in the
  fastest-access form: no weight, no decay, overwrite-on-update. Use for facts eLo must
  never have to "recall" — it simply *knows* them.
- **The Memory Pack — `memory/memory_pack.json` via `memory_pack_builder.py`.** A ≤2000-char
  **derived working digest** (identity · entities · active projects · emotional carry ·
  recent context · `high_priority[]`) merged from vault + state + registry at session start.
  It is **not a memory type** — it is the per-session retrieval cache the Executive reads
  (Ch.4 §4.3). It is rebuildable and disposable; nothing durable lives only here.

**Rule (MUST):** the fact store and memory pack are **caches/fast-paths over** the durable
store, never parallel sources of truth. A fact that matters long-term is also a vault
record; the pack is always regenerable from vault + state.

## 2.6 Open Questions / PENDING

- **First-class procedural + emotional records.** Today `memory-type` codes cover
  build/fix/decision/learn/connect/design/conversation — a *procedural* code and an explicit
  *emotional* code do not exist; procedural lives implicitly in `personality_drift` /
  `project_registry`, emotional lives implicitly as `weight`. Whether to add explicit type
  codes or keep them as facets of the existing seven is an open decision (relates to Vol V
  Ch.4 emotional, Vol X personality). Flag for CA/David.
- **`17_memory_update.md` is a stub.** Ch.1 and this volume's metadata cite its "§6/§7" for
  the write path/tiers; the file reads `STATUS: PENDING`. Either (a) write it as the prose
  write-path spec pointing at `vault_layer.py`, or (b) retire the reference and make Vol VIII
  the sole memory root (the D-F direction). Recommend (b). Flag for reconciliation.
- **Semantic (embedding) retrieval is best-effort.** `embedding_store.py` needs
  `OPENAI_API_KEY`; without it, retrieval silently falls back to keyword scoring
  (`vault_layer.lookup`). Meaning-retrieval (Vol V Ch.3 "meaning not keyword") is therefore
  **degraded, not guaranteed**, in the local/offline brain floor. See Ch.4 §4.3.

## 2.7 References
- Code: `memory/vault_layer.py` (tiers, write, lookup), `memory/vault_codec.py` (spot code,
  weight labels, compression), `memory/fact_store.py`, `memory/memory_pack_builder.py`,
  `memory/embedding_store.py`, `memory/obsidian_loader.py` (sole reader).
- Canon: Volume_VIII Ch.1 (model), Ch.3 (consolidation/forgetting), Ch.4 (writer/retrieval/boundary);
  Volume_V Ch.3 (six-layer view), Ch.5 (significance → weight), Ch.4 (emotional tag).

---
**Status: READY FOR REVIEW** — the four types as storable categories, the three-tier vault
schema, spot-code addressing, and the two companion stores, all grounded in live code.
Reconciles with Vol V Ch.3 (does not fork). Flags: stub `17_memory_update.md`; procedural/
emotional first-class typing PENDING.
