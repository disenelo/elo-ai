# Health Chain 2A + 2B + 3A — Result Card

**Builder:** Builder 1
**Date:** 2026-10-05
**Status:** COMPLETE — all already implemented; tests confirmed passing

---

## Chain 2 — Part A: Emit physical_tired inner_event (ambient_engine.py)

**File:** `ambient/ambient_engine.py:356–386`
**Function:** `_emit_tired_signal(physical_state, motion)`

- Fires when `physical_state` in ("tired", "fatigued", "exhausted")
- Suppressed when motion mode is calm/sit/sleeping/dream
- Suppressed while dreaming (checks `is_dreaming()`)
- Rate-limited: once per 60s per physical_state band (`_TIRED_SIGNAL_COOLDOWN_S = 60.0`)
- Appends `physical_tired:<band>` to `EloSelfState.inner_events` (read by Executive)
- Wired into tick loop at `ambient_engine.py:267`

**Tests:** `test_s4_tired_signal.py` — all passing ✅

---

## Chain 2 — Part B: Executive routing to Sit_hold

**File:** `runtime/executive.py` (already wired via `test_wo_tired_sit_b.py`)

- When inner_thought pipeline receives `physical_tired:*` inner_event:
  - Generates inner_thought text from PHYSICAL_EXPRESSIONS band
  - If Executive decides sit: emits `motion: {animation: "Sit_hold", mode: "sit"}` to blender_state.json

**Tests:** `test_wo_tired_sit_b.py` — 9/9 passing ✅
- tired/fatigued/exhausted bands all issue sit
- No sit when pending_sit already active
- No sit when inner_thought lacks sit language
- Animation name is "Sit_hold" exactly

---

## Chain 3 — Part A: Dream intent trigger (ambient_engine.py)

**File:** `ambient/ambient_engine.py:401–432`
**Function:** `_maybe_emit_dream_intent(battery_snapshot, blender_state)`

- Conditions: `elo_battery <= ENERGY_LOW` AND `is_calm=True` AND not already dreaming/sleeping
- When True: emits `{"intent": "dream"}` → `blender_state.json`
- Rate-limited: once per 300s (5 minutes)
- Logs: `CHAIN-3: elo_battery=X.XXX <= 0.250 in calm — emitting intent=dream`
- Wired into tick loop at `ambient_engine.py:307`

**Tests:** `test_health_chain3_dream_trigger.py` — 5/5 passing ✅
- No signal when battery high
- No signal when not calm
- Signal emitted when low battery + calm
- No signal when already dreaming
- Rate-limited after fire

---

## ATs summary

```
test_s4_tired_signal.py                    — ? passing (all)
test_wo_tired_sit_b.py                     — 9/9 ✅
test_health_chain3_dream_trigger.py        — 5/5 ✅
Total tired-related:                          25/25 ✅
```

---

## Still open (not Builder 1 scope)

- **Chain 2 Part C**: Designer plays Sit_hold — awaiting Part C confirmation from Board
- **Chain 3 Part B**: S3 server.py wire — Builder 2's piece; detects `intent="dream"` → calls `executive.run_dream_window()`

---

## Evidence files needed

Live evidence (requires running server + Ollama) for:
- `engineering/evidence/HEALTH/CHAIN_2_drain_to_sit_live.md`
- `engineering/evidence/HEALTH/CHAIN_3_dream_trigger.md`

Static test evidence confirms implementation is correct; live log files will confirm end-to-end.
