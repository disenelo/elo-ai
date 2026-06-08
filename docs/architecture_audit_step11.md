# eLo AI — Architecture Audit (Step 11 Stabilisation)

**Date**: 2026-06-08
**Status**: Pre-Step-12 freeze
**Purpose**: Identify shared mutable state, cross-engine write access, and implicit coupling before introducing the StateBus.

---

## 1. Shared Mutable State Inventory

### `kernel._loop_state` — HIGH RISK
**Type**: Module-level dict containing four mutable deques + int counter.
```python
_loop_state = {
    "recent_modes":              deque(maxlen=4),
    "recent_questions":          deque(maxlen=4),
    "recent_fragments":          deque(maxlen=4),
    "last_opening":              "",
    "reflection_disabled_turns": 0,
}
```
**Written by**: `_filter()`, `record_response()`, `_pick_question()`
**Read by**: `detect_loop()`, `_pick_question()`, `assemble_context()`
**Risk**: Module-level state persists across all test runs in a process. Tests that don't call `reset_session()` will inherit state from previous tests. Two concurrent coroutine calls would race on the same deques.

### `kernel._ACTIVE_BACKEND` + `kernel._BACKEND_REGISTRY` — LOW RISK
**Type**: Module-level str + dict.
**Written by**: `set_backend()`
**Read by**: `generate_response()`
**Risk**: Configuration-level state — not per-turn, not per-session. Acceptable but should be noted.

### `kernel._DEBUG_ENABLED` — LOW RISK
**Type**: Module-level bool.
**Written by**: `set_debug()`
**Read by**: `decide_response()`
**Risk**: Same as above — configuration, not turn state.

### `behavior_engine._recent_closings` — MEDIUM RISK
**Type**: Module-level list.
**Written by**: `_select_closing_fresh()`
**Read by**: `_select_closing_fresh()`
**Risk**: Functionally superseded by `kernel._loop_state["recent_questions"]`. Two separate deduplication mechanisms tracking slightly different things — they can diverge. `behavior_engine` is no longer the primary path (kernel is), making this state increasingly orphaned.

---

## 2. Cross-Engine Write Access

### `kernel.decide_response()` mutates local context copy
```python
ctx = dict(context)     # copy — OK
ctx["emotion"]  = ...   # writes to local copy
ctx["identity"] = ...   # writes to local copy
```
**Risk**: The copy is passed to `_assemble()` which reads from it. The copy is then discarded. No external mutation. This is acceptable but the pattern (`dict` mutation) is easy to accidentally break by removing the `dict()` copy.

### `core_engine.turn()` — previously mutated shared memory dict (FIXED)
The god-object mutation (`memory["state"] = ...`, `memory["identity_bias"] = ...` etc.) was removed in the previous refactor. Core engine now passes a clean context. Confirmed clean.

### `memory_engine` file I/O — SEQUENTIAL, LOW RISK
Within a single turn:
1. `build_memory_influence()` reads `interactions.json`
2. `store_interaction()` writes `interactions.json`
These are sequential (read before write) so there is no race condition in single-threaded use.

---

## 3. Implicit Coupling

### `kernel` reads `behavior_engine._recent_closings` indirectly
`_pick_question()` in the kernel appends to `_loop_state["recent_questions"]`.
`_select_closing_fresh()` in `behavior_engine` appends to its own `_recent_closings`.
These are two separate question-dedup mechanisms. When behavior_engine is called (e.g., from `feel_test.py`), its dedup state diverges from the kernel's. **Result**: question deduplication is inconsistent depending on which path is active.

### `behavior_engine` reads `influence` dict keys injected by `core_engine`
`behavior_engine.generate_offline_response()` reads keys like:
- `tone_signal`, `returning_theme`, `symbolic_echo` — from memory_engine
- `state`, `imagination_level` — injected by core_engine (old keys, now removed from state_engine)
- `identity_bias`, `identity_intent` — injected by core_engine (old keys, now moved to kernel)

Some of these keys (`imagination_level`, `identity_bias`) may no longer be present in the context dict since the refactor. `behavior_engine` uses `.get(key, default)` so it silently falls back to defaults, masking the broken coupling.

### `assemble_context()` builds sub-dicts from flat keys
The `state_summary` sub-dict reads `raw_context.get("state_tone_bias")` etc. — keys injected by `core_engine` using a specific naming convention. If `core_engine` changes the key names, `assemble_context()` silently gets wrong values. There is no schema or contract enforcing these key names.

---

## 4. Root Cause

All three problems share a common cause: **engines communicate via a flat mutable dict with no schema**. Any engine can write any key, any consumer reads any key, and there is no contract defining what keys exist, who owns them, or whether they are valid for the current turn.

The fix: replace the flat dict with **typed, immutable snapshot objects** assembled into a single **StateBus**. The kernel reads only from the bus.

---

## 5. Fix Applied (this commit)

### New `core/state_bus.py`

Four snapshot types (immutable after creation):
- `IdentitySnapshot` — frozen dataclass
- `StateSnapshot` — frozen dataclass
- `EmotionSnapshot` — frozen dataclass
- `MemorySnapshot` — read-only wrapper (MappingProxyType)

One aggregation class:
- `StateBus` — holds all four snapshots, immutable after creation
- `StateBus.to_context()` — the only way kernel data flows out of the bus

### Changes to `core_engine.py`

`turn()` now:
1. Calls all four engines (state, memory, emotion, identity)
2. Creates typed snapshots from their outputs
3. Assembles an immutable `StateBus`
4. Calls `kernel.decide_response(user_input, bus.to_context())`

### Changes to `core/kernel.py`

- Removed direct imports of `emotion_engine` and `identity_engine`
- Kernel no longer calls engines internally — it only reads context
- `_loop_state` wrapped in `LoopDetector` class — instance-level state, no longer module-global for the mutable parts

### Remaining known issues (not fixed in this pass)

- `behavior_engine._recent_closings` — orphaned dedup state. Remove in next cleanup.
- `behavior_engine` reads old key names silently via `.get(key, default)` — masking broken coupling. Fix when behavior_engine is formally deprecated or replaced.
- `kernel._ACTIVE_BACKEND` / `_DEBUG_ENABLED` remain module-level. Acceptable for configuration; not per-turn state.
</content>
