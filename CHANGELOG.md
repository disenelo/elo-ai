# eLo AI OS — Change Log

Format: [MAJOR.MINOR.PATCH] — YYYY-MM-DD

---

## [1.0.0-stable] — 2026-06-10  ← FREEZE POINT

**STATUS: STABLE BASELINE — DO NOT MODIFY ARCHITECTURE**

Allowed from this point: bug fixes, stability improvements, prompt correction, output consistency fixes only.

### What this version is

Stable cognitive + emotional conversational system passing 95% protocol test and 21/21 quality tests.
Behavioural stability under repetition, emotion, and memory pressure is the goal — not intelligence expansion.

### Includes

- Living Presence spec (prompts/living_presence_spec.txt) — eLo identity, voice, relationship style
- 8-step cognitive cycle: state → memory → attention → executive → voice → generate → stability filter → output
- Attention layer (core/attention.py) — intent classification, memory scoring, emotional spectrum
- State machine (runtime/state_machine.py) — mode, loop counter, stability score, attention snapshot
- Executive function (runtime/executive.py) — response goal, cognitive load, tone selection
- Mock backend (backends/mock_backend.py) — 20+ pools, anti-repetition buffer, inquiry-first routing
- Memory persistence (memory/state_manager.py) — emotion, intent, loop counter persisted per turn
- Session anchor — meaning-based continuity summary written on /exit
- Memory pack (memory/memory_pack_builder.py) — high_priority field, vault + state merged
- Personality drift (memory/personality_drift.py) — slow clamped drift, stability lock
- Unity signal layer (unity/unity_signal.py) — emotion-to-motion, available in /debug mode
- Exit pool — identity-consistent closure messages, no software-like output
- Quality test suite (tests/test_conversation_quality.py) — 21 tests across 6 categories

### Protocol test results (v1.0-week1-final tag)

| Category   | Score | Status |
|---|---|---|
| Identity   | 3/3   | 100% PASS |
| Project    | 4/5   | 80% PASS  |
| Memory     | 3/3   | 100% PASS |
| System     | 4/4   | 100% PASS |
| Emotional  | 4/4   | 100% PASS |
| Fallback   | 1/1   | 100% PASS |
| **Overall**| **19/20** | **95% PASS** |

### Rollback

If instability appears: `git checkout v1.0-week1-final`
Safe minimal state: identity + emotion handling + session memory + basic response generation.

---

## [1.0.0] — 2026-06-09

### Breaking changes
- None (first stable release)

### Added
- `RELEASE.md` — architecture lock declaration
- `VERSION` — version file
- `VERSIONING.md` — versioning rules, version history, breaking change rules
- `CHANGELOG.md` — this file
- `docs/final_system_report.md` — complete system documentation
- `docs/proposed_repo_structure.md` — v2.0 migration target

### Frozen
- `core/kernel.py` routing logic
- Engine role definitions (emotion, state, memory, identity)
- `StateBus` immutability contract
- Loop detection rules (4 patterns)
- 6-mode vocabulary (DIRECT, GENTLE_GROUNDED, CREATIVE, STRUCTURED, SIMPLIFY, CONVERSATIONAL)

### Test coverage
- 91 tests passing (100%)

---

## [0.4.0] — 2026-06-09

### Breaking changes
- None

### Added
- `plugins/voice/tts_output.py` — TTS stub (print / pyttsx3 / elevenlabs)
- `core/session_persistence.py` — save / restore StateEngine + active mode
- `world/world_state.py` — persistent node graph for eLo Planet
- Auto-save on `/exit`, auto-restore on startup
- `memory/session_state.json` persistence format
- Session info: `CoreEngine.session_info()`

---

## [0.3.0] — 2026-06-09

### Breaking changes
- None

### Added
- `avatar/unity_signal.py` — kernel output → Unity animation parameters
- `avatar/unity_bridge.py` — JSON file bridge (file polling path)
- `dashboard/unity_bridge_server.py` — real-time SSE Unity bridge
- Unity C# (`EloStateController`, `EloAnimationMapper`, `EloSignalData`)
- `core/api_layer.py` — backend abstraction (offline / claude / local_llm)
- `core/backend_manager.py` — unified `switch_backend()` call
- `dashboard/server.py` — HTTP SSE server + web UI
- `dashboard/terminal_ui.py` — terminal live dashboard
- `dashboard/observer.py` — kernel hook (no source modification)
- `dashboard/event_bus.py` — thread-safe event queue
- `plugins/voice/plugin.py` — voice I/O hooks
- `plugins/anthropic/plugin.py` — Claude API adapter
- `plugins/local_llm/plugin.py` — Ollama / LM Studio adapter
- `core/cognitive_debugger` — `set_cognitive_debug()` parallel side channel
- `core/memory_engine` — memory drift control (`_detect_tone_stable`, `tone_confidence`, `tone_drift`)

---

## [0.2.0] — 2026-06-08

### Breaking changes
- None

### Added
- `core/kernel.py` — single decision pipeline (`decide_response()`, 5-layer)
- `core/state_bus.py` — immutable turn context (4 frozen snapshots)
- `core/state_engine.py` — `LoopDetector` class (encapsulated state)
- 6-mode routing (DIRECT, GENTLE_GROUNDED, CREATIVE, STRUCTURED, SIMPLIFY, CONVERSATIONAL)
- Loop detection (repeated_phrase, repeated_question, recursive_reflection, mode_stagnation)
- `set_cognitive_debug()` side-channel observability
- `core/emotion_engine.py` — tone modifier only
- `core/identity_engine.py` — values / perspective / intent / bias
- `core/avatar_bridge.py` — emotion + state → animation signal
- `core/visual_memory.py` — memory → spatial cluster graph
- `core/project_engine.py` — project registry management
- `tests/cognitive_test_suite.py` (34 tests)
- `tests/engine_isolation_tests.py` (29 tests)
- `tests/loop_resilience_tests.py` (13 tests)
- `ELO_BEHAVIOUR_SPEC.md` — canonical behaviour specification
- `identity/` — permanent identity documents
- `projects/` — project context documents

### Changed
- `state_engine` output narrowed to passive style weights only
  (removed: `response_length`, `imagination_level`, `project_focus`, `elo_voice_hint`)
- `emotion_engine` role narrowed to tone/pacing/warmth only
- `memory_engine` `tone_signal` now stability-weighted (older patterns resist recent spikes)

---

## [0.1.0] — 2026-06-07

### Breaking changes
- None (initial release)

### Added
- `core/behavior_engine.py` — 5-phase offline response simulation
- `core/memory_engine.py` — JSON persistent store + 5-category influence signals
- `core/core_engine.py` — session orchestrator
- `main.py` — CLI loop (`You:` / `eLo:` format)
- `plugins/hardware/orb_engine.py` — Core Orb state machine
- `config/system_prompt.txt` — eLo identity layer
- `config/personality.json` — modes, traits, universe entities
- `memory/project_registry.json` — 4 active project namespaces
- `tests/test_basic_loop.py` — 15 routing + behaviour tests
- `feel_test.py` — standalone behaviour test loop
- `TRACKER.md` — development roadmap
- `VISION.md` — long-term vision document
