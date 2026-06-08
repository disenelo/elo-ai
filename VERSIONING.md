# eLo AI OS — Versioning System

---

## Version format

```
MAJOR.MINOR.PATCH
```

| Segment | Increments when |
|---|---|
| MAJOR | Kernel behaviour changes, routing logic changes, breaking API changes |
| MINOR | New modules, new adapters, new integrations (no kernel changes) |
| PATCH | Bug fixes, documentation, test additions, minor wiring corrections |

---

## Version history

### v0.1 — Prototype

**Theme:** Offline intelligence engine foundation.

Established:
- Deterministic offline response generation (5-phase pipeline)
- Basic memory storage and retrieval
- CLI conversational loop
- `You:` / `eLo:` format
- Mode switching (studio / companion / adventure)
- Project registry

---

### v0.2 — Stable kernel + debug layer

**Theme:** Architecture solidification and observability.

Established:
- Kernel as single decision pipeline (`decide_response()`)
- 6 routing modes (DIRECT, GENTLE_GROUNDED, CREATIVE, STRUCTURED, SIMPLIFY, CONVERSATIONAL)
- `LoopDetector` class (encapsulated, no module-level mutation)
- `StateBus` immutability (frozen dataclasses, MappingProxyType)
- `CognitiveDebugger` side-channel (zero response contamination)
- Engine isolation (emotion, state, memory, identity cannot influence routing)
- Cognitive test suite (34 tests)
- Engine isolation tests (29 tests)
- Loop resilience tests (13 tests)

---

### v0.3 — Unity + API integration

**Theme:** External system connectivity.

Established:
- `avatar/unity_signal.py` — kernel → Unity animation parameters
- `avatar/unity_bridge.py` — JSON file bridge
- `dashboard/unity_bridge_server.py` — real-time SSE Unity bridge
- Unity C# layer (`EloStateController`, `EloAnimationMapper`, `EloSignalData`)
- `core/api_layer.py` — backend abstraction (offline/claude/local_llm)
- `core/backend_manager.py` — unified backend switching
- `dashboard/server.py` — real-time SSE dashboard
- `dashboard/observer.py` — kernel hook (no source modification)

---

### v0.4 — Voice + persistence

**Theme:** Session continuity and audio layer.

Established:
- `plugins/voice/tts_output.py` — TTS stub (print/pyttsx3/elevenlabs)
- `core/session_persistence.py` — StateEngine save/restore
- `world/world_state.py` — persistent world node graph
- Auto-save on `/exit`, auto-restore on startup
- `memory/session_state.json` persistence format

---

### v1.0 — Stable release system

**Theme:** Architecture frozen, full test coverage, production ready.

Established:
- All 91 tests passing (100%)
- `RELEASE.md` — architecture lock declaration
- `docs/final_system_report.md` — full system record
- Stress test suite (stability confirmed)
- `VERSIONING.md` — this document

**Frozen at v1.0:**
- Kernel routing logic
- Engine roles
- StateBus immutability
- Loop detection rules
- Mode vocabulary

---

## Version rules

### PATCH increment (x.x.N)

Allowed:
- Bug fixes in adapters, dashboard, wiring layers
- New test cases
- Documentation updates
- New configuration options (config/ only)
- Dependency version updates

Not allowed in a patch:
- Any change to `core/kernel.py`
- Any change to routing priority or mode vocabulary
- Any new engine or cognitive rule

### MINOR increment (x.N.0)

Allowed:
- New adapter modules (plugins/, dashboard/, avatar/)
- New observability tools
- New Unity signals or voice backends
- New world graph features
- Test suite additions
- New public API in core/ that does not change existing behaviour

Not allowed in a minor:
- Kernel routing changes
- New cognitive rules (classification signals, loop detection rules)
- Changes to engine output schemas that break callers

### MAJOR increment (N.0.0)

Required for:
- Any change to `core/kernel.py` routing logic
- New classification types or routing modes
- Loop detection rule changes
- Changes to `StateBus` fields or immutability contract
- Changes to engine roles (e.g., state_engine starts affecting routing)
- Changes to `EloSignalData` schema that break Unity receivers
- Any change that causes existing tests to fail

A major version increment ALWAYS requires:
1. Full test suite pass (91+ tests)
2. `RELEASE.md` update with new frozen state
3. `CHANGELOG.md` entry with explicit "Breaking changes" section
4. `docs/final_system_report.md` update

---

## Change log format

```markdown
## [MAJOR.MINOR.PATCH] — YYYY-MM-DD

### Breaking changes
- (none) or explicit list of what breaks and migration path

### Added
- New module / feature description

### Changed
- What changed (must not affect routing or cognitive behaviour for PATCH/MINOR)

### Fixed
- Bug description

### Notes
- Context or rationale
```

---

## Breaking change rules

A change is **breaking** if any of the following are true:

1. Existing test(s) fail after the change
2. `route()` returns a different mode for any input that previously worked
3. `decide_response()` signature changes
4. `StateBus` fields are renamed, removed, or retyped
5. `EloSignalData` JSON schema changes incompatibly
6. `generate_response(mode, input, context)` interface changes
7. Any engine's output schema changes in a way that breaks existing callers
8. `kernel._BACKEND_REGISTRY` contract changes

**Breaking changes require MAJOR version increment. No exceptions.**

---

## Current version

See `VERSION` file.

```
cat VERSION
```
