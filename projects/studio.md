# Project: eLo AI Studio

**Type**: ai_system
**Status**: active
**Namespace**: elo_ai_core

---

## What it is

The eLo AI Creative Personality Operating System — this repo.

A local, offline-first conversational intelligence system with:
- Deterministic behaviour engine (no model needed)
- Active memory influence (tone, themes, symbolic patterns)
- Project-aware response generation
- Modular backend (offline → Claude API → local LLM)
- Core Orb simulation layer
- Voice hooks (future)

---

## Architecture

```
main.py                  ← conversational CLI loop
core/
  core_engine.py         ← runtime orchestration
  behavior_engine.py     ← 5-phase response simulation
  memory_engine.py       ← persistent JSON store + influence signals
  project_engine.py      ← project registry management
  state_engine.py        ← conversational state tracking
identity/                ← permanent identity documents
plugins/                 ← swappable backends
memory/                  ← JSON data files
projects/                ← project context documents (this folder)
```

---

## Current status

- Offline simulation: working
- Memory influence: active (tone, returning themes, symbolic echoes, concept pairs)
- Grounding/imagination balance: calibrated
- Contradiction handling: hold-and-name approach
- Tests: 15/15 passing

---

## Next milestones

- [ ] Connect ANTHROPIC_API_KEY for live Claude responses
- [ ] Whisper STT integration
- [ ] pyttsx3 TTS integration
- [ ] NeoPixel hardware integration
- [ ] Web interface wrapper
