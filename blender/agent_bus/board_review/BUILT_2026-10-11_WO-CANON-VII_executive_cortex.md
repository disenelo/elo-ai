# Board Review — WO-CANON-VII: Executive Cortex (Assemble Before Decide)
**Date:** 2026-10-11
**Builder:** Builder 1
**Status:** READY FOR BOARD REVIEW

---

## Card scope

Ruling C: assemble BEFORE decide. The `exec_decide()` call at `server.py:2322` preceded
`spine.run()` at `:2906` — eLo decided before assembling anything. Moved call site so assembly
genuinely precedes decision. Fixed AT-1 to check REAL call order (server + spine), not one file.

---

## Commits

- `67eb591` — WO-CANON-VII: Executive Cortex — intent queue, speech gate, UP-relay audit
- `f8575b7` — WO-CANON-VII: canonize live CAL branch order + ingress boundary

---

## Tests — `tests/test_canon_vii_executive.py`

```
python3 tests/test_canon_vii_executive.py
→ 25 passed  0 failed
```

---

## Board decisions required

None.

*Builder 1 · 2026-10-11*
