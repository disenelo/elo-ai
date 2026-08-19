# 0002_WO-118 — ⚡ **ROUTE (row 14): Designer shipped the report. Nothing reads it. Close it — it's small.**

**Seat:** builder · **Priority:** P1, do it with the one-liners · **Gate?** none
**Rows:** 14 ROUTE → VERIFIED · **unblocks 17 GAP's `reliable_range`**

## What landed (Designer, ~19:30) — verified in the live file
`blender/elo_spatial.json` now carries:
```json
"goal": 54676,
"route": [24],
"last_move": {"goal":54676,"route":[24],"legs":["drop"],"arrived":true,"fell":false,
              "outcome":"arrived","issued_by":"reflex","cost_secs":0.4,"cost_dist":0.363,
              "retries":0,"_ts":1786644853.851}
```
**Ruling E is satisfied on the body side.** The body now reports goal · route · legs · arrived · fell ·
cost · retries · `issued_by`.

## 🔴 The gap
[VERIFIED] **Nothing in Python reads `last_move`.** Grep for `last_move` / `cost_secs` over non-test `.py`:
**zero hits.** `issued_by` is read for **gaze only** (`spatial_state.py:129`, `live_world_state.py:325`).

And `self/route_memory.py` **already exists with exactly the right shape** — `"arrived"` at `:60`, success
counting at `:98`, a rolling success-rate window at `:138` — and has **zero importers.**
Built, never wired. Same fault, seventh time today.

## Build — small, mostly wiring
1. **Read `last_move`** in `desktop/spatial_state.py` (beside the existing gaze read at `:129`) and in
   `world/live_world_state.py` (beside `:325`). Add the fields to the dataclasses.
2. **Feed `self/route_memory.py`** with each completed move — it already computes success rates; it just
   needs an input and a caller.
3. **Surface it to the Executive** via the assembled state (pairs with `WO-106`) so route history is
   consultable, not just logged.
4. **Rule 1 alarm:** if `last_move` is absent for N moves while the body is moving, log WARNING. A body
   that stops reporting must not look like a body that stopped moving.

## Why this one matters beyond row 14
`reliable_range` for **GAP (row 17)** can only ever be *learned* from reported outcomes. `WO-113` is
building the gap-state machine against **declared** limits tonight — this card is what lets it switch to
**learned**. And `arrived: false` / `fell: true` rows are the negative evidence the learning loop has never
had.

## Test (without David)
- A completed move appears in `route_memory` with its outcome.
- A **failed** move (`arrived: false`) is recorded as failure — assert the negative case, not just success.
- Success rate for a repeated route changes after repeated attempts.
- `last_move` absent while moving ⇒ WARNING fires.

## Done when
Committed. **Outbox: a real `route_memory` entry, and the success rate after 3 attempts on one route.**

---

## RESULT — 2026-08-19 (builder)

**STATUS: DONE.** Implementation already committed as **`3112e40`** on 2026-08-15
(`WO-118 (card 0002): wire last_move → route_memory, surface to Executive, Rule 1 alarm`).
Card was left in `DOING/` after that commit and closed on this pass — no new code.

### Wiring in place (verified against disk, 2026-08-19)
| Requirement | Where | Evidence |
|---|---|---|
| Read `last_move` from `elo_spatial.json` | `desktop/spatial_state.py:128-163` | `_lm = d.get("last_move")` block |
| Feed each completed move into `route_memory` | `desktop/spatial_state.py:137-149` | `remember_route(..., ack_received=True)` |
| Dedup on `_ts` (no double-count on same read) | `desktop/spatial_state.py:39-40,134-135` | `_seen_move_ts` set |
| Surface to Executive via world state | `world/live_world_state.py:397-406` | `recent_routes(5) → LiveWorldState.route_history` + `domain_health["route"]` |
| Rule 1 alarm — last_move absent while moving | `desktop/spatial_state.py:41-42,152-163` | WARNING at N≥3 consecutive reads |

### Acceptance — all four pass
- **AT-1** completed move recorded — `test_last_move_feeds_route_memory` PASSED.
- **AT-2** failed move recorded as failure — verified live: `arrived=False, fell=True` row present in `recent_routes()`.
- **AT-3** success rate changes with repeat attempts — 3 attempts (T/F/T) on `top_of_chrome` → `route_confidence = 0.667`.
- **AT-4** Rule 1 alarm fires — WARNING: `WO-118 Rule 1: body navigating (goal=54676) but last_move absent for 3 consecutive reads — body may have gone silent.`
- Dedup: `test_last_move_deduplicates_on_ts` PASSED.

### Live artefact (from `blender/elo_spatial.json` at 2026-08-19)
```json
"last_move":{"goal":162,"route":[29,28],"legs":["hop"],"arrived":true,"fell":false,
             "outcome":"arrived","issued_by":"reflex","cost_secs":0.23,"cost_dist":0.196,
             "gap_distance_sizes":0,"max_hop_sizes":6,"retries":0,"_ts":1787113776.702}
```
Body is emitting the Ruling-E fields; the read path is now built and consumed.

**Commit:** `3112e40`
**Pairs with:** WO-106 (surfaces `route_history` to Executive via `LiveWorldState`).
**Unblocks:** row 17 GAP `reliable_range` can now switch from *declared* to *learned* (WO-113).
