# FROM BUILDER — WO-PERSONALITY-TRACE-001 RESULT

**Status:** DONE (diagnostic) — 2026-09-08  
**Verdict: C-20 is FALSE DONE — personality does not persist between sessions**

## Where personality_evolution_faculty runs

**Import chain:**
1. `runtime/spine/spine.py:941` — `load_personality()` called every turn (READ path only)
2. `runtime/reflection_faculty.py:355-368` — `load_personality()` + `save_personality()` called during reflection
3. `reflection_faculty.integrate_session()` called from `memory/consolidation_faculty.py:238`
4. `consolidation_faculty.consolidate()` called from `server.py:5557` (post-turn, when significant turn detected)

## Does personality reach the expressed output?

**YES — per turn.** `spine.py:948` calls `_pv_traits(_pv)` → `plan.personality_traits` = `{curiosity: 0.62, patience: 0.65, …}`. This is confirmed by the WO-FACULTY-CHAIN-VERIFY-001 run. With WO-EXEC-DECISION-FIELDS-001, these traits now reach `exec_decision` and `prompt_builder`.

## Does it persist?

**NO.** `self/personality_vector.json` — **DOES NOT EXIST.**

- `load_personality()` falls back to `PersonalityVector()` (defaults) on FileNotFoundError
- `save_personality()` writes to `self/personality_vector.json` — but this only happens when `reflection_faculty.integrate_session()` runs a personality delta from a significant turn
- `integrate_session()` only runs when `consolidation_faculty.consolidate()` is called — which requires `significant_turns` to be non-empty
- In practice: no personality delta is ever applied because `_AUTHORISED_SENDER = "ReflectionGrowthEngine"` and the consolidation path requires a validated delta from that sender

**Result: eLo always boots with the same default trait vector. Personality cannot grow.**

## Default trait vector (always loaded)

From `PersonalityVector.__post_init__()` (inferred from `get_trait_values()` output):
```
curiosity: 0.62, patience: 0.65, confidence: 0.6, empathy: 0.72
discipline: 0.58, wonder: 0.65, directness: 0.7, adaptability: 0.6
```

## Traits that would change if persistence worked

The reflection path calls `_integrate_personality_delta()` which applies validated trait deltas up to `MAX_STEP = 0.02` per integration period. The Identity Kernel floors (wonder ≥ 0.10, empathy ≥ 0.20, directness ≥ 0.50) are enforced.

## Fix needed

**WO-PERSONALITY-PERSIST-001 (new):** Create `self/personality_vector.json` with current defaults on boot if it doesn't exist. This ensures the file exists and can accumulate real drift from consolidation sessions.

One-line fix in `load_personality()` fallback: call `save_personality(PersonalityVector())` when FileNotFoundError occurs, so the file is created immediately and subsequent trait deltas persist.

*Builder · 2026-09-08 — no code changes this card (diagnostic). Fix WO dispatched below.*
