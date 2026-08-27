# WO-CANON-XX — Cognitive Economy: tier selector + value-gated escalation

**Status:** DONE (Builder close)
**Closed:** 2026-08-27
**Seat:** SEAT-ENG-001 (Builder)

---

## Finding

With Presentable v1 retired as gate (board 2026-08-10) and CANON Tier A complete,
WO-CANON-XX had no remaining blockers. Running the test suite confirmed the implementation
was already fully in place:

- `runtime/backend_router.py` tier→provider mapping (M-1/M-2/M-3/M-4)
- Value-gated escalation: cheapest-capable default; `escalated` flag on promoted turns
- Mock-honesty gate (Ch.3): mock never fabricates factual answers; downgrades expressed as reduced capability
- `backend_name` truthful to the Executive; priority order (safety > user interaction > …) enforced
- `_token_budget()` tier-aware; provider cost class explicit (free-local / cheap-cloud / premium-cloud)

## Evidence

```
~/miniconda3/bin/python3 tests/test_canon_xx_economy.py

WO-CANON-XX cognitive economy   16 passed   0 failed

pytest suite:
57 passed, 1 xfailed
```

**WO-CANON-XX is DONE.**
