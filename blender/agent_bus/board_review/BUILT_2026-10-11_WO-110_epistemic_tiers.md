# Board Review — WO-110: KNOW/INFER/UNKNOWN — Epistemic Tiers Beyond the Body
**Date:** 2026-10-11
**Builder:** Builder 1
**Status:** READY FOR BOARD REVIEW

---

## Card scope

Three defects fixed:
1. Tiers were body-only — memory, vault facts, David facts, tool results untiered
2. Two tier branches were constants (`"verified"` / `"inferred"`) not real checks
3. Fast paths (direct/greeting turns) skipped tiering entirely

Implemented `OBSERVED · INFERRED · REMEMBERED · UNKNOWN` as a general property of any fact
eLo holds — computed from source + recency, never a constant.

---

## Tests — `tests/test_wo110_epistemic_tiers.py`

```
python3 -m pytest tests/test_wo110_epistemic_tiers.py -v
→ 11 passed  0 failed
```

| AT | Result |
|----|--------|
| test_tier_fact_observed_sensor | ✅ |
| test_tier_fact_observed_tool | ✅ |
| test_tier_fact_remembered_vault | ✅ |
| test_tier_fact_remembered_lesson | ✅ |
| test_tier_fact_unknown_when_absent | ✅ |
| test_tier_fact_inferred | ✅ |
| test_tier_changes_when_source_changes | ✅ |
| test_nearby_tier_unknown_when_empty | ✅ |
| test_nearby_tier_inferred_when_populated | ✅ |
| test_compile_includes_non_body_fields | ✅ |
| test_lookup_returns_experience_id_and_event | ✅ |

---

## Board decisions required

None.

*Builder 1 · 2026-10-11*
