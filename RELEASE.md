# eLo AI OS — Stable Release

**Version**: 1.0.0-stable
**Date**: 2026-06-09
**Status**: FROZEN — architecture locked

---

## Architecture Lock

This system is frozen at v1.0.0-stable.

The following architectural decisions are permanent and may NOT be modified without a version increment and full regression test pass:

### Locked: Core decision pipeline

```
input
  → classify_input()         core/kernel.py
  → assemble_context()       core/kernel.py
  → route()                  core/kernel.py
  → generate_response()      core/kernel.py + core/api_layer.py
  → loop_filter()            core/kernel.py
  → output
```

### Locked: Engine roles

| Engine | Role | May change |
|---|---|---|
| `kernel.py` | Classification, routing, loop detection, generation | FROZEN |
| `memory_engine.py` | Storage, retrieval, influence signals | FROZEN |
| `state_engine.py` | Passive style weights only | FROZEN |
| `emotion_engine.py` | Tone modifier only | FROZEN |
| `identity_engine.py` | Values/perspective/intent/bias | FROZEN |
| `behavior_engine.py` | Offline response simulation | FROZEN |
| `core_engine.py` | Session orchestration, context assembly | FROZEN |
| `state_bus.py` | Immutable turn context | FROZEN |

### Locked: Routing rules

- `DIRECT` — factual questions, loop detected (non-emotional)
- `GENTLE_GROUNDED` — emotional/distorted inputs (loop-immune)
- `CREATIVE` — imagination, entities (symbolic), world-building
- `STRUCTURED` — project queries, system/architecture language
- `SIMPLIFY` — short inputs, no strong signals
- `CONVERSATIONAL` — default, contradictions

Routing priority order is fixed:
1. Emotional/distorted → GENTLE_GROUNDED (never overridden)
2. Loop detected (non-emotional) → DIRECT
3. Type mapping (deterministic)

### Locked: Immutability guarantees

- `StateBus` — immutable after `prepare_context()` returns
- `IdentitySnapshot`, `StateSnapshot`, `EmotionSnapshot` — frozen dataclasses
- `MemorySnapshot` — MappingProxyType (read-only)
- `LoopDetector` — encapsulated, no external mutation

---

## Allowed after freeze

| Allowed | Not allowed |
|---|---|
| New adapters (plugins/, dashboard/, avatar/) | Routing logic changes |
| TTS/STT wiring | New cognitive rules |
| Unity signal mapping | Kernel modifications |
| Dashboard UI updates | Engine role expansion |
| New test cases | Behaviour engine changes |
| Documentation | Memory retrieval changes |
| Session persistence tweaks | Loop detection rule changes |
| World state graph additions | Identity/state/emotion role expansion |

---

## Module stability markers

All modules in `core/` are marked STABLE.
All modules in `plugins/`, `dashboard/`, `avatar/`, `world/` are EXTENSIBLE (adapters).

```
core/           STABLE     — frozen, no cognitive changes
plugins/        EXTENSIBLE — add backends, no kernel coupling
dashboard/      EXTENSIBLE — observability only
avatar/         EXTENSIBLE — translation only
world/          EXTENSIBLE — spatial graph, no AI logic
tests/          MAINTAINED — add test cases, no system changes
identity/       REFERENCE  — documentation, no runtime effect
```

---

## Regression gate

Before any change is accepted, all three test suites must pass at 100%:

```bash
python tests/test_basic_loop.py           # 15 tests
python tests/cognitive_test_suite.py      # 34 tests
python tests/engine_isolation_tests.py    # 29 tests
python tests/loop_resilience_tests.py     # 13 tests
```

Total: 91 tests, all must pass. No exceptions.

---

*This file is the architectural authority for eLo AI OS v1.0.0-stable.*
*Changes to this file require a version bump and maintainer sign-off.*
