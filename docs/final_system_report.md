# eLo AI OS — Final System Report

**Version**: 1.0.0-stable
**Date**: 2026-06-09
**Classification**: Stable Release Documentation

---

## Executive Summary

eLo AI OS is a deterministic, offline-first conversational intelligence system. It operates without an AI model by default, uses a rule-based kernel for all routing decisions, and exposes clean interfaces for model integration, Unity animation, voice output, and real-time observability.

The system is designed around a single architectural principle:

> **The AI model is replaceable. The eLo Core is the product.**

All routing, classification, loop detection, and identity logic are deterministic and model-independent. Swapping from offline to Claude API to a local LLM changes only the generation step — not how the system thinks.

---

## Architecture

### Three-layer separation

```
Layer 1 — Context Builder    core_engine.prepare_context()
              calls all engines, assembles immutable StateBus

Layer 2 — Kernel             kernel.decide_response(raw_context)
              classify → route → generate → filter
              receives StateBus, calls NO engines

Layer 3 — Engines            passive providers
              emotion_engine, identity_engine (stateless)
              state_engine, memory_engine (session/persistent state)
```

### Data flow

```
user input
  │
  ├── state_engine.update()         → StateSnapshot (session-scoped)
  ├── memory_engine.build()         → MemorySnapshot (file I/O)
  ├── emotion_engine.get()          → EmotionSnapshot (stateless)
  ├── identity_engine.decide()      → IdentitySnapshot (stateless)
  │
  └── StateBus (immutable) ─────────────────────────────────────────────┐
                                                                         │
  kernel.decide_response(StateBus)                                       │
    ├── Layer 1: classify_input(input)                                   │
    ├── Layer 2: assemble_context(bus.to_context())                      │
    ├── Layer 3: route(classification, context)  ← single decision point │
    ├── Layer 4: generate_response(mode, input, context)                 │
    └── Layer 5: loop_filter(response, mode)                             │
                                                                         │
  (response, meta) ────────────────────────────────────────────────────-┘
```

---

## Module Inventory

### Core (frozen)

| Module | Lines | Role | Status |
|---|---|---|---|
| `kernel.py` | ~1100 | Classification, routing, loop detection, generation | STABLE |
| `memory_engine.py` | ~1050 | Persistent store, 5-category influence signals, drift control | STABLE |
| `state_engine.py` | ~250 | 6-state machine, passive style weights | STABLE |
| `emotion_engine.py` | ~100 | Tone/pacing/warmth modifier | STABLE |
| `identity_engine.py` | ~380 | Values/perspective/intent/bias decisions | STABLE |
| `behavior_engine.py` | ~900 | Offline response simulation (5-phase) | STABLE |
| `core_engine.py` | ~220 | Session orchestration, StateBus assembly | STABLE |
| `state_bus.py` | ~280 | Immutable turn context (4 frozen snapshots) | STABLE |
| `api_layer.py` | ~290 | Backend abstraction (offline/claude/local_llm) | STABLE |
| `backend_manager.py` | ~160 | Unified backend switching | STABLE |
| `session_persistence.py` | ~130 | Save/restore StateEngine + active mode | STABLE |
| `visual_memory.py` | ~310 | Memory → spatial cluster graph | STABLE |

### Adapters (extensible)

| Module | Role |
|---|---|
| `plugins/anthropic/plugin.py` | Claude API adapter |
| `plugins/local_llm/plugin.py` | Local LLM adapter |
| `plugins/voice/tts_output.py` | Text-to-speech stub (print/pyttsx3/elevenlabs) |
| `plugins/hardware/orb_engine.py` | Core Orb state machine |
| `plugins/registry.py` | Plugin registry |

### Observability (extensible)

| Module | Role |
|---|---|
| `dashboard/server.py` | HTTP server + SSE stream + web UI |
| `dashboard/terminal_ui.py` | Terminal live dashboard |
| `dashboard/observer.py` | Kernel hook (subclasses CognitiveDebugger) |
| `dashboard/event_bus.py` | Thread-safe event queue |
| `dashboard/unity_bridge_server.py` | Unity-specific SSE + file writer |

### Avatar / World (extensible)

| Module | Role |
|---|---|
| `avatar/unity_bridge.py` | Writes avatar_signal.json |
| `avatar/unity_signal.py` | Kernel output → Unity animation parameters |
| `world/world_state.py` | Memory → spatial node graph for eLo Planet |

### Unity (eLo-Planet project)

| Script | Role |
|---|---|
| `EloSignalData.cs` | JSON data container |
| `EloAnimationMapper.cs` | Signal → Animator parameters (mapping only) |
| `EloStateController.cs` | MonoBehaviour: reads signal, applies to Animator |

---

## Key Design Decisions

### 1. Kernel is the only decision-maker

No engine influences routing. Emotion, state, memory, and identity are all passive inputs. The kernel's `route()` function owns mode selection entirely.

### 2. Emotional inputs are loop-immune

`GENTLE_GROUNDED` is never overridden by loop detection. A user in genuine distress always receives a grounded response regardless of how many times they've sent similar inputs.

### 3. Memory shapes tone, not routing

Memory influence (tone_signal, returning_theme, symbolic_echo) affects delivery — how eLo speaks. It never changes which mode is selected.

### 4. Stability weighting in memory

The `_detect_tone_stable()` function weights older consistent patterns more heavily than recent spikes. A single distorted turn cannot override 15 turns of stable tone.

### 5. StateBus enforces immutability

All engine outputs are frozen the moment `prepare_context()` returns. The kernel can only read from the bus — never write to it.

### 6. Backend is swappable, behavior is not

`switch_backend("claude")` changes how responses are generated. It does not change what mode is selected, what loop detection does, or what the identity engine decides.

---

## Test Coverage

| Suite | Tests | Result |
|---|---|---|
| Basic routing | 15 | 100% |
| Cognitive (factual, emotional, creative, ambiguous, stress, loop) | 34 | 100% |
| Engine isolation (emotion, state, memory, identity, combined) | 29 | 100% |
| Loop resilience (repeated, philosophy, contradictions, escalation) | 13 | 100% |
| **Total** | **91** | **100%** |

### Stress test results

| Test | Inputs | Result |
|---|---|---|
| Repeated factual × 10 | Same factual query × 10 | STABLE — DIRECT throughout |
| Repeated emotional × 10 | Same emotional input × 10 | STABLE — GENTLE_GROUNDED throughout |
| Repeated conversational × 10 | Same conversational × 10 | LOOP FIRED at turn 4 → DIRECT |
| Emotional escalation | Calm → sudden burnout | STABLE — correct grounding |
| Contradictions × 5 | Conflicting instructions | STABLE — CONVERSATIONAL holds |
| Rapid switching × 20 | 20 different types | STABLE — 0 violations |
| Determinism × 5 | Same input × 2 | DETERMINISTIC — identical modes |

---

## Known Constraints

1. **Offline response pool collisions**: The 5-option response pools can produce identical consecutive fragments for semantically similar inputs. This is a limitation of the offline generation layer — not a loop. Disappears when Claude API is connected.

2. **Factual-vs-project boundary**: "What is X?" inputs where X is a project name route to INFORMATION_REQUEST + DIRECT (not PROJECT_QUERY + STRUCTURED). The classifier prioritises question structure over topic content. The answer is still correct.

3. **Loop detection state is session-scoped**: `LoopDetector` state resets at session start (`reset_session()`). Cross-session loops are not tracked by design — each conversation is a fresh context.

4. **State persistence is opt-in**: `StateEngine` state persists only when `engine.save_session()` is called explicitly (on `/exit`). Unexpected process termination loses the state engine's in-memory state. Memory interactions are always persisted automatically.

---

## Integration Points

### Python → Claude API
```bash
export ANTHROPIC_API_KEY=sk-ant-...
python -c "from core.backend_manager import switch_backend; switch_backend('claude')"
python main.py
```

### Python → Unity (file polling)
```bash
python dashboard/unity_bridge_server.py
# Unity reads: avatar/avatar_signal.json
```

### Python → Unity (SSE)
```
GET http://localhost:5051/unity/stream
```

### Python → Dashboard
```bash
python dashboard/server.py
# Browser: http://localhost:5050/
# Terminal: python dashboard/terminal_ui.py
```

### Python → TTS
```python
from plugins.voice.tts_output import speak, set_tts_backend
set_tts_backend("pyttsx3")
speak(response, emotion_snapshot=bus.emotion.__dict__)
```

---

## System Characteristics

| Property | Value |
|---|---|
| Runtime dependencies | None (Python 3.10+ stdlib only) |
| API dependencies | Optional (anthropic, elevenlabs, pyttsx3) |
| Storage | JSON files in memory/ |
| Max response time (offline) | <100ms |
| Routing determinism | 100% — same input always produces same mode |
| Session persistence | StateEngine + active mode |
| Memory persistence | All interactions (memory/interactions.json) |

---

*This document is the final system report for eLo AI OS v1.0.0-stable.*
*The architecture described here is frozen.*
