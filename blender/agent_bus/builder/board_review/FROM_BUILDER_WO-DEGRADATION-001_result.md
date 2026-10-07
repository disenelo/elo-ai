# Board Review — WO-DEGRADATION-001

**Filed by**: Builder 1  
**Date**: 2026-10-06  
**Commit**: 3501b8b  
**Status**: COMPLETE — ready for Board sign-off

---

## What was built

Faculty result validation gate + `MEMORY_UNAVAILABLE` / `WKG_UNAVAILABLE` flags in CognitiveState.

### Files changed

| File | Change |
|---|---|
| `runtime/contracts.py` | CognitiveState: `memory_unavailable: bool = False`, `wkg_unavailable: bool = False`, `failed_faculties: tuple = ()` |
| `runtime/spine/spine.py` | Faculty validation gate: checks `working_memory`, `high_priority_memory` (from attention), `_wkg_context`, `_self_model`. Populates all three new flags. Wired into CognitiveState construction. Also fixes pre-existing NameError: `high_priority_memories` was undefined — now `_high_priority_memories = (attention or {}).get("high_priority_memory", [])` and used in `reasoning_tier` computation (was silently causing `assemble_cognitive_state` to always raise NameError, always returning None to spine.run() which swallowed it) |
| `server.py` | Reads `_cs.memory_unavailable` and `_cs.wkg_unavailable` to inject `[SYSTEM — MEMORY_UNAVAILABLE]` / `[SYSTEM — WKG_UNAVAILABLE]` blocks into the system prompt |
| `tests/test_wo_degradation_001.py` | NEW — 6 tests DEG-1..DEG-6 |

---

## Important fix: pre-existing NameError in assemble_cognitive_state

`reasoning_tier` computation used `high_priority_memories` which was never defined in the function. This caused every call to `assemble_cognitive_state()` to raise `NameError`, which spine.run()'s try/except swallowed — meaning `_cognitive_state` was always `None` in production. This is now fixed as part of the degradation gate work.

---

## Test results

```
6 passed in 0.24s  (DEG-1 through DEG-6)
Full suite: 7 failed (all pre-existing), 3530 passed — no regressions
```

---

## Board decisions required

None. Standard P2 instrumentation WO.

---

**Next WOs**: WO-CAP queue or remaining items from IS-ELO VERDICTS REMAINING DOMAINS brief
