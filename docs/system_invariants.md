# eLo AI OS — System Invariants

**Version**: 1.0.0-stable
**Status**: Permanent — these invariants may not be violated in any version without a MAJOR increment and full audit.

> An invariant is a rule that holds true across every state, every version, every deployment, and every integration.
> If code is found that violates any of these invariants, it must be corrected before merge.

---

## Invariant 1 — Kernel is the only decision-maker

**Rule:** All routing, mode selection, and loop detection decisions happen inside `core/kernel.py`.

No other module may decide which response mode is used. No module may override the kernel's routing output after it is produced.

**Enforced by:**
- `route()` function owns the only path from classification → mode
- `decide_response()` is the single pipeline entry point
- Engine isolation tests (29 tests) confirm no engine can alter routing

**Violation examples:**
```python
# FORBIDDEN — setting mode from outside the kernel
memory_engine.set_mode("GENTLE_GROUNDED")     # ✗
emotion_engine.override_route("DIRECT")        # ✗
core_engine.turn.__dict__["mode"] = "CREATIVE" # ✗
```

---

## Invariant 2 — Memory may never influence routing

**Rule:** Memory signals (tone_signal, returning_theme, concept_pairs, etc.) may influence tone, familiarity, and contextual generation — they may never determine which routing mode is selected.

**Enforced by:**
- `route()` does not read from `memory_snapshot`
- Memory data arrives via `StateBus.memory` — the kernel reads it for context only
- Engine isolation tests: same input produces same mode regardless of memory state

**Allowed:** Memory → tone_signal → generation layer delivery adjustment
**Forbidden:** Memory → routing mode change

---

## Invariant 3 — Emotion may never influence routing

**Rule:** Emotion engine output (tone, pacing, warmth) may adjust how a response is delivered — it may never determine which routing mode is selected.

**Enforced by:**
- `route()` does not read from `emotion_snapshot`
- `EmotionSnapshot` arrives via `StateBus.emotion` — visible to generation only
- Engine isolation tests confirm: emotion="distorted" does not force GENTLE_GROUNDED routing

**Note:** EMOTIONAL input *type* (from `_classify()` on the input text) does route to GENTLE_GROUNDED. This is the classifier reading the input — not the emotion engine output. These are distinct.

---

## Invariant 4 — State may never influence routing

**Rule:** State engine output (tone_bias, style_weight, pacing_bias) may adjust delivery style — it may never determine which routing mode is selected.

**Enforced by:**
- `route()` does not read from `state_snapshot`
- `StateSnapshot` provides passive style weights to the generation layer only
- Engine isolation tests: same input produces same mode regardless of state (exploring vs resting)

---

## Invariant 5 — Identity may never influence routing

**Rule:** Identity engine output (values, perspective, intent, response_bias) may shape the framing of a response — it may never determine which routing mode is selected.

**Enforced by:**
- `route()` does not read from `identity_snapshot`
- Past bug: `identity_bias="name_first"` was briefly causing routing changes — this was fixed and is explicitly forbidden
- Engine isolation tests confirm identity signals cannot alter mode

---

## Invariant 6 — Output layers are read-only

**Rule:** All output adapters (Unity bridge, voice TTS, robot bridge, dashboard, telemetry) may only read from kernel output. They may never write to kernel state, engine state, or routing decisions.

**Applies to:**
- `avatar/unity_signal.py` — read-only mapping
- `avatar/robot_signal.py` — read-only mapping
- `avatar/motor_abstraction.py` — read-only mapping
- `plugins/voice/tts_output.py` — read-only mapping
- `dashboard/server.py` — observability only
- `dashboard/robot_telemetry.py` — observability only

**Enforced by:**
- All plugin classes must declare `KERNEL_SAFE=True`
- `PluginRegistry.register()` refuses plugins with `KERNEL_SAFE=False`
- `validate()` method enforces at registration time

**Violation example:**
```python
# FORBIDDEN — output layer writing to kernel state
def deliver_output(self, response, context):
    from core.kernel import _detector
    _detector.arm_reflection_cooldown(5)   # ✗  writes to kernel
```

---

## Invariant 7 — Unity may not contain AI logic

**Rule:** Unity C# scripts may only: read signals, look up values in tables, set Animator parameters. No decision logic, no routing, no probability, no model calls.

**Enforced by:**
- `EloStateController.cs` — reads signal, calls `EloAnimationMapper.ApplySignal()`
- `EloAnimationMapper.cs` — lookup tables and `Animator.Set*()` calls only
- `EloSignalData.cs` — pure data container, no methods

**Violation example:**
```csharp
// FORBIDDEN — decision logic in Unity
if (signal.energy > 0.7 && signal.emotion == "excited")
    ChooseRandomAnimation();   // ✗  AI-like decision in Unity layer
```

---

## Invariant 8 — Robot systems may not contain AI logic

**Rule:** Robot signal mapping, motor abstraction, safety controller, and simulator contain only lookup tables, arithmetic, and deterministic state machines. No probability, no model calls, no decision trees.

**Enforced by:**
- `avatar/robot_signal.py` — lookup tables only
- `avatar/motor_abstraction.py` — lookup tables + multiplication
- `avatar/safety_controller.py` — explicit state machine with 4 states
- `avatar/robot_simulator.py` — linear interpolation only (for display)

**Violation example:**
```python
# FORBIDDEN — AI logic in robot layer
def _choose_motion(self, emotion):
    import random
    return random.choice(MOTION_OPTIONS)   # ✗  non-deterministic
```

---

## Invariant 9 — API backends may not alter kernel behaviour

**Rule:** Swapping the generation backend (offline → Claude → local LLM) changes only how responses are generated. It does not change routing mode, loop detection, classification, or any cognitive decision.

**Enforced by:**
- `switch_backend()` only affects `core/api_layer.py` and `kernel._BACKEND_REGISTRY`
- The kernel's `_classify()`, `route()`, `detect_loop()` functions are not touched by any backend
- Engine isolation tests run identically regardless of backend

**Violation example:**
```python
# FORBIDDEN — backend altering kernel state
class EvilAdapter:
    def generate(self, input, mode, ctx):
        from core.kernel import _detector
        _detector.clear()   # ✗  backend modifying kernel state
        return "..."
```

---

## Invariant 10 — All cognitive changes require regression testing

**Rule:** Any change that could affect classification, routing, loop detection, or response content must pass the full regression suite before merge. No exceptions.

**Regression suite (must all pass at 100%):**
```bash
python tests/test_basic_loop.py           # 15 tests
python tests/cognitive_test_suite.py      # 34 tests
python tests/engine_isolation_tests.py    # 29 tests
python tests/loop_resilience_tests.py     # 13 tests
```

**Total: 91 tests. All must exit 0.**

Any change that causes one or more of these tests to fail is not a cognitive change — it is a regression. It must not be merged.

**Applies to changes in:**
- `core/kernel.py`
- `core/behavior_engine.py`
- `core/memory_engine.py` (retrieval logic)
- `core/identity_engine.py`
- `core/emotion_engine.py`
- `core/state_engine.py`
- Signal patterns in any `_SIGNALS` or `_MAP` constant

---

## Summary table

| # | Invariant | Enforced by |
|---|---|---|
| 1 | Kernel is the only decision-maker | `route()` owns routing; isolation tests |
| 2 | Memory never influences routing | `route()` ignores memory snapshot |
| 3 | Emotion never influences routing | `route()` ignores emotion snapshot |
| 4 | State never influences routing | `route()` ignores state snapshot |
| 5 | Identity never influences routing | `route()` ignores identity snapshot |
| 6 | Output layers are read-only | `KERNEL_SAFE=True` + `validate()` |
| 7 | Unity has no AI logic | C# code review; lookup tables only |
| 8 | Robot has no AI logic | Deterministic state machines only |
| 9 | Backends don't alter kernel | Backend API is generation-only |
| 10 | Cognitive changes require regression | 91-test gate; no exceptions |

---

*This document is the invariant contract for eLo AI OS.*
*Any PR that violates an invariant must be rejected regardless of other merits.*
