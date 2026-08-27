# FROM BUILDER — WO-SP31-SP32 Self-Initiation Gate
**Seat:** Builder  
**WO:** WO-SP31-SP32 — Self-Initiation Gate: ATTENDING Detection + Autonomous Spine Call Path  
**Date:** 2026-08-27  
**Authority:** DISPATCH_BOARD 2026-08-24 · Q-ATT-1 Design ruling · WO-NAV-013 ✅ · WORLD-001 ✅

---

## D-1 — `runtime/self_initiation.py` ✅

Gate module: all SP-32 permission conditions, all Design constants, SelfInitResult type.

**ATTENDING detection (A1/A2/A3):**
- A1: `_last_conversing_ts` within 45s (updated by `record_conversation_pulse()`)
- A2: `presence_state.json eloOnFront==True` (proxy for appFocused — closest available signal)
- A3: `_last_interact_ts` within 20s (updated by `record_direct_interaction()`)

**HARD-QUIET detection (Q1-Q4):**
- Q1: `presence.json state=="away"`
- Q2: `presence_state.json mode` in (DORMANT, PRIVACY, TAKE_FIVE, HIDDEN)
- Q3: `eloOnFront==False` AND `engagement` in (DEEP_IDLE, DEEP_FOCUS)
- Q4a: `(now - _last_self_init_ts) < 180s`
- Q4b: `(now - _last_dismiss_ts) < 300s`

**Gate logic:**
```
disabled (ELO_SELF_INITIATION≠1)   → blocked / self_initiation_disabled
HARD_QUIET                          → blocked / hard_quiet
ATTENDING + score ≥ 0.72            → verbal / attending+significant
NOT ATTENDING + score ≥ 0.90        → verbal / exceptional_significance
score < 0.72                        → ambient_only / below_threshold
NOT ATTENDING + 0.72 ≤ score < 0.90 → ambient_only / not_attending
```

**Public API:**
- `is_enabled() → bool`
- `record_conversation_pulse()` — A1 signal; call on each user turn
- `record_direct_interaction()` — A3 signal
- `record_self_init()` — Q4a cooldown start
- `record_dismiss()` — Q4b quiet window start
- `may_self_initiate(significance_score) → SelfInitResult`

---

## D-2 — `server.py` wiring ✅

**`record_conversation_pulse()` wired at turn start:**
After `_state["last_user_ts"]` stamp in `_process_turn()` — every user turn updates A1.

**`_world_event_thought()` function added:**
- Reads `world_delta.compute_delta()` + `significance_faculty.compute_significance()`
- Calls `may_self_initiate(score)` 
- If allowed (verbal): acquires lock non-blocking → `spine.run(intent_source="world_event")` → journals with `trigger_source="world_event"` → calls `record_self_init()` on non-silence
- Fail-quiet: any exception → silent return

**`_world_event_thought()` called at top of `ambient_thought()`:**
Runs first on each ambient cycle. Non-blocking. Behind the same ambient daemon schedule (2–4 min cycle).

**ACTIVATION:** `ELO_SELF_INITIATION=1` (David L3) required. Default `"0"` — no spine call fires. All gate logic is fully built and tested; only the activation flag is missing.

---

## D-3 — 13/13 ATs PASS ✅

```
/Users/Disenelo/miniconda3/bin/python3 -m pytest tests/test_sp31_sp32_self_initiation.py -q
.............
13 passed in 0.02s
```

AT-1  disabled by default ✅  
AT-2  HARD-QUIET Q1 user away ✅  
AT-3  HARD-QUIET Q4a cooldown ✅  
AT-4  HARD-QUIET Q4b dismiss window ✅  
AT-5  ATTENDING A1 verbal allowed ✅  
AT-6  ATTENDING A2 (eloOnFront) verbal allowed ✅  
AT-7  exceptional score not attending → verbal ✅  
AT-8  below threshold → ambient_only ✅  
AT-9  not attending midrange → ambient_only ✅  
AT-10 record_conversation_pulse advances timestamp ✅  
AT-11 cooldown expired → allowed ✅  
AT-12 is_enabled() False when absent ✅  
AT-13 is_enabled() True when set ✅  

---

## Status

WO-SP31-SP32: COMPLETE.  
Self-initiation gate built. Default OFF. Server.py wired. 13/13 ATs PASS.  
Activation: David L3 sets `ELO_SELF_INITIATION=1` when ready to observe behaviour.

Lane: WO-NAV-013 ✅ → WORLD-001 ✅ → WO-CAP-001 (Board-gated) → WO-SP31-SP32 ✅

*Builder · 2026-08-27*
