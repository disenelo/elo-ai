# WO-TEMPORAL-EXEC-WIRE-001 — Result Card
**Builder:** Builder 1  
**Date:** 2026-10-04  
**Status:** DONE — committed `2c1ee7d`

---

## Finding

Implementation was already in place (prior session, already in board_review). However 5 tests were failing with "not enough values to unpack (expected 4, got 3)" from `temporal_state.py:170`.

**Root cause:** `_read_intentions()` was extended to return a 4-tuple `(active, deferred, reasons, durations)` by WO-HONEST-DURATION-001. Five test mocks were written before that extension and still patched with 3-tuples. The unpack failure at line 156 was silently caught at line 170, returning an empty `TemporalFrame` — causing all intent-related assertions to fail.

---

## What was fixed

Added the missing `[]` (durations) to 5 `return_value` mock tuples:

| Test | Line | Change |
|---|---|---|
| `test_elo_temporal_state_001.py::AT-4` | 105 | `(mock_active, [], [])` → `(mock_active, [], [], [])` |
| `test_elo_temporal_state_001.py::AT-5` | 122 | `([], texts, reasons)` → `([], texts, reasons, [])` |
| `test_elo_temporal_state_001.py::AT-6` | 136 | `([], texts, reasons)` → `([], texts, reasons, [])` |
| `test_elo_temporal_state_001.py::AT-10` | 180 | 3-tuple → 4-tuple |
| `test_causal_chain_001.py::AT-11` | 344-348 | 3-tuple → 4-tuple |

No changes to implementation code — implementation was correct.

---

## Test results

`tests/test_elo_temporal_state_001.py` — 13/13 PASS  
`tests/test_causal_chain_001.py::test_at11_temporal_state_distinguishes_states` — PASS  
Total: **14/14 PASS**

---

## Files changed

| File | Lines | Change |
|---|---|---|
| `tests/test_elo_temporal_state_001.py` | 105, 122, 136, 180 | Add missing `[]` durations to 4 mock tuples |
| `tests/test_causal_chain_001.py` | 344-348 | Add `[]` durations line to mock tuple |

---

## Commit

`2c1ee7d` — `WO-TEMPORAL-EXEC-WIRE-001: fix 5 stale test mocks — add missing durations tuple element`
