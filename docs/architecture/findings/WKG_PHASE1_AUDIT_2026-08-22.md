# WKG Phase 1 — Audit Report
**Date:** 2026-08-22
**Builder:** Claude (Sonnet 4.6)
**Authority:** David L3 + Lead Architect ruling 2026-08-22
**Contract:** `docs/architecture/WKG_BUILD_CONTRACT_AMENDED_2026-08-22.md`
**Status:** IN_REVIEW — Phase 1 complete; Phase 2 (corpus ingestion) blocked pending David APPROVE

---

## Deliverable

Phase 1 per §16 of the amended contract: schema extension, write gate, and
`retrieve_wkg()` integration — auditable before any corpus data is written.

**Files created / modified:**

| Path | Action | Description |
|---|---|---|
| `knowledge/wkg_schema.py` | NEW | WKG epistemic classes, relationship vocabulary, dual-classification mapping, write gate, Claim/Source/Provenance dataclasses |
| `knowledge/graph_loader.py` | MODIFIED | `_WKG_CLAIMS_KEY` constants + WKG section load in `_load_all()` + `retrieve_wkg()` |
| `relationships/world_graph.json` | MODIFIED | Added `wkg_claims: []`, `wkg_sources: []`, `wkg_proposed_claims: []`, `_wkg_meta` |
| `tests/test_wkg_phase1.py` | NEW | 20 acceptance tests (AT-W1–AT-W13) |

---

## Amendment A — Epistemic reconciliation ✅

**Requirement:** Retain 8 epistemic classes. Add `wkg_epistemic_class` to Claim.
Map to Vol XXIV `kind` + `confidence` at retrieval boundary. No second epistemic system.

**Evidence:**

`knowledge/wkg_schema.py`:

- `WKGEpistemicClass` enum: 8 classes (VERIFIED, HISTORICAL, SOURCE_ATTRIBUTED, SYMBOLIC,
  HYPOTHESIS, SPECULATIVE, DISPUTED, UNKNOWN).
- `EPISTEMIC_TO_VOL_XXIV` mapping table: all 8 classes map to `kind` + `confidence`
  + `provisional` per the contract's §3 table.
- `WKGClaim.wkg_epistemic_class`: mandatory field on every Claim node.
- `WKGClaim.vol_xxiv_kind()` / `vol_xxiv_confidence()`: computed at retrieval from
  `wkg_epistemic_class`; not stored in the graph.
- `retrieve_wkg()` (`graph_loader.py`): injects `kind` and `confidence` via
  `map_to_vol_xxiv()` at the retrieval boundary; passes both `wkg_epistemic_class`
  (for display) and `kind` (for Executive reasoning) in the result envelope.

No second epistemic system: there is one mapping table, one retrieval function, one
envelope shape.

**Test coverage:** AT-W5 (all 8 classes), AT-W6 (mapping table), AT-W8 (envelope),
AT-W13 (helper methods).

---

## Amendment B — Governed graph-write gate ✅

**Requirement:** Proposal stages SOURCE → … → HYPOTHESIS produce no graph write.
Four-condition write gate for VERIFIED, HISTORICAL, SOURCE_ATTRIBUTED, SYMBOLIC,
HYPOTHESIS, SPECULATIVE, DISPUTED. HYPOTHESIS/SPECULATIVE remain `proposed_claim`
pending David L3 confirmation.

**Evidence:**

`knowledge/wkg_schema.py` — `evaluate_write_gate(claim: dict) → WriteGateResult`:

| `wkg_epistemic_class` | Evidence present? | Decision |
|---|---|---|
| VERIFIED | yes | WRITE |
| VERIFIED | no | NEEDS_EVIDENCE |
| HISTORICAL | yes | WRITE |
| HISTORICAL | no | NEEDS_EVIDENCE |
| SOURCE_ATTRIBUTED | any | WRITE_AS_PERSPECTIVE |
| SYMBOLIC | any | WRITE_AS_PERSPECTIVE |
| HYPOTHESIS | any | PROPOSED_PENDING_L3 |
| SPECULATIVE | any | PROPOSED_PENDING_L3 |
| DISPUTED | any | WRITE_BOTH_CONTRADICTS |
| UNKNOWN | any | PROPOSED_PENDING_L3 |

ADR-Exec-005 D1: "Language-only processing is never evidence" — VERIFIED/HISTORICAL
with empty `evidence` list return NEEDS_EVIDENCE, not WRITE.

**Test coverage:** AT-W7a through AT-W7h (all 8 gate paths).

---

## Amendment C — Single canonical graph ✅

**Requirement:** WKG is an extension of Vol XXIV. No `wkg_graph.json`. No
`wkg_loader.py`. Extend existing `knowledge/graph_loader.py`. WKG-originated nodes
use `wkg:` namespace. Use existing Vol XXIV write path.

**Evidence:**

- `relationships/world_graph.json`: three new sections added (`wkg_claims`,
  `wkg_sources`, `wkg_proposed_claims`) in the existing file. No new file created.
- `knowledge/graph_loader.py`: WKG sections loaded in the existing `_load_all()`;
  `retrieve_wkg()` added to the existing module. No `wkg_loader.py`.
- `wkg:` namespace prefix: enforced in `WKG_NAMESPACE_PREFIX = "wkg:"` constant;
  required on all `id`, `subject`, `object`, `source` fields of WKG nodes.
- `retrieve_wkg()` returns the same `{label, content, confidence, kind, evidence,
  score}` envelope as `retrieve()`, compatible with the existing `KnowledgeContext`
  contract. Phase 7 will extend `build_context()` to support structured
  `KnowledgeQuery` input — not done here.
- Existing eLo-universe data: 17 entities + 17 relationships unchanged (AT-W11
  verified entity/relationship counts).

**Confirmed absent:**
```
knowledge/wkg_graph.json        — DOES NOT EXIST ✅
knowledge/wkg_loader.py         — DOES NOT EXIST ✅
relationships/wkg_graph.json    — DOES NOT EXIST ✅
```

**Test coverage:** AT-W9 (no second store), AT-W11 (sections in canonical file).

---

## Amendment D — FREEZE unlock ✅

**Requirement:** Record David L3 ruling: `wkg:` is a governed namespace within
the canonical knowledge graph, outside the FREEZE prohibition on new eLo-universe
entities/viewpoints.

**Evidence:**

- `docs/architecture/FREEZE_V1_CARVEOUT_WKG_2026-08-22.md`: existing document
  (pre-existing — written before Phase 1 by Board). Records Option 2 ruling.
  Confirms: eLo-universe namespace remains frozen; cross-namespace promotion requires
  explicit governance approval.
- `relationships/world_graph.json` → `_wkg_meta.freeze_status`:
  `"wkg: namespace is a governed FREEZE V1 carve-out (Amendment D). eLo-universe namespace remains frozen."`
- `knowledge/wkg_schema.py` module docstring: cites carve-out document.
- No new CAL action introduced (FREEZE_V1_LOCK — all 9 actions frozen).

**Test coverage:** AT-W10 (no new CAL action).

---

## 5-Question Component Gate (01_PRINCIPLES.md) ✅

Does WKG Phase 1 improve at least one of:
understanding · continuity · creativity · relationships · long-term learning?

**Understanding**: YES — enables eLo to hold multiple interpretations of reality
simultaneously, preserve provenance, and distinguish evidence from belief. The
Contradiction Engine (Phase 6) directly improves understanding.

**Long-term learning**: YES — governed write gate + proposed_claim mechanism creates
a structured path from new information to verified knowledge.

**Provenance tag:** `[ENGINEERING]` — system-design choice (schema + gate) governed
by the WKG build contract.

---

## Phase 1 acceptance test results

```
WKG Phase 1 acceptance tests   20 passed   0 failed
```

| Test | Description | Result |
|---|---|---|
| AT-W1  | WKGClaim schema with wkg_epistemic_class | ✅ |
| AT-W2  | WKGSource schema | ✅ |
| AT-W3  | wkg: namespace prefix | ✅ |
| AT-W4  | Provenance fields (§4) | ✅ |
| AT-W5  | All 8 epistemic classes representable | ✅ |
| AT-W6  | Dual-classification mapping table (Amendment A) | ✅ |
| AT-W7a | Write gate: VERIFIED + evidence → WRITE | ✅ |
| AT-W7b | Write gate: VERIFIED, no evidence → NEEDS_EVIDENCE | ✅ |
| AT-W7c | Write gate: SOURCE_ATTRIBUTED → WRITE_AS_PERSPECTIVE | ✅ |
| AT-W7d | Write gate: SYMBOLIC → WRITE_AS_PERSPECTIVE | ✅ |
| AT-W7e | Write gate: HYPOTHESIS → PROPOSED_PENDING_L3 | ✅ |
| AT-W7f | Write gate: SPECULATIVE → PROPOSED_PENDING_L3 | ✅ |
| AT-W7g | Write gate: DISPUTED → WRITE_BOTH_CONTRADICTS | ✅ |
| AT-W7h | Write gate: UNKNOWN → PROPOSED_PENDING_L3 | ✅ |
| AT-W8  | retrieve_wkg() KnowledgeContext-compatible | ✅ |
| AT-W9  | No wkg_graph.json, no wkg_loader.py (Amendment C) | ✅ |
| AT-W10 | No new CAL action (FREEZE_V1_LOCK) | ✅ |
| AT-W11 | world_graph.json carries WKG sections | ✅ |
| AT-W12 | retrieve_wkg() returns [] on empty corpus | ✅ |
| AT-W13 | vol_xxiv_kind() / vol_xxiv_confidence() match table | ✅ |

---

## Regression

```
Vol XXIV (test_canon_xxiv_world_graph.py): 5/5 ✅
BDRIFT-U (test_bdrift_u_trait_isolation.py): 18/18 ✅
```

---

## Phase 1 not-done list (boundaries respected)

| Item | Status | Reason |
|---|---|---|
| Joseph corpus ingestion | NOT STARTED | Phase 2 — after David APPROVE on Phase 1 |
| Sun/Moon/Seasons graph | NOT STARTED | Phase 3 |
| Number system (13/28/364) | NOT STARTED | Phase 4 |
| Contradiction Engine | NOT STARTED | Phase 6 |
| Structured KnowledgeQuery interface | NOT STARTED | Phase 7 |
| SPG (Semantic Point Graph) | NOT TOUCHED | Remains INERT/PARKED per E-1 RED |

---

## What Phase 2 requires from David

1. **APPROVE Phase 1** → Builder proceeds to Phase 2 corpus ingestion
2. HYPOTHESIS/SPECULATIVE claims from Joseph corpus will arrive as `proposed_claim`
   nodes; each requires David L3 confirmation before promotion to full Claim node.

---

— David review: ☐ APPROVE (→ DONE, Phase 2 opens)   ☐ LOOP BACK: <notes>
