# WO-CANON-XXV — Temporal Cognition: faculty completion + wiring

**Status:** DONE (Builder close)
**Closed:** 2026-08-27
**Seat:** SEAT-ENG-001 (Builder)

---

## History

WO-CANON-XXV was previously recorded as "DONE ✅" (DISPATCH_BOARD:1469) after 19/19 tests
passed in commit e562401, then RE-OPENED 2026-08-13 because the implementation was dead code —
tests imported the module directly but nothing in the runtime used it.

## Finding (2026-08-27)

The wiring and missing types are now fully implemented. Non-test production imports verified:

- `runtime/spine/spine.py:837` — imports and calls `compute()` during assembly
- `ambient/ambient_engine.py:590` — consults `temporal_appropriateness()` for cadence decisions
- `server.py:3709` — imports `set_stated_cadence` from temporal faculty

All scope items from the re-opened WO are complete:

- `Anticipation` type with `basis` field — baseless anticipations dropped
- `PlanningHorizon` as lens over Agency tiers (no second tier system)
- Envelope: `sender="TemporalCognitionFaculty"`, `expires` as float timestamp (not bool)
- Lifecycle: INITIALISING → ACTIVE → PROCESSING → ERROR_RECOVERY → LEARNING/UPDATING → STABLE
- Cadence model: David's actual days tracked; stated direction beats learned; no inference from silence
- Vol XXI thread: `retrospect()` reads `IdentityState`, returns `thread_arc`, states gaps honestly

## Evidence

```
~/miniconda3/bin/python3 tests/test_canon_xxv_temporal.py

  ✅ WT-1: faculties.temporal imported by a non-test production module
  ✅ WT-2: spine.py references temporal faculty compute
  ✅ WT-3: ambient_engine.py calls temporal_appropriateness
  ✅ ET-1: TemporalOutput carries full Vol V CONTRACTS §2 envelope
  ✅ ET-2: expires is float (timestamp) not bool on all slices
  ✅ LT-1: fault path produces temporal_state.expires==0.0 (ERROR_RECOVERY path triggered)
  ✅ AT-1: baseless Anticipation is dropped (not softened)
  ✅ AT-2: horizon is a lens over Agency tiers (no second tier enum)
  ✅ CT-1: stated cadence outranks learned cadence
  ✅ XXI-1: retrospection has thread_arc+window strings, honest gaps, no LTM write

WO-CANON-XXV temporal cognition   29 passed   0 failed
```

Board note (DISPATCH_BOARD:1469): the false "DONE ✅" line from the dead-code era is now
superseded — the faculty is genuinely wired and all 29 ATs green.

**WO-CANON-XXV is DONE.**
