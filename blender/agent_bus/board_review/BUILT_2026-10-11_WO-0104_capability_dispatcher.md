# Board Review — WO-0104: Capability Dispatcher
**Date:** 2026-10-11
**Builder:** Builder 1
**Status:** READY FOR BOARD REVIEW

---

## Card scope

Wire `tools/system_primitives.py` into the kernel as a truth boundary:
- `runtime/capability_dispatcher.py` (NEW) — `classify()` + `dispatch_fact()`
- FACT tier: time, date, math, battery, disk, uptime — answered deterministically, no LLM
- STATE tier: eLo's working memory / blender_state
- COGNITION tier: pre-classified problem packet for faculty
- Every result carries `source/authority/confidence/freshness` metadata
- Wired into server.py before Executive fires

---

## Implementation status

Already fully implemented. `runtime/capability_dispatcher.py` and `tools/system_primitives.py`
both exist; spoken-sum routing through system_primitives confirmed working.

Commits: `7b9f955`, `eb3ad11`, `ee28841`, `a11f968`

---

## Tests — `tests/test_capability_dispatcher.py`

```
python3 -m pytest tests/test_capability_dispatcher.py -v
→ 34 passed in 0.20s
```

Covers: classify (time/battery/math/state/cognition/unknown), dispatch_fact
(time/date/tomorrow/yesterday/math ops/injection safety), fact-is-not-overridden,
spoken-sums routing, and battery no-primitives graceful degradation.

---

## Board decisions required

None. Implementation correct, 34/34 green.

*Builder 1 · 2026-10-11*
