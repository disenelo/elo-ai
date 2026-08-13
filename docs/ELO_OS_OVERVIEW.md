# eLo OS + DISENELO Presence — Architecture Overview
**As of 2026-07-06 · Session 17+**

> Hand this to anyone reviewing or routing new architecture. It covers the full system as it stands today — what's live, what's wired but dormant, what's outstanding.

---

## What eLo OS is

A persistent creative operating system. Not a chatbot. Not an assistant.

eLo is a character first — David Charles's long-standing personal character, "adorable childhood imagination paired with adult reality." The OS is the runtime that gives that character a voice, memory, presence, and the ability to act on the desktop.

**Core rule:** The model is replaceable. eLo is not.

---

## The two systems

### 1. eLo OS (`~/elo-ai/`)
Python server. The brain. Runs at `localhost:5050`.
Receives text → runs cognitive cycle → returns response + drives `blender_state.json`.

### 2. DISENELO Presence (Unity Desktop Avatar)
Separate Unity project. The body. Transparent floating app on the desktop.
Reads `blender_state.json` → drives animation, expression, lipsync.
Sends user chat to eLo OS via HTTP POST `/chat`.

These two are intentionally separate. eLo OS does not know about Unity internals. Unity does not run Python logic.

---

## eLo OS — Cognitive Pipeline

```
User input
    ↓
Language Faculty       — normalise, repair typos, detect social intent
    ↓
Relationship Faculty   — relationship context from vault
    ↓
Capability Faculty     — which agents/tools could handle this
    ↓
System Faculty         — macOS system actions (volume, launch, etc.)
    ↓
Executive Faculty      — ONE decision → CognitivePlan
    ↓
Executive Enrich       — relationship + emotional vector added
    ↓
Emotional Light Engine — CognitivePlan → PresencePlan (colour/animation state)
    ↓
Conversation Faculty   — direct response (social/greeting/pools) OR LLM
    ↓
Backend Router         — OpenAI → Gemini → Claude → Groq → Ollama → Mock
    ↓
Response + state write to blender_state.json
    ↓
Voice engine (ElevenLabs → OpenAI TTS → macOS say)
```

### CAL — 9 Executive Actions
`BUILD · CELEBRATE · CONNECT · ANSWER · GROUND · WITNESS · SILENCE · SHORT_AFFIRM · SYSTEM`

These drive tone, prompt directive, response length, avatar state, and TTS pacing.

---

## Direct Response Pools (bypass LLM entirely)

High-volume predictable turns never hit the LLM. Handled by `server.py` pools, wired through `spine.py _conversation_faculty`:

| Pool | Triggers | Examples |
|---|---|---|
| Pure greeting | "yo", "wagwan", "hey" | Regional + patois variants |
| Farewell | "safe", "laters", "byeeeee" | South London farewell pool |
| How are you | "you good", "what you sayin" | Slang variants included |
| Thank you | "appreciate you", "big up" | Patois + standard |
| Identity | "who are you", "are you eLo" | Warm, certain responses |
| Existence/age | "how long have you been alive" | Honest session-to-session answers |
| Self-ref/capability | "what can you do", "how is your memory" | Factual eLo OS answers |
| Animation commands | "gun check", "gun fire", "gun run" | eLo responds in character — correctives, not weapons |
| Rasta phrases | "Jah!", "give thanks", "Rastafari" | Mirrored back with weight |
| Farewell (regex) | "byeeeee", elongated variants | Regex catch for extensions |

---

## Backend Status (2026-07-06)

| Backend | Key | Status | Notes |
|---|---|---|---|
| OpenAI GPT-4o-mini | `OPENAI_API_KEY` | ✗ 429 | Quota exhausted — needs credit top-up |
| Gemini Flash 2.0 | `GOOGLE_API_KEY` | ✗ 429 | Daily free quota hit — resets midnight |
| Claude Sonnet | `ANTHROPIC_API_KEY` | — | Key commented out in .env — uncomment to activate |
| Groq llama-3.1-8b | `GROQ_API_KEY` | ✓ Live | Active fallback. Upgrade to 70b: `ELO_GROQ_MODEL=llama-3.3-70b-versatile` |
| Ollama | local | ✓ if running | Requires Ollama installed + model pulled |
| Mock | none | ✓ always | Anti-repetition buffer, 30+ pools — last resort |

**Effective chain right now:** Groq → Mock

---

## Voice Pipeline

```
speak(text)
    ↓
Background thread
    ↓
_play_elevenlabs()   ← primary (needs valid key + voice ID)
    ↓ fail
_play_openai()       ← shimmer, tts-1-hd (needs credit)
    ↓ fail
_play_say()          ← macOS system voice (always available)
    ↓
afplay (audio) + write_active_flag() simultaneously
    → lipsync_state.json → Unity reads IsSpeaking
```

**Key fix (this session):** Text fires to Unity when audio starts, not before. Single TTS call per response (no inter-sentence re-fetch gaps).

### ElevenLabs Status
- New paid tier active (2026-07-06)
- New voice in creation: young adult woman, warm mezzo, West/South London — calibration prompts at 1000/500/350 char written
- `ELEVENLABS_API_KEY` needs updating with new key when ready
- `ELEVENLABS_VOICE_ID` needs new voice ID once created
- Voice mix: `ELEVENLABS_VOICE_MIX=0.65` (blend between voice_id and voice_id_2)

---

## Tool Agents (all in `tools/`)

| Agent | Key needed | Status |
|---|---|---|
| Weather (AccuWeather) | AccuWeather | ✓ Live |
| Time | none | ✓ |
| Calculator | none | ✓ |
| Wikipedia / DuckDuckGo | none | ✓ |
| News (BBC RSS) | none | ✓ |
| Translation | Gemini / OpenAI | ✓ when keys live |
| Vision (screen) | Gemini / OpenAI | ✓ code ready — both keys 429 currently |
| Draft agent | OpenAI / Gemini | ✓ when keys live |
| Spotify | Client ID/Secret/Refresh | ✓ Live (connected 2026-07-06) |
| Apple Calendar | none | ✓ AppleScript |
| Apple Reminders | none | ✓ AppleScript |
| Apple Notes | none | ✓ AppleScript |
| iMessage | none | ✓ AppleScript (2-step confirm) |
| Clipboard | none | ✓ pbpaste/pbcopy |
| Timer | none | ✓ Background thread + notification |
| Screenshot | none | ✓ screencapture |
| Volume / Brightness | none | ✓ osascript |
| Dark mode | none | ✓ osascript |
| File read | none | ✓ Path-based, .env blocked |
| File ops (mv/cp/del) | none | ✓ Trash-based |
| LLM file agent | OpenAI / Gemini | ✓ Natural language file ops |
| Web summariser | OpenAI / Gemini | ✓ URL fetch + summary |
| GitHub | `GITHUB_TOKEN` | ⚠️ Key not set |
| Google Calendar | OAuth credentials | ⚠️ Setup not completed |

---

## Vision Agent (`tools/vision_agent.py`)

```
screencapture (macOS) → PNG bytes
    ↓
_describe_gemini()   ← GOOGLE_API_KEY (429 currently)
    ↓ fail
_describe_openai()   ← OPENAI_API_KEY (429 currently)
    ↓ fail
descriptive error string
```

Keys read inside functions (not at module load) — env changes always picked up. When either key is live, vision is live.

---

## Memory System

### Session memory
`memory/session.json` — persists between server restarts. Tracks session count, last topics.

### Semantic memory
`memory/embedding_store.py` — embeds conversation turns, boosts attention scoring ×5 for relevant memories.

### Obsidian vault (`obsidian_vault/`)
Internal vault, single bridge via `memory/obsidian_loader.py`. Domains: current, identity, universe, relationship, ai-os, game, robot, session, **memory** (new).

### Tiered memory vault (new — 2026-07-06)
Three-tier system in `obsidian_vault/09 Memory/`:

```
SPOT_CODES.md          ← master scannable index
    ↓ links to
summary/EO-BL-2607-8.md   ← one-sentence note + wikilink
    ↓ links to
deep/EO-BL-2607-8-deep.md ← full compressed memory block
```

Spot code format: `EO·BL·2607·8` = [project]·[type]·[YYMM]·[weight]
Bit format: `1100·1111·0111·1000` (human-readable binary layer)

API: `memory/vault_layer.py` — `write_memory()`, `compress_session()`, `lookup()`, `load_deep()`

**Not yet wired:** `offline_engine.integrate_session()` never called — session compression doesn't fire automatically yet.

---

## DISENELO Presence (Unity Desktop Avatar)

**Status:** App formerly called "Desktop Buddy" — name retired until multi-character support (eLo / K-7 / Chunk). Currently eLo-only.

### What it is
Transparent floating Unity app on the macOS desktop. eLo lives here — animated, conversational, context-aware.

### Architecture

```
User types in chat panel (Unity UI)
    ↓
TryLocalCommand() — Unity-side local commands (gun run, exit, etc.)
    ↓ if not local
HTTP POST → localhost:5050/chat → eLo OS
    ↓
Response text returned
    ↓
eLo speaks (via eLo OS voice engine) + Unity drives animation
```

### State bridge
`blender_state.json` — written by eLo OS Python, read by Unity `EloOSAvatarReceiver.cs` via `FileSystemWatcher`.

Key fields:
- `motion.animation` — clip name (idle/walk/run/wave/jump/celebrate/gun_check/gun_run/gun_fire/calm)
- `state.mode` — presence mode (drives NeoPixels on robot + Dynamic Island on iOS)
- `expression.shape_keys` — blend shape weights
- `expression.head_lean` — head posture
- `head_motion` — gesture (nod/shake/tilt/lookup)
- `exit_event` — triggers ExitSequence in Unity
- `lipsync_state.json` — separate file, written by voice engine, read by Unity for IsSpeaking

### Animation system
All animations via `Animator.CrossFadeInFixedTime(stateName, fade, layer)` — states crossfaded by name, no trigger parameters.

Two sources:
- **eLo OS-driven:** Python writes `motion.animation` → `EloOSAvatarReceiver.ApplyMotion()` → crossfade
- **Unity-driven:** `SetLocomotion()`, `PlayGunCheck()`, `PlayGunRun()`, `PlayGunJumpFire()` called directly

Guard: `_gunHoldUntil` — while gun pose is playing, `ApplyMotion()` early-returns so Python motion can't stomp it.

### Exit sequence (`ExitSequence` coroutine, `DesktopBuddy.cs:1059`)

```
Triggered by: "exit" / "run off" / StartAmbientRunOff / exit_event from eLo OS
    ↓
1. Force fullscreen-explore, cancel other movement
2. Wait for IsSpeaking = false (8s cap)
3. PlayGunCheck() — hold until GunCheckNormalized ≥ 0.92 or 1.2s
4. SetLocomotion(true, true) — Run clip, slide roamVp to edge until AvatarClearedScreen or 8s
5. HideAvatar(true) — dormant
6. ReturnFromRunoff — on mouse-move + 0.4s (or 8s): run back in → jump to window → idle
```

**Exit suppression flag (new — 2026-07-06):**
`blender_bridge/exit_state.py` — `mark_exiting()` fires when `exit_event` is written. `is_exiting()` returns True for 35s. Ambient engine checks this alongside `_is_speaking()` — no speech, smiles, emotion flickers, or animation wanders fire while eLo is off-screen.

---

## Colour / State Language

One shared colour system across all surfaces:

| Mode | Colour | Hex approx |
|---|---|---|
| idle | teal | #00B4B4 |
| listening | white | #FFFFFF |
| thinking | amber | #FFB300 |
| speaking | coral | #FF6B6B |
| calm | violet | #9B6BFF |

Surfaces that read this: DISENELO Presence avatar → Robot NeoPixels (Pi 5) → iOS Dynamic Island orb (future).
Single source: `blender_state.json → state.mode`.

---

## API Keys — Current State

| Service | Key name | Status |
|---|---|---|
| Groq | `GROQ_API_KEY` | ✓ Live |
| AccuWeather | `ACCUWEATHER_API_KEY` | ✓ Live |
| Spotify | `SPOTIFY_CLIENT_ID/SECRET/REFRESH_TOKEN` | ✓ Live (2026-07-06) |
| OpenAI | `OPENAI_API_KEY` | ✗ 429 quota |
| Gemini | `GOOGLE_API_KEY` | ✗ 429 quota (resets midnight) |
| ElevenLabs | `ELEVENLABS_API_KEY` | ⚠️ New paid tier — key needs updating |
| Anthropic | `ANTHROPIC_API_KEY` | — commented out |

---

## What's Outstanding / Not Yet Wired

| Item | State |
|---|---|
| ElevenLabs new key + voice ID | Pending — new voice being created |
| `integrate_session()` wiring | `compress_session()` built, never called |
| Google Calendar OAuth | Needs credentials.json + one-time setup |
| iOS Dynamic Island / Live Activity | Designed, not built |
| Robot NeoPixel bridge (Pi 5) | Designed, hardware not yet built |
| Anthropic key uncommented | One line in .env |
| Groq upgrade to 70b | One line in .env when quota resets |
| Vision when keys live | Code ready, waiting for quota |

---

## File Map (key files only)

```
~/elo-ai/
├── server.py                          ← HTTP server, direct pools, main entry point
├── .env                               ← all API keys (gitignored)
├── runtime/
│   ├── spine/spine.py                 ← cognitive pipeline orchestrator
│   ├── executive.py                   ← CAL routing, register detection
│   ├── prompt_builder.py              ← directive sandwich → spec → memory → directive
│   ├── backend_router.py              ← OpenAI → Gemini → Claude → Groq → Ollama → Mock
│   └── light_engine/light_engine.py  ← emotional state → colour/animation
├── voice/voice_engine.py              ← EL → OpenAI TTS → say, lipsync writer
├── ambient/ambient_engine.py          ← idle utterances, smiles, wanders (exit-suppressed)
├── blender_bridge/
│   ├── state_writer.py                ← atomic blender_state.json writes
│   └── exit_state.py                  ← exit sequence suppression flag (new)
├── tools/
│   ├── tool_router.py                 ← all agent dispatch
│   └── vision_agent.py                ← screencapture → Gemini → OpenAI fallback
├── memory/
│   ├── obsidian_loader.py             ← sole vault reader, MemoryPack builder
│   ├── vault_codec.py                 ← spot code encoder/decoder (new)
│   └── vault_layer.py                 ← three-tier vault writer/lookup (new)
└── obsidian_vault/
    ├── 00–08 ...                      ← existing vault folders
    └── 09 Memory/                     ← tiered memory vault (new)
        ├── SPOT_CODES.md
        ├── summary/
        └── deep/
```
