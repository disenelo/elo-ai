# 01b_WO-100 — two live bugs found in verification: the gaze cue is dropped, and LiveWorldState imports a function that doesn't exist

**WO:** WO-100 · **Seat:** builder · **Priority:** P1 (small, high value — do alongside WO-CANON-I)
**Gate?** none. **Found by:** Architect implementation-readiness verification 2026-08-13, all [VERIFIED].

---

## A. 🟢 GOOD NEWS FIRST — the brain DOES now emit gaze. WO-099b is essentially built.
[VERIFIED] `blender_bridge/state_writer.py:143-148` and `:231-236` write a `gaze: {yaw, pitch, active}`
object; derived at `server.py:3443-3450`; passed at `:3470`, `:3558`, `:3561`. Unity reads it at
`EloOSAvatarReceiver.cs:419-425`. **The board said nothing on the Python side emits gaze — that is now out
of date.** Correcting my own earlier finding.

## B. 🔴 BUT IT NEVER ARRIVES — `gaze` is missing from `_PRESERVE_KEYS`
[VERIFIED] `state_writer.py:243` — `"gaze"` is **not** in `_PRESERVE_KEYS`, so **any background patch write
strips it.** And the live file proves it: `blender/blender_state.json` currently has
`_ts, expression, intent, motion, state, vision` — **no `gaze` key at all.**

So the brain writes the cue and the next partial write deletes it. Unity is still effectively listening to
a silent channel — for a completely different reason than we thought.

**Fix:** add `gaze` to `_PRESERVE_KEYS`.
**Rule 1 alarm (mandatory):** a test that asserts **every** key the writer can emit is present in
`_PRESERVE_KEYS`. This class of bug — emit a new field, forget the preserve list, lose it silently — will
recur on the next field otherwise. That test is the real deliverable here, not the one-line fix.

## C. 🔴 `world/live_world_state.py:194` imports `get_active_window` — which does not exist
[VERIFIED] `desktop/window_state.py` does not define `get_active_window`. Check how this currently fails:
if it's inside a `try/except`, **that is a silent failure and it is forbidden** (WORKING_STANDARD Rule 1) —
it is the same shape as the swallowed `ImportError` that killed desktop perception for weeks (WO-096).

**Fix:** implement the function or correct the import, and make the failure loud either way.

## Test (without David)
- `gaze` survives a background patch write — write gaze, trigger a patch write, assert it's still there.
- Preserve-list completeness test (B above) — fails if a writer key is missing from `_PRESERVE_KEYS`.
- `world/live_world_state.py` imports cleanly; the window lookup returns real data or raises visibly.
- End-to-end: brain sets gaze → the value is readable in `blender_state.json` after a normal turn.

## Done when
Both fixed, both alarms in place, committed, hash to outbox. Then **WO-099b can actually be closed** —
report whether it needs anything further beyond this.
