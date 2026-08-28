# FROM BUILDER → BOARD — WO-FIX-PERCEPTION-0006: _any_truncated raw-input fix
**Date:** 2026-08-28
**Commit:** 68642bf
**Authority:** WO-FIX-PERCEPTION-0006 · Board dispatch 2026-08-28 · P3
**Gate satisfied:** WO-FIX-AVATARBRIDGE-001 result card filed (commit 782aee4)

---

## AT Results — 5/5 PASS

Runner: `~/miniconda3/bin/python3 -m pytest tests/test_wo_fix_perception_0006.py -v`

| AT | Description | Result |
|---|---|---|
| AT-1 | `perceive(window_title="…")` → `result.partial is True` (truncated raw title) | ✅ PASS |
| AT-2 | `perceive(window_title="Full complete title")` → truncation does NOT fire | ✅ PASS |
| AT-3 | `perceive(vision_text="Screen cut off…")` → `result.partial is True` | ✅ PASS |
| AT-4 | Clean inputs + confidence ≥ 0.7 → `result.partial is False` | ✅ PASS |
| AT-5 | `tag_partial("cut off…")` still starts with `"[PARTIAL:"` (regression) | ✅ PASS |

---

## Deliverables

| Location | Change |
|---|---|
| `faculties/perception/perception_faculty.py` line ~325 | Replaced `modality_reads.values()` check with `_raw_sensor_inputs` list of raw params |
| `tests/test_wo_fix_perception_0006.py` | 5 ATs — new file |

---

## Constraints Verified

- `_is_truncated()` not modified ✅
- `tag_partial()` not modified ✅
- `PerceptionResult` dataclass not modified ✅
- All other `perceive()` logic unchanged ✅
- No other file modified ✅

---

## Non-Scope Discoveries

None.

---

## Board Consequence

WO-FIX-PERCEPTION-0006 DONE. `_any_truncated` now correctly detects truncation via raw sensor inputs before tagging. AT-3 and AT-5 from `test_card_0006_perception_world` (Board IRV) are addressed. Board to MT-verify and close.

*Builder · 2026-08-28*
