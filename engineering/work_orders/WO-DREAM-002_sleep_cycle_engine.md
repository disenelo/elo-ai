# WO-DREAM-002 — Dream Faculty: Sleep Cycle Engine

**Status:** OPEN — P0 CLEARED 2026-09-26
**Priority:** P1 | **Assigned:** Builder 1 | **Authored:** 2026-09-27 (David L3)
**Source:** engineering/work_orders/WO-DREAM-ENGINE-001_eLo_Dream_State_Complete.md

---

## PHASE 1 — Sleep Cycle Engine

**File:** `faculties/dream/sleep_cycle.py` (new)

Replace the current single-cycle NREM/REM binary with a controllable generative schedule.

```
CYCLE 1: NREM → DEEP → REM
CYCLE 2: NREM → DEEP → REM
CYCLE 3: NREM → DEEP → REM
CYCLE 4: NREM → LIGHT → REM
CYCLE 5: NREM → LIGHT → LONG REM
```

Each cycle has:
- `cycle_number` (1–5)
- `phase` ("nrem" / "deep" / "light" / "rem")
- `rem_duration` (grows with each cycle — Cycle 1 REM ~10min, Cycle 5 REM ~40min)
- `dream_intensity` (float 0.0–1.0, derived from cycle position)

**Dream Intensity scale:**
```
0.00 — waking residue
0.25 — fragmented memory
0.50 — associative dream
0.75 — strong symbolic dream
1.00 — maximum surreal / emotional synthesis
```

Intensity drives: prompt abstraction, number of concepts merged, visual distortion, layer opacity, blend modes, randomness, colour transformation.

**Cycle content weighting:**
- Early cycles (1–2): recent experiences, concrete memories, recent conversations, current projects, grounded imagery
- Middle cycles (3): memory recombination, WKG relationships, older experiences, recurring SPG patterns, unresolved ideas
- Late cycles (4–5): abstraction, unusual associations, distant memories, emotional transformation, surreal imagery, creative recombination

Write `blender_state.json` → `"dream_cycle": N, "dream_phase": "nrem|deep|rem", "dream_intensity": 0.0–1.0` on each phase transition. Unity reads for visual state.

---

## BUILDER RESULT — 2026-09-27

**Status:** BUILT + UNIT TESTED — LIVE VERIFIED (pipeline run)
**Commit:** `a2331e2`
**File:** `faculties/dream/sleep_cycle.py`
**Evidence:** `engineering/evidence/DREAM/WO-DREAM-001-005_pipeline_core_evidence.md`

### What was built

- 5-cycle schedule via `build_schedule(n_cycles)` — returns list of `CyclePhase` objects (NREM→REM×5)
- `CyclePhase` fields: `cycle_number`, `phase`, `duration_s`, `dream_intensity`, `content_band`, `long_rem`, `index`
- `dream_intensity` rises with cycle number (0.08 at cycle 1 → 1.0 at cycle 5)
- `SleepCycle` state machine with `publish()` — writes `dream_cycle`, `dream_phase`, `dream_intensity` to `blender_state.json`
- `publish_phases=True` wired at `server.py:1042` (later updated to `server.py:1088`)

### Live pipeline run result

```
sched = build_schedule(5)  # → 15 CyclePhase objects
CyclePhase(cycle_number=1, phase='nrem', duration_s=900,
           dream_intensity=0.08, content_band='early', ...)
```

15 phases generated. Phase structure intact. Intensity ramp confirmed.

### Tests

`test_dream_sleep_cycle` — 12 passed

Builder 1 · 2026-09-27 / 28
