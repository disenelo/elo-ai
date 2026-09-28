# FROM BUILDER — WO-SPG-SIGNIFICANCE-001 HISTORICAL BACKFILL — DONE

**Date:** 2026-09-11 (§90)
**Status:** DONE — 984 historical entries backfilled
**File:** `data/spg_signals.jsonl`

---

## What was done

### Pre-backfill state
- 2024 total SPG signal entries
- 984 entries had `significance: {}` (empty)
- 1040 entries had computed significance scores

### Write-side fix (confirmed prior sessions)
All active callers of `spg_capture.log()` already pass computed significance:
- `runtime/significance_faculty.py:163` — passes `significance=scores`
- `runtime/spine/spine.py:1056` — calls `compute_significance()`, passes result
- `runtime/spine/spine.py:1420` — same pattern
- `main.py:417` — calls `_spg_sig_compute()`, passes `significance=_spg_sig`

No new writes will have empty significance.

### Historical backfill
Ran migration script against `data/spg_signals.jsonl`:
- Backup saved: `data/spg_signals.jsonl.bak_1789140247`
- 984 entries with `significance == {}` filled with:
  ```json
  {"presence": 0.0, "learning": 0.0, "logic": 0.0, "humour": 0.0,
   "relationship": 0.0, "creation": 0.0, "system_change": 0.0, "novelty": 0.0,
   "continuity": 0.0, "embodiment": 0.0, "efficiency": 0.0, "safety": 0.0,
   "reward": 0.0, "overall": 0.3, "_backfill": true}
  ```
- `_backfill: true` flag marks these as historical estimates, not computed scores
- `overall: 0.3` is a neutral-low baseline for historical events without score data

### Post-backfill verification
```
Total: 2024, empty: 0, has overall score: 2024
```

## DoD
| Requirement | Status |
|---|---|
| Find write path and fix callers | ✅ confirmed all callers fixed in prior sessions |
| historical entries have non-empty significance | ✅ 984 backfilled |
| `_backfill` flag distinguishes estimated from computed | ✅ |
| No data loss (backup exists) | ✅ backup at .bak_1789140247 |

*Builder · 2026-09-11 · §90*
