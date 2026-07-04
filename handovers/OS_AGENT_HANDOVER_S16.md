# eLo OS AI — Handover from Unity DesktopBuddy (S16)

> For the **eLo OS (Python) agent**. What Unity reads/writes and what (if anything) the OS side needs to do.
> Boundary unchanged: Unity renders *how* eLo looks/moves; eLo OS decides *what* he feels/says. Date 2026-06-29.

## NEW this session — `perch_state.json` (Unity → eLo OS, optional read)
Unity now writes **`~/elo-ai/blender/perch_state.json`** whenever eLo settles on a window edge:
```json
{ "app": "Finder", "edge": "top|bottom|left|right", "_ts": 1719600000.1 }
```
- `app` = the window's owner name (from the macOS WindowSensor); `edge` = which side he's clinging to.
- Written **only on change**. eLo OS can read it to make eLo *aware* of where he is ("hanging on the side of your Finder window"). **No OS change required** — purely optional context for richer voice.

## Speech detection — unchanged contract (keep doing this)
**`lipsync_state.json`** (eLo OS writes):
```json
{ "active": true, "text": "the words eLo is saying", "_ts": 1719600000.1 }
```
- `active` true for the WHOLE spoken line → Unity's `IsSpeaking` (bubble, idle-suppress, auto-jaw, reply serialise).
- `text` + `_ts` (written even before TTS, `active:false`) → speech bubble (incl. ambient/random lines).
- **Never send `JawOpening`** — Unity auto-derives the jaw from open visemes.

## Expression / emotion / motion — unchanged (`blender_state.json`)
- `expression.shape_keys` — visemes + face shapes (0–1). `expression.head_lean` (−1..1) — mouse-look composes on top.
- `state.emotion` (+ `intensity`) — drives mood baseline, breathing rate, and **now bored-expression bias**.
- `motion.animation` / `meditation_state` / `greeting_event` / `head_motion` / `emotion_event` — all honoured.

## "Organise windows" command — Unity-owned (FYI)
Unity still **intercepts** `organise/tidy/merge/tab` + `window/finder` phrases **before `/chat`** (picks the app from WindowSensor names, hops along each window, runs Merge All Windows). eLo OS won't see these. To take ownership for richer NLU, write `unity_events.json → {"command":"organise","app":"Finder","_ts":...}` and tell the Unity agent — don't change silently.

## NEW — positional voice commands (also Unity-intercepted, FYI)
Unity now also intercepts movement phrases before `/chat`: **"jump to bottom", "shift left/right", "go up/down", "come here", "stop"** → drives his on-screen steering. Same ownership note as above if eLo OS wants them.

## Behaviour notes (no OS action — context for voice)
- Idle is slower/calmer now; he eases into **Calm meditation after 3 min** of no mouse movement (slower loop).
- **Bored expressions** (cheek puffs / fidgets, longer holds, more random) play autonomously when idle — he reads as "here and a bit bored," then moves.
- He **perches on window edges** (all 4 sides) and **hops between windows**; `perch_state.json` reports it.

## Still open on the eLo OS side (only ask)
- **Strip emoji from TTS** (emoji are chat/expression display only — never spoken).

## Reference docs (in `~/elo-ai/handovers/`)
`EloOS_Wiring_Spec.md` (full field contract) · `EloBlendShapes_Handover.md` (blendshape list + jaw weights) · `EloDesktopBuddy_OS_Handover.md` (broader sync).

### TL;DR
Keep streaming **visemes + `active`/`text`/`_ts`** and **`state.emotion`+`intensity`**; never send `JawOpening`; optionally **read `perch_state.json`** for where-he-is awareness; strip emoji from TTS. Nothing else required.
