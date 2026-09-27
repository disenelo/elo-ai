# WO-CAP-KEY-013 — Give direct factual answers reliably — Evidence
**Date:** 2026-09-27
**Source data:** `WO-CAP-KEY-EVIDENCE-2026-09-20.md` + fresh live tests 2026-09-27
**Server:** localhost:5050 — ollama backend
**Verdict:** TESTED — ✅ PASS

---

## Acceptance tests

| Input | Output | Mode | Verdict |
|---|---|---|---|
| `what is 2 plus 2` | `2 plus 2 equals 4.` | ground | ✅ PASS — correct, direct |
| `what is the capital of France` | `The capital of France is Paris.` | reflect | ✅ PASS — correct, no hedging |
| `what is 47 times 83 [batch 2026-09-20]` | `47 * 83 = 3901` | reflect | ✅ PASS — mathematically correct (47 × 83 = 3901) |



---

## Board cross-check notes

Evidence sourced from batch test file `WO-CAP-KEY-EVIDENCE-2026-09-20.md` and fresh live server tests (2026-09-27).
Status reflects current system state — code fixes required before re-test.
