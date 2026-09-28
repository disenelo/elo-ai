# BUILDER RESULT — GAP-06 LEGACY RETIREMENT + WO-CANON-XI-SERVER-ACK CORRECTION
Date: 2026-09-11
Status: DONE — all legacy paths verified retired; brain_route fix moved to spine path

## Critical bug found in prior WO-CANON-XI-SERVER-ACK fix

The §73 brain_route fix placed the extraction code at server.py lines 4964-4992. These lines are inside the `else:` block at line 4887 (legacy fallback), which fires ONLY when `_plan is None` or `_plan.presence_plan` is falsy. Since the spine always succeeds and always produces a presence_plan via light_engine, this block NEVER executes.

Result: brain_route was still always None. The §73 fix was dead code.

## Fix applied: PENDING_MOVE added to spine path

**File:** `server.py` — inside the `if _plan is not None and _plan.presence_plan:` block, after `_PENDING_SIT` tracking (line ~4867).

When `_sp_intent.get("name") == "move"` (spine move intent):
1. Activates `_PENDING_MOVE["active"] = True`
2. Sets direction, sub_type, route_timeout_s from intent
3. Extracts brain_route from route legs (from_win_id/goal_win_id)
4. Falls back to elo_spatial.json for directly-reachable hops (no route legs)

This mirrors the legacy logic identically but is now in the code path that actually runs.

## GAP-06 Legacy Path Audit

| Legacy path | Retirement status |
|---|---|
| `_tool_enrich` (legacy regex tool routing) | ✅ RETIRED — imported, never called; `_tool_enrich_from_plan` governs |
| `exec_decide` (legacy intent routing) | ✅ RETIRED — line 3088, spine-failure only |
| `_movement_intent()` / `_movement_trigger()` | ✅ RETIRED — line 4887 else block, spine-failure only |
| `_state_write` / `_state_write_presence` | ✅ RETIRED — legacy fallback only |
| `_PENDING_SIT` spine tracking | ✅ PRESENT — line 4861 |
| `_PENDING_EXIT` spine tracking | ✅ PRESENT — line 4873 |
| `_PENDING_MOVE` spine tracking | 🔴 MISSING → ✅ FIXED this session |

One Brain governs all execution paths. Legacy paths are defensive fallbacks (spine-failure only). PENDING_MOVE gap was the single remaining structural hole.

## WO-CANON-XI test state

XI-AD-2 now has a real path to parity entries:
- Spine dispatches "move" intent → `_PENDING_MOVE["brain_route"]` set from spine path
- Unity ACK arrives → ACK handler reads `_PENDING_MOVE["brain_route"]` + `unity_route`
- `remember_route()` called with both → parity entry created in route_memory.jsonl

Test stays RED until first real navigation round-trip after server restart.

— Builder · 2026-09-11
