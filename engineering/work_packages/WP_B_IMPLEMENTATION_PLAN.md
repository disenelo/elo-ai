# WP_B — Implementation Plan

**Status:** READY FOR REVIEW — awaiting approval before implementation
**Precedes:** Implementation stage
**Follows:** Gap Analysis (`WP_B_GAP_ANALYSIS.md`)
**Proof output:** `engineering/proofs/00_one_brain_proof.md`

---

## Scope

Three bounded changes. No new capability. No architecture changes. Nothing touches FREEZE_V1_LOCK.

Implementation order is fixed — GAP 2 first because it is a live data corruption risk.

---

## Step 1 — GAP 2: One Coordinator for blender_state.json

**Principle (new Invariant 16):**
> A shared state object has one coordinator. Many contributors. Never many owners.

**Root cause:** Four threads write `blender_state.json` independently.

| Writer | File | Atomic? | Locked? |
|---|---|---|---|
| Main server (state_writer.py) | `blender_bridge/state_writer.py` | ✓ .tmp + os.replace | ✓ main _lock |
| Ambient engine | `ambient/ambient_engine.py` `_patch_state()` | 🔴 No — direct json.dump | 🔴 No |
| Vision loop | `tools/vision_loop.py` `_write_vision()` | ✓ .tmp + os.replace | 🔴 No |
| Spotify agent | `tools/spotify_agent.py` `_write_widget_state()`, `_patch_spotify_field()` | 🔴 No — direct json.dump | 🔴 No |

**Fix: add `patch()` to state_writer.py — the single coordinator**

`blender_bridge/state_writer.py` becomes the sole read-modify-write coordinator. Add:

```python
# Module-level lock — all writers must acquire this before touching blender_state.json
_STATE_LOCK = threading.Lock()

def patch(update: dict) -> None:
    """
    Deep-merge `update` into blender_state.json.
    Thread-safe. Atomic write. All background writers must call this.
    """
    with _STATE_LOCK:
        try:
            with open(_STATE_PATH, encoding="utf-8") as f:
                state = json.load(f)
        except Exception:
            state = {}
        _deep_merge(state, update)
        state["_ts"] = time.time()
        tmp = _STATE_PATH + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(state, f)
        os.replace(tmp, _STATE_PATH)
```

The existing `write()` and `write_with_presence()` functions also acquire `_STATE_LOCK` before their existing atomic writes.

**Files to change:**

1. **`blender_bridge/state_writer.py`**
   - Add `import threading`, `import time`
   - Add `_STATE_LOCK = threading.Lock()` at module level
   - Add `_deep_merge(base, update)` helper (recursive dict merge)
   - Add `patch(update: dict)` function
   - Wrap existing `write()` and `write_with_presence()` internal writes with `with _STATE_LOCK:`

2. **`ambient/ambient_engine.py`**
   - Remove local `_patch_state()` function (lines 190–202)
   - Replace all `_patch_state(...)` call sites with `from blender_bridge.state_writer import patch as _patch_state`
   - One import, same call signature — all call sites unchanged

3. **`tools/vision_loop.py`**
   - In `_write_vision()`: replace the local read-modify-write + .tmp + os.replace block
   - Replace with `from blender_bridge.state_writer import patch as _patch_state`
   - Call: `_patch_state({"vision": {...}})`

4. **`tools/spotify_agent.py`**
   - In `_write_widget_state()`: replace local read-modify-write with `_patch_state({"spotify": {...}})`
   - In `_patch_spotify_field()`: replace local read-modify-write with `_patch_state({"spotify": {key: value}})`
   - Import: `from blender_bridge.state_writer import patch as _patch_state`

**Result:** One lock, one coordinator, four contributors. Invariant 12 and Invariant 16 both satisfied.

**Regression check:**
- Run eLo OS for 10 minutes with vision enabled and spotify polling
- Confirm blender_state.json does not show truncated or missing keys
- Confirm ambient expressions still update Unity correctly

---

## Step 2 — GAP 1: Presence Reflex (Formal Exception)

**Principle:** Ambient speech is presence maintenance, not cognition. The architecture review names this distinction precisely:
> "Does ambient think?" → No. "Does ambient speak?" → Yes, from fixed pools.

This is closer to breathing than decision-making. It should be formalised as a permitted presence exception, not routed through the Executive.

**What to verify first (before any changes):**

Read `ambient/ambient_engine.py` to confirm:
- `_STARTUP_LINES` — is it a fixed Python list? (no LLM call)
- `_AMBIENT_LINES` — same
- Does `_speak()` ever call an LLM? Does it ever choose based on session state or user input?

If the answer to all three is "fixed pools, no LLM, no input-dependent selection" → formal exception is valid.

**Changes:**

1. **`ambient/ambient_engine.py`**
   - Update module docstring to: "Presence Reflex — ambient presence maintenance. Not cognition. Speaks from fixed pools only. See engineering/proofs/00_one_brain_proof.md § Authority."
   - No logic changes

2. **`engineering/proofs/00_one_brain_proof.md`**
   - Update § Authority: add "Presence Reflex" row to the permitted exceptions table
   - Update Invariant 01: "Executive is the only cognitive decision-maker. Presence Reflex is a permitted presence exception — fixed pools only, no LLM, no input-dependent selection."
   - Update Invariant 09: "Every cognitive response originates from one CognitivePlan. Presence Reflex utterances are not cognitive responses — they are presence maintenance."
   - Update § Proof: mark Disproof Attempt 1 and 5 as "resolved by formal exception"
   - Update § Freeze: raise score to reflect resolution

3. **`WP_B_GAP_ANALYSIS.md`**
   - Mark GAP 1 as resolved

**What this does NOT do:**
- Does not rename any files or classes (naming is architecture documentation, not implementation)
- Does not change any logic in ambient_engine.py
- Does not route ambient through the spine

**Result:** Invariants 01 and 09 updated with the exception. Presence Reflex formally designated. No cognitive violation remains.

---

## Step 3 — GAP 3: pipeline.run() — Clarify Dead Orchestrator

**Corrected finding from Implementation Plan research:**

The router modules are NOT dead — the spine imports them directly:

| Module | Used by Spine? | Used by Server? |
|---|---|---|
| `intent_engine.py` | ✓ `detect()` in spine.py:61 | — |
| `meaning_engine.py` | ✓ `normalise()` in spine.py:43 | — |
| `typo_engine.py` | ✓ `repair()` in spine.py:52 | — |
| `agent_router.py` | ✓ `route()` in spine.py:105 | — |
| `conversation_matrix.py` | ✓ `push()` in spine.py:481 | — |
| `execution_gate.py` | ✓ `gate()` in spine.py:183 | — |
| `pipeline.py` | — | ✓ `push_turn()` in server.py:997 |
| `confidence_engine.py` | — | — |
| `learning_buffer.py` | — (pipeline.py only) | — |
| `context_matrix.py` | — (pipeline.py only) | — |

**What is actually dead:** `pipeline.run()` — the orchestration entry point. The spine has absorbed that role.

**What is live:** All individual modules. `push_turn()` from pipeline.py is used by server.py for session continuity.

**Changes:**

1. **`runtime/router/pipeline.py`**
   - Add to module docstring: "NOTE: `pipeline.run()` is superseded by `runtime/spine/spine.py`. The spine imports individual modules directly. Only `push_turn()` from this file remains in active use (server.py:997). Do not call `pipeline.run()` — it is not part of the main request path."
   - No logic changes

2. **`engineering/README.md`** (or engineering docs)
   - Document: "`runtime/router/` contains the individual faculty modules (intent, meaning, typo, etc.) used by the spine. `pipeline.py`'s `run()` function is superseded by `spine.py` — only `push_turn()` is in active use."

**What this does NOT do:**
- Does not delete any files (live imports would break)
- Does not change any logic

**Result:** Anyone reading pipeline.py immediately understands its status. No future engineer accidentally reactivates pipeline.run() thinking it's the main path.

---

## Step 4 — Add Invariant 16

**File:** `engineering/proofs/00_one_brain_proof.md` § Invariants

Add row to invariants table:

```
| 16 | A shared state object has one coordinator. Many contributors. Never many owners. | ✓ (after GAP 2) | blender_state.json: state_writer.py is coordinator. ambient, vision, spotify are contributors via patch(). |
```

This invariant applies beyond blender_state.json — it becomes the pattern for:
- Robot telemetry state
- Voice state
- Desktop presence state
- Unity presence state
- Emotion state
- Any future shared file or object

---

## Step 5 — Post-implementation proof document

After steps 1–4 are complete and regression-tested:

Create `engineering/proofs/01_runtime_ownership_proof.md`

**Purpose:** Answer "who owns X?" for every runtime responsibility. Every answer resolves to exactly one owner. Two owners = architectural defect.

**Questions the document must answer:**

| Responsibility | Owner |
|---|---|
| Cognition | Executive |
| Speech (cognitive turns) | Executive via CognitivePlan |
| Speech (presence) | Presence Reflex (ambient_engine.py) — fixed pools only |
| Movement | Presence Faculty via _motion_map() |
| Shared state (blender_state.json) | state_writer.py (coordinator) |
| Memory updates | memory/vault.py |
| Embodiment delivery | Per-embodiment consumers (read-only) |
| File writes | state_writer.patch() — all writers route through this |
| Timing / turn lifecycle | server.py _process_turn() under _lock |
| Interrupts | — (not yet implemented) |
| Session state | state_manager.save() — main thread only |
| Intent classification | intent_engine.detect() via spine |
| Tool enrichment | tool_router.enrich() — context only |

This becomes the ownership constitution for all future WPs.

---

## Implementation order

```
Step 1 — GAP 2: blender_state.json write lock   [4 files]  ← START HERE
    ↓
Step 2 — GAP 1: Presence Reflex formalisation   [2 files + proof doc]
    ↓
Step 3 — GAP 3: pipeline.py docstring           [1 file + README]
    ↓
Step 4 — Add Invariant 16                        [proof doc]
    ↓
Regression test
    ↓
Step 5 — Write 01_runtime_ownership_proof.md
    ↓
WP_B FREEZE
```

---

## What does NOT change

- `runtime/executive.py` — FREEZE_V1_LOCK
- `prompts/` — FREEZE_V1_LOCK
- Any spine logic
- Any faculty logic
- Any LLM routing
- Any response generation
- Any pre-spine interceptors
- Ambient engine speech logic (pools, timing, triggers)

---

## Freeze criteria (after implementation)

| Criterion | Current | After Implementation |
|---|---|---|
| Complete runtime trace | ✓ | ✓ |
| Zero duplicate logic (or canonical designation) | ✓ | ✓ |
| Every faculty has authority statement | ✓ | ✓ |
| Every data object has one documented owner | ⚠️ | ✓ |
| Every runtime object has lifecycle documentation | ✓ | ✓ |
| Adversarial disproofs resolved | ⚠️ | ✓ |
| All embodiments removable | ✓ | ✓ |
| Faculty dependency graph acyclic | ✓ | ✓ |
| All 16 invariants confirmed | 9/15 | 13–14/16 |
| Regression tests pass | — | ✓ |

**Projected One Brain Score after implementation: 88–92/100**
