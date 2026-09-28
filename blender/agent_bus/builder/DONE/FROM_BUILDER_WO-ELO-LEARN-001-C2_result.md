# FROM BUILDER — WO-ELO-LEARN-001 Component 2 (SPG as Real Link Layer) — DONE

**Date:** 2026-09-12 (§91 continued)
**Status:** DONE + VERIFIED
**Files changed:** `memory/spg_faculty.py` (query_spg_entities)

---

## Problem

`query_spg_entities()` had 129 SPG nodes loaded (26 KB graph) but NEVER consulted them during entity retrieval. The function did pure text search + CCM relationship-type filter. SPG significance scores were written but never read. The SPG was infrastructure without function.

---

## Fix

Added Step 2/3 to `query_spg_entities()`:

1. Load SPG graph → build `claim_id → significance` dict from nodes
2. Load `memory/wkg/claims.json` → for each candidate entity_id, find all associated claims (subject OR object role) → get max SPG significance
3. Re-sort entity_ids by max SPG significance (descending) before CCM filter

This makes SPG nodes act as a genuine ranking signal: entities associated with high-significance claims surface first, pushing lower-significance structural edges down the list.

---

## Verification

```
DEBUG: SPG rerank: 27 entities; top sig=0.70
```
- 27 candidate entities from text search, reranked by SPG significance
- Top entity: `eLo` (CONCEPT) at sig=0.70 — correct, eLo should dominate any eLo universe query
- SPG fallback path preserved: if graph load fails, entity order stays as text-search order

---

## Architecture

Before:
```
text_search → [entity_ids unranked] → CCM filter → [:10]
SPG (129 nodes, 10 edges) → unused
```

After:
```
text_search → [entity_ids] → SPG significance rerank → CCM filter → [:10]
SPG significance used as primary sort before CCM filter
```

---

## Remaining Components

- **Component 3** (WKG write enrichment for DEEP turns) — partially complete via WO-WKG-LIVE-WRITE-001
- **Component 4** (Living Presence in base_cognition path) — blocked on LIVING-PRESENCE-UPDATE-001 FREEZE

*Builder · 2026-09-12 · §91 continued*
