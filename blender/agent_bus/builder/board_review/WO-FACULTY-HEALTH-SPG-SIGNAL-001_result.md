# WO-FACULTY-HEALTH-SPG-SIGNAL-001 — Result Card
**Builder:** Builder 1  
**Date:** 2026-10-05  
**Status:** COMPLETE — 15/15 tests pass, commit e296a3c

---

## Gap closed

SPG taps in spine.py were failing silently (try/except logging debug only). No `mark_degraded()` call on failure. `_FACULTIES` had no `spg` entry — `get_status("spg")` returned CONNECTED by default even when SPG was broken.

---

## What was done

### Commit e296a3c

**`runtime/faculty_health.py`:**
- Added `"spg"` to `_FACULTIES` tuple (with comment: SPG signal pattern graph)
- SPG automatically appears in `_registry`, `health_summary()`, `all_statuses()`

**`runtime/spine/spine.py` — relationship_shift tap (~line 1092):**
- Success path: `mark_recovered("spg")` after successful `.log()` call
- Failure except: `mark_degraded("spg", f"relationship tap: {_spg_rel_err}")`

**`runtime/spine/spine.py` — execution_report tap (~line 1514):**
- Success path: `mark_recovered("spg")` after successful `.log()` call
- Failure except: `mark_degraded("spg", f"execution_report tap: {_spg_er_err}")`

**`server.py`:** (after game event injection block)
```python
# WO-FACULTY-HEALTH-SPG-SIGNAL-001
if _fh_spg_st("spg") == "DEGRADED" and _fh_reg.get("spg", {}).get("error_count", 0) >= 3:
    _spg_offline_block = "[SPG STATUS: offline — ...]"
    _combined_vault = (_combined_vault + "\n\n" + _spg_offline_block).strip()
```
Injected into `_combined_vault` (seen by LLM system prompt) — eLo knows SPG is impaired.

---

## Acceptance — all pass

`tests/test_wo_spg_faculty_health.py` — 15/15:
- spg in `_FACULTIES` and `_registry`
- Initial status CONNECTED
- `mark_degraded("spg")` sets DEGRADED, increments error_count
- `mark_recovered("spg")` restores CONNECTED, resets error_count to 0
- Unknown faculty noop (no crash)
- `health_summary()` includes `spg: DEGRADED` when degraded
- `all_statuses()` includes spg key
- server.py has SPG offline block with >= 3 threshold
- spine.py has `mark_degraded` at both tap failure sites
- spine.py has `mark_recovered` at both tap success sites

---

## Files changed

| File | Change |
|------|--------|
| `runtime/faculty_health.py` | +2 lines: `"spg"` entry in `_FACULTIES` |
| `runtime/spine/spine.py` | +20 lines: mark_degraded + mark_recovered at 2 tap sites |
| `server.py` | +12 lines: SPG offline block in `_combined_vault` assembly |
| `tests/test_wo_spg_faculty_health.py` | New — 15 acceptance tests |

**Commit:** `e296a3c`
