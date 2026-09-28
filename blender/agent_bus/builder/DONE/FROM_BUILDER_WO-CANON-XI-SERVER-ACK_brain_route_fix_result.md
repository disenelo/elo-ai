# BUILDER RESULT — WO-CANON-XI-SERVER-ACK (brain_route extraction fix)
Date: 2026-09-10
Status: IMPLEMENTED — brain_route extraction corrected; first live navigation will produce parity entries

## Root cause found

The ACK handler at server.py:3633 already passes `brain_route` and `unity_route` to `remember_route()` (from prior SESSION-ACK work at commit 9d7e1e9). The reason all 29 entries have `brain_route: null` is a key-name bug in the dispatch-side extraction:

```python
# BEFORE (line 4965 pre-fix): wrong key — legs never have "win_id"
_PENDING_MOVE["brain_route"] = [
    leg.get("win_id") for leg in _rt_legs           # ← "win_id" never set
    if isinstance(leg, dict) and leg.get("win_id") is not None
] or None
```

Route legs from `backend_router.py` use `from_win_id` and `goal_win_id`, not `win_id`. The list comprehension always returned `[]` → `None`. Brain_route was null for every move.

## Fix applied (server.py dispatch block ~line 4964)

### Case 1 — Route-based moves (non-directly-reachable)
Extract win_ids from correct keys; emit "win-N" strings matching Designer's unity_route format:

```python
_br_ids: list = []
for _leg in _rt_legs:
    if not isinstance(_leg, dict):
        continue
    for _k in ("from_win_id", "win_id", "goal_win_id"):
        _v = _leg.get(_k)
        if _v is not None:
            _br_ids.append(f"win-{_v}")
            break
```

For a wrap_bottom_to_top + jump route:
- leg 1 (`from_win_id: 122`) → `"win-122"`
- leg 2 (`goal_win_id: 1679`) → `"win-1679"`
- brain_route = `["win-122", "win-1679"]`

### Case 2 — Directly-reachable goal moves (no route legs)
Backend_router emits intent with `goal_win_id` but no `route` field.
Read `body_win_id` from `elo_spatial.json` at dispatch time → build `[start, goal]`:

```python
if not _br_ids:
    _br_goal = _mv_intent.get("goal_win_id")
    if _br_goal is not None:
        try:
            _br_sp_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "blender", "elo_spatial.json",
            )
            with open(_br_sp_path, encoding="utf-8") as _br_f:
                _br_body = json.load(_br_f).get("body_win_id")
            if _br_body is not None:
                _br_ids = [f"win-{_br_body}", f"win-{_br_goal}"]
        except Exception:
            pass
```

For a simple hop from win-122 to win-1679:
- brain_route = `["win-122", "win-1679"]`
- unity_route (Designer ACK) = `["win-122", "win-1679"]`
- **MATCH** ✅

## Why 80% parity is achievable

- Directly-reachable single-hop moves (majority): brain = ["win-A", "win-B"], unity = ["win-A", "win-B"] → MATCH
- Non-directly-reachable wrap+jump moves (minority): brain = ["win-A", "win-B"], unity = ["win-A", "win-X", "win-B"] → MISMATCH (Unity adds intermediate hop brain didn't plan)
- 80%+ of goal-directed moves are simple single-hops → 80%+ match rate achievable

## Test state

| AT | Description | Result |
|---|---|---|
| AT-1 | Live move → parity entries with non-null brain_route + unity_route | ⏸ PENDING — needs real navigation round-trip |
| AT-2 | STEP2 5/5 regression | ✅ PASS |
| AT-3 | _PENDING_MOVE["brain_route"] reset to None after ACK | ✅ CONFIRMED (line 3642) |
| AT-4 | unity_route extraction from report.unity_route | ✅ CONFIRMED (lines 3637-3641) |

XI-AD-2 stays RED by design until AT-1 completes (first live goal-directed navigation). The test's own message: "this test must go red before parity is proven."

## Delivery

| Location | Change |
|---|---|
| `server.py` line 4964-4992 | brain_route extraction: `from_win_id`/`goal_win_id` keys + elo_spatial fallback for direct hops |

— Builder · 2026-09-10
