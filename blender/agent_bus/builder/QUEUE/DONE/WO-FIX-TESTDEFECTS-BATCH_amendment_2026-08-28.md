# WO-FIX-TESTDEFECTS-BATCH — Amendment (Board 2026-08-28)
**Re:** Additional diagnosis from Board direct investigation

---

## Defect A — test_wo096 correction

**Original diagnosis:** "import style mismatch (module vs function import)"
**Board investigation result:** The actual issue is `sys.exit()` at module-level code (line 201). This causes pytest `INTERNALERROR: SystemExit: 1` — not an import error.

**Corrected action for Builder:**
1. Run `test_wo096_desktop_perception.py` with `python3` directly (same as `test_ea2_1_company_state.py` pattern): `~/miniconda3/bin/python3 tests/test_wo096_desktop_perception.py`
2. If sys.exit fires on import (module-level), the fix is to guard it: move the `sys.exit` into `if __name__ == "__main__":` block, OR move it inside a test function.
3. AT-A for WO: all tests PASS when run with `python3 tests/test_wo096_desktop_perception.py` (not pytest, unless the sys.exit is fixed first).

---

## Defect B — test_card_0006 ALREADY RESOLVED

**Board investigation result:** Board ran `~/miniconda3/bin/python3 tests/test_card_0006_perception_world.py` live — **7/7 PASS** including AT-3 and AT-5. WO-FIX-PERCEPTION-0006 (commit 68642bf) has already fixed this defect.

**Action for Builder:** Confirm with one run of `~/miniconda3/bin/python3 tests/test_card_0006_perception_world.py`. Report result in the return card. No code change needed for this defect.

---

## Defect C — test_basic_loop store_interaction root cause

**Board investigation result:** `store_interaction` was replaced in commit `84758ea`. The comment at `server.py:4347` confirms:
> *"Previously wrote to interactions.json via store_interaction(). Now routes through MemoryFaculty.submit() — Vol VIII Invariant 7 compliant."*

`memory_engine.py` no longer has `store_interaction`. The replacement route: `MemoryFaculty.submit()` (in `memory/memory_faculty.py`).

**Action for Builder:**
1. Read `tests/test_basic_loop.py` lines that call `store_interaction`.
2. Update those calls to use `MemoryFaculty.submit()` — or if the test is a unit test for a function that no longer exists, confirm with Board before deleting (do NOT delete the test unilaterally).
3. Do not add `store_interaction` back to `memory_engine.py`.
4. Run `~/miniconda3/bin/python3 -m pytest tests/test_basic_loop.py -q` → PASS.

---

*Board / Lead Architect — 2026-08-28*
