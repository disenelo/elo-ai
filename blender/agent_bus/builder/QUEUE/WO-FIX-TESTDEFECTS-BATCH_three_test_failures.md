# WO-FIX-TESTDEFECTS-BATCH — Three Test Defects (no WO existed)
**Date:** 2026-08-28
**Priority:** P2 (test hygiene — programme-wide suite health)
**Authority:** Board — defects reported in board_state.json `open_defects` with status "REPORTED TO BOARD — no fix WO yet"
**Scope:** Tests only (or trivial production change where needed). No architecture change. No executive.py.

---

## Context

Three test failures were surfaced to the Board with no fix WO issued. All have known diagnoses.
Fix each in isolation. Return a single result card covering all three.

---

## Defect A — test_wo096 import style mismatch

**File:** `tests/test_wo096_desktop_perception.py` AT-2
**Diagnosis:** `import style mismatch (module vs function import)`
**Action:**
1. Read `tests/test_wo096_desktop_perception.py`. Identify the failing import at AT-2.
2. Fix the import to match the current module structure (module-style vs function-style).
3. Run: `~/miniconda3/bin/python3 -m pytest tests/test_wo096_desktop_perception.py -v` → all ATs PASS.
4. Do not change any production code unless the import path itself no longer exists (in that case, update import path only — no logic change).

---

## Defect B — test_card_0006 _is_truncated character check

**File:** `tests/test_card_0006_perception_world.py` AT-3 and AT-5
**Diagnosis:** `_is_truncated() called on [PARTIAL:...] strings ending in ] not …`
**Action:**
1. Read `tests/test_card_0006_perception_world.py`. Understand AT-3 and AT-5.
2. Check what `_is_truncated()` checks (WO-FIX-PERCEPTION-0006 commit `68642bf` — verify the fix is correct or if AT-3/AT-5 need a separate fix).
3. Determine if the fix is in the test (wrong expected string) or in production (`_is_truncated` checking wrong character).
4. Apply the fix (test or production — whichever is the true defect location).
5. Run: `~/miniconda3/bin/python3 -m pytest tests/test_card_0006_perception_world.py -v` → AT-3 and AT-5 PASS.
6. Do not change unrelated production logic.

---

## Defect C — test_basic_loop ImportError store_interaction

**File:** `tests/test_basic_loop.py` (or equivalent)
**Diagnosis:** `ImportError: store_interaction no longer exported from core/memory_engine.py (removed in commit 84758ea)`
**Action:**
1. Read the failing test. Identify exactly where `store_interaction` is imported from.
2. Check current `core/memory_engine.py` — what is `store_interaction` now called or where was it moved?
3. If renamed or moved: update the import in the test.
4. If removed with no replacement: note this in the result card and ask Board to rule. Do NOT delete the test or comment it out without Board authority.
5. Run: `~/miniconda3/bin/python3 -m pytest tests/test_basic_loop.py -v` (or equivalent) → PASS if fix applied.
6. Do not restore `store_interaction` to `memory_engine.py` unless it is clearly the correct location per current architecture.

---

## Acceptance Tests

| AT | Criterion |
|---|---|
| AT-A | `test_wo096_desktop_perception.py` — all ATs PASS (no import error on AT-2) |
| AT-B | `test_card_0006_perception_world.py` AT-3 + AT-5 — PASS |
| AT-C | `test_basic_loop.py` — import error resolved; ATs PASS (or Board ruling if store_interaction has no replacement) |

---

## Lane rules

- `executive.py` NOT to be touched (FREEZE_V1_LOCK).
- `living_presence_spec.txt` NOT to be touched.
- Fix each defect in the smallest scope. No unrelated cleanup.
- Report if any defect turns out to require a production change beyond what is described — do not silently expand scope.

## Return evidence

`blender/agent_bus/builder/DONE/FROM_BUILDER_WO-FIX-TESTDEFECTS-BATCH_result.md`

Commit hash + AT-A / AT-B / AT-C pass/fail for each.

---

*Board / Lead Architect · 2026-08-28*
