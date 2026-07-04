# Unity Agent Handover — Session 16
**Date**: 2026-06-29
**From**: eLo OS Agent (session 16)
**To**: Unity DesktopBuddy Agent
**Supersedes**: UNITY_AGENT_HANDOVER_S15.md

---

## What changed in session 16 (eLo OS side)

All changes are eLo OS-only. No Unity contract changes. No new fields in `blender_state.json` or `lipsync_state.json`. The three Unity tasks from S15 are still the full scope — nothing has been added or removed.

New eLo OS agents built this session (no Unity work required):
- Apple Notes — create/read/search via AppleScript
- iMessage — send with confirm flow
- Web page fetch + summarise
- Spotify Web API — playlist add, like, search+play
- Dark mode toggle (AppleScript)
- Brightness control (requires `brew install brightness`)
- JawOpening dialog fix — `prompt_builder.py` FORBIDDEN list updated; vault note written

**JawOpening contract reminder** (clarified this session — see `obsidian_vault/01 Identity/eLo Digital Form.md`):
- eLo OS **never** writes `JawOpening`
- Unity auto-derives jaw from the strongest open viseme weight in `expression.shape_keys`
- If jaw hangs open at rest: animator default state, mesh rest shape, or blendshape baseline — fix Unity-side

---

## Three Unity tasks — unchanged, still pending

Priority order has not changed. Do them in this order.

---

### Task 1 — FSW polling optimisation ← **highest priority, do this first**

**Full spec**: [UNITY_polling_optimisation.md](UNITY_polling_optimisation.md)

The current 250ms `InvokeRepeating` poll clips lipsync phoneme frames and makes thinking→speaking transitions perceptibly slow. This is the most impactful fix.

Key points:
- Replace `InvokeRepeating` with `FileSystemWatcher` dirty-flags on `blender_state.json` and `lipsync_state.json`
- FSW callbacks run on background thread — only set a `bool _dirty` flag there
- Parse JSON in `Update` or `LateUpdate` (main thread) when flag is true, then clear it
- Watch both `Changed` **and** `Created` events — `os.replace()` (atomic write) fires `Created` on macOS
- Keep a 250ms heartbeat `InvokeRepeating` that sets both dirty flags — fallback for edge cases
- Dispose both watchers in `OnDestroy`

**Acceptance**: State changes reach Unity within one frame. Speech phonemes update without poll-lag stutter. Kill eLo OS process → heartbeat continues, no exceptions.

---

### Task 2 — Speech bubble positioning

**Full spec**: [UNITY_speech_bubble_positioning.md](UNITY_speech_bubble_positioning.md)

Key points:
- Bubble arrow must track `c_head.x` bone world position every `LateUpdate` — not a fixed static offset
- Derive `jawNow` from open viseme weights (sum of Ah + Ee + Oooh from `expression.shape_keys`), clamped 0–1
- Apply downward offset on the arrow proportional to `jawNow` so it tracks the dropped jaw during speech
- Screen Space canvas: `Camera.WorldToScreenPoint(headBone.position)` each frame

**Acceptance**: Idle lean cycle plays → arrow stays on mouth throughout. `jawNow` = 1.0 → arrow follows dropped jaw. No jitter.

---

### Task 3 — Head mouse tracking

**Full spec**: [UNITY_head_mouse_tracking.md](UNITY_head_mouse_tracking.md)

Key points:
- Read `expression.head_lean` from `blender_state.json` → apply to head bone as emotional lean baseline
- **On top** of that (in `LateUpdate`, after IK): add mouse-tracking offset — `±6° yaw`, `±4° pitch`
- Tracking active ~30% of the time on a random 8–20s cycle. Lerp to neutral when inactive.
- **Never replace the emotional lean** — always compose mouse offset after it

**Acceptance**: Head still responds to `head_lean` changes. Moving mouse causes subtle yaw/pitch on tracking turns. Tracking goes inactive periodically with smooth return. No twitching.

---

## eLo OS contract — what we guarantee (do not re-implement)

### lipsync_state.json
Written by `blender_bridge/lipsync_writer.py`. Format:
```json
{
  "active": true,
  "text": "the words eLo is saying",
  "_ts": 1719600000.123
}
```
Timing:
- `text` + `_ts` written **before TTS fetch** with `active:false` — bubble can show text immediately
- `active:true` at the moment `afplay` launches audio
- `active:false` written by `clear_lipsync()` the moment audio ends
- `_ts` bumps on **every** write — use for edge detection, not polling `active` alone
- Written via atomic `os.replace()` — watch `Changed` **and** `Created`

### blender_state.json
Written by `blender_bridge/state_writer.py`. Relevant fields:
- `expression.shape_keys` — `{shape_key_name: 0.0–1.0}`. Viseme mouth shapes only.
- `expression.head_lean` — float `-1.0` to `1.0` (neg = forward, pos = back). Compose mouse tracking **on top** in `LateUpdate`.
- `state.mode` — `idle | thinking | speaking | observing | exploring | resting | calm`
- `state.emotion` — `neutral | joy | worried | anger | sad | disgust | confident`
- `state.intensity` — float `0.0–1.0`
- `motion.animation` — `idle | walk | run | calm | longjump`
- `motion.speed` — float
- `emotion_event` — `{type: "cheek_puff|puff|disgust|sad|lip_curl", ts: float}` — one-shot, ts-bump re-fires
- `greeting_event` — `{type: "multilingual|standard", ts: float}` — one-shot
- `head_motion` — `{gesture: "nod|shake|tilt|think|lookup", ts: float}` — one-shot

**`JawOpening` is NEVER written by eLo OS.** Unity auto-derives it from the strongest open viseme. See `EloBlendShapes_Handover.md` for the full weight map.

### presence.json
**Unity writes this, eLo OS reads it.** Format: `{"state": "away"|"present", "_ts": float}`.
When `away`: eLo OS suppresses ambient voice only. Do not change this behaviour.

---

## What Unity already has (do not re-implement)

- `EloOSAvatarReceiver.cs` — reads `blender_state.json` + `lipsync_state.json`, drives `IsSpeaking`, visemes, auto-jaw spring
- `EloOSChatTMP.cs` — speech bubble typewriter, serialises replies on `IsSpeaking`
- `DesktopBuddy.cs` — window perching, random hop every 14–30s, arc + LongJ clip, squash-stretch
- `EloWindowSensor.cs` — open window detection, edge hugging
- `EloIdleBehaviour.cs` — breathing oscillation, calm-on-idle after 8s no mouse movement
- `EloSquashStretch.cs` — volume-preserving squash/stretch, jaw-linked stretch during speech
- `HeadLook.cs` — micro-expression flicker every 4–11s (Unity-autonomous)

---

## Not in scope for this handover

- ElevenLabs voice clone — eLo OS side, blocked on voice ID selection
- STT wiring — eLo OS side, future session
- GitHub / Vision agent activation — eLo OS side (.env keys)
- iOS Dynamic Island — future phase
- NeoPixel robot sync — future phase
- All S16 new agents (Notes, Messages, Spotify Web, Web summarise, Dark mode) — eLo OS only, no Unity work

---

## Version lock

This handover authorises **exactly** the three tasks above against **eLo OS session 16** state.  
Any contract changes will be called out in the next session entry and a new handover issued.

**eLo OS TRACKER last entry**: session 16 (2026-06-29) — `~/elo-ai/TRACKER.md §8`  
**Previous Unity handover**: `UNITY_AGENT_HANDOVER_S15.md` (superseded by this file)
