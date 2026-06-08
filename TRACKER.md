# eLo AI OS — Development Tracker

**v1.0.0-stable** — Released 2026-06-09 — Architecture FROZEN

See `RELEASE.md` for the full architecture lock declaration.
See `docs/final_system_report.md` for the complete system report.

---

## Mission

The goal is **not** to build a chatbot.

The goal is to build eLo AI as a **persistent creative operating system** that can eventually exist as:

- a conversational AI
- a desktop companion
- a visual project organiser
- a game character
- a voice assistant
- a robot

All future development must support this vision.

---

## Golden Rule

> The AI model is replaceable.
> The eLo Core is the product.

Identity + Memory + Behavior + State must remain consistent whether eLo exists as text, desktop avatar, voice, game character, or robot.

---

## Quick start

```bash
python main.py                   # start conversation
python main.py --export-memory   # write memory snapshot
python main.py --orb-cli         # Core Orb simulator
python tests/test_basic_loop.py  # run tests (no API key needed)
python feel_test.py              # standalone behaviour test loop
```

Commands during conversation:
```
You: /mode studio        → building / planning mode
You: /mode companion     → reflection / conversation mode
You: /mode adventure     → world logic / storytelling mode
You: /project            → show active project registry
You: /export             → save memory snapshot mid-session
You: /debug              → toggle reasoning phase output
You: /exit               → save memory and quit
```

---

## Phase Roadmap

---

### Phase 1 — Foundation ✅ (complete)

**Goal:** Create a stable eLo Core.

Core components built:
- [x] Identity system (`identity/` — elo_identity.md, behavior_rules.md, communication_style.md, universe_reference.md, voice_profile.md)
- [x] Behavior engine — 5-phase offline reasoning (grounding, imagination, contradiction tolerance)
- [x] Memory engine — 5 typed categories (identity, project, creative, world, user), active influence signals
- [x] State engine — 6 states (focused, building, exploring, reflecting, playful, resting), natural transitions
- [x] Project registry — 4 active namespaces (disenelo_universe, sugarcore_arc, orb_device, elo_ai_core)
- [x] Offline conversation system — deterministic, no API required
- [x] Plugin architecture — base contract, registry, fallback chain
- [x] Avatar foundation — emotion_engine, avatar_bridge, visual_memory, dual-body architecture spec

**Before moving to Phase 2:**

- [ ] Complete `tests/personality_tests.md` — log responses, patterns, identity drift
- [ ] Run 20+ real conversation turns and evaluate against success criteria
- [ ] Confirm no excessive question loops
- [ ] Confirm grounding works on everyday inputs
- [ ] Confirm contradiction handling holds without forcing resolution

**Success criteria:**
- eLo feels conversational, not like a command tool
- eLo does not loop excessively
- eLo remembers relevant context across turns
- eLo feels consistent session to session
- eLo feels like eLo, not a generic assistant

---

### Phase 2 — Identity Stabilisation

**Goal:** Refine eLo's personality until it feels right.

Review questions:
- Is eLo too philosophical for everyday inputs?
- Is eLo playful enough, or too serious?
- Is eLo practical when the situation calls for it?
- Does imagination activate naturally, or feel forced?
- Does eLo feel like a companion, or an interface?

Work:
- [ ] Read through `tests/personality_tests.md` — identify patterns
- [ ] Review `identity/elo_identity.md` — does this match how eLo actually behaves?
- [ ] Review `identity/behavior_rules.md` — are any rules causing problems?
- [ ] Review `config/system_prompt.txt` — adjust tone if needed
- [ ] Review `config/behavior_rules.txt` — tighten or loosen as needed
- [ ] Run another 20+ turns, update personality tests

**Success criteria:**

Conversation feels balanced between:
- grounded (responds simply to simple inputs)
- imaginative (expands when the idea calls for it)
- reflective (holds space without rushing)
- practical (gives concrete next steps in studio mode)

---

### Phase 3 — State Engine Refinement

**Goal:** Replace any remaining manual mode switching with fully natural state transitions.

State engine is built. This phase is refinement:
- [ ] Test all 6 state transition paths in real conversation
- [ ] Verify hysteresis is correctly resisting jitter
- [ ] Verify forced transitions (resting on exhaustion signals)
- [ ] Map state → voice_profile pacing (for future voice layer)
- [ ] Confirm state behavioral hints affect response style noticeably

States → behavioral profiles:
| State | Tone | Length | Imagination | Project focus |
|---|---|---|---|---|
| exploring | curious, open | medium | high | open |
| building | grounded, action | medium | low | tight |
| focused | precise, direct | short | low | tight |
| reflecting | slow, spacious | short | medium | loose |
| playful | light, experimental | short | medium | loose |
| resting | minimal | short | low | open |

**Success criteria:** eLo naturally changes behavior based on context without being told to.

---

### Phase 4A — Unity Embodiment

**Goal:** Connect eLo Core to the Unity character. Same brain, first visual body.

```
Python eLo Core → avatar_signal.json → EloSignalReceiver.cs → EloAnimationMapper.cs → eLo Character
```

Communication: local JSON file — no networking, easy to debug.

Signal format:
```json
{ "state": "reflecting", "emotion": "gentle", "energy": 0.3, "intent": "hold_space",
  "animation_hints": {"head_tilt_deg": -2.4, "lean_amount": 0.0, "bounce_intensity": 0.0},
  "orb": {"intensity": 0.16, "mode": "dim_breathe"} }
```

- [x] `avatar/unity_bridge.py` — Python signal exporter
- [x] `avatar/signal_schema.json` — canonical JSON schema
- [x] `docs/unity_connection.md` — Unity C# setup guide + EloSignalReceiver.cs + EloAnimationMapper.cs
- [ ] Add `EloSignalReceiver.cs` to eLo-Planet Unity project
- [ ] Add `EloAnimationMapper.cs` to eLo-Planet Unity project
- [ ] Wire Animator parameters (Energy, HeadTilt, Lean, Bounce, state triggers)
- [ ] Enable bridge in core_engine (`UNITY_BRIDGE_ENABLED=1`)
- [ ] Test: Python state change → Unity character responds

**Success criteria:** eLo's internal state visibly changes the Unity character's behavior.

---

### Phase 4B — eLo's Planet (Memory World)

**Goal:** Create a persistent world for eLo. Memory becomes geography.

The memory world is already built in Python (`core/visual_memory.py`). Phase 4B brings it into Unity.

Architecture:
```
core/visual_memory.py → cluster world graph → Unity scene generator
                                             → Islands = concept clusters
                                             → Bridges = concept connections
                                             → eLo walks through his own memory
```

Projects become islands. Ideas become structures. Connections become bridges.

- [x] `core/visual_memory.py` — memory → spatial cluster world (terminal version)
- [ ] Export world data to JSON (`avatar/world_signal.json`)
- [ ] Unity WorldBuilder.cs — reads JSON, spawns island prefabs
- [ ] Connect project namespaces to island types
- [ ] eLo can walk between project islands
- [ ] Memory items visible as world objects (scrolls, nodes, etc.)

**Long-term vision:** eLo literally walks through your ideas inside eLo's Planet.

**Success criteria:** eLo can navigate project spaces visually inside Unity.

---

### Phase 4 — Desktop Avatar

**Goal:** Create eLo Desktop — animated character with state-driven presence.

Architecture:
```
eLo Core → {state, emotion, intent, energy} → Avatar Bridge → Desktop Renderer
```

eLo has no eyes. Expression comes from:
- head tilt — curiosity, listening
- lean — interest (forward), withdrawal (back)
- bounce / pulse — excitement, aliveness
- stillness — focus, resting
- orb glow — emotion type + energy level
- movement speed — energy

Work:
- [ ] `avatar/terminal.py` — ASCII renderer (test full pipeline, no GUI needed)
- [ ] `avatar/canvas_2d.py` — tkinter 2D desktop renderer
- [ ] Idle animation loop (eLo present even when not responding)
- [ ] State-driven animation selection
- [ ] Integration with `core_engine.py` — signal on every turn

Foundation already built:
- [x] `core/emotion_engine.py` — state + input → {emotion, intent, energy, posture, pace}
- [x] `core/avatar_bridge.py` — packages signals for any embodiment layer
- [x] `docs/avatar_architecture.md` — full dual-body architecture spec

**Success criteria:** eLo feels present on the desktop. Body responds to what the brain is doing.

---

### Phase 5 — Visual Project World

**Goal:** Transform project memory into a navigable visual world.

Projects become islands. Ideas become structures. Connections become bridges.

```
eLo: "You have 17 Sugarcore notes.
      Grouped: Story (7)  ·  Enemy Design (4)  ·  Levels (3)  ·  Dialogue (2)  ·  Future (1)"
```

Then visually: floating islands, connected by bridges, representing idea relationships — not folders.

Work:
- [x] `core/visual_memory.py` — memory → cluster world graph (terminal version works)
- [ ] `avatar/canvas_2d.py` — render world as 2D canvas (islands, bridges, labels)
- [ ] `/map` command in CLI — render current project memory as visual world
- [ ] Cluster navigation (click island → see items)
- [ ] Connection weight visualisation (thicker bridge = stronger concept link)

**Success criteria:** Projects are navigated visually. eLo can organise and present ideas spatially.

---

## Future Phases

### Voice Layer

- Driven by `core/emotion_engine.py` + `identity/voice_profile.md`
- Voice calibration: pacing, emotional cadence, pause placement
- STT: Whisper local or Deepgram API
- TTS: pyttsx3 local or ElevenLabs API
- Voice must be driven by eLo Core — not the other way around

### Local Intelligence Layer

- Offline simulation: working now
- Local LLM: Ollama / LM Studio via `plugins/local_llm/plugin.py`
- Anthropic API: `plugins/anthropic/plugin.py` (set `ANTHROPIC_API_KEY`)
- Behavior and identity unchanged regardless of model

### Robot Embodiment

eLo Core → Robot Body (same architecture as desktop avatar, different renderer)
- Raspberry Pi 5 brain
- NeoPixel orb — driven by `plugins/hardware/plugin.py`
- Servo cable-tension skeleton
- Omni-wheel base
- Voice I/O

The robot is an embodiment of eLo, not a separate system.

---

## Architecture reference

```
elo-ai/
│
├── main.py                      ← CLI entry point
│
├── core/
│   ├── behavior_engine.py       ← 5-phase offline response simulation
│   ├── memory_engine.py         ← 5-category store + active influence signals
│   ├── core_engine.py           ← runtime orchestration
│   ├── state_engine.py          ← 6 states, natural transitions
│   ├── emotion_engine.py        ← state → emotion + intent + energy
│   ├── avatar_bridge.py         ← packages signals for any embodiment layer
│   ├── visual_memory.py         ← memory → spatial cluster world
│   └── project_engine.py        ← project registry management
│
├── identity/                    ← permanent identity documents
│   ├── elo_identity.md
│   ├── behavior_rules.md
│   ├── communication_style.md
│   ├── universe_reference.md
│   └── voice_profile.md
│
├── plugins/
│   ├── base.py                  ← PluginBase contract
│   ├── registry.py              ← plugin manager + fallback chain
│   ├── anthropic/plugin.py      ← Claude API
│   ├── local_llm/plugin.py      ← Ollama / local model
│   ├── voice/plugin.py          ← STT + TTS hooks
│   ├── hardware/plugin.py       ← Orb + sensors
│   └── vision/plugin.py         ← image understanding (future)
│
├── projects/                    ← project context docs
├── docs/                        ← architecture docs
├── config/                      ← system_prompt.txt, personality.json, behavior_rules.txt
├── memory/                      ← JSON data files
└── tests/
    ├── test_basic_loop.py       ← 15 automated tests
    └── personality_tests.md     ← manual conversation log
```

---

## Known constraints

- Deterministic selection: same input always produces same offline response
- Memory influence activates after 3+ interactions — cold sessions use defaults
- `concept_pairs` requires 2+ co-occurrences to register an association
- Offline responses are structured — connect Claude API for open-ended output
- State transitions require 2 consecutive signals (hysteresis) — single words don't trigger

---

*Last updated: 2026-06-08*
