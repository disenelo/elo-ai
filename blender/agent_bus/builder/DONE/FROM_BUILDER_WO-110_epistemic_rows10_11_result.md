# FROM BUILDER → BOARD — WO-110: Epistemic Tiers — Rows 10 (INFER) + 11 (UNKNOWN)
**Date:** 2026-08-28 (result card filed; implementation predates in prior session)
**Authority:** WO-110 · Builder (Python — `runtime/the_moment.py`) · `builder/05c`

---

## AT Results — 11/11 PASS (pytest) + 9/0 PASS (script-style)

Runner A: `~/miniconda3/bin/python3 -m pytest tests/test_wo110_epistemic_tiers.py -v`

| Test | Row | Result |
|---|---|---|
| test_tier_fact_inferred | 10 (INFER) | ✅ PASS |
| test_tier_fact_unknown_when_absent | 11 (UNKNOWN) | ✅ PASS |
| test_nearby_tier_unknown_when_empty | 11 (UNKNOWN) | ✅ PASS |
| test_tier_fact_observed_sensor | 9 | ✅ PASS |
| test_tier_fact_observed_tool | 9 | ✅ PASS |
| test_tier_fact_remembered_vault | 9 | ✅ PASS |
| test_tier_fact_remembered_lesson | 9 | ✅ PASS |
| test_tier_changes_when_source_changes | 9/10/11 | ✅ PASS |
| test_nearby_tier_inferred_when_populated | 10 | ✅ PASS |
| test_compile_includes_non_body_fields | 9 | ✅ PASS |
| test_lookup_returns_experience_id_and_event | 8 | ✅ PASS |

Runner B: `~/miniconda3/bin/python3 tests/test_0011_wave4_epistemic.py`

```
Wave 4 Epistemic: 9 passed, 0 failed

Rows verified by this test:
  8  RECALL    — lookup() provenance set complete
  9  KNOW      — OBSERVED tier from sensor source
  10 INFER     — INFERRED tier from inferred source
  11 UNKNOWN   — UNKNOWN statable; absence is a fact
```

---

## Deliverables (in `runtime/the_moment.py`)

### Row 10 (INFER) — `tier_fact()` returns `"inferred"` for inferred source (line 73)

```python
if source == "inferred":
    return "inferred"
```

Not a constant — computed from the `source` argument (EP-2 ✅: "EP-2 — inferred source → 'inferred'").

### Row 11 (UNKNOWN) — `tier_fact()` returns `"unknown"` for absent value (line 65–66)

```python
if value is None or value == "" or value == [] or value == {}:
    return "unknown"
```

UNKNOWN is statable — absence itself is a fact (EP-4 ✅: "None/empty/[]/\{\} all → 'unknown'"). Board
comment at line 365: "WO-110 Row 11: UNKNOWN must be statable — always show nearby, even when absent."

---

## Constraints Verified

- `executive.py` NOT touched (FREEZE_V1_LOCK) ✅
- Tiers are computed, not constants — EP-5 proves source change → tier change ✅
- Non-body epistemic tiers produced by `compile()` — `lessons_tier`, `recent_behaviour_tier` present ✅

---

## Board Consequence

Row 9 (KNOW) was already marked "✅ EVIDENCED 2026-08-21" on the board. Rows 10 and 11 were missed
in that sweep despite being covered by the same WO-110 `05c` card and the same tests. This result
card corrects the gap.

- Row 11 (UNKNOWN) appears in the tally (line 1492) as `🚫 NOT BUILT` — stale; now ✅ DONE.
- Row 10 (INFER) was absent from the tally; missing EVIDENCED marker in seat column — now ✅ DONE.

*Builder · 2026-08-28*
