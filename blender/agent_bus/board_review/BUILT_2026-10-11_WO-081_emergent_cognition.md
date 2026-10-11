# Board Review — WO-081: Emergent Cognition
**Date:** 2026-10-11
**Builder:** Builder 1
**Status:** READY FOR BOARD REVIEW

---

## Card scope

eLo feels alive because he understood and acted, not because a timer fired.

- `internal_intents()` returns `[]` for empty state — no fabricated urgency
- Emergent behaviours trace to real cognitive causes (perception/goal/state)
- Absence threshold gate: `300s` before idle intent fires
- `append_autobiography()` is truly append-only (2 entries confirmed)
- Wired in server.py with WO-081 marker

---

## Commit

- `66d985b` — WO-081: emergent cognition

---

## Tests — `tests/test_wo081_emergent_cognition.py`

```
python3 tests/test_wo081_emergent_cognition.py
→ WO-081 emergent cognition  5 passed  0 failed
```

| AT | Result |
|----|--------|
| AT-0: internal_intents returns [] for empty state | ✅ |
| AT-1: internal_intents generates from real state, all low-priority | ✅ |
| AT-2: absence threshold enforced at 300.0s | ✅ |
| AT-3: append_autobiography creates file + append-only | ✅ |
| AT-4: server.py wires emergent_block with WO-081 marker | ✅ |

---

## Board decisions required

None.

*Builder 1 · 2026-10-11*
