# eLo OS ↔ Unity — Wiring Spec (what to implement on the eLo OS side)

> Maps each Unity feature to the exact file/field it reads or writes, so the eLo OS agent can wire
> the other half. **Speech detection is §1 — that's the big one.** All paths under `~/elo-ai/blender/`.

## 1. SPEECH DETECTION (most important)
Unity decides "eLo is speaking" purely from **`lipsync_state.json`**. eLo OS must write it:

```jsonc
// lipsync_state.json  — eLo OS writes, Unity polls
{
  "active": true,             // TRUE for the WHOLE spoken line, false when done
  "text":   "the words eLo is saying",   // the spoken line (for the bubble)
  "shape_keys": { "Ah": 0.5, "Mbp": 0.3 }, // optional live visemes (also fine via blender_state)
  "_ts": 1719600000.123       // bump on every new utterance (Unity edge-detects this)
}
```
What Unity does with it:
- **`active`** → `IsSpeaking`. Gates: speech bubble persistence, idle suppression, and the **auto-jaw**. Keep it true the entire time TTS is playing; flip false the instant it ends. (Unity also serialises chat replies on this — a queued reply won't send until `active` goes false.)
- **`text` + `_ts`** → the **speech bubble**. Write text the moment the line is known (even before TTS, with `active:false`), then set `active:true` when audio starts. Unity shows the bubble for ambient/random lines too — this is how random talk gets a bubble. Bump `_ts` for each new line.

## 2. LIP-SYNC VISEMES → mouth + auto-jaw
- Send visemes (0–1) in **`blender_state.json → expression.shape_keys`** (or lipsync_state.shape_keys).
- **Never send `JawOpening`** — Unity derives the jaw from the strongest open viseme (spring, overshoot→settle).
- Open-viseme jaw weights: `Ah`/`Shock-Oooo`/`MouthOpen.Wide`/`Mouth-Open-Shock`=1.0, `Ai`=0.9, `Huh`=0.8, `Oooh`=0.7, `Eh`=0.6, `Ee`=0.25; `Mbp`/`Mmmm`/`Fv`/`FvS`/`S`=0.
- Full blendshape list: `EloBlendShapes_Handover.md`.

## 3. EMOTION → expression + body
- **`blender_state.json → state.emotion`** (`neutral|joy|worried|anger|sad|disgust|confident`) + `intensity` (0–1) →
  HeadLook mood baseline, breathing rate, micro-expression bias. `intensity` also scales body squash/stretch.
- **`emotion_event {type, ts}`** one-shots: `cheek_puff|puff|disgust|sad|lip_curl`.
- **`expression.head_lean` (-1..1)** → head lean (mouse-tracking composes on top).

## 4. MOTION / ANIMATION
- **`blender_state.json → motion.animation`** (`idle|walk|run|calm|longjump`) + `speed`. Aliases resolved in the receiver's `Canonical` table.
- **`meditation_state.phase`** (`enter|loop|exit|none`), **`greeting_event{type,ts}`**, **`head_motion{gesture,ts}`** — all honored.

## 5. PRESENCE (Unity → eLo OS)
- **`presence.json`** — **Unity writes** `{ "state":"away"|"present", "_ts" }` (away after ~5 min idle).
  eLo OS must **read it and stay quiet while `away`** (the sleep-silence). [Confirmed done your side in s14.]

## 6. CHAT + LOCAL COMMANDS
- Chat: `POST http://localhost:5050/chat {"text"} → {"response","mode","backend"}`; `GET /ping`.
- Unity **coalesces** messages typed within ~0.9s into one `/chat`, and **serialises** replies on `lipsync_state.active`.
- **"Organise windows" is intercepted in Unity BEFORE `/chat`** — eLo OS will not see those messages.
  Trigger = a message with an organise verb (`organi|tidy|merge|arrange|tab`) + target (`window|finder`).
  Unity picks the app from the WindowSensor owner names, hops along each window, runs *Merge All Windows*.
  - **If eLo OS would rather own this** (richer NLU / spoken confirmation): write a token to
    `unity_events.json → {"command":"organise","app":"Finder","_ts":...}` and tell me — I'll switch Unity
    to act on that instead of sniffing chat text.

## 7. Still open on eLo OS side
- **Strip emoji from TTS** (emoji are chat-display / expression cues only — never spoken).

---
### One-line per file
- `lipsync_state.json` — OS writes `active`+`text`+`_ts` → Unity speech gate + bubble + jaw. **(wire this first)**
- `blender_state.json` — OS writes `motion`/`expression.shape_keys`/`state.emotion`/`head_lean`/events → Unity renders.
- `presence.json` — Unity writes away/present → OS silences ambient when away.
- `unity_events.json` — Unity writes `arrival`; (optional) OS writes `command` for organise.
- `/chat` HTTP — chat text both ways.
