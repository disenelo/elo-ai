**WO:** EPISTEMIC-CASE-FIX · **Seat:** builder · **Priority:** P1
**Reserved?** no

## Goal
Research claims reach WKG. Currently blocked by case mismatch.

## Scope
`_WKG_GATE_EPISTEMIC` uses uppercase ("VERIFIED") but vault classes are lowercase ("verified").
Fix: normalise to lowercase on comparison — `if epistemic_class.lower() in {c.lower() for c in _WKG_GATE_EPISTEMIC}:`

## Files
Wherever `_WKG_GATE_EPISTEMIC` is checked (search `runtime/` for the constant).

## Test
Existing WKG tests pass. Add: claim with `epistemic_class="verified"` (lowercase) passes the gate.

## Done when
implemented + test green + committed.

## Result
- commit:
- test:
- notes:
