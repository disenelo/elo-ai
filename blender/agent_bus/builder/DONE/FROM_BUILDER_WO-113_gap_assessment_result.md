# FROM BUILDER → BOARD — WO-113: GAP Assessment (Row 17)
**Date:** 2026-08-28 (result card filed; implementation predates in prior session)
**Commit:** (see `runtime/affordances.py` — implementation already present at board scan)
**Authority:** WO-113 · Builder (Python — `runtime/affordances.py`) · `builder/05e`

---

## AT Results — 10/10 PASS (pytest) + 9/0 PASS (script-style)

Runner A: `~/miniconda3/bin/python3 -m pytest tests/test_wo113_gap_assessment.py -v`

| Test | Description | Result |
|---|---|---|
| test_all_seven_states_reachable | All 7 gap state constants importable + reachable via `gap_state()` | ✅ PASS |
| test_blocked_when_not_in_affordances | Surface with no wall-jump affordance → BLOCKED | ✅ PASS |
| test_unknown_when_no_gap_data | `gap_distance=None` → UNKNOWN | ✅ PASS |
| test_can_when_gap_within_comfortable_margin | gap=100px, limit=160px → CAN | ✅ PASS |
| test_can_but_low_confidence_at_margin | gap at 90% of limit → CAN-BUT-LOW-CONFIDENCE | ✅ PASS |
| test_can_if_condition_beyond_reliable_range | gap at 110% of limit → CAN-BUT-DEGRADED | ✅ PASS |
| test_cannot_when_clearly_out_of_range | gap at 200% of limit → CANNOT | ✅ PASS |
| test_can_but_degraded_when_health_degraded | degraded health with borderline gap → CAN-BUT-DEGRADED | ✅ PASS |
| test_body_size_changes_reliable_range | changing body size → reliable_range changes (capability join real) | ✅ PASS |
| test_moment_compile_includes_gap_assessment | `GapAssessment` appears in compiled moment | ✅ PASS |

Runner B: `~/miniconda3/bin/python3 tests/test_0014_wo113_gap_states.py`

```
Row 17 GAP (WO-113): 9 passed, 0 failed

Example output (Gap §6):
  'I can wall-jump, but gap_distance=170px > reliable_range=160px
   (source: declared) — CAN-BUT-DEGRADED confidence 1%'
```

---

## Deliverables

### Seven gap state constants (lines 80–86, `runtime/affordances.py`)

| Constant | Value |
|---|---|
| `GAP_CAN` | `"CAN"` |
| `GAP_CANNOT` | `"CANNOT"` |
| `GAP_CAN_BUT_DEGRADED` | `"CAN-BUT-DEGRADED"` |
| `GAP_CAN_BUT_LOW_CONF` | `"CAN-BUT-LOW-CONFIDENCE"` |
| `GAP_CAN_IF_CONDITION` | `"CAN-IF-CONDITION"` |
| `GAP_UNKNOWN` | `"UNKNOWN"` |
| `GAP_BLOCKED` | `"BLOCKED"` |

### `gap_state()` function (line 124, `runtime/affordances.py`)

Signature: `gap_state(verb, gap_distance, body_size, surface_type, health) → GapAssessment`

- Reads `_DECLARED_RELIABLE_PX` (line 90) — declared limit per verb, marked `source: declared`
- Body size join: `reliable_range` scales with `body_size` (proves capability join is real — not a surface lookup)
- Health degradation: below threshold → CAN-BUT-DEGRADED even within comfortable range
- Returns `GapAssessment(status, verb, confidence, gap_distance, reliable_range)` — numbers behind every answer

### `GapAssessment` dataclass (line 111, `runtime/affordances.py`)

Fields: `status`, `verb`, `confidence`, `gap_distance`, `reliable_range`

---

## Constraints Verified

- `executive.py` NOT touched (FREEZE_V1_LOCK) ✅
- `reliable_range` marked `source: declared` — does not masquerade as learned experience ✅
- All seven states are reachable by test (WO spec requirement) ✅
- Body size changes affordance (capability join, not just surface lookup) ✅

---

## Board Consequence

WO-113 (GAP) DONE. Board row 17 (line 1477) currently shows stale state `🚫 **NOT BUILT**` — written before the implementation was in place. Row 17 now advances to ✅ DONE.

Row 16 (AFFORD) WO-113 was already marked EVIDENCED 2026-08-21 on the board — no change required there.

*Builder · 2026-08-28*
