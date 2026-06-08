# eLo AI OS — Proposed Production Repository Structure

**Status**: Design document — migration target for v2.0
**Current**: Flat structure in elo-ai/ (v1.0.0-stable)

> This document describes a cleaner production structure.
> It does NOT refactor the current stable codebase.
> It is a target for a future migration, not an immediate task.

---

## Proposed structure

```
elo-ai/
│
├── core/                          ← COGNITION LAYER (frozen in v1.0)
│   ├── kernel.py                  decision pipeline (classify → route → generate)
│   ├── behavior_engine.py         offline response simulation
│   ├── memory_engine.py           persistent store + influence signals
│   ├── state_engine.py            conversational state machine
│   ├── emotion_engine.py          tone/pacing/warmth modifier
│   ├── identity_engine.py         values/perspective/intent/bias
│   ├── state_bus.py               immutable turn context
│   ├── core_engine.py             session orchestrator
│   ├── api_layer.py               backend abstraction
│   ├── backend_manager.py         unified backend switching
│   ├── session_persistence.py     save/restore engine state
│   └── visual_memory.py           memory → spatial cluster graph
│
├── interface/                     ← OUTPUT LAYER (extensible)
│   ├── unity/
│   │   ├── unity_signal.py        kernel output → Unity animation params
│   │   └── unity_bridge_server.py SSE bridge + file writer
│   ├── voice/
│   │   └── tts_output.py          text-to-speech (print/pyttsx3/elevenlabs)
│   └── api/
│       └── api_layer.py           (same as core/ — surfaced here for clarity)
│
├── dashboard/                     ← OBSERVABILITY LAYER (extensible)
│   ├── server.py                  HTTP + SSE server + web UI
│   ├── terminal_ui.py             terminal live dashboard
│   ├── observer.py                kernel hook
│   ├── event_bus.py               thread-safe event queue
│   └── unity_bridge_server.py     (also in interface/unity/ — deduplicate in v2)
│
├── world/                         ← SPATIAL LAYER (extensible)
│   └── world_state.py             memory → node graph for eLo Planet
│
├── plugins/                       ← BACKEND ADAPTERS (extensible)
│   ├── base.py                    PluginBase contract
│   ├── registry.py                plugin manager
│   ├── anthropic/plugin.py        Claude API
│   ├── local_llm/plugin.py        Ollama / LM Studio
│   ├── voice/plugin.py            STT/TTS hooks
│   ├── hardware/orb_engine.py     Core Orb state machine
│   └── vision/plugin.py           image understanding (future)
│
├── tests/                         ← VALIDATION
│   ├── test_basic_loop.py         15 routing tests
│   ├── cognitive_test_suite.py    34 cognitive tests
│   ├── engine_isolation_tests.py  29 isolation tests
│   ├── loop_resilience_tests.py   13 resilience tests
│   └── personality_tests.md       manual conversation log
│
├── config/                        ← CONFIGURATION (editable)
│   ├── system_prompt.txt          eLo identity layer
│   ├── personality.json           modes, traits, universe entities
│   └── behavior_rules.txt         runtime behaviour constraints
│
├── identity/                      ← REFERENCE DOCUMENTS
│   ├── elo_identity.md            permanent identity specification
│   ├── behavior_rules.md          behaviour rules explained
│   ├── communication_style.md     how eLo speaks
│   ├── universe_reference.md      entity definitions
│   └── voice_profile.md           future voice calibration spec
│
├── memory/                        ← RUNTIME DATA (gitignored except schema)
│   ├── project_registry.json      active project namespaces
│   ├── universe.json              eLo universe entity definitions
│   ├── user_profile.json          user creative patterns
│   ├── interactions.json          ← GITIGNORED (user conversations)
│   ├── session.json               ← GITIGNORED
│   ├── session_state.json         ← GITIGNORED
│   └── export_memory.md           ← GITIGNORED (generated snapshot)
│
├── projects/                      ← PROJECT CONTEXT
│   ├── elo_universe.md
│   ├── sugarcore.md
│   ├── orb_system.md
│   └── studio.md
│
├── docs/                          ← DOCUMENTATION
│   ├── avatar_architecture.md
│   ├── unity_connection.md
│   ├── system_audit_step11.md
│   ├── final_system_report.md     ← this release
│   └── proposed_repo_structure.md ← this file
│
├── main.py                        ← CLI entry point
├── feel_test.py                   behaviour test loop
├── RELEASE.md                     stable release declaration
├── TRACKER.md                     development roadmap
├── VISION.md                      long-term vision
├── ELO_BEHAVIOUR_SPEC.md          canonical behaviour specification
├── LLM_INTERFACE.py               legacy interface (superseded by api_layer)
├── pyproject.toml
├── requirements.txt
└── .gitignore
```

---

## Circular import prevention rules

```
core/       may NOT import from: interface/, dashboard/, world/, plugins/
interface/  may NOT import from: dashboard/, world/
dashboard/  may NOT import from: interface/, world/
world/      may NOT import from: interface/, dashboard/
plugins/    may NOT import from: dashboard/, world/

All layers may import from: core/
main.py may import from: all layers
```

---

## Duplication to resolve in v2.0

| Duplicated concern | Current locations | Resolution |
|---|---|---|
| `generate_response()` | `kernel.py`, `api_layer.py`, `LLM_INTERFACE.py` | Keep `api_layer.py`, remove others |
| Unity bridge | `dashboard/unity_bridge_server.py`, `avatar/unity_bridge.py` | Merge into `interface/unity/` |
| Entity definitions | `kernel.py`, `identity_engine.py`, `behavior_engine.py` | Single source in `identity/universe_reference.md` + parsed at boot |
| Classification signals | `kernel.py` (× 2 functions) | Single `classify_input()` |

---

*This document is a migration target, not an immediate action item.*
*No code changes in v1.0.0-stable.*
