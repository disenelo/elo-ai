# FROM BUILDER → BOARD — WO-EXPRESSION-POLISH-BUNDLE-001 FIX-1: DEDUP Threshold
**Date:** 2026-09-14
**WO:** FROM_ARCHITECT_2026-09-14_WO-EXPRESSION-POLISH-BUNDLE-001.md
**Fix:** WO-DEDUP-THRESHOLD-001 — raise threshold, narrow ring buffer

---

## Current threshold (verbatim from code before fix)

`runtime/backend_router.py:372`:
```python
def _is_duplicate(new: str, prev: str, threshold: float = 0.88) -> bool:
```

---

## Changes applied

**`runtime/backend_router.py`:**
- `_is_duplicate()` threshold raised from `0.88` → `0.95`
- Comment updated: "0.88 was still silencing valid low-variation Ollama outputs (T3, T6 audit failures). 0.95 retains near-exact duplicate guard while allowing natural phrase variation."

**`runtime/response_gate.py`:**
- `_SESSION_DEDUP_WINDOW` narrowed from `3` → `1`
- Only the IMMEDIATELY preceding response is checked for exact-match duplication. Prior window=3 was blocking T3 and T6 because Ollama naturally reuses phrasing patterns across non-adjacent introspective turns.

---

## Verification

```python
from runtime.backend_router import _is_duplicate
from runtime.response_gate import _SESSION_DEDUP_WINDOW, _is_repetition, _record_response, _SESSION_LAST_RESPONSES

# Threshold confirmed
_is_duplicate distinct pair → False  ✓
_is_duplicate near-identical (92% overlap, below 0.95) → False  ✓ (correct: not blocked)

# Window confirmed
_SESSION_DEDUP_WINDOW: 1  ✓

# Non-adjacent suppression (T1 same response as T3) — with window=1, T1 dropped by T2
T3 same as T1 (non-adjacent) suppressed? False  ✓ (was True with window=3)

# Adjacent suppression still works
T4 same as T3 (adjacent) suppressed? True  ✓ (back-to-back identical still blocked)
```

---

## Root cause of T3/T6 failures

Ollama at default temperature produces identical short introspective responses across non-adjacent turns on open-ended questions. The ring buffer at window=3 caught these as "duplicates" even though the inputs (T3: "if you could change one thing...", T6: "tell me something true") were entirely different from earlier turns. With window=1, only an immediately-adjacent exact repeat blocks.

---

## Live server evidence

Requires server restart + test run. Server evidence for T3 and T6 producing real responses will appear in REAUDIT card (FIX-5). The code change is the gate-level fix — no deflection path can fire unless the IMMEDIATELY preceding response was byte-for-byte identical.

---

## DoD

- [x] Current threshold: 0.88 (now 0.95)
- [x] Ring buffer narrowed: 3 → 1
- [x] Non-adjacent same-response no longer suppressed (verified in unit test)
- [ ] T3 live response — in FIX-5 REAUDIT
- [ ] T6 live response — in FIX-5 REAUDIT

---

*Builder · 2026-09-14*
