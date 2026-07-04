# Unity Agent Handover — Session 17
**Date**: 2026-06-29
**From**: eLo OS Agent (session 17)
**To**: Unity DesktopBuddy Agent
**Supersedes**: UNITY_AGENT_HANDOVER_S16.md

---

## Session 17 delta (eLo OS side)

No Unity contract changes. No new fields in `blender_state.json` or `lipsync_state.json` except one new event field documented in Task 6.

eLo OS changes this session:
- Recovery routing fixes: technical bug reports → ANSWER, identity introductions → ANSWER
- Context reduction: simpler prompt, less world injection
- FREEZE_V1_LOCK.md declared — no new eLo OS systems during recovery

**New Unity work from live testing today:**
- Speech bubble still coming from belly — Task 2
- Some responses not showing at all — Task 3
- Movement is random bumping, not purposeful navigation — Task 4 (major)
- Puffy hold too intense and too long — Task 5
- Corner jumping — fixed inside Task 4 movement system
- "Going off" exit sequence — Task 6
- Conversation presence: responses must feel connected to what was said — woven throughout Tasks 2–4

---

## ⚠️ URGENT AMENDMENT — 2026-06-30 (do before Task 1)

**Observed in live testing**: eLo is moving too much. David described the avatar as "glitchy" and asked "why are you moving so much." The existing random hop/wander in `DesktopBuddy.cs` is firing too frequently — the avatar appears hyperactive and unresponsive to conversation state.

**Immediate fix before Task 1:** Find the existing idle movement timer in `DesktopBuddy.cs` (or wherever random hop is triggered) and change the interval to **120–180 seconds minimum**, or **disable random movement entirely** until Task 4 (EloDesktopNavigator) is implemented.

Every movement must have a reason. Frequency is not presence. Stillness during conversation IS presence.

This is a one-line change. Do it first.

---

## Seven Unity tasks — do them in this order

---

### Task 1 — FSW polling optimisation ← **do this first**

**Full spec**: [UNITY_polling_optimisation.md](UNITY_polling_optimisation.md)

Replace `InvokeRepeating` (250ms) with FileSystemWatcher dirty-flags. This makes lipsync and state changes reach Unity within one frame instead of up to 250ms late — the single most impactful fix before any other work.

**Acceptance**: Phonemes update without poll-lag stutter. Kill eLo OS → heartbeat continues.

---

### Task 2 — Speech bubble from jaw rig (not belly)

**Problem observed**: Speech bubble arrow originates from mid-body, not the mouth.

**Additional context**: Some responses are not showing at all. Both issues share a root — the bubble is either off-screen or in the wrong position. Fix positioning first; if responses still vanish, see Task 3.

**What to fix:**

The bubble anchor must track the jaw bone world position every `LateUpdate`. The jawbone in Auto-Rig Pro naming is `c_jaw.x` or the head equivalent (`c_head.x` → add a downward offset to reach mouth). Do not use a fixed offset from the armature root — animations move it continuously.

```csharp
// LateUpdate — every frame
Vector3 jawWorld = jawBone.position; // c_jaw.x or c_head.x + offset
float jawNow = receiver.jawNow;      // from EloOSAvatarReceiver

// World-space mouth approximation
Vector3 mouthWorld = jawWorld + Vector3.down * (jawNow * jawDropScale);

// Screen Space canvas
Vector2 screenPos = Camera.main.WorldToScreenPoint(mouthWorld);
bubbleRect.position = screenPos + new Vector2(bubbleSideOffset, bubblePaddingPx);
```

Tune `jawDropScale` against the mesh. The bubble arrow tip must point to `mouthWorld`. If the bubble has a fixed arrow sprite, ensure the pivot is at the arrow tip.

**Acceptance**:
- Idle lean cycle plays — arrow stays on the mouth throughout.
- During speech — arrow follows the jaw drop.
- Bubble never appears at belly or body centre.

---

### Task 3 — Responses not showing at all

**Problem observed**: Some eLo responses generated no visible speech bubble.

**Two likely causes:**

**A. Off-screen (root cause is Task 2)** — Bubble was showing but below the visible window. Fix Task 2 first, then retest.

**B. IsSpeaking flicker clearing text too early** — `EloOSChatTMP.cs` clears text when `IsSpeaking` goes false. If audio is short or lipsync_state.json updates rapidly, the bubble may clear before the user has time to read.

Fix for B: add a minimum display time.

```csharp
// In EloOSChatTMP.cs — wherever you clear text on IsSpeaking → false
private float _lastActiveTime;
private const float MIN_DISPLAY_SECONDS = 1.5f;

// When IsSpeaking goes false:
if (Time.time - _lastActiveTime >= MIN_DISPLAY_SECONDS) {
    ClearBubble();
}
// When IsSpeaking goes true:
_lastActiveTime = Time.time;
```

**C. Response was generated but not written to lipsync_state.json** — This is eLo OS side (being investigated separately). Unity cannot fix this, but the symptom is: no text appears AND no audio plays.

**Acceptance**: All eLo responses produce visible text in the bubble for at least 1.5 seconds.

---

### Task 4 — Movement system: WindowSensor-aware navigation ← **largest task**

**Problem observed**: Movement is random bumping. eLo jumps to corners. Run animation plays but eLo goes nowhere. WindowSensor is wired but movement doesn't use it.

**Design principle**: Window borders are the level. eLo is a character in a game where the platforms are whatever windows are open. He walks with purpose, peeks before jumping, and his attention is driven by what's active on the desktop.

---

#### 4a — New script: `EloDesktopNavigator.cs`

This script owns all movement decisions. It reads from:
- `WindowSensor.cs` — window bounds and proximity to borders
- `EloOSAvatarReceiver.cs` — `state.mode`, `motion.animation`, `IsSpeaking`
- Mouse position (Input.mousePosition)
- Active window focus (WindowSensor already tracks this)

It writes to:
- `DesktopBuddy.cs` — position and animator triggers
- `EloSquashStretch.cs` — scale hint for depth movement

---

#### 4b — Navigation states

```csharp
public enum NavState {
    Idle,          // stationary, breathing — no nav target
    Walking,       // moving to destination at walk speed
    Running,       // moving to destination at run speed
    Approaching,   // near edge, slowing down before peek
    Peeking,       // at window edge, facing destination, about to jump
    Jumping,       // arc trajectory in progress (LongJ)
    WalkingBack,   // facing camera, moving on depth axis
    Exiting,       // gun check → run off-screen sequence
}
```

---

#### 4c — Movement along window borders

eLo navigates in 2D screen space (X = horizontal, Y = vertical). Depth is a visual trick on the Z axis.

**Walk and run** move eLo along the current window's geometry:
- Walk speed: 60–80 px/s
- Run speed: 180–220 px/s
- eLo faces his direction of travel — flip localScale.x (or rotate Y 180°) when moving left

**Destination selection** (priority order):
1. `IsSpeaking = true` → do not move. Stay within 80px of speech bubble anchor.
2. Active window changed in the last 3s → navigate toward that window.
3. Mouse has moved >300px in the last 2s AND eLo has been stationary for 3s → walk toward cursor.
4. Idle wander → pick a point along the current window border, walk to it. Choose next point when arrived.

**Distance threshold** for gait:
- Destination within 200px → walk
- Destination 200–500px → run
- Destination requires crossing a window border → jump (via peek, Task 4d)

---

#### 4d — Peek before jumping

When eLo's destination is in another window or requires a border crossing:

```
[Walking toward border]
  → Within 100px of border edge: transition to Approaching (slow to 40% speed)
  → Within 25px of border edge: stop. Set NavState.Peeking.

[Peeking]
  → Face direction of destination (flip or rotate)
  → Hold 0.5–1.0 seconds
  → If valid destination confirmed: trigger LongJ animation, arc to destination
  → If no destination: turn around (face opposite direction), walk back

[Jumping]
  → LongJ arc: lerp position from current to destination over 0.6–0.8s
  → On landing: squash (EloSquashStretch), set NavState.Idle or immediately start next destination
```

**Valid jump destinations:**
- Any visible window within 400px horizontal or 300px vertical of current position
- Floor/taskbar/menubar areas if WindowSensor reports them
- Do NOT jump to screen corners — clamp all destinations to `[cornerMargin, screenW - cornerMargin] × [cornerMargin, screenH - cornerMargin]` where `cornerMargin = 100px`

**Vertical jumps (window to window, up or down):**
- WindowSensor can report windows above/below current window
- If a window is directly below: eLo walks to bottom border, peeks down, drops to the window below using LongJ
- If a window is above: eLo walks to top border, peeks up, jumps up using LongJ (scale up during jump to imply height)

---

#### 4e — Facing camera and depth movement

eLo can move on the depth axis for visual presence — this is a scale effect, not actual Z translation.

**Walk backward (facing camera):**
- NavState.WalkingBack
- eLo faces camera (default forward facing — no flip)
- Play walk animation
- Every frame: increase localScale.x and localScale.y by `depthRate * Time.deltaTime`
- Clamp scale to [0.7, 1.3] relative to base scale
- This makes eLo appear to walk toward the viewer

**Walk away from camera:**
- Same but decrease scale — eLo appears to recede

**When to use depth movement:**
- As part of idle wander: occasional depth walk adds life
- After landing from a jump: can walk "in" toward camera briefly
- Do NOT use depth movement when IsSpeaking — keeps eLo steady during conversation

---

#### 4f — Conversation-presence rule for movement

When eLo is responding to David:
- Movement must feel like it responds to the emotional register, not random
- `state.mode = "speaking"` → very still, subtle sway only
- `state.mode = "thinking"` → small, slow oscillation — considering
- `state.mode = "celebrating"` → LongJ hop, energetic
- `state.mode = "observing"` → very slow drift, watchful

The navigator reads `state.mode` from `EloOSAvatarReceiver` each frame and adjusts movement intensity accordingly.

**Conversation window suppression** (amendment 2026-06-30):

Track two timestamps:
- `_lastInputTime` — updated whenever a new message arrives (lipsync_state.json `_ts` changes OR new text appears)
- `_lastResponseTime` — updated whenever eLo stops speaking (`active` goes `false`)

If `Time.time - _lastInputTime < 8f` → suppress ALL position movement. Breathing idle only.
If `Time.time - _lastResponseTime < 5f` → suppress ALL position movement. Breathing idle only.

Only resume idle wander when both timers have expired. This means eLo is visually still while David is talking to him and immediately after eLo responds — which is when it matters most.

---

#### 4g — Acceptance

- eLo walks somewhere when walking — position updates, animation and translation are synchronised
- eLo peeks at window borders before jumping
- eLo does not jump to screen corners
- eLo walks backward (depth) occasionally — feels intentional, not broken
- Attention follows: walk toward active window when it changes, attention moves toward cursor when idle
- Movement stops when eLo is speaking
- Random bumping gone — every movement has a destination

---

### Task 5 — Puffy emotion fix

**Problem observed**: Cheek puff emotion holds too long and too intensely. Looks extreme.

**Where to fix**: In the `emotion_event` handler in `EloOSAvatarReceiver.cs` (or wherever one-shot emotion events apply blendshape weights).

**Find the handler for `emotion_event.type == "cheek_puff"` or `"puff"`.**

Apply these limits:

```csharp
// When applying cheek_puff emotion_event:
const float PUFFY_MAX_WEIGHT   = 0.45f;  // was probably 1.0 — reduce significantly
const float PUFFY_HOLD_SECONDS = 0.35f;  // how long to hold peak before fading
const float PUFFY_FADE_SECONDS = 0.4f;   // fade-out duration

// Pattern: ramp up over 0.1s → hold 0.35s → fade out over 0.4s
// Total duration: ~0.85s max
```

If the same handler applies to other emotion types: apply the weight cap and hold duration only to `"cheek_puff"` / `"puff"`. Other emotions may have different targets.

**Acceptance**: Cheek puff reads as light, momentary — a flicker of expression, not a held grimace. Duration under 1 second, weight clearly below full.

---

### Task 6 — "Going off" exit sequence

**Design**: eLo announces he's going in, does a gun check pose, runs off screen. This is the handoff moment between desktop eLo and the eLo game.

**eLo OS trigger (wired 2026-06-30):**
David says a game-entry phrase to eLo OS — e.g. "have you popped into your work yet?" / "pop into the game" / "head into the game". eLo OS detects this, writes `exit_event` to `blender_state.json`, and eLo says a short going-in line ("Okay. Going in." / "On my way." / "Let me check."). Unity then plays the full sequence.

**Unity timing rule — wait for speech first:**
After detecting `exit_event._ts` change, Unity should NOT start the gun check immediately. Wait for `lipsync_state.json.active` to go `false` — meaning eLo has finished saying his line. THEN start the gun check pose. This prevents the animation starting while eLo is still speaking.

**Trigger** — eLo OS writes a new one-shot event field to `blender_state.json`:

```json
"exit_event": {
  "type": "game_entry",
  "direction": "right",
  "_ts": 1234567890.0
}
```

`direction` is `"left"` or `"right"` — which edge eLo runs toward. eLo OS chooses based on current position.

Unity reads this exactly like `emotion_event` — edge-detect on `_ts`, play once.

**Sequence in Unity (on `exit_event.type == "game_entry"` detected):**

```
Step 1: Cancel current navigation. NavState → Exiting.
Step 2: Face direction (flip localScale.x based on exit_event.direction).
Step 3: Gun hold pose (1.5 seconds):
  - Blend in an arm-layer override at weight 1.0
  - The target pose is the gun hold pose from eLo_Run frames 39–43 (c_arm_fk bones)
  - If a dedicated "GunCheck" Animator state exists — trigger it
  - If not: sample eLo_Run clip at normalizedTime = 39/totalFrames and hold as a pose layer
Step 4: Start Run animation on body layer.
Step 5: Move toward screen edge:
  - Target X = screen edge + 300px (off-screen)
  - Lerp at run speed (220 px/s) — eLo visually runs off
Step 6: When fully off-screen (position.x < -200 or > screenW + 200):
  - Hide the DesktopBuddy window (or fade alpha to 0 over 0.3s)
  - Set a "dormant" state — do not re-show until eLo OS writes normal state.mode again
```

**eLo OS contract for this event:**
- Before writing `exit_event`, eLo OS writes the spoken line to `lipsync_state.json` — the speech bubble shows "Okay. Going in." before the sequence starts
- `state.mode` is set to `"exploring"` — suppresses further ambient responses while dormant

**No new eLo OS fields required beyond `exit_event`** — it follows the same one-shot `{type, _ts}` pattern as `emotion_event` and `greeting_event`.

**Acceptance**: eLo says the line (shown in speech bubble), holds gun pose 1.5s, runs off screen, window hides. Clean. Repeatable. No leftover state.

---

### Task 7 — Head mouse tracking

**Full spec**: [UNITY_head_mouse_tracking.md](UNITY_head_mouse_tracking.md)

- Read `expression.head_lean` → emotional lean baseline
- On top (in LateUpdate, after IK): mouse-tracking offset ±6° yaw, ±4° pitch
- Tracking active ~30% of time on 8–20s random cycle, lerp to neutral when inactive
- Never replace emotional lean — always compose mouse offset after it

**Acceptance**: Head responds to `head_lean`. Mouse causes subtle yaw/pitch. No twitching.

---

## eLo OS contracts — unchanged

### lipsync_state.json
```json
{
  "active": true,
  "text": "the words eLo is saying",
  "_ts": 1719600000.123
}
```
- `text` + `_ts` written before TTS fetch with `active:false`
- `active:true` at the moment `afplay` launches
- `active:false` when audio ends
- Written via atomic `os.replace()` — watch `Changed` AND `Created`

### blender_state.json
```json
{
  "expression": {
    "shape_keys": { "Ah": 0.0, "Ee": 0.0, "Oooh": 0.0 },
    "head_lean": 0.0
  },
  "state": {
    "mode": "idle",
    "emotion": "neutral",
    "intensity": 0.5
  },
  "motion": {
    "animation": "idle",
    "speed": 1.0
  },
  "emotion_event":  { "type": "cheek_puff", "_ts": 0.0 },
  "greeting_event": { "type": "standard",   "_ts": 0.0 },
  "head_motion":    { "gesture": "nod",      "_ts": 0.0 },
  "exit_event":     { "type": "game_entry", "direction": "right", "_ts": 0.0 },
  "user_nav_event": { "type": "jump_to_app", "target": "Finder", "_ts": 0.0 }
}
```

**`JawOpening` is NEVER written by eLo OS.** Unity auto-derives it from the strongest open viseme weight in `expression.shape_keys`.

One-shot events (`emotion_event`, `greeting_event`, `head_motion`, `exit_event`, `user_nav_event`): fire when `_ts` changes. Store last-seen `_ts` and compare each `LateUpdate`.

### user_nav_event — user-directed navigation

Written by eLo OS when David gives a movement command ("jump to Finder", "shift over", "jump around", etc.). Unity reads and executes the navigation. eLo OS acknowledges with one word ("Sure." / "On it.") — all movement execution is Unity's responsibility.

**nav_type values and expected Unity behaviour:**

| type | behaviour |
|------|-----------|
| `jump_to_app` | Find the named app window via WindowSensor. Walk/run toward it, peek at border, jump to it. `target` = app name (e.g. "Finder"). |
| `jump_bottom` | Walk to bottom border of current window. Peek down. Jump to the window below, or to taskbar/dock area. |
| `jump_top` | Walk to top border. Peek up. Jump to window above or menu bar area. |
| `jump_left` | Walk to left border. Peek left. Jump to window left of current, or screen edge. |
| `jump_right` | Walk to right border. Peek right. Jump to window right of current, or screen edge. |
| `wander` | Pick a random valid destination on current window border. Walk/run there. Repeat. Duration: 8–15s. |
| `shift` / `shift_left` / `shift_right` | Move eLo left or right by 15–20% of current window width. Walk animation. No peek needed (short distance). |
| `come_back` | Navigate back to the most recently active window or last known user focus point. |

**Implementation pattern** (same as other one-shots):
```csharp
// In LateUpdate or a polling coroutine after FSW wires up
float _lastNavTs = 0f;

void ProcessNavEvent(BlenderState state) {
    var nav = state.user_nav_event;
    if (nav == null || nav._ts <= _lastNavTs) return;
    _lastNavTs = nav._ts;
    navigator.ExecuteNav(nav.type, nav.target);  // EloDesktopNavigator
}
```

### presence.json
Unity writes this, eLo OS reads it:
```json
{ "state": "away" | "present", "_ts": float }
```
When `away`: eLo OS suppresses ambient voice only.

---

## What Unity already has (do not re-implement)

- `EloOSAvatarReceiver.cs` — reads both JSON files, drives `IsSpeaking`, visemes, `jawNow`
- `EloOSChatTMP.cs` — speech bubble typewriter, serialises on `IsSpeaking`
- `DesktopBuddy.cs` — window perching, hop arc, squash-stretch (movement logic moves to EloDesktopNavigator)
- `WindowSensor.cs` — window bounds, proximity to borders, adjacent windows detection
- `EloWindowSensor.cs` — open window detection, edge hugging (EloDesktopNavigator uses this)
- `EloIdleBehaviour.cs` — breathing oscillation, calm-on-idle
- `EloSquashStretch.cs` — volume-preserving squash/stretch, jaw-linked stretch during speech
- `HeadLook.cs` — micro-expression flicker every 4–11s

---

## Not in scope for this handover

- ElevenLabs voice clone — eLo OS side, blocked on voice ID
- STT wiring — future session
- iOS Dynamic Island — future phase
- NeoPixel robot sync — future phase

---

## Version lock

Authorises exactly the seven tasks above against **eLo OS session 17** state.
Any contract changes will be called out in the next session handover.

**Previous handover**: `UNITY_AGENT_HANDOVER_S16.md` (superseded by this file)
