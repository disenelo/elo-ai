# WO-NAV-006 — World-Change Detection + Significance Faculty Schema
**From:** Board / Lead Architect  
**To:** Builder  
**Authority:** David L3 — Execution Directive 2026-08-24  
**Date issued:** 2026-08-24  
**Priority:** HIGH — Wave 1 independent  
**RTR:** RTR-048 (significance schema), RTR-050 (world-change detection, trigger_source), RTR-051 (compute_delta schema)  
**SPEC basis:** `specs/SPEC_STAGE2_EMBODIED_ONE_BRAIN_2026-08-23.md` — SP-27, SP-28, SP-29 schema layer, SP-30

---

## Context

eLo currently has no mechanism to detect that the world has changed between turns. Without world-change detection:
- Curiosity remains a static float (0.5) — not a response to novelty
- The significance faculty (SP-29) cannot score any delta
- Self-initiation (SP-33) cannot determine whether anything warrants attention

This WO builds the infrastructure: SP-27 (save previous world state) → SP-28 (compute delta) → SP-29 schema layer (significance faculty structure without final weights) → SP-30 (trigger_source annotation).

**Key constraint from execution directive:** SP-29 weights are D-gated (David L3 decides final values). Build the faculty structure with uniform `[ESTIMATE]` weights as explicit placeholders. Do not invent final values.

---

## Deliverables

### D-1 — SP-27: `PreviousWorldSummary` written per turn
**File:** `runtime/spine/spine.py` (at turn end) or world assembly — Builder's call based on existing code structure  
**Contract:** At the end of each turn, save a summary of the current world state to a stable location (`world_dict["previous_world"]` or equivalent). The summary must capture at minimum:
- Current platform / body position (`body_win_id` or best available equivalent until Unity B1 is built)
- Current gaze target
- Current live_world summary (platforms visible, any recent events)
- Turn timestamp

This is a point-in-time snapshot, not a full copy of EloSelfState. Sufficient detail to compute a meaningful delta next turn.

### D-2 — SP-28: `compute_delta()` function (schema layer)
**File:** `runtime/spine/spine.py` or a new `runtime/world_delta.py`  
**Contract:**
```python
def compute_delta(previous_world: dict, current_world: dict) -> dict:
    """
    Returns a WorldDelta dict comparing previous and current world state.
    Fields include (at minimum):
    - position_changed: bool
    - gaze_changed: bool
    - new_platforms_visible: list
    - lost_platforms_visible: list
    - elapsed_turns: int
    - any_change: bool  # True if any of the above are non-trivial
    """
```

The delta is computed at the start of each turn (comparing previous_world saved by SP-27 to current world state). Result is stored in world_dict as `world_delta`.

**Note:** This is the schema layer. The weights that interpret these deltas into significance scores are in SP-29.

### D-3 — SP-29 schema layer: `significance_faculty.py`
**File:** `runtime/significance_faculty.py` (new file)  
**Contract:** Create the significance faculty structure:
```python
def compute_significance(world_delta: dict, elo_self_state: dict) -> dict:
    """
    Returns a significance_score dict with 14 dimensions:
    presence, learning, logic, humour, relationship, creation,
    system_change, novelty, continuity, overall, embodiment,
    efficiency, safety, reward
    
    All values: float 0.0–1.0
    
    [ESTIMATE] weights: currently uniform / placeholder.
    David L3 will specify final weights when behavioural decisions are made (D-gate SP-29).
    """
```

Wire this faculty into the turn loop so it runs after world_delta is computed. Result stored in world_dict as `significance_score` (or equivalent — verify existing key name in `last_significance.json`).

### D-4 — SP-30: `trigger_source` annotation
**Files:** attention dict, decision journal, lesson_store (wherever these records are created)  
**Contract:** Add field `trigger_source: str` to three record types:
- Attention dict: records what triggered this attention cycle (`"user_message"` | `"world_change"` | `"self_initiation"` | `"scheduled"` | `"unknown"`)
- Decision journal: records what triggered the Executive decision
- Lesson record in lesson_store: records what triggered the learning event

No new logic — just add the field and populate it from available context. Default to `"user_message"` if source is not determined.

---

## Forbidden Scope

- No changes to `executive.py` or FREEZE_V1_LOCK files
- Do not set final significance weights — placeholders only, clearly marked `[ESTIMATE]`
- Do not implement SP-31/SP-32 (self-initiation threshold — Design/MT gated)
- Do not change existing consequence or lesson logic

---

## Verification

| AT | Description | Pass condition |
|---|---|---|
| AT-1 | PreviousWorldSummary saved | After a turn, world_dict contains `previous_world` (or equivalent) with expected fields |
| AT-2 | compute_delta runs | world_dict contains `world_delta` after turn with correct comparison (position_changed, gaze_changed etc.) |
| AT-3 | significance_faculty returns 14-dim dict | `compute_significance()` returns dict with all 14 required dimension keys |
| AT-4 | significance stored | world_dict / `last_significance.json` updated with new significance_score after each turn |
| AT-5 | trigger_source present | attention dict, decision journal, and lesson records all contain `trigger_source` field |
| AT-6 | [ESTIMATE] weights explicit | `significance_faculty.py` contains explicit `# [ESTIMATE]` comments on all weight values |

---

## RTR Traceability

After implementation, update in `RECOVERY_TRACEABILITY_REGISTER_2026-08-24.md`:
- RTR-048: add WO-NAV-006, commit, AT-3/AT-4/AT-6 pass
- RTR-050: add WO-NAV-006, commit, AT-1/AT-2/AT-5 pass
- RTR-051: add WO-NAV-006, commit, AT-2 pass

---

*Board / Lead Architect — 2026-08-24*  
*Authority: David L3 — Execution Directive 2026-08-24*

---

## Result — Builder 2026-08-24

**Status:** DONE  
**Commit:** `5257fa5` — WO-NAV-006: world-change detection + significance faculty schema  
**Tests:** 15/15 PASS (`tests/test_wo_nav_006.py`)

### Deliverables executed

| D | SP | File | Status |
|---|---|---|---|
| D-1 | SP-27 | `runtime/world_delta.py` — `save_world_summary()`, `load_previous_world()` | ✅ |
| D-2 | SP-28 | `runtime/world_delta.py` — `compute_delta()` | ✅ |
| D-3 | SP-29 | `runtime/significance_faculty.py` (new) — `compute_significance()`, 14-dim, all `[ESTIMATE]` | ✅ |
| D-4 | SP-30 | `runtime/spine/spine.py`, `self/decision_journal.py`, `self/lesson_store.py` — `trigger_source` | ✅ |
| Wire | — | `runtime/executive_context.py` — previous_world, world_delta, significance_score wired; save_world_summary called | ✅ |

### Acceptance tests

| AT | Result |
|---|---|
| AT-1: previous_world in world_dict | PASS |
| AT-2: world_delta computed and in world_dict | PASS (4 sub-tests) |
| AT-3: significance_faculty 14-dim dict | PASS (3 sub-tests) |
| AT-4: significance_score in world_dict | PASS |
| AT-5: trigger_source in attention/journal/lesson | PASS (4 sub-tests) |
| AT-6: [ESTIMATE] comments explicit in source | PASS |

### RTR updates required
- RTR-048: WO-NAV-006, commit 5257fa5, AT-3/AT-4/AT-6 PASS
- RTR-050: WO-NAV-006, commit 5257fa5, AT-1/AT-2/AT-5 PASS
- RTR-051: WO-NAV-006, commit 5257fa5, AT-2 PASS

*Builder — 2026-08-24*
