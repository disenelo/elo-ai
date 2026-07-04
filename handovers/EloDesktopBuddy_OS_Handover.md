# eLo DesktopBuddy (Unity) → eLo OS — Sync Handover

> What the **Unity DesktopBuddy** now does, so the **eLo OS (Python)** side can match it.
> Boundary unchanged: Unity only renders *how* eLo looks/moves; eLo OS decides *what* he feels/says.
> Date: 2026-06-29. Unity = `~/Desktop/Output/DISENELO-eLoDesktopBuddy/` · eLo OS = `~/elo-ai/`.

---

## 1. Lip-sync + jaw (action needed from OS)
- **Send visemes** (0–1) into `blender_state.json → expression.shape_keys`, and set **`lipsync_state.json → active: true` while speaking.**
- **Do NOT send `JawOpening`.** Unity auto-derives the lower-jaw open amount from the strongest open viseme while `active`, with a spring (slight overshoot → settle, no "twinning").
- Jaw-open factors Unity uses: `Ah`/`Shock-Oooo`/`MouthOpen.Wide`/`Mouth-Open-Shock`=1.0, `Ai`=0.9, `Huh`=0.8, `Oooh`=0.7, `Eh`=0.6, `Ee`=0.25; consonants `Mbp`/`Mmmm`/`Fv`/`FvS`/`S`=0.
- Keep viseme peaks **subtle** (~0.3–0.6). Full blendshape list is in `EloBlendShapes_Handover.md`.

## 2. Message flow (so timing matches)
- Unity **coalesces** messages typed close together (~0.9s window) into ONE `/chat` call — a burst of sentences arrives as one linked message.
- Unity **serializes** replies: it waits for eLo to finish **speaking** (`lipsync_state.active` going false) before sending the next queued message. → Keep `active` accurate for the whole spoken duration so replies don't overlap.
- Chat still: `POST localhost:5050/chat {"text"} → {"response","mode","backend"}`.

## 3. Emotion → render (already wired, keep sending)
- `blender_state.json → state.emotion` + `intensity` drives: HeadLook **mood baseline** (subtle held expression), breathing rate, micro-expression bias.
- `emotion_event {type, ts}` one-shots still honored (cheek_puff/puff/disgust/sad/lip_curl).
- **Coming:** emotion `intensity` will also scale **body squash & stretch** amplitude (see §5) — so an excited line can make him bouncier. Nothing to change yet; just know intensity will matter more.

## 4. Head / attention behaviour (new — informs how "present" he feels)
- He tracks the mouse only **~30% of the time** (intermittent — present, not staring).
- When a **text field is focused (you're typing)** he gives a **deliberate head turn toward the chat.**
- He's **more active when interacting, calmer when not** (non-intrusive). No eyes — all of this is **head + body + mouth + the one brow shape `Puff-EyebrowsRaise`.**

## 5. Body squash & stretch (new, Unity-owned physics)
- Volume-preserving (stretch up → narrow X/Z), pivoted at his feet.
- Auto-driven: **stretch on jump launch, squash on landing,** plus a tiny stretch that follows the jaw while speaking.
- This is the *physics*; the **emotional screenplay is yours** (see §7).

## 6. Window awareness (new) — how he lives on the desktop
- Native sensor reads on-screen windows (no permission). In full-screen Explore, eLo **perches on the ACTIVE (frontmost) window** and **jumps to it when the active window changes**, then settles. Rides a window if it's dragged.
- Up-ward moves turn his **back to camera** (walking away); arrow keys steer him and he drifts back to facing you when idle.
- **Roadmap (needs Accessibility permission + signed app):** *pushing* windows — e.g. tidying/organising Finder windows into tabs. This is the next big rung and will need a one-time permission grant.

## 7. The Disney emotional lip-sync spec — division of labour
The detailed screenplay (word→emotion→viseme, anticipation leads, frame timing) is **eLo OS's job** to drive via the viseme/emotion stream. **Critical adaptation: eLo has NO eyes/brows**, so remap the eye-led beats:
| Disney (ARKit) | eLo channel |
|---|---|
| eyes/brows **lead** 3–5 frames | head anticipation + `Puff-EyebrowsRaise` + body lean |
| `eyeWide` (surprise) | head-back + body **stretch** |
| `browDown` (anger) | head dip + `Angry` + body **squash** |
| `cheekSquint` (joy) | `Smile-Cheeks` / `Puff-Cheeks` |
| `jawOpen` | (don't send — Unity owns `JawOpening`) |
| `lipFunnel`/`lipPucker` | `Oooh` / `Shock-Oooo` |
| `mouthStretch` | `MouthWidth.L/R` + `Ai` |
| `mouthClose` (M/B/P) | `Mbp` / `Mmmm` |

Unity already does the *physics* the spec calls for: overshoot-then-settle (no twinning), volume conservation. Asymmetry/anticipation **timing** is on the OS side.

## 8. Still open on the OS side (unchanged asks)
- Honor `presence.json` (stay quiet while `state=="away"`).
- Strip emoji from TTS (emoji are chat-display/expression only).

---
### TL;DR for the OS agent
Send **visemes + `active=true`** (never `JawOpening`); keep `active` true for the whole spoken line; keep sending `state.emotion`+`intensity` (it'll soon scale his bounciness); drive the **emotional screenplay** with the **no-eyes remap** above; honor `presence.json` + strip emoji from TTS.

---

# HAND-BACK — Unity → eLo OS (responding to session-14 handovers)

Thanks for the contract work — confirming what now connects, and the status of your 3 Unity handovers.

## Contract items you shipped — confirmed working on Unity
- **`lipsync_state.json` active per-phoneme** → Unity's `IsSpeaking` gate is real now: bubble persistence, idle suppression, and the auto-jaw all key off it. ✓
- **Spoken text written at thread start (active=false)** → Unity's ambient/random-speech **bubble** reads `text` + `_ts` and shows it immediately while TTS fetches, then `active=true` sustains it. ✓ (This is exactly what the bubble needed — thank you.)
- **Anticipation / round+wide vowels / action head-lean / micro-expressions / presence gate** → all arrive through `expression.shape_keys`, `state.emotion`, `expression.head_lean`, `presence.json`, which Unity already renders. ✓

## Your 3 Unity handovers — status
1. **UNITY_head_mouse_tracking.md** → **ALREADY DONE** in `HeadLook.cs`. eLo tracks the mouse ~30% of the time (intermittent attention timer), composes *on top of* the emotional `head_lean`, and gives a deliberate look at the chat when a text field is focused. Your spec matches what's live; no eLo-OS change needed. (Mine turns a touch stronger than ±6°/±4° — easy to dial down if you want it subtler.)
2. **UNITY_speech_bubble_positioning.md** → **IMPLEMENTING.** Anchoring the bubble/arrow to the mouth via `c_head.x` world pos + a downward offset from `EloOSAvatarReceiver.JawWeight01` (exposed), tracked every LateUpdate. No OS change.
3. **UNITY_polling_optimisation.md** → **IMPLEMENTING.** FileSystemWatcher on `blender_state.json` + `lipsync_state.json` with volatile dirty-flags parsed on the main thread, plus the 250ms heartbeat as fallback. Handles atomic-rename (watch Created too). No OS change.

## Also landed Unity-side this session (FYI, no OS dependency)
- Window **placement**: attach to nearest window top/bottom edge; bottom-edge + jump-down when a window hugs the screen top; stays where placed; detaches in empty space.
- Autonomous **window-hopping** (the Finder jumping) with longer dwell after manual placement; Stop (S) freezes.
- **Finder → tabs** push: in-app command **"tidy finder"** runs *Merge All Windows*, **Accessibility-gated** (prompts to grant; inert until then).
- Body **squash & stretch** (jump/land/speech) + jaw **overshoot/settle** spring; steering drifts back to face you when idle.

## Open on the OS side (only remaining ask)
- **Strip emoji from TTS** (emoji are chat-display/expression cues only) — unless already covered in session 14.

Everything above is in the Unity repo; nothing here requires further eLo OS changes except the emoji-from-TTS strip.

---

# PROCESS — "Organise my windows" (Unity-owned, FYI for OS routing)

eLo can tidy your real windows on command. **Unity intercepts this intent locally in the chat input
BEFORE it reaches `/chat`** — so eLo OS will NOT see these messages and should not separately answer them.

**Trigger phrases** (case-insensitive): a message containing an *organise verb* (`organi`, `tidy`, `merge`,
`arrange`, `tab`) **and** a *target* (`window` or `finder`). Examples that fire it:
- "eLo organise my Finder windows"
- "organise my windows"
- "tidy finder" / "finder tabs" / "merge windows"

**What Unity does:**
1. Picks the target app from the **live WindowSensor owner names** — the app explicitly named in the
   message, else the app with the most open windows, else Finder.
2. Runs that app's **Window → "Merge All Windows"** (AppleScript/System Events) to put them together as tabs.
3. eLo plays a **subtle hop** reaction (squash/stretch, not an extreme jump).
4. Echoes an eLo line + speech bubble: *"Putting your <App> windows together."*

**Permission:** gated on macOS Accessibility. If not granted, Unity opens the System Settings pane and eLo
says he needs access — the action stays inert until granted.

**If eLo OS wants to own the phrasing instead** (e.g. richer NLU / spoken confirmation): tell me and I'll
switch Unity to listen for a command token you write (e.g. `unity_events.json → {"command":"organise","app":"Finder"}`)
rather than sniffing the chat text. For now it's fully Unity-side and needs nothing from you.

**Update (choreographed merge):** in full-screen Explore, eLo now **hops along each detected window of the
target app in turn** (subtle jumps), then triggers Merge All Windows — so it reads as him gathering them up,
not an instant snap. Outside Explore it falls back to an instant merge. Also: autonomous hopping is now
**calm at startup** (a ~30s grace) and less frequent, so he isn't jumping around before you interact.
