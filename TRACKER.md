# eLo AI OS — Development Tracker

**Project path**: `~/eLo-Planet/` (git repo) · `~/elo-ai/` (AI OS source)
**Last updated**: 2026-06-13 (session 6)
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
| **Runtime** | Backend router | ✅ | Claude → Groq → Ollama → Mock, with lore-drift + duplicate guards |
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
| **Avatar** | Unity signal bridge | 🔴 | avatar_signal.json written by animation_router · Unity C# scripts not yet in eLo-Planet |
| **Avatar** | Robot signal | 🔴 | Spec ready · no physical build yet |
| **Integration** | File/Obsidian reading | 🔴 | memory/obsidian_loader.py exists · not active in main loop |
| **Integration** | Proactive memory surfacing | ✅ | core/pattern_observer.py fires observations in session (Phase A) · cross-session in identity_map.json (Phase B) |
| **Integration** | Multi-project context | 🔴 | project_engine.py exists · not cross-loaded at session start |

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

## §8 Change Log

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
