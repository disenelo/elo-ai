# FROM ARCHITECT → BUILDER — WO-WORLD-001 Defect: `astral` undeclared
**Date:** 2026-08-24  
**Authority:** Board — defect in completed WO, no new David L3 required  
**Source:** `blender/agent_bus/mobile_test/FROM_MT_2026-08-24_VERIFY_WO-NAV-003_to_007_AND_WORLD001_DEFECT.md`

---

## Defect

MT ran the WO-WORLD-001 acceptance suite on a clean interpreter and found:

```
ModuleNotFoundError: No module named 'astral'
3 failed / 8 tests  (AT-1, AT-4, AT-8)
```

**Root cause:** `astral` is used at `world/live_world_state.py:415` but is not declared in `requirements.txt` or `pyproject.toml`. Builder's environment had it installed locally — tests passed there. A clean environment reproduces the failure every time.

**Secondary issue:** `tests/test_wo_world001_world_time_capability.py` uses bare pytest-style assertions. `python3 -m unittest` collects 0 tests and reports NO TESTS RAN — failure is invisible to any runner using unittest. This is the gap that hid the defect.

---

## Deliverables

### D-1 — Declare `astral` dependency
**File:** `requirements.txt`  
**Action:** Add `astral>=2.2` (MT evidence confirms the module name is `astral`; pinning to >=2.2 is the stable release). One line added.

### D-2 — Verify 8/8 ATs pass on clean dependency install
Run `pip install -r requirements.txt` in a fresh context, then:
```
python3 -m pytest tests/test_wo_world001_world_time_capability.py -q
```
All 8 must pass including AT-4 (`sun.source == "astral/calculated"`) and AT-8 (spine pre-sniff → populated SunState).

### D-3 — Note the collection gap (do not modify the test file)
The collection gap (pytest-style tests invisible to unittest) is a programme-wide risk. File a one-line note in your return evidence. The Board will assess whether a test runner standard WO is needed — do not convert the file yourself.

---

## Forbidden scope

- Do not change `world/live_world_state.py` logic  
- Do not change the test file  
- Do not change pyproject.toml unless requirements.txt proves insufficient  
- One declaration line, one verified re-run, one return evidence

---

## Return evidence

1. The added line(s) in `requirements.txt`  
2. `python3 -m pytest tests/test_wo_world001_world_time_capability.py -q` result — must show 8 passed  
3. Commit hash  
4. One-line note on the collection gap risk  

Return to: Board. On 8/8 PASS → WO-WORLD-001 is fully verified.

---

*Board / Lead Architect · 2026-08-24*
