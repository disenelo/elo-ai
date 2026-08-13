# WO-CANON-XXIV — Knowledge: the promotion threshold, the demotion/unlearn path, and who decides

**Owner:** Builder (eLo OS — `knowledge/`, with Vol VIII Consolidation). **Priority:** P3 — Tier B.
**Status:** OPEN — **AMENDED + RE-OPENED 2026-08-13.** The graph/retrieval half shipped (board line 1467,
commit `964228c`). The previous version of this WO **omitted the promotion threshold entirely and specified
no demotion, retraction or unlearn path** — so "what eLo learns forever" shipped with an undefined knob and
no way back. That is the scope this amendment adds, plus two verified gaps in the shipped retrieval half.
**Nothing here is DONE; nothing here is RATIFIED.**

**Canon refs:** Volume XXIV — Ch.1 `01_Ontology_and_the_Knowledge_Graph.md` (§1.3.7 the Memory/Knowledge
split, §1.7 sole runtime writer, §1.3.8 ontology), Ch.2 `02_Semantic_Retrieval_Confidence_Evidence.md`
(§2.2 `kind`, §2.4 evidence, §2.5 world_state citation), Ch.3 `03_Compression_and_Reasoning_Support.md`
§3.4 (**The Memory bridge**). One-Brain Invariant #1 · Runtime Invariant 7 (Memory Ownership) ·
ADR-Exec-005 (Learning Through Verified Consequences) · Ruling A (2026-08-10) ·
**`docs/architecture/LEARNING_LOOP_v1.md` §3 (the promotion model these thresholds MUST agree with)**.

---

## IRV — shipped state (verified 2026-08-13 by reading the code and the data)

| Item | Verified |
|---|---|
| Ruling A (one canonical graph) | **Closed in code.** `knowledge/graph_loader.py:25` reads `relationships/world_graph.json`. `identity/world_graph.json` carries `{"_retired": true, "_retired_date": "2026-08-11", "_successor": "relationships/world_graph.json", "_note": "…Do not read from this file."}` and no non-test module reads it. |
| Ranked retrieval | **Present.** `retrieve(user_input, top_k)` at `graph_loader.py:98`; results sorted by `(score, confidence)` descending; `build_context()` retained for back-compat. |
| `confidence` + `evidence[]` | **Present as fields** (`graph_loader.py:126–128, 142–144`), defaulting to `1.0` / `[]`. |
| **🟠 Epistemic `kind` is not implemented** | Ch.2 §2.2 requires `kind ∈ {fact, perspective, inference, promoted_memory}`. The shipped code sets `"kind": e.get("type", "entity")` (L127) and `"kind": "relationship"` (L143) — that is the **ontology type**, not the epistemic kind. The name is overloaded; the confidence bands and the "perspective always tagged" rule cannot be enforced on it. |
| **🟠 `evidence[]` is unenforced** | Default `[]` means an orphan fact is representable. Ch.2 §2.4: *"a `fact`/`promoted_memory` unit MUST carry non-empty `evidence[]` — no orphan facts."* Nothing asserts it. |
| **🔴 Promotion** | **No promotion code exists anywhere.** Nothing in `knowledge/` or the Consolidation path writes a `promoted_memory` node. The canon bar is prose only — Ch.1 §1.3.7 rule 2: *"Promotion requires the durable, repeatedly-verified bar — one mention is a memory, not knowledge"*; Ch.3 §3.4: *"durable, repeatedly-verified"*. **No number is stated anywhere in Volume XXIV.** |
| **🔴 Demotion / retraction** | **Does not exist in canon or code.** Ch.1 §1.3.7 rule 4 says *"deleting a memory does not delete the knowledge"* — which, with no retraction path, means **a promoted node is permanent and unreachable by correction**. If eLo promotes something wrong, there is no mechanism by which he can stop believing it. |

## Problem / Goal

Volume XXIV is the store of **what eLo knows forever**. It ships today with (a) an undefined promotion
knob — "durable, repeatedly-verified" with no number, so any implementer invents one — and (b) **no way to
unlearn**: no demotion, no retraction, no path for David to say *"that's wrong"* and have it take effect.
Meanwhile `LEARNING_LOOP_v1.md` §3.4 already defines a fully-numbered promotion/demotion/retirement model
for the lessons ledger. Two promotion models in one brain, one of them undefined, is the One-Brain
violation this volume exists to prevent.

Goal: state the Memory→Knowledge promotion threshold as numbers, give it a demotion/retraction path with a
named decider at each tier, and make both agree with `LEARNING_LOOP_v1.md` §3 so there is one promotion
model in eLo, not two.

## Scope to DoD

### A. The promotion threshold — Memory → Knowledge (the missing knob)

Promotion is performed **only** by the Consolidation Faculty (Vol VIII §1.3), **timed** (session-close /
nightly), **never per-turn** — eLo cannot learn a hallucination in the response path. It is the **only**
runtime writer to the graph (Ch.1 §1.7).

A semantic fact is promoted out of Memory into Knowledge only when **all** hold:

| Condition | Rule | Agrees with |
|---|---|---|
| Strength | memory `strength >= 0.70` | `LEARNING_LOOP_v1.md` §3.4 (candidate → confirmed) |
| Distinct evidence | `>= 3` distinct `episode_ref` (SPOT codes, Vol VIII §1.2) | §3.3 / §3.4 |
| Spread | those refs span `>= 2` distinct sessions | §3.4 |
| Verification | `>= 2` of those episodes carry `verified: true` (a body ACK, tool result, or a fact David stated) | §3.3 + ADR-Exec-005 |
| Durability | the fact is about the **world**, not about a single event — it has outlived the conversation about it (Ch.1 §1.3.7 rule 1) | Ch.1 |
| Provenance | the new node carries `evidence[]` pointing back at the vault records (SPOT_CODE); knowledge **points at** memory, never copies it | Ch.1 §1.3.7 rule 3 |

**Hard exclusions (assert in code, do not merely document):**
- A **text-only** episode (`verified: false`) **counts toward nothing** — it may be recorded, it may never
  promote (`LEARNING_LOOP_v1.md` §3.3, ADR-Exec-005 enforced numerically).
- **World State never promotes directly.** A live-derived claim is *cited* at reasoning time with
  `evidence.type: world_state` and must travel Memory → Consolidation → promotion to become durable
  (Ch.3 §3.4).
- Promotion **never** touches identity, values, or personality. Those are Vol X / Vol XXI and are
  proposal-only under David's yes (Ruling XXI, 2026-08-10).
- A promoted node's `kind` MUST be `promoted_memory` — never `fact` (authored canon). The distinction must
  stay auditable forever (Ch.1 §1.7).

**Tunability:** these numbers are **Architect defaults, tunable by the Builder without an L3** — matching
`LEARNING_LOOP_v1.md` §3.4's stated latitude. What is **not** tunable without David is the *shape*: timed-
only, verified-only, provenance-mandatory, Consolidation-only.

### B. The demotion / retraction / unlearn path (does not exist today)

Mirror of promotion, same evidence discipline, **nothing is ever silently deleted**:

| Transition | Rule | Decider |
|---|---|---|
| **weaken** | a contradicting verified episode lowers node `confidence` by `0.20` (floor 0.0) | Consolidation (automatic, timed) |
| **demote** `promoted_memory` → `contested` | `confidence < 0.50`, **or** 3 consecutive contradictions | Consolidation (automatic, timed) |
| **retract** `promoted_memory` → `retracted` | `confidence < 0.20`, **or** 60 days with zero confirming evidence, **or** the underlying evidence refs no longer resolve | Consolidation (automatic, timed) |
| **re-promote** `retracted` → `promoted_memory` | only on a fresh **verified** confirming episode; `confidence` resets to `0.30` and must re-earn the §A bar | Consolidation |
| **David's correction** — *"that's wrong, forget that"* | immediate `retracted` with `reason: "david_correction"`, effective the same turn (not deferred to nightly) | **David.** This is the user-facing unlearn path and it must exist. |
| **authored canon** node (`kind: fact`) | may **never** be demoted or retracted by Consolidation | **Architect only**, via an ADR / canon change (D-LANES, D-M). Consolidation attempting it is a violation. |
| **identity- / values-adjacent** node | never auto-anything | **David L3** (Ruling XXI: any change to VALUES is proposal-only and needs David's yes) |

**Retraction semantics (MUST):**
- `retracted` nodes are **kept**, not deleted — with `retracted_at`, `reason`, and their original
  `evidence[]` intact. Provenance is part of the record; every decision must remain explainable
  (`LEARNING_LOOP_v1.md` §3.4, *"Nothing is ever deleted"*).
- A `retracted` or `contested` node is **excluded from retrieval** (`retrieve()` must not return it as
  grounding), so retraction is behaviourally real and not cosmetic.
- Retraction is **logged** — a retraction eLo cannot explain is indistinguishable from forgetting.
- Deleting the source memory does **not** delete the knowledge (Ch.1 §1.3.7 rule 4) — but it **does**
  invalidate that evidence item, which may push the node under the retraction bar. Both rules hold together.

### C. Cross-reference and reconcile with `LEARNING_LOOP_v1.md` (so the two agree)

- `LEARNING_LOOP_v1.md` §3 governs the **lessons ledger** (`self/lessons_ledger.jsonl`, candidate →
  confirmed → retired, sole writer `lesson_store.promote_pass()`); this WO governs the **knowledge graph**
  (memory → `promoted_memory` → contested → retracted, sole writer Consolidation). **Two ledgers, one
  promotion model.**
- The shared, non-negotiable model: evidence is `ref`-bearing and verified · repeats strengthen rather than
  duplicate · promotion is timed and never in the response path · demotion mirrors promotion · nothing is
  deleted · one named sole writer per store.
- **If a number changes in one, it changes in both.** Add an explicit cross-reference note in
  `docs/architecture/Volume_XXIV/` §3.4 pointing at `LEARNING_LOOP_v1.md` §3.4 and vice versa
  (Architect lane).
- **Do not build a third promotion mechanism.** Check-Before-Build binds here.

### D. Close the two verified retrieval gaps (small, and they block §A/§B being testable)

- Add the epistemic `kind ∈ {fact, perspective, inference, promoted_memory}` as its **own** field, distinct
  from the ontology `type`. Retire the overload at `graph_loader.py:127/143`. Confidence bands
  (≥0.9 assert · 0.6–0.9 light qualification · 0.3–0.6 hedge · <0.3 or absent ⇒ treat as not known) are
  Executive-consumed and derived from this field, not stored.
- Enforce `evidence[]` non-empty for `fact` and `promoted_memory`; `perspective` needs none but MUST be
  tagged. Keep `strength` as **salience only, never confidence** — do not overload it. Enforce referential
  integrity: every relationship `from`/`to` resolves to an existing entity `id`.
- Empty retrieval returns `""` — silence over noise, and **MUST NOT** fall back to base-model general
  knowledge (Verified Speech, ADR-Exec-001).

## Files to TOUCH
- `knowledge/graph_loader.py` (epistemic `kind`; evidence enforcement; exclude contested/retracted from
  retrieval; referential integrity)
- the Consolidation write path (Vol VIII) — promotion pass, demotion pass, retraction, `david_correction`
- `relationships/world_graph.json` (schema fields: `kind`, `evidence[]`, `confidence`, `promoted_at`,
  `retracted_at`, `reason`, `status ∈ {promoted_memory, contested, retracted}`) — additive, back-compatible
- `tests/test_canon_xxiv_world_graph.py` and a new `tests/test_canon_xxiv_promotion.py`
- `docs/architecture/Volume_XXIV/03_Compression_and_Reasoning_Support.md` §3.4 + `LEARNING_LOOP_v1.md` §3.4
  cross-reference — **Architect lane**, relayed.

## Files MUST-NOT-TOUCH
- `identity/world_graph.json` (retired per Ruling A — do not read, do not revive)
- `self/lessons_ledger.jsonl` / `self/lesson_store.py` (the lessons ledger is `LEARNING_LOOP_v1.md`'s lane —
  agree with it, do not implement it here)
- Personality / values / identity stores (Vol X, Vol XXI — never written by promotion)
- `world/live_world_state.py` (cited via `evidence.type: world_state`, never absorbed)

## Definition of Done
- The promotion threshold exists **as numbers in code**, enforced by Consolidation only, timed only,
  verified-only, with mandatory provenance.
- A demotion path, a retraction path, and a **David-correction unlearn path** all exist and are
  behaviourally real — a retracted node stops appearing in retrieval.
- Every transition names its decider (Consolidation · Architect · David · David L3) and is logged.
- Retracted nodes are kept with `reason` + `retracted_at`; nothing is silently deleted.
- The thresholds in this WO and in `LEARNING_LOOP_v1.md` §3.4 are cross-referenced and do not contradict.
- Epistemic `kind` is a real field; no orphan facts; contested/retracted excluded from grounding.
- **This WO does not confer DONE** and does not promote Vol XXIV to RATIFIED.

## Tests (`tests/test_canon_xxiv_promotion.py` — new; existing `test_canon_xxiv_world_graph.py` stays)
- **PT-1** A fact with 3 verified refs across 2 sessions and `strength >= 0.70` promotes to
  `kind: promoted_memory` with `evidence[]` pointing at the SPOT codes.
- **PT-2** A fact with 3 refs but **only text-only** episodes (`verified: false`) **never** promotes.
- **PT-3** Promotion never runs in the response path — assert the promoter is invoked only from the timed
  consolidation entry point, never from `server.py` / `spine.run()`.
- **PT-4** A live World-State-derived claim cannot promote directly; it must travel through Memory.
- **DT-1** Three consecutive contradictions demote `promoted_memory` → `contested`.
- **DT-2** A retracted node is **excluded from `retrieve()`** and cannot ground a reply.
- **DT-3** David's *"that's wrong, forget that"* retracts the node **in the same turn**, with
  `reason: "david_correction"`.
- **DT-4** Nothing is deleted: after retraction the row still exists with `retracted_at`, `reason`, and its
  original `evidence[]`.
- **DT-5** Consolidation attempting to demote an **authored** (`kind: fact`) node is refused — Architect
  lane only.
- **DT-6** Re-promotion from `retracted` requires a fresh verified episode and re-earns the full §A bar.
- **AG-1 (agreement)** The numeric constants used here match `LEARNING_LOOP_v1.md` §3.4 (strength ≥0.70,
  ≥3 refs, ≥2 sessions, ≥2 verified, demote <0.50, retire <0.20 / 3 contradictions / 60 days). A drift
  between the two files fails this test.
- **KT-1** Epistemic `kind` is distinct from ontology `type`; `perspective` always tagged; a `fact` or
  `promoted_memory` with empty `evidence[]` is rejected.
- **KT-2** Referential integrity — no dangling `from`/`to`; `strength` never read as confidence.
- **KT-3** Empty retrieval returns `""` and never falls back to base-model general knowledge.

## Dependencies + blocked-by
- **Blocked by:** none for §A/§B/§D. Ruling A is closed (verified above), which released the graph half.
- **Depends on:** **Vol VIII Consolidation** being callable on the timed cadence (it is the sole writer —
  if it is not wired, promotion has no host and this WO must wire it or explicitly stop at the spec).
  Coordinate with `LEARNING_LOOP_v1.md` §7's `lesson_store` work so the two promotion passes are built
  against the same model rather than diverging.
- Cross-volume: Vol VIII (sole bridge/writer; SPOT_CODE vault = the evidence target) · Vol XV (composed,
  never merged) · Vol V Executive (sole asserter) · Vol X/voice (phrases qualification only) · Vol XXI
  (narrates over the graph; values changes stay David's).
- **Gate:** **David** owns the correction/unlearn semantics for anything he stated, and **David L3** any
  identity/values-adjacent retraction (Ruling XXI). The numeric thresholds are Architect defaults, Builder-
  tunable, no L3. Architect promotes Vol XXIV only after CA acceptance.

## Lane
Builder (Python — `knowledge/graph_loader.py` + the Consolidation promotion/demotion passes + schema
fields). Architect writes the Vol XXIV ↔ `LEARNING_LOOP_v1.md` cross-reference and carries the
correction/unlearn semantics to David.
