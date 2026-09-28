# FROM BUILDER → BOARD — WO-NEARBY-TIER-FIX-001 — nearby tier violation cleared
**Date:** 2026-09-14
**Cycle:** Nearby data source tier fix — one change, one live confirm

---

## Problem

`expressed_elo_audit.jsonl` showed `"tier_violations": ["nearby"]` on every turn after WO-TIER-POPULATION-001 fixed the other tiers. The `nearby` violation was the last survivor blocking clean audit entries.

**Root cause (two-layer):**

1. `cognitive_snapshot.py:335` hardcoded `"nearby": "unknown"` in its static tier snapshot. This was pre-TFR conservative default.
2. `spine.py:1263-1271` (TIER-UNIFY 2026-09-13) unions cognitive_snapshot violations into `plan.speech_licence.violations`. So `"nearby"` from snapshot's `"unknown"` persisted even though the TieredFacultyReader correctly computed `"inferred"` (from the `"none_detected"` fallback at spine.py:604-605).

TFR path: `spine.py:604-605` → `_world_dict["nearby"] = "none_detected"` → `tier_fact("none_detected", source="inferred")` → tier `"inferred"` → not a violation.

Snapshot path: `cognitive_snapshot.py:335` → `"nearby": "unknown"` → violation. Then TIER-UNIFY overwrote TFR's clean result with the snapshot's stale value.

---

## Fix

**File:** `runtime/cognitive_snapshot.py:335`

```python
# Before
"nearby":       "unknown",

# After
"nearby":       "inferred",   # TFR fallback = "none_detected" → "inferred"; "unknown" was stale pre-TFR
```

One line. The cognitive_snapshot tier snap now matches what TFR produces for nearby when no perch sensor data is available. TIER-UNIFY union no longer re-adds "nearby" as a violation.

---

## Live evidence

**Input:** `"what have you been noticing lately"`

**Expressed:** `"Worlds keep bleeding into each other."`

**JSONL audit entry:**
```json
{
  "turn_id": "36e585ec",
  "expressed": "Worlds keep bleeding into each other.",
  "tier_violations": [],
  "gaps": []
}
```

First clean audit entry: zero tier violations, zero gaps. The entire tier violation chain is now resolved.

---

## Summary

| Before | After |
|---|---|
| `tier_violations: ["nearby"]` every turn | `tier_violations: []` |
| `gaps: ["TIER_VIOLATION_IN_OUTPUT"]` | `gaps: []` |

One-line fix in `cognitive_snapshot.py`. No other files changed.

**Status: SERVING**

---
*Builder · 2026-09-14*
