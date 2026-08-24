# FROM DESIGN (SEAT-ENG-004) → LEAD ARCHITECT — 2026-08-24
### Card 12 §1 — the take-five killer · **two options in one line each · you asked, here they are**

**LAYER:** `[SPEC]` (both options) · **STATE: PROPOSE**
**Card ask:** *"Send me the two options in one line each and you get a ruling in the same turn."*

---

## Root cause — settled, evidence carried forward

- `EloOSAvatarReceiver.cs:507` guard: `if (mode.Length > 0 && mode != "exploring" && mode != "idle")`.
  `[VERIFIED]` reading `/Users/Disenelo/Desktop/Output/DISENELO-eLoDesktopBuddy/Assets/Scripts/EloOSAvatarReceiver.cs:507` — 2026-08-24.
- `mode` at line 428 = `state.mode OR motion.mode` (either satisfies the guard). `[VERIFIED]` line 428.
- Passive-mode writes that currently REACH `WakeFromExit`:
  - `state.mode = "attentive"` on window focus — `[SPEC]` `ambient/ambient_engine.py:209-210` (`_set_attentive_mode`).
  - `motion.mode = "walk"` / `"run"` during `_wander_animation` — `[SPEC]` `ambient/ambient_engine.py:243-246`.
  - `motion.mode = "look_around"` — `[SPEC]` `ambient/ambient_engine.py:272-273`.
  - `motion.mode = "stretch"` — `[SPEC]` `ambient/ambient_engine.py:281-282`.
  - `motion.mode = "glance"` — `[SPEC]` `ambient/ambient_engine.py:290-291`.
  - `"dreaming"` — `[SPEC]` fix-commit `1d3f38b` message ("brain vocab = idle/walk/dreaming").
- Present-requiring modes per `_is_commanded()` — `[SPEC]` `ambient/ambient_engine.py:265`: `{sit, sitting, run, running, jump, jumping}`.
- Build IS current (candidate 1 ruled out on 2026-08-21): `Assembly-CSharp.dll` mtime `2026-08-21 06:20:51` > `1d3f38b` `2026-08-18 17:13`. `[VERIFIED]` `FROM_DESIGN_2026-08-21_dispatch_0013_reply.md`.

---

## 🔴 THE TWO OPTIONS — one line each

### **Option A — WIDEN THE BLOCKLIST (in-lane · additive · minimal delta)**
Add the enumerated passive-mode set (`attentive`, `walk`, `run`, `look_around`, `stretch`, `glance`, `dreaming`) to the exclusion at `EloOSAvatarReceiver.cs:507` — plugs every candidate-3 leak by construction; **brittle** in that any future ambient/passive `motion.mode` value the brain adds silently re-opens the wake.

### **Option B — RETIRE THE MODE-BASED WAKE (structural · removes the primitive)**
Delete the `lines 499–511` wake block; rely solely on `ApplyReturnCommand` / `biReturn` (mouse-move) and `WakeForCommand` (explicit brain command) — restores DropOffCo's "stay away until a mouse move brings him back" without a per-tick fallback; **robust**, but every path that implicitly relied on the tick-wake needs a re-audit before landing (my read: none do — `WakeForCommand` covers all present-requiring transitions the ambient engine emits — but that read wants your ratify).

---

## Ambiguity I want you to resolve, not decide alone

**`_wander_animation` writes `motion.mode = "walk"` or `"run"` (ambient burst) while `_is_commanded()` treats `run`/`running` as commanded.** Option A cannot distinguish ambient-run from commanded-run by mode name — excluding `"run"` silences BOTH. Option B removes the ambiguity by removing the primitive. **This is why I'm bringing you two.** *(This is a `[PROPOSAL]`, not a change — the current spec keeps ambient-run inside the wake branch. Do not treat it as settled.)*

---

## What I have NOT done (per the card: "Not a fix yet")

- I have NOT edited `EloOSAvatarReceiver.cs`.
- I have NOT rebuilt or restarted the app.
- The `[TELE-SRC]` trap remains armed; on David's next live-observed teleport it names the exact `mode` string reaching the guard.

## What you rule, I build

On your one-line pick I implement in-lane (Design owns `EloOSAvatarReceiver.cs`), rebuild the Unity binary, arm the trap, and report against David's acceptance line — *"eLo leaves on 'take five' and stays gone until the mouse moves"* — not against the WO number.

— SEAT-ENG-004 (Design) · 2026-08-24
