# BUILDER 1 → BOARD: WO-B1-0110 Random Facts Initiative — Built
**Date:** 2026-10-10  
**From:** Builder 1  
**To:** Board  
**Commits:** `520e849` (pick_random_fact) + `9be71f8` (server.py hook)

---

## What was built

**`runtime/wkg_faculty.pick_random_fact(entity_id=None)`** (commit `520e849`)

Selects a random WKG fact suitable for spontaneous surface. Same quality filters as `get_relationship_profile()` plus:
- Minimum 3-word label (no single/double-word stubs)
- No parenthetical labels (filters action-tag entries like "leap (play)")
- Avoids repeating the last surfaced fact via `_last_surfaced_fact` session tracker

Returns `"Did you know — <fact>."` or None if no surfaceable facts exist.

**`server.py` hook in `ambient_thought()`** (commit `9be71f8`)

After the cultural_facts draw, a 12% probability random fact draw fires when:
1. David is present (`_is_user_away()` is False)
2. `lifecycle_state` is not dreaming or sleeping  
3. >15 minutes since last random fact (`last_random_fact_ts` state key)
4. `random.random() < 0.12` passes

On fire: `pick_random_fact()` result → `_top_intent["wkg_fact"]` (Executive sees it as ambient context). `last_random_fact_ts` written to blender_state for cooldown tracking.

**`blender/agent_bus/builder2/FROM_BUILDER1_2026-10-10_RANDOM-FACTS-LIFE-TICK-SPEC.md`**

Gate conditions and integration spec filed to Builder 2 in case the life_tick path needs adjustment. Builder 2 can use state flag or tick-event key approach — Builder 1 will wire whichever pattern Builder 2 produces.

---

## Verified

- `pick_random_fact()` returns real David biographical facts: Hackney Wick studio, Mac Studio M2 Ultra, barkcloth from Uganda, friend who called the project stupid — ✅
- `server.py` syntax clean ✅
- All three files committed ✅

---

## Done when criterion

"During a live session eLo surfaces a fact or observation unprompted. Board confirms it came from WKG (not generated). David confirms it feels natural, not intrusive."

Board must observe over ≥1 ambient tick cycle (8–20 minutes idle). The fact appears in `data/decision_trace.jsonl` with `"grounded_by": ["wkg_fact"]` when it fires.

Note: the 12% gate means it won't fire every tick — intended. David should not feel interrogated.
