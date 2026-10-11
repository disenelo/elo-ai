# Board Review — 0093: Executive Weather/Clipboard Fix
**Date:** 2026-10-11
**Builder:** Builder 1
**Status:** READY FOR BOARD REVIEW

---

## Card scope

"What's the weather?" routes to screen-reading instead of the weather tool.
Executive never proposes weather or clipboard as a capability because single-verb
matches (score=1) were dropped by the 2+ word min_score gate before the router
boost could rescue them.

---

## Root cause (per card §3)

In `runtime/spine/spine.py`, the `agent_route` boost that promotes router-confirmed
capabilities ran AFTER the min_score gate:

```
"what is the weather" (4 words → min_score=2)
    → weather scores 1 → DROPPED by gate
    → agent_route boost never applied
```

---

## Fix status at review time

Already implemented. `runtime/spine/spine.py:141-165` (WO-EXECUTIVE-WEATHER-CLIPBOARD):

```python
# Pre-compute router-confirmed IDs BEFORE the score gate so capabilities like
# "weather" and "clipboard" (single-verb matches) are not silently excluded.
_pre_routed_ids: set = set()
try:
    from runtime.router.agent_router import route as _pre_agent_route
    _pre_routed = _pre_agent_route(intent, meaning, chain=None)
    _pre_routed_ids = {a[0] for a in _pre_routed}
except Exception as _pra_err:
    _log.warning("WO-105: capability_faculty/pre_route failed: %s", _pra_err)
...
# Router-confirmed caps bypass the minimum score gate.
if score >= _min_cap_score or cap.id in _pre_routed_ids:
    candidates.append(...)
```

---

## Tests

```
python3 -m pytest tests/ -k "weather or clipboard" -v
→ 51 passed in 1.18s
```

Includes `test_at2_tell_me_weather_routes_answer` (test_wo_seam_a_executive_repair.py) —
confirms "tell me the weather" routes to `answer`, not screen-reading.

---

## Board decisions required

None. Implementation correct, 51/51 tests green.

*Builder 1 · 2026-10-11*
