# WO-B1-0117 — Calculations (Percentages + Unit Conversions)
**Seat:** Builder 1  
**Priority:** P1  
**Date:** 2026-10-11  
**Commit:** 1ec8473

---

## What was built

Extended `runtime/capability_dispatcher.py` so eLo handles arithmetic, percentages, and unit conversions entirely in the FACT tier — no LLM call, no hallucinated numbers.

### Percentage-of (new `math_pct` key)

Bare expressions like "15% of 340" were previously failing: `_extract_math_expr` was plucking just "340" from the string and calculating that. Fix: a dedicated `math_pct` FACT pattern detects `\d+% of \d` and routes the **full request** straight to `system_primitives.math.calculate()`, which already has `_clean_expr` expanding `15% of 340` → `(15/100)*340` → `bc` → 51.

### Unit conversions (new `convert` key)

Added `_convert_units()` inline helper — no system_primitives, no shell, just Python math. Supports:
- Distance: km ↔ miles, cm ↔ inches, ft ↔ cm
- Weight: kg ↔ lbs
- Temperature: °C ↔ °F (special formula, not a factor)
- Volume: litres ↔ gallons (US)
- Speed: mph ↔ kph

Pattern ordering: `convert` inserted **before** the arithmetic digit+operator pattern so "100 km to miles" doesn't get captured as arithmetic first. Same fix for alternation order inside `_CONV_RE` — `celsius`/`fahrenheit` full words before the single-char `°?[CF]` fallback, which was otherwise matching "f" from "fahrenheit".

Both keys wired into `dispatch_fact()` (system_primitives path) and `_dispatch_fact_builtin()` (stdlib fallback).

### Smoke-tested (all 11 pass)

| Input | Expected | Got |
|---|---|---|
| `15% of 340` | 51 | ✓ 51 |
| `15 percent of 340` | 51 | ✓ 51 |
| `100 km to miles` | 62.1371 miles | ✓ |
| `convert 5 kg to lbs` | 11.0231 lbs | ✓ |
| `72°F to celsius` | 22.2222°C | ✓ |
| `30 celsius to fahrenheit` | 86°F | ✓ |
| `10 miles to km` | 16.0934 km | ✓ |
| `100 cm to inches` | 39.3701 in | ✓ |
| `5+3` | 8 | ✓ |
| `28 * 74` | 2072 | ✓ |
| `what is 6 times 7` | 42 | ✓ |

### Not tested (needs live turn)

Board verify: say "15% of 340" to eLo in a live session — response should arrive in < 8s with no LLM call.

*Builder 1 · 2026-10-11*
