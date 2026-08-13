# eLo OS — Architecture Audit
## Bible vs. Implementation Gap Report
**Version**: Auto-generated reference (update after each major build)
**Bible reference**: Architecture Bible Volumes I–XXII (David Charles, 2026)

---

## How to use this document

This is the briefing for the Architecture Agent. When starting a new architecture session:

> "Read ARCHITECTURE_AUDIT.md in ~/elo-ai/architecture/. That is the current gap between the eLo OS Architecture Bible and the live Python spine. Tell me what to build next in priority order, and what risks exist in the current implementation."

---

## Volume-by-volume implementation status

### Foundation (Volumes I–III)

| Volume | Title | Status | Notes |
|--------|-------|--------|-------|
| I | Philosophy | ✅ Exists | `prompts/living_presence_spec.txt` + `VISION.md` — One Brain, One Personality |
| II | Cognitive Principles | ✅ Exists | `architecture/17_cognitive_principles.md` |
| III | System Architecture | ✅ Exists | `architecture/16_runtime_contracts.md` — full loop documented |

### Brain (Volumes IV–VII)

| Volume | Title | Status | Notes |
|--------|-------|--------|-------|
| IV | Cognitive Spine | ✅ Live | `runtime/spine/spine.py` — Language, Memory, Relationship, Capability, Executive faculties in sequence |
| V | Faculty Contracts & Runtime APIs | ⚠️ Partial | `runtime/contracts.py` defines `CognitiveState`, `CognitivePlan`, `EmbodimentState`, `ExecutionReport`. **Gap**: Faculty lifecycle (boot/register/heartbeat/sleep) not implemented. Message bus envelope `{id, sender, receiver, priority, context, payload, confidence, expires, trace}` not enforced. |
| VI | Working Memory & Attention | ⚠️ Partial | `core/attention.py` computes attention model. Working memory lives in `_state` dict — not a typed object. Attention competition (novelty vs importance vs urgency) is implemented but not as explicit competing weights. |
| VII | Executive Cortex | ✅ Live | `runtime/executive.py` (FREEZE_V1_LOCK protected) + `runtime/spine/executive_faculty.py`. Produces one CognitivePlan per turn. |

### Learning (Volumes VIII–X)

| Volume | Title | Status | Notes |
|--------|-------|--------|-------|
| VIII | Memory Architecture | ⚠️ Partial | Semantic memory: vault system (489 records). Episodic: `memory/journal_router.py`. Procedural: `memory/personality_drift.py`. **Gaps**: Memory consolidation as a timed distinct faculty not implemented. Forgetting curve not implemented. Knowledge graph exists (`relationships/`) but not integrated into main memory retrieval. |
| IX | Dream Architecture | ✅ NEW — just built | `faculties/dream/dream_faculty.py` + `symbol_engine.py`. Symbol engine, narrative generation, journal, insight integration, Unity sleep signal. Hooks into ambient engine. **Gap**: No image generation pipeline (DeepDream / DALL-E) yet. No dream phases (REM/NREM equivalent). |
| X | Personality Engine | ⚠️ Partial | `self/elo_self_model.py` — mood, curiosity, satisfaction, inner events, session read, lifetime threads. `memory/personality_drift.py` — separate trait drift system. **Gap**: These two are not unified. Personality vectors (curiosity/patience/confidence/empathy etc.) are in self_model but not as explicit named dimensions with slow evolution. |

### Embodiment (Volumes XI–XIII)

| Volume | Title | Status | Notes |
|--------|-------|--------|-------|
| XI | Motor Cortex | ✅ Live | `avatar/` system — Unity bridge, animation router, motor abstraction, robot signal. `tools/computer_control_agent.py` — cursor/keyboard. |
| XII | Perception System | ⚠️ Partial | `plugins/vision/` + `tools/vision_agent.py` — screenshot + GPT-4o vision. `desktop/` — window/app context. `voice/stt.py` — Whisper STT. **Gap**: No unified Perception Faculty object. Raw observations go directly to attention rather than through a perception transform layer. |
| XIII | Presence Engine | ✅ Live | `presence/` system — scheduler, state, engine. `ambient/ambient_engine.py` — 2-4 min cycles. Idle behaviours, emotion, movement. Social timing and silence awareness in spec. |

### Expansion (Volumes XIV–XVI)

| Volume | Title | Status | Notes |
|--------|-------|--------|-------|
| XIV | Plugin Architecture | ✅ Live | `plugins/` — registry, base, voice, vision, hardware, anthropic, local_llm. Dynamic loading works. |
| XV | World Model | ⚠️ Partial | `world/world_state.py` — spatial node graph for Unity (not the cognitive world model). `relationships/world_graph.py` — concept graph. **Gap**: No unified World State object read by all faculties. The Bible's World State (Desktop, User, Unity, Browser, Files, Internet, Music, Calendar, Environment, Time, Weather) is fragmented across tools. |
| XVI | Multi-Agent Coordination | 🔴 Future | Not implemented. `tools/` agents are all called serially from server.py, not coordinated by an Executive. Single Executive exists. |

### Research (Volumes XVII–XIX)

| Volume | Title | Status | Notes |
|--------|-------|--------|-------|
| XVII | Reflection Engine | ⚠️ Partial | `memory/journal_router.py` routes significance. `continuity/continuity_engine.py` — session summaries. **Gap**: No daily/weekly/monthly journal structure. No formal lessons-learned or failure log. |
| XVIII | Self-Evolution | ⚠️ Partial | `self/elo_self_model.py` — self-state tracks eLo's own experience. Personality drift exists. **Gap**: No code review of own behaviour. No prompt optimisation loop. No performance measurement system. |
| XIX | Artificial Consciousness Research | 🔴 Future | Not implemented. No experimental framework. Research questions not formally documented. |

### Extensions (Volumes XX–XXII)

| Volume | Title | Status | Notes |
|--------|-------|--------|-------|
| XX | Cognitive Economy | 🔴 Future | No resource budgeting (API cost, latency, attention budget per turn). Every call is made without cost awareness. |
| XXI | Narrative Identity Engine | ⚠️ Partial | `continuity/identity_state.py` + `continuity/continuity_engine.py`. **Gap**: Not a continuous autobiographical thread — it's session-level summaries. No cross-project, cross-session story arc. |
| XXII | Faculty Genome | 🔴 Future | Faculties are not versioned, composable units with declared interfaces. The capability registry (`runtime/capabilities/registry.py`) is closest but covers tools, not cognitive faculties. |

---

## Critical Architecture Gaps (priority order)

### 1. Faculty Bus — HIGHEST PRIORITY
**Bible reference**: Volume V — the `{id, sender, receiver, priority, context, payload, confidence, expires, trace}` message envelope.
**Current state**: Faculties communicate via direct Python imports and free-form dicts. No message trace. No inter-faculty observability.
**Risk**: As faculties grow, debugging becomes impossible. Currently no way to know which faculty produced which part of the response.
**Fix**: Implement `core/faculty_bus.py` — a typed message envelope and routing layer all faculties pass through.

### 2. Unified World State — HIGH PRIORITY
**Bible reference**: Volume XV — one object all faculties read from.
**Current state**: World context is assembled ad-hoc in server.py from 12+ different sources. Some faculties re-query their sources directly instead of reading a shared state.
**Risk**: Race conditions, stale data, and inconsistent world models across faculties.
**Fix**: `world/live_world_state.py` — a typed object assembled once per turn from all sensors, read by all faculties.

### 3. Working Memory as typed object — HIGH PRIORITY
**Bible reference**: Volume VI — current task, goals, interruptions, attention weights.
**Current state**: `_state` dict in server.py. Untyped, mutable, shared.
**Risk**: Any faculty can write any key. No contract on what working memory contains.
**Fix**: Promote `runtime/contracts.py → CognitiveState` as the explicit Working Memory. Already designed, not fully used.

### 4. Memory Consolidation Faculty — MEDIUM PRIORITY
**Bible reference**: Volume VIII — runs periodically, asks what happened/changed/learned.
**Current state**: `memory/journal_router.py` routes significant turns. `continuity/` handles session end. No timed consolidation cycle.
**Fix**: Add a scheduled consolidation task (every 24 hours or on session close) that runs the full Bible consolidation pipeline.

### 5. Perception Faculty — MEDIUM PRIORITY
**Bible reference**: Volume XII — transforms raw observations into World State understanding.
**Current state**: `plugins/vision/` takes screenshots. `desktop/` reads window state. Both feed directly to attention, not through a perception transform.
**Fix**: `faculties/perception/perception_faculty.py` — assembles all sensor inputs into a unified PerceptionResult before attention.

### 6. Personality unification — MEDIUM PRIORITY
**Current state**: `self/elo_self_model.py` (mood/curiosity/satisfaction) and `memory/personality_drift.py` (trait drift) are separate systems that don't know about each other.
**Fix**: Merge into one Personality Faculty. Named trait vectors (curiosity, patience, confidence, empathy, discipline, wonder) with slow evolution rates.

### 7. Dream image generation — LOW PRIORITY (deferred)
**Bible reference**: Volume IX — DeepDream or image model as one renderer inside Dream Faculty.
**Current state**: Dream Faculty runs narrative generation. No image output.
**Fix**: Add image prompt generation in `dream_faculty.py`, route to `tools/image_gen_agent.py`.

---

## What the Architecture Agent should know about the live system

- **Entry point**: `server.py` (~2800 lines) is the spine. All faculties are called from here.
- **FREEZE_V1_LOCK**: `runtime/executive.py` is locked. Do not modify. Wrap, don't replace.
- **No Rigidbody**: Unity side uses CharacterController only. Permanent.
- **Language models**: GPT-4o-mini primary → Claude → Groq → Ollama → Mock.
- **State persistence**: `elo_state.json` (session), `self/elo_self_state.json` (eLo inner), `self/dream_journal.jsonl` (dreams).
- **Unity bridge**: `blender_bridge/state_writer.py` writes `blender/blender_state.json`. Unity reads this file.
- **Dream state signal**: `state.mode = "dreaming"` + `motion.animation = "sleep"` — Unity reads this for sleep animation.
- **South London register**: eLo OS detects and mirrors David's voice register (UK urban, patois). Don't strip this.

---

## Feedback loop instructions

After reading this document, an Architecture Agent should:

1. Pick the highest-priority gap.
2. Propose the exact file(s) to create or modify — with function signatures.
3. Identify any risks to existing FREEZE_V1_LOCK systems.
4. Specify what test would confirm the gap is closed.
5. Return a brief updated version of the relevant row in the table above.

David reviews the proposal. If approved, pass to Claude Code for implementation.
Claude Code updates this document after implementation.

---

*Last updated: 2026-07-26*
*Updated by: Claude Code (session b15c1e7a)*
