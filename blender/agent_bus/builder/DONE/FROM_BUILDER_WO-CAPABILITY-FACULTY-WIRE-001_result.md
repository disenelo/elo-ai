# FROM_BUILDER — WO-CAPABILITY-FACULTY-WIRE-001
**Status:** DONE  
**Date:** 2026-09-09  
**Builder:** Claude (session b15c1e7a)

---

## What was built

Capability faculty audit log added to `server.py`. Main turn loop already uses `_tool_enrich_from_plan()` which defers to spine faculty output — the wire was structurally present. Audit log closes AT-2.

### Existing wire (already in place, confirmed)

Line 4349: `_enriched, _agent = _tool_enrich_from_plan(raw, _plan_caps)`

Where `_plan_caps = list(_plan.capabilities) if _plan and _plan.capabilities else []`

`enrich_from_plan()` behavior:
- If plan has selected capabilities → dispatches them (no regex re-run)
- If plan has no capabilities → returns `(raw, None)` — no fallback to legacy keyword regex

### New: AT-2 capability audit log

```python
if _plan_caps:
    _logging.info("[capability-faculty] Executive selected capabilities: %s", [...])
else:
    _logging.debug("[capability-faculty] no capability selected this turn — no data agent will run")
```

### AT verification

1. ✅ Spotify-type request with high capability score → faculty path (not regex) — `enrich_from_plan` receives plan_caps from spine
2. ✅ Capability selection appears in turn log — INFO line added when capabilities selected
3. ✅ No capability match → no legacy regex fallback — `enrich_from_plan` returns `(raw, None)` when plan_caps empty

---

## Test result

```
1569 passed, pre-existing failures unchanged
```
