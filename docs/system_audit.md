# eLo AI — System Audit

**Date**: 2026-06-08
**Status**: Pre-refactor freeze
**Purpose**: Map the current system before restructuring into a clean kernel architecture.

> This document does not modify any logic.
> It is a read-only map of what exists and where the risks are.

---

## 1. Engine Inventory

| Engine | File | Size | Role |
|---|---|---|---|
| **Kernel** | `core/kernel.py` | 471L, 9fn | Single decision pipeline — `decide_response()` |
| **Behavior** | `core/behavior_engine.py` | 869L, 17fn | Offline response generation — 5-phase simulation |
| **Memory** | `core/memory_engine.py` | 1022L, 32fn | Persistent store + 5-category influence signals |
| **Identity** | `core/identity_engine.py` | 377L, 8fn | Highest-level value/intent/bias decisions |
| **State** | `core/state_engine.py` | 305L, 12fn | 6-state machine with inertia + hysteresis |
| **Emotion** | `core/emotion_engine.py` | 195L, 3fn | State → emotion/intent/energy/posture signal |
| **Avatar Bridge** | `core/avatar_bridge.py` | 147L, 2fn | Packages signals for any embodiment layer |
| **Visual Memory** | `core/visual_memory.py` | 307L, 5fn | Memory → spatial cluster world graph |
| **Project** | `core/project_engine.py` | 68L, 5fn | Project registry loading and namespace resolution |
| **Orchestrator** | `core/core_engine.py` | 213L, 8fn | Session runtime — assembles all engines per turn |

---

## 2. Current Data Flow (per turn)

```
User input
    │
    ▼
core_engine.CoreEngine.turn()
    │
    ├─1─ state_engine.update(input)
    │       → current_state, transitioned, state_hint
    │
    ├─2─ memory_engine.build_memory_influence(input, project)
    │       → large flat dict (25+ keys)
    │       → internally calls: retrieve_structured(), 5 category extractors,
    │                           _synthesize_behavioral_guidance()
    │
    ├─3─ identity_engine.decide(input, state, memory, project)
    │       → {values, perspective, intent, response_bias, entities, project}
    │
    ├─4─ core_engine mutates memory dict in-place
    │       memory["state"]             = current_state
    │       memory["state_tone"]        = state_hint["tone"]
    │       memory["response_length"]   = state_hint["response_length"]
    │       memory["imagination_level"] = state_hint["imagination_level"]
    │       memory["project_focus"]     = state_hint["project_focus"]
    │       memory["elo_voice_hint"]    = state_hint["elo_voice_hint"]
    │       memory["identity_values"]   = identity["values"]
    │       memory["identity_perspective"] = identity["perspective"]
    │       memory["identity_intent"]   = identity["intent"]
    │       memory["identity_bias"]     = identity["response_bias"]
    │
    ├─5─ kernel.decide_response(input, memory)
    │       → internally: _classify(), _assemble(), _route(), _generate(), _filter()
    │       → reads from memory dict (assembled in step 4)
    │       → returns (response, meta)
    │
    └─6─ memory_engine.store_interaction(input, response, mode, project)
```

---

## 3. Dependency Map

### Imports between engines

```
core_engine.py
    ├── imports kernel.decide_response
    ├── imports behavior_engine.generate_offline_response   ← UNUSED after kernel added
    ├── imports memory_engine.{build_memory_influence, store_interaction, ...}
    ├── imports state_engine.StateEngine
    └── imports identity_engine.decide

kernel.py
    └── NO engine imports (stdlib only)
        NOTE: kernel reads signals from the flat memory dict passed in from core_engine
              it does NOT import memory/state/identity directly

behavior_engine.py
    └── NO engine imports (stdlib only)
        NOTE: still called by feel_test.py and llm_client.py fallback paths

avatar_bridge.py
    └── imports emotion_engine.{from_state, orb_intensity}

visual_memory.py
    └── lazy import of memory_engine._load_store (inside function body)

emotion_engine.py   → no engine imports
state_engine.py     → no engine imports
identity_engine.py  → no engine imports
memory_engine.py    → no engine imports
project_engine.py   → no engine imports
```

### Who reads what from the shared memory dict

The memory dict produced by `build_memory_influence()` is a **shared mutable object** that gets keys injected by `core_engine` from three other engines before being passed to `kernel`. This is the central architectural risk.

| Key in memory dict | Produced by | Read by |
|---|---|---|
| `tone_signal` | memory_engine | behavior_engine (blended_emotion), kernel (_assemble) |
| `returning_theme` | memory_engine | behavior_engine (_assemble), kernel (_generate) |
| `symbolic_echo` | memory_engine | behavior_engine |
| `concept_pairs` | memory_engine | behavior_engine |
| `recurring_concepts` | memory_engine | behavior_engine |
| `response_style` | memory_engine | behavior_engine |
| `key_association` | memory_engine | behavior_engine |
| `future_idea` | memory_engine | behavior_engine |
| `raw_blocks` | memory_engine | behavior_engine |
| `memory_categories` | memory_engine | behavior_engine |
| `state` | **core_engine (injected)** | kernel, behavior_engine |
| `state_tone` | **core_engine (injected)** | behavior_engine |
| `response_length` | **core_engine (injected)** | behavior_engine |
| `imagination_level` | **core_engine (injected)** | kernel (_assemble→_route), behavior_engine |
| `project_focus` | **core_engine (injected)** | behavior_engine |
| `elo_voice_hint` | **core_engine (injected)** | behavior_engine |
| `identity_values` | **core_engine (injected)** | — (written, never read by kernel/behavior) |
| `identity_perspective` | **core_engine (injected)** | behavior_engine |
| `identity_intent` | **core_engine (injected)** | behavior_engine, kernel |
| `identity_bias` | **core_engine (injected)** | behavior_engine (partially), kernel |

---

## 4. Failure Risks

### Risk 1 — CRITICAL: Dead code path (behavior_engine imported but not called)

`core_engine.py` imports `generate_offline_response` from `behavior_engine` but the active path now calls `kernel.decide_response()`. The `generate_offline_response` import is a ghost — it adds confusion about which path is live.

**Failure mode**: Future changes to `behavior_engine` may be assumed to affect production behavior but won't.
**Location**: `core/core_engine.py` line 22.

---

### Risk 2 — HIGH: Shared mutable memory dict (the god object)

`build_memory_influence()` returns a large dict (~25 keys). `core_engine` then mutates it in-place by injecting 10 more keys from `state_engine` and `identity_engine`. This same dict is then passed to `kernel.decide_response()`.

The memory dict is acting as a **god object** — a shared communication channel between four different engines with no schema enforcement.

**Failure modes**:
- Key name collisions (e.g., `state` from state_engine overwrites any `state` key memory might add)
- Silent missing-key bugs (engine reads `.get("key", default)` — wrong default silently applied)
- No clear ownership: who is authoritative for `imagination_level`? state_engine? memory? kernel?
- `build_memory_influence()` is expensive (reads and re-processes the full interaction store) — called once per turn with all results stuffed into one dict

**Location**: `core/core_engine.py` lines 158–181.

---

### Risk 3 — HIGH: Kernel and behavior_engine duplicate classification logic

Both `kernel._classify()` and `behavior_engine._classify_input_type()` independently detect the same signals (factual questions, emotional expressions, entity mentions, contradictions). Neither calls the other.

**Current state**: They produce compatible but not identical results. Routing decisions in the kernel may diverge from behavior_engine's internal grounding decisions.

**Failure mode**: A query classified as `INFORMATION_REQUEST` by the kernel takes the `DIRECT` path, but if behavior_engine is ever called on the same input, it may route differently. Inconsistent behavior depending on which path is active.

**Location**: `core/kernel.py` lines 60–118, `core/behavior_engine.py` lines 22–86.

---

### Risk 4 — MEDIUM: Loop detection state is module-level (session bleed)

`kernel._loop_state` is a module-level deque. `reset_session()` must be called at the start of each conversation or the loop detection state bleeds between sessions.

Currently `CoreEngine.__init__()` calls `reset_session()`. But:
- `feel_test.py` calls `generate_offline_response` directly, bypassing the kernel entirely — its sessions never reset
- Any test that imports the kernel accumulates loop history unless it calls `reset_session()` explicitly

**Failure mode**: After running automated tests that trigger CONVERSATIONAL mode 3+ times, the next real session starts with loop detection already counting toward the DIRECT-mode threshold.
**Location**: `core/kernel.py` lines 36–48.

---

### Risk 5 — MEDIUM: Identity engine intent → behavior_engine conflict (now removed, but pattern remains)

A previous bug: `identity_bias == "name_first"` was forcing `blended_emotion = "distorted"` in `behavior_engine`, which caused "Something is overloaded" to fire for all inputs. The force-override was removed in the most recent fix. However, `behavior_engine` still reads `identity_bias` and `identity_intent` from the memory dict for debug output and future use.

**Current state**: The fix is correct. But the pattern of one engine (identity) writing values that another engine (behavior) reads and could act on is still in the architecture. A future change that re-adds any of these:
```python
if identity_bias == "name_first" and not is_contradiction:
    blended_emotion = _blend_emotion(blended_emotion, "distorted")
```
would re-introduce the loop.
**Location**: `core/behavior_engine.py` lines 740–750, memory dict keys `identity_bias`, `identity_intent`.

---

### Risk 6 — MEDIUM: `_blend_emotion` sticky-state logic

The previous implementation made "distorted" a sticky state that overrode neutral inputs from memory history. The fix narrowed it to only apply when locally detected emotion is exactly "neutral". However the function still exists and is still called — it just has less range.

**Failure mode**: Any future change to `_EMOTION_SIGNALS` that makes "neutral" harder to detect (e.g., adding more signals) could re-activate the stickiness for inputs that should get a direct response.
**Location**: `core/behavior_engine.py` `_blend_emotion()` function.

---

### Risk 7 — LOW: `behavior_engine` is no longer the primary path but is still tested

`tests/test_basic_loop.py` tests `behavior_engine.generate_offline_response()` directly. These tests pass — but they test a path that `core_engine` no longer takes (it calls kernel instead). The tests give false confidence that production behavior is stable.

**Failure mode**: `behavior_engine` tests pass. `kernel.decide_response()` behavior diverges. Nobody notices because tests are green.
**Location**: `tests/test_basic_loop.py`, `core/kernel.py`.

---

### Risk 8 — LOW: `visual_memory.py` lazy import inside function body

```python
from core.memory_engine import _load_store
```
This imports a private function (`_load_store`) across module boundaries. If `_load_store` is renamed or moved during refactor, it will fail silently at runtime (not caught by import-time checks).
**Location**: `core/visual_memory.py` line 145.

---

## 5. Engines not connected to the live path

These engines exist and work in isolation but are NOT called during a normal conversation turn:

| Engine | Status | Gap |
|---|---|---|
| `emotion_engine` | Works, tested | Only called from `avatar_bridge`. Not in core_engine turn. |
| `avatar_bridge` | Works, tested | Not called from core_engine. Only used if `unity_bridge.export_from_core()` is explicitly invoked. |
| `visual_memory` | Works, tested | No CLI command or core_engine integration. Only callable manually. |
| `project_engine` | Works | Duplicate of what `memory_engine.resolve_project()` does. Both exist. |

---

## 6. Summary — Pre-refactor state

### What is clean

- `state_engine`: self-contained, no engine imports, clean public API
- `emotion_engine`: self-contained, no engine imports, clean public API
- `identity_engine`: self-contained, no engine imports, clean public API
- `memory_engine`: self-contained (no engine imports), but very large (1022L, 32 functions)
- `kernel._classify()` and `kernel._route()`: clean, deterministic, no engine dependencies

### What needs fixing in the refactor

1. **Dead import**: remove `generate_offline_response` from `core_engine.py` — kernel is now the live path
2. **God object**: replace the mutated memory dict with a structured `Context` dataclass that has explicit owners per field
3. **Duplicate classification**: merge `kernel._classify()` and `behavior_engine._classify_input_type()` into one canonical function, one location
4. **Loop state bleed**: move `_loop_state` into `CoreEngine` instance rather than module-level
5. **Disconnected engines**: wire `emotion_engine` into the turn pipeline, or formally declare it avatar-only
6. **Test coverage gap**: add kernel-path tests alongside (or replacing) the behavior_engine-path tests
7. **Private import across modules**: `visual_memory` should use the public `retrieve()` API, not `_load_store`

---

## 7. Recommended refactor sequence

1. Define a `Context` dataclass — explicit fields, typed, owned
2. Move classification to one canonical function (kernel owns it)
3. Move loop state into `CoreEngine` instance
4. Wire `emotion_engine` explicitly into the turn (or document it as avatar-only)
5. Remove dead `generate_offline_response` import from `core_engine`
6. Add kernel-path tests
7. Clean `memory_engine` (32 functions — split or reduce)

---

*No logic was modified to produce this report.*
*All line numbers and function counts verified from live files.*
