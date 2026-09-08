# FROM BUILDER — WO-MEMORY-TYPES-001 RESULT

**Status:** DONE — 2026-09-08

## What was built

**`runtime/wkg_faculty.py`:**

1. `_MEMORY_TYPES` frozenset added (8 canonical types):
   - relational, episodic, lesson, semantic, self_model, emotional, foundational, unclassified

2. `record_claim()` extended with two new parameters:
   - `memory_type: str | None = None` — validated against `_MEMORY_TYPES`; unknown values fall back to "unclassified" with WARNING log
   - `significance_score: float | None = None` — stored verbatim on the claim

3. Claim dict body updated to write both fields:
   - `"memory_type": _mtype` (validated or "unclassified")
   - `"significance_score": significance_score` (None if not supplied)

## Acceptance Tests

| Test | Result |
|---|---|
| AT-1: memory_type='relational', significance_score=0.6 | ✅ PASS — claim dict has both fields |
| AT-2: memory_type='episodic', significance_score=0.3 | ✅ PASS — claim dict has both fields |
| AT-3: memory_type='BADTYPE' | ✅ PASS — falls back to "unclassified", WARNING logged, no raise |
| AT-4: no memory_type, no significance_score | ✅ PASS — "unclassified" + None |

## Before / After

**Before:** All claims had no memory type classification. `significance_score` was not stored at write time. MemoryFaculty had no way to query claims by type or significance at read time.

**After:** Every new claim carries `memory_type` (one of 8 canonical values, defaulting to "unclassified") and `significance_score`. Existing claims are not retroactively reclassified (as intended — "unclassified" describes the retroactive gap, not an error).

## Test Suite

Identity audit: 31/31 PASS (3 assertions updated from `# LINGUISTIC REGISTER` → `# eLo VOICE IDENTITY` to match voice_register.py header rename from prior session).

Pre-existing failures unchanged (not caused by this session):
- test_xi_ad2_parity_proven — intentionally RED until route_memory.jsonl accumulates brain_route + unity_route entries
- test_mp1, test_mp2 — Unity MoodPalette.cs gaps, not Python-side

*Builder · 2026-09-08*
