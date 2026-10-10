**WO:** FIX-FAILING-TESTS · **Seat:** builder · **Priority:** P0
**Reserved?** no

## Goal
Fix all confirmed code failures from the full test run. These are not import path errors — these are real assertion failures in the code.

## Confirmed failures to fix — investigate each, fix the code, rerun until green

### Backend / routing
- `test_wo030_weather_location.py` — **12/14 FAILING**. Weather routing broken. Highest failure count.
- `test_wo032_backend_voice_drift.py` — 3 failed
- `test_wo032_pinned_backend.py` — 1 failed
- `test_0020_ct0033_bypass_handlers.py` — FAIL: expected 53 `_bypass_journal` calls, found 55. Count changed since test was written.
- `test_wo122_route_capability_to_executor.py` — 1 failed

### Identity / memory
- `test_0009_row1_identity.py` — 1 failed
- `test_0017_autobiography_provenance.py` — 1 failed
- `test_card_0021_p0_identity_and_world.py` — 1 failed
- `test_wo039_f4_cross_session_recall.py` — 1 failed
- `test_wo039_f6_mirror_scrub.py` — 1 failed
- `test_wo_relationship_style.py` — 4 failed
- `test_wo081_emergent_cognition.py` — 1 failed
- `test_wo102_person_place_event.py` — 3 failed

### Architecture / ordering
- `test_canon_iii_system_arch.py` — 1 failed
- `test_canon_iv_ordering_invariants.py` — 2 failed
- `test_0038_exception_list_ratified.py` — 2 failed
- `test_card_0020_d6_silent_turn_alarm.py` — 2 failed
- `test_drop_loop_0001.py` — 2 failed
- `test_orch_no_false_close.py` — 5 errors
- `test_wo004_contracts.py` — 1 failed

### Perception / wave
- `test_0005_wo120_spatial_faculty.py` — 2 failed
- `test_0010_wo103_wave3.py` — PW-2: `_write()` strips gaze (WO-100 open)
- `test_0012_wave4_verify_choose.py` — 1 failed
- `test_wo016_019_voice_completeness.py` — 1 failed

### Stale hash (executive.py changed — update the hash in the test)
- `test_d3_lesson_reaches_executive.py` — hash mismatch. Update expected hash to `9f55186da3386234b065ccb1b0efeb98afa56d2f`

### Capability
- `test_wo_create_capability.py` — 1 failed

### Memory / learning
- `test_wo_memory_unlearn_001.py` — investigate failure

## Process
For each: run the test, read the failure output, fix the code, rerun until green. Do not mark fixed until the test passes.

## Files to touch
Whatever each failing test points to — read the failure message first.

## Done when
All above tests green. Committed. Move to BUILT/.

## Result
- commit: 8248723 (WO-0101: fix all confirmed test failures across 22 files)
- tests fixed: 71 WO-0101 targets — all green (71 passed, 0 failed)
- remaining failures (if any): 18 pre-existing environmental/design-gap issues —
  all out of scope per WO spec ("not import path errors"):
  - 16 missing-module failures: numpy (dream FX), cryptography (Alexa ingress), openai (dream scene)
  - 1 deliberate red marker: test_canon_xi_a_d_route::test_xi_ad2_parity_proven (sys.exit(1) by design — WO-CANON-XI-UNITY-ROUTE open)
  - 1 collection error: test_b3_interrogative_routing (pre-existing)

## Live turn needed
> Board reruns the full test suite and confirms failure count dropped to 0 real failures.
