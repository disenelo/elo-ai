# WO-064 — Builder pickups: conversing field + move words (P1/P2)

**Full WO:** `engineering/work_orders/WO-064_Builder_Pickups_From_Designer.md`
**Priority:** BP-1 = P1 · BP-2 = P2 · **Status:** OPEN (spec'd 2026-08-07, never dispatched)
**From:** Board — gap found 2026-08-29

---

## BP-1 — Publish `conversing` to `blender_state.json` (P1 — HIGH)

Write boolean `conversing` top-level field every turn: `true` while `_idle_sec < 30`, else `false`. Do NOT write raw `last_user_ts` (clock mismatch risk). Brain already tracks `last_user_ts` (server.py:1405) and `_idle_sec` (:684).

**Test:** `tests/test_wo064_conversing_field.py` — after simulated user turn: `conversing == true`; after >30s idle: `conversing == false`. Field present every write.

This unblocks Design's sit-linger gate (WO-065 / heartbeat item).

---

## BP-2 — Spoken intent words for free-form moves (P2)

Map spoken phrases → `move_command{type,_ts}` in `blender_state.json`:
- "fire jump" → `fire_jump`
- "climb that" / "wall jump" → `wall_jump`
- "back up and run at it" → `step_back_run_fire`
- "drop down" → `drop`

Reuse the autonomous resolver — one brain, no divergence. Non-move phrase must NOT emit.

**Test:** `tests/test_wo064_move_words.py` — each phrase → correct `move_command.type`; non-move phrase → no emit.

---

## BP-3 — SKIP (WO-045 — now DONE 2026-08-29)

---

**Return:** `DONE/FROM_BUILDER_WO-064_conversing_move_words_result.md` · ATs (both tests) · commits

*Board / Lead Architect · 2026-08-29*
