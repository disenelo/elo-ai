# FROM_BUILDER — WO-KNOWLEDGE-PERSIST-001
**Status:** DONE — 3 facts written, persistence verified, WKG-to-prompt path confirmed
**Date:** 2026-09-09
**Builder:** Claude (session b15c1e7a resumed)

---

## Step 1 — Three knowledge facts written to WKG

All written via `record_claim()` with `epistemic_class='VERIFIED'`, `memory_type='foundational'`, `confidence=0.99`:

| Claim | source_id | claim_id (prefix) |
|---|---|---|
| David IS London-based (PLACE entity) | S-KP-001 | 7a42e542 |
| David ASSOCIATED_WITH DISENELO (CONCEPT) | S-KP-002 | f6795059 |
| eLo REPRESENTS David | S-KP-003 | d8c495a5 |

## Step 2 — Cold boot persistence check

`_load("claims")` in `wkg_faculty.py` reads directly from `memory/wkg/claims.json` on disk every call. No in-memory cache between calls. All 3 S-KP-* claims confirmed present on disk.

WKG `_load()` design: `open(path).json.load()` — no singleton, no session cache. Every call to `get_claims_about()` / `_load("claims")` re-reads the file. Cold boot CANNOT lose WKG data (it was never in memory to begin with).

## Step 3 — Verified claim counts

Post-write:
- David entity claims via `get_claims_about()`: **36**
- eLo entity claims via `get_claims_about()`: **17**
- Total KP facts on disk: **3** (S-KP-001/002/003 confirmed)

## Step 4 — WKG-to-prompt path confirmed active

`server.py:3130-3140`: `retrieve_wkg_context_items(raw)` → `render_context_block()` → appended to `g_ctx` → system prompt. Path is wired. Claims about David and eLo will surface when `raw` input triggers entity retrieval.

## INTENT PROOF

"Verify recovered knowledge cannot silently disappear." — Knowledge CANNOT silently disappear. `_load()` reads from disk every turn. Claims written this run are immediately available on next server start. The data is not session-scoped.

## Observation

36 claims for David includes many `ASSOCIATED_WITH` turns from today's WO-WKG-LIVE-WRITE-001 broad-pattern fallback work. The WKG is now accumulating at a higher rate per turn.
