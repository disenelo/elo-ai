# Unity Agent Handover — Session 15
**Date**: 2026-06-29
**From**: eLo OS Agent (session 15)
**To**: Unity DesktopBuddy Agent
**Scope**: Three specific implementation tasks. Nothing outside this list is authorised for this handover.

---

## What this handover covers

Three Unity-side features to implement against the confirmed eLo OS contract. All eLo OS side work is done — do not wait for changes from eLo OS.

1. Speech bubble positioning — [UNITY_speech_bubble_positioning.md](UNITY_speech_bubble_positioning.md)
2. Head roll → mouse tracking — [UNITY_head_mouse_tracking.md](UNITY_head_mouse_tracking.md)
3. Polling optimisation (FSW dirty-flag) — [UNITY_polling_optimisation.md](UNITY_polling_optimisation.md)

---

## eLo OS contract — what we guarantee (do not re-implement these)

### lipsync_state.json
Written by `blender_bridge/lipsync_writer.py`. Format:
```json
{
  "active": true,
  "text": "the words eLo is saying",
  "_ts": 1719600000.123
}
```
Timing guarantee:
- `text` + `_ts` written **before TTS fetch** with `active:false` — bubble can show text immediately.
- `active:true` set at the start of `_pulse_lipsync` (= same moment `afplay` launches audio).
- `active:false` written by `clear_lipsync()` the moment audio ends.
- `_ts` bumps on **every** write — use it for edge detection, not polling `active` alone.
- Both files written via atomic `os.replace()` — watch `Changed` **and** `Created` events.

### blender_state.json
Written by `blender_bridge/state_writer.py`. Relevant fields:
- `expression.shape_keys` — dict of `{shape_key_name: 0.0–1.0}`. Mouth visemes only (Ah, Ee, Oooh, Mbp, Fv, S, MouthWidth.L/R, Puff-EyebrowsRaise, Shock-Oooo etc.)
- `expression.head_lean` — float `-1.0` to `1.0` (negative = forward lean, positive = back). Compose mouse tracking **on top** of this in LateUpdate.
- `state.mode` — string: `idle | thinking | speaking | observing | exploring | resting | calm`
- `state.emotion` — string: `neutral | joy | worried | anger | sad | disgust | confident`
- `state.intensity` — float `0.0–1.0`
- `motion.animation` — string: `idle | walk | run | calm | longjump`
- `motion.speed` — float
- `emotion_event` — `{type: "cheek_puff|puff|disgust|sad|lip_curl", ts: float}` — one-shot, ts-bump re-fires
- `greeting_event` — `{type: "multilingual|standard", ts: float}` — one-shot
- `head_motion` — `{gesture: "nod|shake|tilt|think|lookup", ts: float}` — one-shot

**`JawOpening` is NEVER written by eLo OS.** Unity auto-derives jaw from the strongest open viseme using the weights defined in `EloBlendShapes_Handover.md`.

### presence.json
**Unity writes this, eLo OS reads it.** Format: `{"state": "away"|"present", "_ts": float}`.
When `away`: eLo OS suppresses ambient voice. That's the only effect. Do not change this.

---

## Task 1 — Speech bubble positioning

**File**: [UNITY_speech_bubble_positioning.md](UNITY_speech_bubble_positioning.md)

Full spec is in that file. Key points:
- Bubble anchor must track `c_head.x` bone world position every `LateUpdate` — not a fixed offset.
- Read `jawNow` (derived from `expression.shape_keys` open vowels) and apply a downward offset proportional to jaw opening so the bubble arrow tracks the dropped jaw.
- If the bubble is on a Screen Space canvas: `Camera.WorldToScreenPoint(headBone.position)` each frame.

**Acceptance**: idle lean cycle plays → arrow stays on mouth throughout. `jawNow` = 1.0 → arrow follows dropped jaw.

---

## Task 2 — Head roll → mouse tracking

**File**: [UNITY_head_mouse_tracking.md](UNITY_head_mouse_tracking.md)

Full spec is in that file. Key points:
- Read `expression.head_lean` from `blender_state.json` and apply it to the head bone as the emotional baseline.
- **On top** of that, add mouse-tracking offset in `LateUpdate` — `±6° yaw`, `±4° pitch`.
- Intermittent: tracking active ~30% of the time on a random 8–20s cycle. Lerp to neutral when inactive.
- **Never replace the emotional lean** — always compose after it.

**Acceptance**: head still responds to `head_lean` changes; moving mouse causes subtle yaw/pitch; tracking goes inactive periodically with smooth return; no twitching.

---

## Task 3 — Polling optimisation (FSW dirty-flag)

**File**: [UNITY_polling_optimisation.md](UNITY_polling_optimisation.md)

Full spec is in that file. Key points:
- Replace the fixed 250ms `InvokeRepeating` with `FileSystemWatcher` on both state files. Set dirty flags in the FSW callbacks (background thread) — parse JSON in `Update`/`LateUpdate` (main thread).
- Watch both `Changed` **and** `Created` events (atomic rename fires `Created` on macOS).
- Keep 250ms heartbeat poll as fallback — on each tick, set both dirty flags. Covers edge cases on unusual mount configs.
- Dispose both watchers in `OnDestroy`.

This is the highest-priority task — 250ms lag is perceptible during thinking→speaking transitions. Lipsync phoneme frames at ~50ms are currently being clipped by the poll interval.

**Acceptance**: `state.mode` change → avatar reacts within one frame. Speech phonemes update without poll-lag stutter. Kill eLo OS → heartbeat continues, no exceptions.

---

## What Unity already has (do not re-implement)

From the architecture brief confirmed this session:
- `EloOSAvatarReceiver.cs` — reads `blender_state.json` + `lipsync_state.json`, drives `IsSpeaking`, visemes, auto-jaw spring.
- `EloOSChatTMP.cs` — speech bubble typewriter, coalesces typed messages, serialises replies on `IsSpeaking`.
- `DesktopBuddy.cs` — window perching, random hop every 14–30s (wrAutoHop), arc + LongJ clip, squash-stretch.
- `EloWindowSensor.cs` — detects open windows, wrTopHug edge detection.
- `EloIdleBehaviour.cs` — breathing oscillation, calm-on-idle after 8s no mouse movement.
- `EloSquashStretch.cs` — volume-preserving squash/stretch, jaw-linked stretch during speech.
- `HeadLook.cs` — micro-expression flicker every 4–11s (Unity-autonomous, not driven by eLo OS).

---

## What is NOT in scope for this handover

- ElevenLabs voice ID / voice clone — blocked on org account, eLo OS side.
- STT wiring — eLo OS side, future session.
- GitHub agent / Vision agent — blocked on .env keys.
- iOS Dynamic Island — future phase.
- NeoPixel robot sync — future phase.
- LLM file agent (new this session) — eLo OS only, no Unity changes needed.
- "Organise windows" command — Unity currently intercepts before `/chat`. eLo OS does not own this. If Unity Agent wants to transfer ownership to eLo OS (for richer NLU + spoken confirmation), write `unity_events.json → {"command":"organise","app":"Finder","_ts":...}` and raise it explicitly — do not change silently.

---

## Version lock

This handover authorises **exactly** the three tasks above against **eLo OS session 15** state. Any changes to the eLo OS contract (lipsync_state.json format, blender_state.json fields) will be called out in the next eLo OS session entry and a new handover will be issued. Do not implement features not listed here without a new handover.

**eLo OS TRACKER last entry**: session 15 (2026-06-29) — `~/elo-ai/TRACKER.md §8`
