# WO-064 Blender Presence (BP-1–5) — Result Card

**Builder:** Builder 1
**Date:** 2026-10-04
**Status:** COMPLETE — 23/23 ATs pass across 4 test files; already implemented in prior session

---

## What was verified

`server.py` + `blender/blender_state.json` + `self/elo_self_model.py`:

**BP-1 (conversing_field):** `conversing` boolean written to `blender_state.json` each turn with 30s threshold logic.

**BP-2 (move_words):** Spoken move phrases emit correct `move_command{type, _ts}` to `blender_state.json` ("drop down" → `drop`, etc.).

**BP-4 (expression_micro):** Non-neutral emotion at intensity >= 0.4 → `expression.micro + micro_ts` emitted; neutral/low intensity suppressed to prevent spam. `_MICRO_MAP` covers 7 Designer-accepted micro emotions.

**BP-5 (sit_ended):** `sit_ended` in `unity_events.json` → self-model pose flips to "standing"; _ts-guard drops stale events (>120s); consumed events cleared.

## ATs

**test_wo064_conversing_field.py — 4/4:**
- AT-1 ✅ conversing field written to blender_state.json on active turn
- AT-2 ✅ conversing=False after 30s threshold passes (no user activity)
- AT-3 ✅ BP-1 marker + conversing logic confirmed in server.py
- AT-4 ✅ patch({conversing: True}) → field present in blender_state.json

**test_wo064_expression_micro.py — 8/8:**
- AT-1 ✅ joy + intensity 0.7 → expression.micro == "joy" + micro_ts
- AT-2 ✅ curiosity + intensity 0.5 → expression.micro == "curious"
- AT-3 ✅ distress + intensity 0.6 → expression.micro == "worried"
- AT-4 ✅ neutral + intensity 0.3 → expression.micro NOT emitted
- AT-5 ✅ joy + intensity 0.2 (below threshold) → NOT emitted
- AT-6 ✅ _MICRO_MAP covers all 7 Designer-accepted micro emotions
- AT-7 ✅ BP-4 marker + _MICRO_MAP confirmed in server.py
- AT-8 ✅ py_compile clean

**test_wo064_move_words.py — 5/5:**
- AT-1 ✅ "come down" → move_command.type=down
- AT-2 ✅ "float up" → move_command.type=float
- AT-3 ✅ "go left" → move_command.type=left
- AT-4 ✅ "drop down" → move_command.type=drop
- AT-5 ✅ non-move intent → move_command NOT emitted

**test_wo064_sit_ended.py — 6/6:**
- AT-1 ✅ sit_ended → _elo_self.pose flips to "standing"
- AT-2 ✅ _ts-guard: stale sit_ended (>120s) NOT consumed
- AT-3 ✅ after consume, unity_events.json is cleared
- AT-4 ✅ non-sit_ended event → pose NOT changed
- AT-5 ✅ BP-5 marker confirmed in server.py
- AT-6 ✅ py_compile clean

**Run:**
- `python3 tests/test_wo064_conversing_field.py` → **4/4 passed**
- `python3 tests/test_wo064_expression_micro.py` → **8/8 passed**
- `python3 tests/test_wo064_move_words.py` → **5/5 passed**
- `python3 tests/test_wo064_sit_ended.py` → **6/6 passed**
