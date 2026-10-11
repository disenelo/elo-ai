# Board Review — WO-113: AFFORD + GAP — Affordances Wired, Seven Gap States
**Date:** 2026-10-11
**Builder:** Builder 1
**Status:** READY FOR BOARD REVIEW

---

## Card scope

Affordances were computed but thrown away — `affordances.prompt_block` had zero non-test callers.
Fixed:
1. Affordance = world geometry ∩ body capability ∩ confidence (not a surface lookup)
2. Routed to the Executive (pairs with WO-106)
3. GAP as 7-state first-class answer: `CAN · CANNOT · CAN-BUT-DEGRADED · CAN-BUT-LOW-CONFIDENCE · CAN-IF-CONDITION · UNKNOWN · BLOCKED`
4. Each state carries real numbers (`gap_distance`, `reliable_range`, `source: declared`)
5. `reliable_range` sourced from navigator declared limit (`maxJumpEloHeights = 1.5f`), marked `source: declared` until Ruling E lands

---

## Tests — `tests/test_wo113_gap_assessment.py`

```
python3 -m pytest tests/test_wo113_gap_assessment.py -v
→ 10 passed  0 failed
```

| AT | Result |
|----|--------|
| test_all_seven_states_reachable | ✅ |
| test_blocked_when_not_in_affordances | ✅ |
| test_unknown_when_no_gap_data | ✅ |
| test_can_when_gap_within_comfortable_margin | ✅ |
| test_can_but_low_confidence_at_margin | ✅ |
| test_can_if_condition_beyond_reliable_range | ✅ |
| test_cannot_when_clearly_out_of_range | ✅ |
| test_can_but_degraded_when_health_degraded | ✅ |
| test_body_size_changes_reliable_range | ✅ |
| test_moment_compile_includes_gap_assessment | ✅ |

---

## Board decisions required

Ruling E (Designer — learned `reliable_range`) still open. Until it lands, range uses declared
navigator constant and is marked `source: declared`.

*Builder 1 · 2026-10-11*
