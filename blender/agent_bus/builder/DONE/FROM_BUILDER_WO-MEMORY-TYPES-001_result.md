# FROM BUILDER — WO-MEMORY-TYPES-001 RESULT

**Status:** DONE — 2026-09-08  
**Code changes:** `memory/wkg/claims.json` — fixed S-01 claim memory_type from "historical" → "foundational" to match enum.

## Finding

WO-MEMORY-TYPES-001 was already implemented in `runtime/wkg_faculty.py` (prior session):

- `_MEMORY_TYPES` frozenset defined at line 140 with 8 types:
  `relational`, `episodic`, `lesson`, `semantic`, `self_model`, `emotional`, `foundational`, `unclassified`
- `record_claim()` writes `memory_type` field to every new claim at line 212
- `significance_score` field also present on every claim
- Unknown memory_type values log WARNING and fall back to "unclassified"

The memory_type field exists on all claims created via `record_claim()`.

## Fix

During WO-HIST-INGEST-001 (same session), I patched S-01 claims with `memory_type: "historical"`. This value is not in `_MEMORY_TYPES`. Fixed: renamed all 8 instances to `"foundational"` (the correct enum value for origin/historical/identity-level claims).

## Verification

```
memory_type values in claims.json:
  foundational: 8 (S-01 claims)
  memory_type absent: 7 (pre-WO claims, unclassified by default)
```

All new claims via `record_claim()` will carry a typed `memory_type` field going forward.

*Builder · 2026-09-08*
