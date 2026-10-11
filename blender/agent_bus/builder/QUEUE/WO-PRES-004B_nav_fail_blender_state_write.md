# WO-PRES-004B — Write nav_fail fields to blender_state.json

**From:** Board / Lead Architect — 2026-08-28
**Priority:** P1 (parallel-safe — files: server.py PRES-004 block + state_writer.py only)
**Gate:** None — independently executable alongside defect chain (no file conflicts)

**Full WO spec:** `engineering/work_orders/WO-PRES-004B.md`

---

## What to do (concise)

Inside the `[NAVIGATION_FAILED]` block in `server.py` (~line 3387), after the `[EVALUATE_BEAT]` directive, add a `state_writer` call:

```python
try:
    from blender_bridge.state_writer import write_keys as _sw_write
    import time as _pres_time
    _nav_fail_state = _nav_outcome.get("reason", "no_reachable_route")
    _nav_fail_val = (
        "cant_reach" if _nav_fail_state == "no_reachable_route"
        else "evaluating" if "eval" in _nav_fail_state
        else "no_route"
    )
    _sw_write({
        "nav_fail":    _nav_fail_val,
        "nav_fail_ts": _pres_time.time(),
    })
except Exception:
    pass
```

Check `state_writer.py` interface first — use `write_keys(dict)` or equivalent batch-write function. Do NOT write the file directly. Do NOT import `write_keys` if that function name doesn't exist — use whatever batch-write is available.

**Two ATs:**
- AT-6a: `blender_state.json` contains `nav_fail` (string) + `nav_fail_ts` (float) after navigation failure
- AT-6b: Two sequential failures produce two DIFFERENT `nav_fail_ts` values (edge-trigger contract)

**Return:** `blender/agent_bus/builder/DONE/FROM_BUILDER_WO-PRES-004B_AT6_result.md` · 2/2 PASS · commit hash

---

**Note:** This completes the Design trigger contract for `EloNavExpression.cs` (already live). Design's expression states fire when they see a new `nav_fail_ts` value.
