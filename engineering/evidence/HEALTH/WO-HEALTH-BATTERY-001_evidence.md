# Evidence — WO-HEALTH-BATTERY-001: Health Battery + ADDENDUM A

**Date**: 2026-09-26  
**Commits**:
- Core implementation: `core/health_battery.py` (prior session — commit referenced in summary)
- Server wiring: `f7a597e`

---

## Part A — Core implementation (`core/health_battery.py`)

Fully implemented across two tracks:

### Cognitive track (WO PART A)
- `drain(amount)` — subtracts from cognitive battery
- `restore(amount)` — adds, capped at ENERGY_FULL (0.95)
- `on_conversation_turn(emotional_intensity)` — drains per turn + extra for high emotion
- `consume_game_events()` — reads game_events.jsonl, applies food/crate item restores
- `on_wake_from_dream(phase)` — NREM+REM → +0.30, NREM → +0.12
- `calm_tick(dt_seconds)` — +0.008/min during calm mode
- `should_auto_calm()` — True when physical exhaustion reached

### Physical track (ADDENDUM A)
- Separate `_physical_battery` float, engaged only once motion is reported
- Per-tick rates: standing −0.0015, walking −0.003, running −0.010, sitting +0.008, lying_down +0.015, sleeping +0.015
- Discrete event costs: jumping −0.015, parkour −0.020 (charged once on transition)
- `physical_conditioning()` — returns canonical expressions for tired/fatigued/exhausted states for inner_thought pipeline (Phase 2 dependency — not yet wired)
- Physical state bands: rested (≥0.75), normal (≥0.40), tired (≥0.20), fatigued (≥0.10), exhausted (≥0.00)

### Combined output
- `snapshot()` returns `elo_battery`, `elo_battery_state`, and when physical engaged: `physical_battery`, `physical_state`, `activity_recent`, `activity_duration_minutes`
- Combination weights: 0.6 cognitive / 0.4 physical (only when physical track engaged)

---

## Part B — Server wiring (`server.py`) — commit `f7a597e`

**File changed**: `server.py` (+54 lines)

### Integration points

#### 1. Ambient tick (STACK item 3 + 4)
**Location**: `ambient_thought()`, before early-return at `_is_user_away() or _is_calm_mode()`

- `_batt_tick_ts: list[float] = [0.0]` — module-level timestamp tracker (line 166)
- `dt_seconds` computed as elapsed since last call (defaults 120s on first fire)
- `motion_state` read from `blender_state.json["motion"]`
- `idle_seconds` from `_state["last_user_ts"]`
- `tick()` result patched back via `blender_bridge.state_writer.patch()`
- Fields written: `elo_battery`, `elo_battery_state`, `physical_battery`, `physical_state`, `activity_recent`, `activity_duration_minutes`

#### 2. Calm mode restore (STACK item 5)
**Location**: same ambient block, `if _is_calm_mode(): calm_tick(dt)`

- `calm_tick(dt_seconds)` fires instead of the normal tick when Unity/Python signals calm/meditation mode
- +0.008/min cognitive restore during calm

#### 3. Physical exhaustion auto-calm (STACK item 5)
**Location**: same ambient block, after tick snapshot patch

- `should_auto_calm()` check after each normal tick
- If True: writes `meditation_state: {phase: "enter", source: "physical_exhaustion"}` to `blender_state.json`
- Triggers `_is_calm_mode()` detection on next cycle

#### 4. Dream wake restore (STACK item 6)
**Location**: `ambient_thought()` dream pipeline, after `run_dream()` completes (~line 1041)

- `on_wake_from_dream(phase)` called with dream result phase
- Phase read from `dream_result.phase` attribute or dict key
- Defaults to `"NREM"` if phase not available
- +0.30 (NREM+REM) or +0.12 (NREM) applied to cognitive + physical tracks

---

## Already wired (prior session)
- `on_conversation_turn` + `publish`: `server.py` lines 3686-3691

---

## Not yet wired (future dependency)
- `physical_conditioning()` → inner_thought pipeline Phase 2 (WO-INNER-THOUGHTS-001 Phase 2 not yet built)

---

## Status

PASS — core implementation complete, all server integration points wired. Committed `f7a597e`. Board crosscheck required before WO close.
