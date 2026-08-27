# WO-SP31-SP32 — Self-Initiation Gate: ATTENDING Detection + Autonomous Spine Call Path
**Priority:** P2 — Parallel track (non-blocking to Waves 1–5)  
**Authority:** DISPATCH_BOARD 2026-08-24 · Q-ATT-1 resolved · WO-NAV-013 ✅ · WORLD-001 ✅  
**Issued:** 2026-08-27 · Architect → Builder  
**Specs:** SPEC_STAGE2_EMBODIED_ONE_BRAIN_2026-08-23.md SP-31/SP-32  
**Design ruling:** `design/FROM_DESIGN_2026-08-24_Q-ATT-1_ruling_david_attending.md`  
**Board acceptance:** `docs/architecture/findings/BOARD_ACCEPTANCE_DESIGN_RULINGS_Q-ATT-1_SP38_2026-08-24.md`

---

## ACTIVATION CONSTRAINT (hard rule, no exceptions)

Self-initiation is default OFF. `ELO_SELF_INITIATION` env var must be `"1"` for any gate to allow a spine call. David L3 flips this flag when ready to observe the behaviour. Build and test behind this flag — fail-quiet when disabled.

---

## SP-31 — Autonomous spine call path

When the SP-32 gate passes, eLo calls:
```python
spine.run("…", state=_state, intent_source="world_event", internal_intent={"trigger": "world_event", "significance_score": score})
```
trigger_source in decision_journal: `"world_event"`.

The spine call path is already built (ambient_thought → spine.run exists). SP-31 adds a WORLD-EVENT trigger that bypasses the internal_intents() proposer and uses significance_faculty output as the intent directly.

## SP-32 — Self-initiation permission conditions

Build `runtime/self_initiation.py` with:

### ATTENDING (§1 from ruling)
ATTENDING = True when ANY of:
- A1: `_last_conversing_ts` updated within `ATTEND_CONVERSE_SECS=45` seconds
- A2: `presence_state.json eloOnFront==True` (proxy for appFocused)
- A3: `_last_interact_ts` within `ATTEND_INTERACT_SECS=20` seconds

### HARD-QUIET (§3 from ruling — override everything)
- Q1: `presence.json state=="away"`
- Q2: `presence_state.json mode` in DORMANT/PRIVACY/TAKE_FIVE/HIDDEN
- Q3: `eloOnFront==False` AND `engagement` in DEEP_IDLE/DEEP_FOCUS
- Q4a: cooldown — `(now - _last_self_init_ts) < SELF_INIT_COOLDOWN=180`
- Q4b: dismiss quiet — `(now - _last_dismiss_ts) < DISMISS_QUIET_SECS=300`

### Gate logic (§2 from ruling)
```
HARD_QUIET → blocked
ATTENDING + score ≥ 0.72 → verbal (allowed)
NOT ATTENDING + score ≥ 0.90 → verbal (allowed, exceptional)
score < 0.72 → ambient_only (not allowed for spine call)
NOT ATTENDING + 0.72 ≤ score < 0.90 → ambient_only
```

### Public API
- `is_enabled() → bool` — True iff ELO_SELF_INITIATION=1
- `record_conversation_pulse()` — call on each user turn (A1)
- `record_direct_interaction()` — call on direct eLo interaction (A3)
- `record_self_init()` — call after self-initiation fires (Q4a cooldown)
- `record_dismiss()` — call when David dismisses initiation (Q4b)
- `may_self_initiate(significance_score: float) → SelfInitResult`
  - `.allowed: bool`
  - `.tier: str` ("verbal" | "ambient_only" | "blocked")
  - `.reason: str`

---

## Server.py wiring (minimal, behind flag)

1. Import self_initiation at top
2. In `_process_turn()` after `_state["last_user_ts"]` stamp: call `record_conversation_pulse()`
3. Add `_world_event_thought()` function — reads significance from live_world_state, calls `may_self_initiate()`, fires spine if allowed
4. Inside `ambient_thought()` — add `_world_event_thought()` call at top (returns immediately when disabled)

---

## Deliverables

- D-1: `runtime/self_initiation.py` — gate module, all constants, all signal detection, SelfInitResult
- D-2: `server.py` — `record_conversation_pulse()` wired at turn start; `_world_event_thought()` function; called from `ambient_thought()`
- D-3: `tests/test_sp31_sp32_self_initiation.py` — ≥9 ATs covering: disabled, hard-quiet conditions, ATTENDING tiers, significance thresholds

---

## Hard constraints

- Do NOT modify `executive.py` (FREEZE_V1_LOCK)
- Do NOT modify `living_presence_spec.txt`
- No new dependencies (no new pip packages)
- Default OFF — ELO_SELF_INITIATION=0 unless David L3 sets it
- Fail-quiet: any signal read failure → most conservative outcome (treat as blocked)

---

*Architect Seat → Builder Seat · 2026-08-27*
