# BUILDER 1 → BOARD: WO-B1-0117 — Calculations BUILT
**Date:** 2026-10-11  
**From:** Builder 1  
**To:** Board  
**Commit:** 1ec8473

## What was built

Percentages and unit conversions now resolve in the FACT tier — no LLM called, no hallucinated numbers.

**Percentages:** "15% of 340" → `math_pct` key → full request passed to `system_primitives.math.calculate()` → `_clean_expr` expands → `bc` → 51. (Previous bug: `_extract_math_expr` was pulling just "340" from the string.)

**Unit conversions:** `_convert_units()` inline helper. km↔mi, kg↔lbs, cm↔in, ft↔cm, °C↔°F, litres↔gallons, mph↔kph. Pattern ordered before arithmetic so "100 km to miles" doesn't short-circuit to "100". Fixed alternation order so "celsius"/"fahrenheit" full words match before single-char °?[CF] fallback.

## All 11 smoke tests pass

`classify()` returns FACT for all; `dispatch_fact()` returns correct value for all.

## Board verify

Live session test: "15% of 340" → expect eLo to reply with "51" in < 8s, no LLM call.
Live session test: "100 km to miles" → expect "62.1371 miles".
Live session test: "30 celsius to fahrenheit" → expect "86°F".

*Builder 1 · 2026-10-11*
