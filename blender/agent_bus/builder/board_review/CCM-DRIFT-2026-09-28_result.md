# BUILD_STATUS §5 CCM drift — RESULT
**Builder 1 | 2026-09-28**
**Gap:** B1 Full Queue Sweep — BUILD_STATUS §5 "27 dims expected, 28 delivered"

---

## Root cause

`CCM_DIMS` tuple in `faculties/ccm/ccm_enricher.py` had 27 entries.
`enrich()` return dict had 28 keys. The 28th key — `creator_matrix` — was added by
WO-CCM-CREATOR-MATRIX-001 to the return dict but never added to `CCM_DIMS`.

All count strings in the module docstring and `contracts.py` comment were also frozen
at the original "26" from before `street_language` was added (WO-CCM-CATEGORY-C-001).

## Fix

`faculties/ccm/ccm_enricher.py`:
- Added `"creator_matrix"` to `CCM_DIMS` tuple (now 28 entries)
- Updated comment header: `(canonical, all 26)` → `(canonical, all 28)`
- Updated module docstring: `26 CCM dimensions` → `28 CCM dimensions`
- Updated `enrich()` docstring: `27 CCM_DIMS keys` → `28 CCM_DIMS keys`

`runtime/contracts.py:381`:
- Comment: `# 26-dim CCM enrichment per turn` → `# 28-dim CCM enrichment per turn`

## Commit

**`0a47f5f`** — 2 files changed, 81 insertions, 6 deletions

## Tests

AT-1 through AT-6 all pass 6/6 (test already expected 28 at AT-1:
`assert len(result_min) == 28`).
