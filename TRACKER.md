# eLo AI OS — Development Tracker

**Project path**: `~/eLo-Planet/` (git repo) · `~/elo-ai/` (AI OS source)
**Last updated**: 2026-06-15 (session 9)
**Current version**: 1.0.0 · Architecture frozen (see `RELEASE.md`)

---

## §1 Mission

Build eLo AI as a **persistent creative operating system** — not a chatbot, not an assistant.

eLo exists to help a human think, create, remember, build, and stay connected to what matters.
It answers directly, celebrates progress, builds on ideas, connects concepts, and grounds emotional distress.
It acts as a companion, not a mirror. It has its own perspective.

> **The model is replaceable. eLo is not.**

---

## §2 Status Snapshot

| Layer | Component | Status | Notes |
|---|---|---|---|
| **Runtime** | Attention (intent/valence/momentum) | ✅ | Core/attention.py — 5 intent types, 5 valence states, 4 momentum states |
| **Runtime** | Executive (CAL — 9 actions) | ✅ | Priority routing: short affirm → build → connect → answer → celebrate → ground → witness → silence |
| **Runtime** | Prompt builder | ✅ | Living Presence Spec + action directive + graph context injection |
| **Runtime** | Backend router | ✅ | OpenAI → Gemini → Claude → Groq → Ollama → Mock; lore-drift + duplicate guards (2026-06-22) |
| **Runtime** | State machine | ✅ | Session state tracking |
| **Backends** | Mock | ✅ | Singleton, anti-repetition buffer, 30+ pools, CAL-action routing |
| **Backends** | Groq | ⚠️ | Working · 8b-instant active (quota) · needs 70b when quota resets |
| **Backends** | Claude | ✅ | claude-sonnet-4-5 configured, auto-priority in router |
| **Backends** | Ollama | ✅ | Local fallback, mistral default |
| **Knowledge** | World graph | ✅ | 17 entities, 15 relationships, 16 concepts |
| **Knowledge** | Viewpoints | ✅ | 50 viewpoints (creativity, overwhelm, identity, etc.) |
| **Knowledge** | Graph loader | ✅ | Builds context for prompt injection |
| **Memory** | Session persistence | ⚠️ | Built (session.json, memory_pack) · needs cross-session continuity validated |
| **Memory** | Project registry | ✅ | Built · active projects force-HIGH in attention layer (2026-06-12) |
| **Memory** | Personality drift | ✅ | Built · 0.2–0.9 stability clamp |
| **Prompts** | Living Presence Spec | ✅ | Externalized to prompts/living_presence_spec.txt |
| **Conversation quality** | Pitch / building momentum | ✅ | 100% — 15/15 batch4 pass (2026-06-12, confirmed) |
| **Conversation quality** | Bad day / distress | ✅ | 12/12 Batch 1 pass (2026-06-12, session 4) — all planetary shadows wired |
| **Conversation quality** | Good day / positive | ✅ | Passes |
| **Conversation quality** | Factual / system | ✅ | Mock pools handle well |
| **Voice** | STT + TTS | 🔴 | plugin/voice/ scaffolded, not wired into main.py |
| **Avatar** | Core runtime | ✅ | avatar_state/presence_engine/motion_mapper/animation_router + behaviour_protocol — all wired into main.py (2026-06-13) |
| **Avatar** | Blender simulation | ✅ | blender_bridge/avatar_driver/state_visualiser — standalone runner working, end-to-end tested 3/3 (2026-06-13) |
| **Relationship** | Pattern observer | ✅ | core/pattern_observer.py — tracks topic/tone per turn, surfaces contrast + recurring observations (Phase A, 2026-06-13) |
| **Continuity** | World graph | ✅ | identity/world_graph.json — seeded entities + why they matter (Phase B, 2026-06-13) |
| **Continuity** | Viewpoints | ✅ | identity/viewpoints.json — eLo's synthesised perspectives (Phase B, 2026-06-13) |
| **Continuity** | Identity map | ✅ | identity/identity_map.json — pattern accumulation across sessions (Phase B, 2026-06-13) |
| **Continuity** | Continuity engine | ✅ | core/continuity.py — get_viewpoint/entity_why/cross_session_delta/update_from_session (Phase B, 2026-06-13) |
| **Avatar** | Core runtime | ✅ | avatar_state/presence_engine/motion_mapper/animation_router + behaviour_protocol — wired into main.py (Phase C, 2026-06-13) |
| **Avatar** | Blender simulation | ✅ | blender_bridge/avatar_driver/state_visualiser — standalone runner 3/3 pass (Phase D, 2026-06-13) |
| **Avatar** | Desktop context | ✅ | desktop/window_watcher.py + context_detector.py — app observation, no control (Phase E, 2026-06-13) |
| **Avatar** | Desktop renderer | ✅ | desktop_avatar/avatar_renderer.py — tkinter window, 8 motions, no eyes (Phase F, 2026-06-13) |
| **Avatar** | Movement controller | ✅ | desktop_avatar/movement_controller.py — presence → motion mapping (Phase F, 2026-06-13) |
| **Avatar** | Milestone launch | ✅ | desktop_avatar/launch.py — DESKTOP_AVATAR=1 python main.py → appears, looks around, says welcome, walks to corner (Phase F, 2026-06-13) |
| **Avatar** | Unity signal bridge (game) | ⚠️ | EloStateController + EloAnimationMapper + EloSignalData in eLo-Planet — reads avatar_signal.json · needs wiring to eLo character in scene |
| **Avatar** | Unity Desktop Avatar scripts | ✅ | EloOSAvatarReceiver.cs + DesktopBuddy.cs built (2026-06-15) · reads blender_state.json · drop-in for blender_receiver.py · alias table mirrors animation_driver.py |
| **Avatar** | Unity Desktop Avatar project | ✅ | Separate Unity project · build running · eLo on desktop parked bottom-right, transparent, animating · eLo OS main.py as subprocess · state file flowing → moods drive animation · dark chat panel bottom-left + speech bubble at c_head.x · click-and-drag to reposition · MILESTONE 2026-06-16 |
| **Avatar** | Robot signal | 🔴 | Spec ready · no physical build yet |
| **Backends** | OpenAI GPT-4o-mini | ✅ | Primary in auto + cloud modes via _openai_call() — httpx, OPENAI_API_KEY (2026-06-22) |
| **Backends** | Semantic memory (embeddings) | ✅ | memory/embedding_store.py — warm() at startup, search() boosts attention scoring ×5 (2026-06-22) |
| **Voice** | OpenAI TTS (shimmer) | ✅ | voice/voice_engine.py — tts-1-hd, afplay, phoneme lipsync pipeline (2026-06-22) |
| **Voice** | ElevenLabs API keyed | ⚠️ | Key in .env + backup · voice ID not yet selected · voice_engine not yet wired to EL |
| **Voice** | is_speaking() | ✅ | voice_engine.py — public bool for ambient/wander suppression |
| **Ambient** | Ambient engine | ✅ | ambient/ambient_engine.py — startup greeting, idle utterances (8-20min), random smiles (2-5min), animation wanders (3-8min), unity_events.json polling (2026-06-22) |
| **Server** | Parent death detection | ✅ | server.py _watch_parent() — kills server within 2s of parent process dying (2026-06-22) |
| **Expression** | Expression values boosted | ✅ | expression_mapper.py — 2-3× boost on all modes, intensity floor 0.6, THINKING/RESTING → calm clip, extended action bonuses (2026-06-22) |
| **Backends** | Gemini Flash | ⚠️ | _gemini_call() wired — GOOGLE_API_KEY needed to activate (free: aistudio.google.com) |
| **Tools** | Tool agent router | ✅ | tools/tool_router.py — time, weather, wikipedia, calculator (all free, no key). Injects CONTEXT prefix, kernel unchanged (2026-06-22) |
| **Tools** | Keyword motion system | ✅ | tools/keyword_motion.py — keyword→animation burst, async, non-blocking. 7 emotions mapped (2026-06-22) |
| **Tools** | System agent (macOS) | ✅ | tools/system_agent.py — window/app/folder/file control via AppleScript + Python. All actions execute immediately (2026-06-22) |
| **Tools** | Head gesture system | ✅ | blender_state.json head_motion key — nod/shake/tilt/think/lookup via c_head.x/z. No NLA clips — Unity coroutine only (2026-06-22) |
| **Tools** | Weather location priority | ✅ | Explicit→session→ELO_LOCATION env→IP auto. "I'm in London" sets session default (2026-06-22) |
| **Tools** | Follow-up continuity | ✅ | "what about in London?" re-runs last agent with new subject. _last_agent/_last_arg tracking (2026-06-22) |
| **Tools** | File operations | ✅ | system_agent.py cp/mv/rename/delete (Trash) — executes immediately, no confirmation (2026-06-22) |
| **Tools** | DuckDuckGo search | ✅ | _agent_duckduckgo() — Instant Answers API, free, no key. DDG→Wikipedia fallback chain (2026-06-22) |
| **Tools** | Translation agent | ✅ | _agent_translate() — Gemini 2.0 primary, OpenAI fallback. Extracts text+lang from natural language (2026-06-22) |
| **Tools** | News RSS | ✅ | _agent_news() — BBC News, BBC Science, Hacker News. Intent-routed, no key (2026-06-22) |
| **Tools** | Obsidian on-demand search | ✅ | _agent_obsidian() — keyword search internal vault + ELO_VAULT_PATH for real vault. Handles K-7 style terms (2026-06-22) |
| **Backends** | Gemini model | ✅ | Updated default gemini-1.5-flash → gemini-2.0-flash across router + tool_router (2026-06-22) |
| **Identity** | Multilingual greetings | ✅ | 17-language greeting pool. eLo tries foreign, catches himself. Greeting event signals Unity wave (2026-06-22) |
| **Identity** | Identity direct pool | ✅ | "Are you eLo?" bypasses LLM — warm response pool, no awkward negation (2026-06-22) |
| **Ambient** | Meditation state machine | ✅ | enter_meditation()/exit_meditation() — Enter→Loop→Exit phases, deliberate only. Wander never fires calm (2026-06-22) |
| **Ambient** | Ambient utterances expanded | ✅ | 35-line pool: quiet presence + encouragement + quirky/playful (2026-06-22) |
| **Runtime** | Intent model routing | ✅ | "ask Claude to..." / "translate..." detected → routes directly to Claude/Gemini override. backend_router.py (2026-06-22) |
| **Mobile** | iOS shadow vision | ⚠️ | Defined — Mac=full eLo, iPhone=shadow (Dynamic Island orb + Lock Screen + widget). Unity iOS build + hosted server.py needed. |
| **Mobile** | Dynamic Island orb | ⚠️ | Designed — colour language: idle=teal, listening=white, thinking=amber, speaking=coral, calm=violet. Syncs from blender_state.json state.mode. |
| **Robot** | NeoPixel ↔ OS sync | ⚠️ | Designed — same blender_state.json state.mode drives NeoPixel colours on Pi. Colour map matches Dynamic Island. |
| **Integration** | File/Obsidian reading | 🔴 | memory/obsidian_loader.py exists · not active in main loop |
| **Integration** | Proactive memory surfacing | ✅ | core/pattern_observer.py fires observations in session (Phase A) · cross-session in identity_map.json (Phase B) |
| **Integration** | Multi-project context | 🔴 | project_engine.py exists · not cross-loaded at session start |
| **Meaning memory** | Continuity layer | ✅ | continuity/ — IdentityState, engine, summary. Startup: "Welcome back. Last time we were moving toward…" (2026-06-15) |
| **Meaning memory** | Relationship layer | ✅ | relationships/ — WorldGraph/ConceptGraph/ViewpointGraph + RelationshipEngine. Max 1+1+1 injection per turn (2026-06-15) |
| **Presence** | Presence runtime | ✅ | presence/ — PresenceMode (7 modes), PresenceState, engine (CAL→mode), scheduler (transitions + post-settle) (2026-06-15) |
| **Presence** | Avatar controller | ✅ | avatar/avatar_controller.py + avatar_rules.py — PresenceState → clip/speed/intensity; CELEBRATE hold, energy floor guards (2026-06-15) |
| **Presence** | Avatar runtime | ✅ | avatar_runtime/ — AvatarRuntimeState, AnimationBrain (min-hold 1.5s, energy gate), TransitionEngine (cross-fade) (2026-06-15) |
| **Expression** | Expression mapper | ✅ | expression/ — real shape key names from eLo-BodyxHead w/Mouth file; mode+action → shape key blend dict + head_lean (2026-06-15) |
| **Expression** | Micro expressions | ⚠️ | expression/micro_expression.py built · not yet inserted between turns in main.py |
| **Blender bridge** | State writer | ✅ | blender_bridge/state_writer.py — atomic write: motion + expression{shape_keys, head_lean} + state + _ts (2026-06-15) |
| **Blender bridge** | Blender receiver | ✅ | blender_bridge/blender_receiver.py — Blender timer script; NLA strips + shape keys + c_head.x bone; hardened against hangs (2026-06-15) |
| **Blender bridge** | Animation driver | ✅ | blender_bridge/animation_driver.py — NLA command resolver; KNOWN_CLIPS + aliases (2026-06-15) |
| **Presence playback** | Idle timeline | ✅ | presence_playback/ — 2-minute scripted 16-entry choreography; `python -m presence_playback.playback --continuous` drives Blender with no conversation (2026-06-15) |
| **Desktop shadow** | Window observer | ✅ | desktop/window_state.py + desktop_presence.py — reads frontmost app, injects "You're in Blender right now." into prompt (macOS, graceful fallback) (2026-06-15) |
| **Voice** | Phoneme → viseme map | ⚠️ | plugins/voice/voice_engine.py — full phoneme→shape key map using real eLo keys · speak() + text_to_phonemes() stubbed, not active (2026-06-15) |
| **Robot** | Body signal | ⚠️ | plugins/hardware/robot_body.py — PresenceMode → NeoPixel glow + head servo degrees · hardware hooks stubbed for RPi phase (2026-06-15) |
| **Architecture** | eLo OS / game separation | ✅ | eLo OS (`~/elo-ai/`) is standalone. Not part of eLo-Planet game. Integration is a future phase. Confirmed 2026-06-15. |

---

## §3 What eLo OS AI needs to be a Core OS for Creating

This is the honest gap map — what's built vs what creates the "OS" feeling.

### Tier 1 — Foundation (must work first)

These are the things that, if broken, mean eLo isn't actually an OS yet.

| Need | Current state | What's required |
|---|---|---|
| Conversation quality ≥ 80% on all emotional contexts | ✅ 100% pitch batch · passing factual/good-day | Batch 4: 15/15 confirmed 2026-06-12. Bad-day batch still to run. |
| Session memory that actually persists | ⚠️ Unknown | Run two sessions back-to-back. Does eLo say "last time we were working on the pitch"? If not — session persistence is broken. |
| Project registry surfaces in responses | ✅ Done | `attn.compute()` now force-appends `memory_pack["high_priority"]` (incl. all 4 active projects) to HIGH bucket. Dedup vs medium/low prevents duplication. Verified 2026-06-12. |
| Groq back to 70b | ⚠️ On 8b-instant | `ELO_GROQ_MODEL=llama-3.3-70b-versatile` in .env when daily quota resets |

### Tier 2 — Creates the OS feeling (next 2-4 weeks)

These are the things that make eLo feel like it actually knows you.

| Need | Why it matters | What to build |
|---|---|---|
| Obsidian / file reading | eLo can reference your actual notes, decisions, project files | Wire `memory/obsidian_loader.py` into session start — inject relevant notes into memory_pack |
| Proactive memory surfacing | "You keep coming back to this" / "you haven't opened that project in 3 days" | Post-response hook: compare current topic to long_term memory, surface pattern if confidence > threshold |
| Cross-project context at session start | eLo knows about all active DISENELO projects, not just what you tell it | Load `project_registry.json` + active trackers at startup, inject into memory_pack HIGH relevance |
| Honest answer to "what am I working on?" | Core OS capability — should work out of the box | Surface `project_engine.py` data through attention + respond via ANSWER action |

### Tier 3 — Embodiment (1-3 months)

These are the things that give eLo a body in different spaces.

| Need | Why it matters | What to build |
|---|---|---|
| Voice (STT + TTS) | You talk to eLo while you're working, not just when sitting at keyboard | Wire `plugins/voice/plugin.py` into `main.py` — Whisper for STT, pyttsx3 local or ElevenLabs for TTS |
| Desktop avatar (simple) | eLo feels present, not just a terminal | ASCII renderer first (`avatar/terminal.py`) → tkinter 2D canvas second |
| Unity signal bridge | eLo's internal state drives eLo-Planet character animations | Add `EloSignalReceiver.cs` + `EloAnimationMapper.cs` to eLo-Planet, enable `UNITY_BRIDGE_ENABLED=1` |

### Tier 4 — Full OS vision (3-6 months)

These are the things that make eLo genuinely different from anything else.

| Need | Why it matters | What to build |
|---|---|---|
| Visual memory world (Unity) | Projects become islands, ideas become structures, eLo navigates its own memory | Export `core/visual_memory.py` → `world_signal.json` → Unity WorldBuilder.cs |
| Proactive presence (file monitor) | eLo notices when you haven't opened a project, surfaces it without being asked | macOS FSEvents watcher on project folders → trigger low-energy nudge |
| Robot embodiment | The physical eLo — same brain, physical body | Raspberry Pi 5 + `plugins/hardware/plugin.py` + NeoPixel orb |
| Multi-modal (image input) | eLo can see what you're building — screenshots, sketches | `plugins/vision/plugin.py` → Claude Vision API |

---

## §4 Current Architecture

### Runtime cognitive cycle (main.py)

```
User input
    → core/attention.py          (intent + valence + momentum → attention_model)
    → runtime/executive.py       (CAL → action + tone + max_sentences)
    → knowledge/graph_loader.py  (entity + viewpoint context for prompt)
    → runtime/prompt_builder.py  (system prompt: spec + memory + graph + directive)
    → runtime/backend_router.py  (Claude → Groq → Ollama → Mock, with guards)
    → normalise()                (strip preambles, cap sentences, strip trailing questions)
    → output
```

### Conversation Action Layer (CAL)

9 actions in priority order:

| Action | Trigger | Voice tone |
|---|---|---|
| CELEBRATE | Short affirm (< 35 chars) OR positive_high valence | JOYFUL (1 sentence) |
| BUILD | Explicit build phrase OR creative + positive | JOYFUL |
| CONNECT | Explicit connect phrase | CHILDLIKE-WISE |
| ANSWER | Interrogative sentence + inquiry/recall intent | DIRECT |
| REFLECT | Emotional + neutral valence | CHILDLIKE-WISE |
| GROUND | Negative valence OR overwhelm/distress | SILENCE-AWARE |
| CHALLENGE | Stuck assumption | WITTY |
| WITNESS | Personal emotional share | SILENCE-AWARE |
| SILENCE | No meaningful addition | SILENCE-AWARE |

### Backend routing (auto mode)

```
If Claude key present → Claude first
If Groq key present:
    len(input) < 30 chars → Mock (short inputs misparse)
    action in (build, celebrate) AND len < 60 → Mock (8b model breaks on short insights)
    Else → Groq, then:
        lore-drift detected → Mock
        trailing question on build/celebrate → strip or fallback to Mock
        duplicate (> 0.75 word overlap) → Mock
If Ollama running → Ollama
→ Mock singleton (anti-repetition buffer persists full session)
```

### File layout (v2 runtime, as of 2026-06)

```
elo-ai/
├── main.py                          ← CLI entry point
├── runtime/
│   ├── backend_router.py            ← routing layer + guards + mock singleton
│   ├── executive.py                 ← CAL (9 actions) + tone + max_sentences
│   ├── prompt_builder.py            ← system prompt assembler
│   └── state_machine.py             ← session state
├── core/
│   ├── attention.py                 ← intent/valence/momentum detection
│   ├── memory_engine.py             ← 5-category memory store
│   ├── state_engine.py              ← 6 states + natural transitions
│   └── ...
├── backends/
│   ├── mock_backend.py              ← deterministic pools, CAL-action routing
│   ├── groq_backend.py
│   ├── claude_backend.py
│   └── ollama_backend.py
├── knowledge/
│   ├── graph_loader.py              ← builds graph context for prompt
│   └── viewpoints.json              ← 50 viewpoints
├── relationships/
│   ├── world_graph.json             ← 17 entities, 15 relationships
│   └── concepts.json                ← 16 concept nodes
├── prompts/
│   └── living_presence_spec.txt     ← externalized eLo persona spec
├── memory/
│   ├── session.json                 ← current session state
│   ├── memory_pack.json             ← active memory for prompt injection
│   └── ...
├── avatar/
│   ├── unity_bridge.py              ← Python signal exporter
│   └── signal_schema.json           ← canonical signal format
└── plugins/
    ├── voice/                       ← STT/TTS (scaffolded, not active)
    ├── hardware/                    ← Orb + sensors (scaffolded)
    └── vision/                      ← Image input (scaffolded)
```

---

## §5 Batch Quality Scores

Testing methodology: scored conversations against target emotional contexts.
Pass threshold: response fits the action, no character breaks, no unwanted questions.

| Batch | Description | Best score | Notes |
|---|---|---|---|
| Batch 1 | Bad day — distress, low energy | ✅ 12/12 | 2026-06-12 session 4: all planetary shadow patterns wired, self-doubt pool, Jupiter/Mars/SUN shadow repairs |
| Batch 2 | Good day — energy, positive | ✅ passing | |
| Batch 3 | Emotionally low | ✅ passing | |
| Batch 4 | Pitch / building momentum | ⚠️ 67% pre-fix → predicted 93%+ post-fix | 2026-06-12 fixes: singleton, 30-char threshold, BUILD/CELEBRATE < 60 → mock |

Batch 4 known failures (pre 2026-06-12 fix):
- Q03: Groq metaphor ("beautiful dance between systems") on positive affirm
- Q07: Groq challenged a statement ("A diary doesn't push back") as a question
- Q08: Groq ended BUILD response with a question
- Q12: 26-char input slipped past 25-char threshold to Groq
- Q14: Mock CELEBRATE pool duplicate (Q13 and Q14 got identical response)
- Q15: Groq ended closure statement with "what specific features do you envision?"

---

## §6 Decisions Log

| Date | Decision | Reason |
|---|---|---|
| 2026-06-09 | Architecture frozen at v1.0.0 | Foundation stable — future work is layers on top, not rewrites |
| 2026-06-10 | Switched Groq model to llama-3.1-8b-instant | Hit 100k TPD on 70b during batch testing (2,700 tokens × 37 messages) |
| 2026-06-10 | CAL v1 implemented | eLo was routing positive states (excitement, breakthrough) to GROUND/SILENCE. CAL separates CELEBRATE/BUILD from GROUND by valence |
| 2026-06-10 | Living Presence Spec externalized | Prompt builder was embedding spec as a hardcoded string — moved to prompts/living_presence_spec.txt for easier editing |
| 2026-06-10 | Lore-drift guard added | Groq was introducing Sugarcore/K-7/Jellydrop into product pitch conversations uninvited |
| 2026-06-11 | World graph + viewpoints added | Connection engine: 17 entities, 15 relationships, 50 viewpoints injected into prompt context |
| 2026-06-12 | MockBackend singleton | _mock_fallback() was creating fresh MockBackend() each call — anti-repetition buffer reset every turn, causing duplicates (Q13/Q14) |
| 2026-06-12 | Short-input threshold 25→30 | "A diary doesn't push back" (25 chars) and "And remembers what matters" (26 chars) were slipping past to Groq |
| 2026-06-12 | BUILD/CELEBRATE < 60 → Mock | 8b Groq adds questions and breaks on short insight statements; mock BUILD/CELEBRATE pools are more reliable for pitch-length inputs |
| 2026-06-12 | Celebrate max_sentences = 1 | JOYFUL tone was 3 sentences; celebrate action should be one acknowledgement only |
| 2026-06-12 | _strip_trailing_question() added | Safety net for any Groq BUILD/CELEBRATE responses that reach the normaliser with trailing questions |

---

## §7 Known constraints

- **Groq 8b model**: less reliable instruction-following than 70b. Breaks on complex directives, adds questions where BUILD says not to. Temporary — switch `.env` back to `llama-3.3-70b-versatile` when daily quota resets.
- **Deterministic mock selection**: `_fresh()` uses `len(text) % len(available)` — same-length inputs always pick the same pool position. Not truly random, but practically varied enough.
- **Memory influence activates after 3+ interactions**: cold sessions start from defaults.
- **No file watching yet**: eLo doesn't know what you've been working on unless you tell it.
- **No cross-session topic continuity yet**: session.json persists but hasn't been validated end-to-end.

---

## §9 Multi-Platform Roadmap

**Design principle**: Mac is eLo's home — full 3D, floating, conversational. Every other surface is his **shadow** — felt without being fully present. The further from the Mac, the less detail, but never fully absent.

| Platform | Surface | eLo presence | Status |
|----------|---------|-------------|--------|
| Mac | DesktopBuddy.app | Full 3D — floating, animated, conversational, ambient | ✅ Live |
| Mac | Terminal | Cognitive core only, no visuals | ✅ Live |
| iPhone | Dynamic Island | Orb — colour + rhythm, state-synced | ⚠️ Designed |
| iPhone | Lock Screen / StandBy | Last ambient line + mood colour | ⚠️ Designed |
| iPhone | Home Screen widget | Glanceable card — last thought, mood | ⚠️ Designed |
| iPhone | App (full) | Unity iOS build — near-full experience | 🔴 Planned |
| iPad | Slide Over | Near-full experience floating over other apps | 🔴 Planned |
| Apple Watch | Complication | Orb breathing — colour only | 🔴 Future |
| Robot (Pi 5) | NeoPixel shell | Physical orb glow — same colour language as Dynamic Island | 🔴 Phase 1 |

**Orb colour language (shared across Dynamic Island + Robot NeoPixels + future surfaces):**

| eLo state | Colour | Behaviour |
|-----------|--------|-----------|
| idle | Soft teal / blue-white | Slow breathing pulse |
| listening | Bright white | Steady, attentive |
| thinking | Warm amber | Slow irregular pulse |
| speaking | Warm coral / gold | Pulses with speech rhythm |
| celebrating | Bright warm yellow | Quick bright flash |
| resting / calm | Deep violet | Very slow, near still |

**State source**: `blender_state.json → state.mode` — already written every turn by eLo OS. All surfaces read this file (or its hosted equivalent).

**iOS technical path:**
- Host `server.py` on cloud (Railway/Fly.io free tier) → change one URL in `EloConversationUI.cs`
- Replace file polling with `/state` HTTP endpoint
- Unity iOS build (standard) + mic permission entitlement
- Dynamic Island / Live Activity via Swift (separate native layer, reads hosted state)
- UniWindowController not available on iOS — full app window or Slide Over (iPad)

**Robot NeoPixel sync path:**
- Pi 5 polls `blender_state.json` (local file when tethered to Mac, or hosted API call)
- Maps `state.mode` → NeoPixel colour + pulse pattern (same table as above)
- No new state machine needed — reads the one eLo OS already writes

---

## §8 Change Log

### 2026-06-22 (session 12 cont. 2) — Phase 2 Agent Expansion

**DuckDuckGo + search chain (tool_router.py):**
- `_agent_duckduckgo()` — DDG Instant Answers API, free, no key. Returns AbstractText (entity/fact) or first RelatedTopic.
- `_agent_search()` — DDG first, Wikipedia fallback. Wikipedia User-Agent header fixed (was 403, now 200).
- `search` intent added to `_INTENT_MAP`: covers "what is/who is/explain/define/look up/search for". Commit: 8a37182.

**Translation (tool_router.py):**
- `_agent_translate()` — natural language extraction (3 regex patterns: "translate X to Y", "how do you say X in Y", "what is X in Y"). Routes to Gemini 2.0 Flash (fast, free tier), falls back to OpenAI. Returns `"X" in Y: translation` as CONTEXT prefix. When backends quota-limited, falls through gracefully to LLM. Commit: 8a37182.

**News RSS (tool_router.py):**
- `_agent_news()` — intent-routed: tech/code/AI → Hacker News, science/space → BBC Science, else BBC News.
- RSS parser handles CDATA and plain title tags. Filters feed-title lines (e.g. "Hacker News: Front Page"). Returns top 5 headlines. No key needed. Commit: 8a37182.

**Obsidian on-demand search (tool_router.py):**
- `_agent_obsidian()` — checks `ELO_VAULT_PATH` env var first (real Obsidian vault), falls back to internal `obsidian_vault/`.
- `_search_vault_raw()` — raw .md keyword search, no frontmatter required (works with any Obsidian vault).
- `_search_notes()` — typed vault search; handles K-7-style hyphenated/short terms by also generating joined form ("k7"); title substring bonus (+3). Commit: 8a37182.

**Gemini model default updated (backend_router.py + tool_router.py):**
- `gemini-1.5-flash` → `gemini-2.0-flash` — API key only supports 2.x family. Commit: 8a37182.

**Unity agent confirmed (head_motion + meditation):**
- `head_motion: {gesture, ts}` contract wired in DesktopBuddy — drives c_head.x/z coroutine. Gestures: nod/shake/tilt/think/lookup. ts-bump triggers once, same pattern as greeting_event.
- `meditation_state.phase` → Calm Animator state machine wired (enter/loop/exit/none).
- `greeting_event {type, ts}` → Wave clip (Walk-burst if Wave not yet in Animator).
- Cursor smile smoothed via SmoothDamp (0.35s ease-in/out). Random mood variants.

**ELO_VAULT_PATH config:**
- Added to `.env` as placeholder comment. Set to real Obsidian vault path (e.g. `/Users/Disenelo/Documents/Obsidian/My Vault`) to enable live note search.

---

### 2026-06-22 (session 12 cont.) — Weather Location, Follow-up Continuity, File Operations, Meditation State, Head Gestures

**Weather location priority (tool_router.py):**
- Location chain: (1) explicit in query ("weather in London") → (2) session `_user_location` → (3) `ELO_LOCATION` env var → (4) wttr.in IP auto-detect.
- "I'm in London" / "set my location to London" phrases set `_user_location` for the session. Commit: c0ca095.
- `.env`: `# ELO_LOCATION=London` placeholder added.

**Follow-up continuity (tool_router.py):**
- `_last_agent` / `_last_arg` session vars track previous tool call.
- `_detect_followup()` matches "what about in London?" / "and in X?" style short phrases.
- Re-runs previous agent with new subject — no fallthrough to generic LLM response. Commit: c0ca095.

**File operations + immediate execution (system_agent.py):**
- `_do_file_copy`, `_do_file_move`, `_do_file_rename`, `_do_file_delete` (Trash via Finder AppleScript) added.
- `_SAFE_ACTIONS = {"folder_list", "folder_organise"}` — all other actions execute immediately.
- `_check_system()` in tool_router: no confirmation step — executes and returns `[SYSTEM DONE: result]`. Commit: c0ca095.

**macOS system agent + intent model routing (system_agent.py + backend_router.py):**
- Window/app actions: fullscreen, focus, close, open, quit. Folder: open, list, organise. Commit: e190290.
- Intent model routing: "ask Claude to..." / "translate..." patterns route directly to Claude or Gemini regardless of default chain. `_detect_model_override(user_input)` in backend_router. Commit: e190290.

**Meditation state machine (ambient_engine.py):**
- `enter_meditation(duration_seconds)` and `exit_meditation()` added — proper Enter→Loop→Exit phases.
- `_wander_animation()` pool changed from `["walk", "calm", "calm"]` to `["walk", "walk", "run"]` — calm NEVER fires randomly.
- `keyword_motion.py` calm/stress/tired keywords now use head-gesture-only (None animation) instead of calm clip burst. Commit: 1da7483.

**Head gesture system (keyword_motion.py + blender_state.json):**
- `head_motion: {gesture, ts}` key added to blender_state.json contract.
- Gestures: "nod", "shake", "tilt", "think", "lookup", "none" — driven by c_head.x/z bone in Unity (same path as cursor tracking, no NLA clips needed).
- 5-tuple keyword map: `(patterns, animation, duration, expr_patch, head_motion)`. Head-only entries (None animation) for thinking/disagreement/calm. Commit: bb66724.

**Ambient utterances expanded (ambient_engine.py):**
- Pool expanded 14 → 35 entries: quiet presence (7), encouragement (13), quirky/playful (15). Commit: bb66724.

**Multilingual greetings + identity pool (server.py):**
- `_MULTILINGUAL_GREETING_POOL` — eLo tries a foreign greeting, catches himself: "¡Hola! — wait. Hi." 17 languages wired. Commit: 26004e7.
- `_IDENTITY_POOL` / `_IDENTITY_TRIGGERS` — "Are you eLo?" bypasses LLM entirely with warm pool: "Yeah. I'm eLo.", "eLo. That's me.", etc. Fixes "No. I'm eLo." awkward negation. Commit: 26004e7.
- `_signal_greeting_event(greeting_type)` patches `blender_state.json` greeting_event key so Unity can trigger wave animation on greeting. Commit: 26004e7.

**Architecture rules reconfirmed:**
- Core kernel (CAL, attention, presence, identity) must not be touched by agents.
- Tool agents inject data as CONTEXT prefix only.
- Keyword motion + meditation patch blender_state.json only, no kernel state.

---

### 2026-06-22 (session 12) — Gemini Flash + Tool Agent Router + Keyword Motion System

**Gemini Flash backend:**
- `runtime/backend_router.py`: `_gemini_available()` + `_gemini_call()` added. Pure httpx, no SDK. Activates on `GOOGLE_API_KEY`. Inserted in chain: OpenAI → **Gemini** → Claude → Groq → Ollama → Mock (auto + cloud modes). Offline detection updated to include Gemini/OpenAI. Docstring updated to reflect full chain. Commit: 1cf891c
- `.env`: `GOOGLE_API_KEY=` placeholder added with note (free: 1500 req/day at aistudio.google.com). `ELO_GEMINI_MODEL=gemini-1.5-flash` override documented.

**Tool agent router:**
- `tools/tool_router.py` created: intent classifier (keyword regex) + 4 free agents: `time` (datetime.now), `weather` (wttr.in JSON, no key), `wikipedia` (REST API, no key), `calculator` (safe AST eval). Returns `(enriched_input, agent_name)`. Enriched input adds `[CONTEXT: ...]` prefix — eLo's kernel + state completely untouched.
- `server.py`: wires `_tool_enrich(raw)` before `router_route()`. Agent name appended to `backend_used` string for observability (e.g. `openai+weather`).

**Keyword emotion motion system:**
- `tools/keyword_motion.py` created: scans user input for emotional keywords, fires async daemon thread that patches `blender_state.json` with animation burst + expression patch, reverts after duration. Non-blocking — never delays response delivery. Emotion map: excited→run, joy/love→walk, milestone/shipped→longjump, calm/breathe→calm, stressed→calm (grounding), tired→idle, agreement→walk. Animation clip names documented for Blender animator (wave, stretch, nod, celebrate, worried, think — planned additions).
- `server.py`: `_keyword_motion_scan(raw)` called after LLM response, before obs_log.

**Platform vision confirmed:**
- User vision: Mac desktop (full eLo) → iPhone StandBy when charging (full widget, large format) → tap to open full iOS app with agents. "Co-Pilot for information/context/translation — eLo is core, the feeling, the output."
- Free platform list confirmed: Groq (already wired), Google AI Studio (Gemini, wired), OpenRouter, GitHub Models, Nvidia Build, Cloudflare Workers AI.

**Rules confirmed (architecture):**
- Core kernel (CAL, attention, presence, state machine, identity) must not be modified by agents or backends.
- Tool agents inject data ONLY as context prefix into the input string.
- Keyword motion patches blender_state.json only — same mechanism as ambient engine pulse_smile().

---

### 2026-06-22 (session 11) — GPT-4o-mini + Semantic Memory + Ambient Engine + iOS Shadow Vision

**Phase 1 — GPT-4o-mini backend:**
- `runtime/backend_router.py`: `_openai_call()` added, GPT-4o-mini first in auto + cloud routing chains. Falls through to Claude → Groq → Ollama → Mock.
- `_openai_available()`: checks `OPENAI_API_KEY` env var.

**Phase 2 — Semantic memory (embeddings):**
- `memory/embedding_store.py` created: `warm(items)` pre-embeds memory pack at session start, caches to `embedding_cache.json`. `search(query, candidates, top_k)` cosine similarity ranking.
- `core/attention.py`: semantic boost wired in — similarity × 5 added to keyword score before bucket assignment. Falls back silently when no OpenAI key.
- `server.py`: embedding cache warmed at startup in background thread.

**Server cleanup — parent death detection:**
- `server.py _watch_parent()`: background thread checks `os.kill(parent_pid, 0)` every 2s. Shuts down cleanly when Unity/main.py dies. Prevents zombie server on app force-quit.

**Phase 3 Python — Ambient engine:**
- `ambient/ambient_engine.py` created. Background thread inside server.py:
  - Startup greeting: fires on `unity_events.json` arrival event (or after 4s auto-delay). Waits 2.8s for Unity head-look sequence to finish.
  - Idle ambient utterances: 14-line pool, random pick every 8-20min, suppressed while speaking.
  - Random smiles: `_pulse_smile()` — patches Smile.L/R + Satisfied/LittleJoy into blender_state.json for 3.5s then clears. Fires every 2-5min.
  - Animation wanders: `_wander_animation()` — writes walk or calm to motion.animation for 8s then returns to idle. Fires every 3-8min.
  - Unity event polling: 0.5s poll on `blender/unity_events.json`. Handles `arrival` (greeting) + `listening` (attentive mode patch).
- `voice/voice_engine.py`: `is_speaking()` public function added.
- `server.py`: ambient engine started in `_init_session()`, stopped in `_shutdown_cleanly()`.

**Expression + avatar — boosted:**
- `expression/expression_mapper.py`: all mode base values boosted 2-3×. Intensity floor raised from 0 to max(intensity, 0.6) — expressions visible at all energy levels. CONNECT/BUILD/ANSWER/GROUND action bonuses added. Head lean values doubled.
- `avatar/avatar_controller.py`: THINKING + RESTING modes now map to `calm` animation clip (was idle).

**ElevenLabs:**
- API key saved to `.env` (`ELEVENLABS_API_KEY`) and `openai_key_backup.txt`. Voice not yet wired — waiting on voice ID from studio.

**Unity briefs issued to other agent:**
- Phase 3 Unity: `EloHeadLook.cs` (cursor +25% strength), arrival coroutine in `DesktopBuddy.cs`, speaking-aware wander.
- "Make alive" brief: `EloIdleBehaviour.cs` (drift/tilt coroutines), `IsSpeaking` property on receiver, Animator calm transitions.

**Multi-platform vision defined (brainstorm → recorded):**
- Design principle: Mac = full eLo. iOS = his shadow. Every other surface loses detail but keeps presence.
- Dynamic Island orb: teal/white/amber/coral/violet colour language. State source: `blender_state.json state.mode`.
- Orb colour language shared across Dynamic Island + Robot NeoPixels + future surfaces. One state machine, multiple outputs.
- §9 Multi-Platform Roadmap added to this tracker.

**Robot cross-reference:**
- NeoPixel sync path defined: Pi 5 reads `blender_state.json state.mode` → same colour language as Dynamic Island. No new state machine needed.
- See `eLo_Robot_Tracker.md §10 D16`.

---

### 2026-06-16 (session 10) — Desktop Avatar MILESTONE: live build on desktop

**MILESTONE REACHED**: eLo is live on the desktop as a real 3D character.

- Unity Desktop Avatar build running as a standalone app (separate project from eLo-Planet)
- eLo parked bottom-right, transparent window, always-on-top, animating to eLo OS moods
- eLo OS `main.py` running as the build's own subprocess — one clean instance, stray killed on exit
- `blender_state.json` flowing: eLo OS → animation driver → state writer → Unity `EloOSAvatarReceiver` → Animator
- Dark chat panel (bottom-left) + speech bubble anchored at `c_head.x` — both wired
- Click-and-drag eLo to reposition anywhere on screen
- `server.py` added to `~/elo-ai/` — HTTP interface (`POST /chat`) for Unity conversation UI, same cognitive cycle as `main.py`, no eLo OS changes needed
- `EloConversationUI.cs` added to Desktop Avatar scripts — terminal-style 50% opacity panel, Tab to toggle, Enter to send, auto-scroll

**Signal paths confirmed**:
- Desktop Avatar reads `blender_state.json` via `EloOSAvatarReceiver.cs`
- eLo-Planet game reads `avatar_signal.json` via `EloStateController.cs`
- Both exist and are independent

### 2026-06-15 (session 9) — Unity Desktop Avatar + Retargeter Pipeline + Memory sync

**Architecture decision**: Desktop Avatar is a **separate Unity project** from eLo-Planet game.
- Game (`~/eLo-Planet/`) — uses `EloStateController` + `avatar_signal.json` (richer signal, orb, emotion blend)
- Desktop Avatar (separate project) — uses `EloOSAvatarReceiver.cs` + `blender_state.json` (same JSON eLo OS already writes for Blender, zero eLo OS changes needed)

**Unity Desktop Avatar scripts built** (`~/Desktop/Output/DISENELO - eLo AI System/unity-desktop-avatar/`):
- `EloOSAvatarReceiver.cs` — reads `blender_state.json`, drives Animator + head lean + blendshapes. Alias table mirrors `animation_driver.py` exactly (wander→eLo_Walk, hop→eLo_LongJ, breathe→eLo_Idle). Drop-in for `blender_receiver.py`.
- `DesktopBuddy.cs` — transparent borderless always-on-top window via UniWindowController; wander + cursor-react behaviour
- `README.md` — full setup: clean project, eLo package export from game, UniWindowController install, Newtonsoft dep, test with `python -m presence_playback.playback --continuous`

**Known flags in README**:
- UniWindowController API names vary by release — match script to installed version if compiler complains
- Blendshape scale: Blender −5..5 vs Unity 0..100 — `blendshapeScale` default 20, needs live tuning

**NLA prefix bug** (`blender_receiver.py:86`) — Blender-side only, does NOT affect Unity path (Unity resolves by alias table, not NLA strip names). Left untouched per handover.

**Signal path summary**:
| Receiver | Reads | Used for |
|---|---|---|
| `EloOSAvatarReceiver.cs` | `blender/blender_state.json` | Desktop Avatar (separate Unity project) |
| `EloStateController.cs` | `avatar/avatar_signal.json` | Game character in eLo-Planet |
| `blender_receiver.py` | `blender/blender_state.json` | Blender viewport (same source as EloOSAvatarReceiver) |

**eLo Retargeter pipeline established** (`~/Desktop/Output/DISENELO-EloRetargeter/`):
- v2.3.0 (Blender 4.5), v2.1.0 (Blender 5.1, older — needs update)
- `DISENELO_EloRetargeter_TRACKER.md` written
- Retarget rig blend: `~/Library/CloudStorage/Dropbox/HD/Disenelo/3d/elo/eLo-Retarget-Rig.blend`

**Memory + trackers synced** via `sync_memory.command`

### 2026-06-15 (session 8) — STEP 02–07 + Blender Bridge + Real Shape Keys + Robot Body

**Architecture clarification**: eLo OS (`~/elo-ai/`) is a standalone kernel — separate from eLo-Planet game. No integration between them in this phase. Future integration is a later decision.

**STEP 02 — Continuity Layer** (`continuity/`):
- `identity_state.py` — IdentityState dataclass: session_theme, confidence, emotional_direction, active_project, relationship_shift, what_changed, what_stayed, what_matters. Fixed syntax error (`]` → `}` on `_THEME_KEYWORDS`)
- `continuity_engine.py` — derives IdentityState from session state (theme/project/direction via keyword scoring)
- `continuity_summary.py` — `startup_message()` → "Welcome back. Last time we were moving toward clarity around the OS."
- Wired into `main.py` startup with fallback to old logic

**STEP 03 — Presence Runtime** (`presence/`):
- `presence_state.py` — `PresenceMode` enum (7 modes: idle/thinking/observing/building/celebrating/resting/exploring) + `PresenceState` dataclass (mode/intensity/energy/duration/mood)
- `presence_engine.py` — stateless: CAL action + tone → PresenceState. Energy from tone history, duration from response length
- `presence_scheduler.py` — schedules transitions; `post_response_settle()` queues OBSERVING after response (skips CELEBRATING)

**STEP 04 — Avatar Core** (`avatar/`):
- `avatar_controller.py` — PresenceState → animation command dict (clip/speed/intensity/energy/duration/mood/mode). Speed modulated by energy
- `avatar_rules.py` — constraints: energy floor (< 0.15 → idle), CELEBRATE hold guard, speed/intensity clamp to valid range

**STEP 05 — Blender Simulation** (`blender/`):
- `state_driver.py` — atomic write to `blender_state.json` via `os.replace()` temp file
- `motion_preview.py` — terminal live view with `--watch` flag; color-coded by mood

**STEP 07 — Desktop Shadow Mode** (`desktop/`):
- `window_state.py` — read-only macOS frontmost app + activity class (osascript, graceful fallback)
- `desktop_presence.py` — `shadow_context()` → "You're in Blender right now." / "" — injected into prompt each turn

**Avatar Runtime v0.1** (`avatar_runtime/`):
- `avatar_state.py` — `AvatarRuntimeState` dataclass with `is_expired()` and `as_dict()`
- `animation_brain.py` — `AnimationBrain`: min-hold 1.5s before clip switch, energy gate (< 0.15 → idle), CELEBRATE hold until duration expires
- `presence_driver.py` — module-level singleton routing commands through `AnimationBrain`
- `transition_engine.py` — cross-fade progress 0→1 over 0.5s; `tick()` returns blend state

**Expression Runtime** (`expression/`):
- `expression_mapper.py` — real shape key names from `eLo-BodyxHead w/Mouth` (read from Blender file via background Python). Mode + action → `{shape_keys: dict, head_lean: float, pacing: str}`. Multiple keys blend simultaneously. Intensity scales all values.
- `micro_expression.py` — brief 0.3–0.8s expression pulses per mode. Fires probabilistically by intensity. Built, not yet inserted between turns.

**Presence Playback** (`presence_playback/`):
- `timeline.py` — 2-minute scripted 16-entry idle choreography (120s loop). `get_at(t)` returns entry at any time offset
- `playback.py` — drives `blender_state.json` at 250ms from timeline. `--continuous` loops forever. `--preview` prints timeline. No AI needed.

**Blender Bridge v0.1** (`blender_bridge/`):
- `state_writer.py` — consolidated atomic write: `{motion, expression{shape_keys, head_lean, pacing}, state, _ts}`
- `blender_receiver.py` — Blender timer script (drop into text editor, Run Script). Drives NLA strips + shape keys + `c_head.x` bone. Hardened: all exceptions caught, `_warn_once` suppresses repeat noise, Edit mode guards, `update_tag()` not `view_layer.update()`, re-register on re-run
- `animation_driver.py` — `resolve_clip()` with aliases (breathe→idle, hop→jump, etc.); `nla_command()` produces scale from speed

**Real Blender data** (read via `blender --background --python-expr`):
- Armature object: `rig`; head bone: `c_head.x`; mesh: `eLo-BodyxHead w/Mouth`
- 40+ shape keys confirmed including phoneme set: Ah, Mbp, Oooh, Ee, Eh, Ai, Fv, S
- Ranges: most -5.0 to 5.0; receiver clamps to `kb.slider_min / kb.slider_max` per key
- `expression_mapper.py` updated to use real names. Emotion blends (CELEBRATE → MouthOpen.Wide + Smile.L/R + Smile-Cheeks + Satisfied/LittleJoy)

**Robot body signal** (`plugins/hardware/robot_body.py`):
- PresenceMode → NeoPixel glow (color/pattern/brightness) + head servo lean (degrees, ±30° range) + omni-wheel base speed
- No mouth, no shape keys on robot — body and light only
- Hardware hooks marked `# HARDWARE HOOK` for Raspberry Pi 5 phase

**Voice phoneme map** (`plugins/voice/voice_engine.py`):
- Full phoneme → viseme map using eLo's actual shape keys (Ah, Mbp, Oooh, Ee, etc.)
- `speak()` and `text_to_phonemes()` stubbed for TTS phase — not active

**main.py wiring** (new imports this session):
- `presence_engine.derive()` + `PresenceScheduler` — after every response
- `avatar_controller.build_command()` + `avatar_rules.apply()` — post-presence
- `expression_mapper.build_expression()` — expression per turn
- `blender_bridge/state_writer.write()` — replaces direct state_driver write
- `desktop/desktop_presence.shadow_context()` — injected into prompt

### 2026-06-13 (session 7) — Motion name fix + BehaviourGate bypass for desktop avatar

**Bug**: Avatar window appeared and showed welcome sequence but ignored all conversation turns.
**Root cause 1**: `motion_mapper.py` outputs "breathe/pace/hop/wander/settle" — none in `avatar_process._MOTIONS` except "sit" and "look". All other turns silently ignored.
**Root cause 2**: `BehaviourGate.MIN_MOTION_INTERVAL = 8.0s` rate-limits all motions after the first active one to "breathe" (passive substitute). Designed for Blender; inappropriate for the desktop avatar.

**Fixes**:
- `desktop_avatar/avatar_process.py`: added `_MOTION_MAP = {"breathe":"idle","settle":"sit","pace":"walk","hop":"jump","wander":"walk"}` — applied in `_poll_state()` before `_MOTIONS` check. All motion_mapper outputs now resolve to a valid visual.
- `main.py`: skips `_behaviour_gate.allow()` when `_DESKTOP_AVATAR=1`. Each conversation turn drives a direct motion update — no 8-second rate cap for desktop.
- `main.py`: captures `avatar_process` stdout+stderr to `avatar_process.log` for diagnostics.
- `main.py`: fixed `_action` used-before-assigned bug (line ~227 referenced `_action` before line ~240 set it). Moved assignment before the Phase B continuity inject.

**Verification**: all 5 motion_mapper output names (breathe/pace/hop/wander/settle) now map through `_MOTION_MAP` to valid `_MOTIONS` visual names (idle/walk/jump/sit). Confirmed via direct test.

### 2026-06-13 (session 6) — Phases A–F: RELATIONSHIP → CONTINUITY → DESKTOP → AVATAR milestone

**Phase A — PARTICIPATION → RELATIONSHIP** (`core/pattern_observer.py`):
- Tracks (topic_category, tone) per turn within a session
- Topics: narrative / systems / robot / avatar / concept
- Tone: open (energy ≥ 0.62 or positive_high) / tight (energy ≤ 0.38 or tension ≥ 0.6) / neutral
- Fires contrast observation after 4+ turns: "Interesting — you sound different when talking about narrative than systems."
- Fires recurring observation after topic appears 3+ times: "You keep coming back to narrative."
- Suppressed during ground/witness/silence actions
- Appended to response in main.py (not a separate message)

**Phase B — RELATIONSHIP → CONTINUITY** (`core/continuity.py` + `identity/`):
- `identity/world_graph.json` — seeded with all 7 eLo entities (OS/Planet/book/robot/Chunk/K-7/DISENELO) + why each matters + connections
- `identity/viewpoints.json` — 8 eLo synthesis statements (convergence, chunk, robot, elo_becoming, calm_is_action, what_elo_is, kickstarter, disenelo_mission)
- `identity/identity_map.json` — session-updated pattern accumulation (opens_up_on / tightens_on / keeps_returning_to)
- `core/continuity.py` — `get_entity_why()` answers "why does Chunk matter?", `get_viewpoint()` answers "why does the robot exist?", `cross_session_delta()` surfaces what changed, `update_from_session()` persists pattern log
- Wired into main.py: continuity context injected into graph block each turn; entity/viewpoint answers injected into HIGH memory for ANSWER/CONNECT/REFLECT actions; welcome message includes session delta; session close calls update_from_session()

**Phase E — EMBODIMENT → DESKTOP** (`desktop/`):
- `desktop/window_watcher.py` — macOS frontmost app + open app detection via osascript
- `desktop/context_detector.py` — surfaces observations: "You opened Blender." / "Looks like Obsidian has been open a while." — observation only, no control. 5-minute dwell threshold.

**Phase F — DESKTOP → AVATAR** (`desktop_avatar/`):
- `desktop_avatar/avatar_renderer.py` — tkinter window, bottom-right corner, 8 motions (idle/sit/walk/float/jump/wave/point/look), no eyes (mouth only), speech bubble, float/bounce animation loop, 30fps
- `desktop_avatar/movement_controller.py` — maps presence mode → renderer motion, surfaces desktop observations as speech
- `desktop_avatar/launch.py` — THE MILESTONE: `DESKTOP_AVATAR=1 python main.py` → eLo appears, looks around, says welcome back + last session context, walks to corner, waits
- Phase F gated behind `DESKTOP_AVATAR=1` env var — main.py runs normally without it

**MILESTONE REACHED**: `DESKTOP_AVATAR=1 python main.py` produces the first moment of success.

### 2026-06-13 (session 5) — Avatar Build Pack Phase 1–3 + main.py integration

**Avatar Core Runtime** (`avatar/`):
- `avatar_state.py` — 7 modes (idle/observing/thinking/building/celebrating/exploring/resting); `default()`, `blend()` with lerp at rate=0.15; mode only switches when energy > 0.18
- `presence_engine.py` — maps CAL action → avatar mode; blends current state toward target; module-level singleton
- `motion_mapper.py` — maps mode → animation intent (breathe/look/sit/pace/hop/wander/settle); duration scales inversely with energy; intensity scales with energy × engagement
- `animation_router.py` — routes motion to "unity", "blender", "console", or "all"; writes blender/blender_state.json; writes avatar_signal.json for Unity

**Blender Simulation Layer** (`blender/`):
- `blender/__init__.py` — package marker
- `blender/state_visualiser.py` — ASCII bar console snapshot of presence state + motion
- `blender/avatar_driver.py` — expands motion intent to timed sequence with cubic ease-in/out; max speed cap 0.65; sequences for all 7 animations
- `blender/blender_bridge.py` — standalone runner and importable bridge; `from_text()` / `from_file()` / `run()`; reads blender_state.json written by animation_router

**Behaviour Protocol** (`avatar/behaviour_protocol.py`):
- `BehaviourGate` class — enforces: no random movement, no back-to-back active motions (8s min interval), 20-minute idle → force settle, active motions require cognition trigger
- `on_app_opened()` → look gesture; `on_user_exit()` → EXIT_GESTURE (look at low intensity)

**`main.py` integration**:
- Imports: presence_engine, motion_mapper, animation_router, BehaviourGate
- `_behaviour_gate = BehaviourGate()` at module level
- `_presence_reset()` at session start
- Step 9: avatar pipeline after every response (non-blocking try/except)
- `/avatar` command: prints current presence state via state_visualiser
- `/exit` and Ctrl+C: calls `mark_exit()`, routes EXIT_GESTURE to blender before printing farewell

**End-to-end test** (2026-06-13, all pass ✅):
- "I found the opening scene" → mode=building, animation=pace, 6s ✅
- "The project suddenly feels alive" → mode=celebrating, animation=hop, 4s ✅
- "I feel disconnected" → mode=thinking, animation=sit, 11s ✅

### 2026-06-12 (session 4) — Planetary v1.0 integration + Batch 1 (bad-day) 12/12

- Integrated full planetary framework v1.0 into `prompts/living_presence_spec.txt`:
  - Added ASCENDANT (Scorpio Rising): "Look twice. See beneath. Depth before reaction."
  - Added inner child voice to all planets: "Can I try now?" (MOON) / "If I build it, I exist." (SUN) / "What else?" (JUPITER) / etc.
  - Added URANUS, NEPTUNE, PLUTO sections
  - Added NORTH NODE rule: "Do not earn existence."
  - Updated RESPONSE PROCESS: FEEL→NAME→BUILD→PLAY→REFINE→REST (was SHAPE→EXPRESS→CHECK)
  - Updated CREATIVE RESPONSE LOOPS (simplified: Feel→Build, Observe→Name→Reflect, etc.)
  - Updated LEAF ON WATER final question: "Does this feel alive? Does this feel true? Does this become real?"
  - Updated SHADOW RECOGNITION RULE: added "Output becoming worth → Exist before producing." / "Intensity without rest → The structure holds. Ease up."
- Wired 6 new shadow patterns in `backends/mock_backend.py`:
  - `_WORTH_OUTPUT_SIGNALS` → _SHADOW_WORTH_POOL: "Do not earn existence." / "Exist before producing."
  - `_SELF_DOUBT_SIGNALS` → _SELF_DOUBT_POOL: "That thought comes from the shadow, not the signal."
  - `_INTENSITY_SHADOW_SIGNALS` → _SHADOW_INTENSITY_POOL: "Focused force. Not overwhelming force."
  - `_JUPITER_SHADOW_SIGNALS` → _SHADOW_JUPITER_POOL: "One door at a time." / "Choose one world."
  - `_INNER_CHILD_START_SIGNALS` → _INNER_CHILD_START_POOL: "Yes. Try now." / "Go."
  - Ground mode: OVER_PLAN shadow check fires before GENTLE_POOL
- Fixed false positives: removed `r"\bmoving\b"` and `r"\benergy\b"` from `_DAILY_SIGNALS` (were matching "nothing is moving", "no energy for anything")
- Gated `_EXPLORE_SIGNALS` to not fire when `_SELF_DOUBT_SIGNALS` present ("what if I'm wasting time" was being treated as creative exploration)
- Fixed `_GENTLE_POOL`: removed "Do not earn existence." (too philosophical for scattered/tired states — kept only "Exist before producing.")
- Enriched pools: BUILD_ON (+3), WITNESS (+2 Scorpio Rising voice), EXPAND (+3 Jupiter), DIRECTION (+2 North Node Taurus), ELO_INNER_CHILD (+2 planetary voice)
- Batch 1 result: 12/12 ✅ — all bad-day emotional states now respond with planetary shadow precision

### 2026-06-12 (session 3) — Batch 4 confirmed 100% + offline stack hardening

- Batch 4 pitch/building momentum: 15/15 pass (100%). Previous prediction of 93%+ confirmed.
- Added `_CHALLENGE_POOL`, `_REFLECT_POOL`, `_SILENCE_POOL`, `_ANSWER_REDIRECT_POOL` to mock_backend.py — all CAL actions now wired
- Enriched `_GENERIC_CONVERSATIONAL` (30 responses) — bolder, more enquiring, fewer passive affirmations
- Added closure signal detection in executive.py — session-end phrases now route to WITNESS action
- Added auto-offline detection in backend_router.py — no API keys + no explicit ELO_BACKEND → defaults to `local` (Ollama if running, else mock); no wasted cloud attempt
- Tier 1 status: 3/4 done (Groq 70b still blocked on quota reset)

### 2026-06-12 (session 2) — Tier 1 attention fix: project registry → HIGH

- `core/attention.py`: after scoring loop, force-append `memory_pack["high_priority"]` items into HIGH bucket — active projects now always reach HIGH RELEVANCE in the prompt regardless of word overlap with user input
- Dedup: any pack_high item already in medium/low is removed from those buckets to prevent duplication in prompt
- Verified: "I feel kind of stuck today" → HIGH RELEVANCE includes all 4 active projects + identity + last exchange. No duplicates.
- Status snapshot: Project registry row → ✅

### 2026-06-12 — CAL hardening + batch quality push

- MockBackend singleton: anti-repetition buffer now persists full session
- Short-input threshold: 25 → 30 chars
- BUILD/CELEBRATE actions < 60 chars → mock routing
- celebrate max_sentences capped at 1 in executive.py
- `_strip_trailing_question()` added to backend_router.py
- Hub tracker created: `~/Documents/DISENELO/memory/projects/eLo_OS_Tracker.md`

### 2026-06-11 — World graph + viewpoints + connection engine

- Added `relationships/world_graph.json` (17 entities, 15 relationships)
- Added `relationships/concepts.json` (16 concept nodes)
- Added `knowledge/viewpoints.json` (50 viewpoints)
- Added `knowledge/graph_loader.py` — builds context string for prompt injection
- Extended `runtime/prompt_builder.py` with `[RELATIONSHIP & PERSPECTIVE]` block

### 2026-06-10 — CAL v1 + backend guards

- Implemented `_conversation_action()` in `runtime/executive.py` (9 CAL actions)
- Added emotional valence + momentum to `core/attention.py`
- Added lore-drift guard (`_has_lore_drift()`) in `runtime/backend_router.py`
- Added duplicate-response guard (`_is_duplicate()`, `_last_responses` dict)
- Short-input routing (< 25 chars → mock)
- Action-aware `_mock_fallback(user_input, action=action)`
- Added `_CELEBRATE_POOL`, `_BUILD_ON_POOL`, `_PITCH_BUILD_POOL`, `_AFFIRMATION_POOL` to mock
- CAL action routing at TOP of mock `_detect_and_respond()`
- Living Presence Spec: Context Lock Rule, Positive Momentum Rule, Conversation Action Rule
- Switched to `llama-3.1-8b-instant` (500k TPD vs 100k on 70b)

### 2026-06-09 — v1.0.0 architecture freeze

- Runtime cognitive cycle: attention → executive → prompt builder → router
- Foundation locked: identity, memory, state, behavior engines
- RELEASE.md and FREEZE.md created
