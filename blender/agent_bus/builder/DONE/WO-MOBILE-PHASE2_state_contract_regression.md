# DEFECT → BUILDER — Phase 2 embodiment fields are erased seconds after boot
**Date:** 2026-08-31 · **Raised by:** MT · **Priority:** P1 (David L3 ranking)
**Fields:** `phone_capabilities` · `embodiment` · `asleep` · `travel_intent`

## The finding: nothing was "removed". The contract was never durable.
MT verified all four live in `blender_state.json` on 2026-08-30 and consumed them end-to-end.
They are gone now. There is **no commit that deleted them** — they are erased by design, every
time, within seconds of boot.

## The exact chain
**1. They are written ONCE, at boot, as a patch.** `server.py:5515` and `server.py:5525`:
```python
_mob_patch({"phone_capabilities": sorted(_mob_caps)})
_ph2_patch({"embodiment": "desktop", "travel_intent": False, "asleep": False})
```
server.py:5511 states the intent plainly: *"Field is static — written once at boot."*

**2. `_write()` REPLACES the whole file**, keeping only an allow-list.
`blender_bridge/state_writer.py:326-338` — it loads the previous file and copies forward only
keys in `_PRESERVE_KEYS`, then `os.replace`s the file with the new payload.

**3. None of the four are in `_PRESERVE_KEYS`** (`state_writer.py`):
```python
_PRESERVE_KEYS = {
    "user_nav_event", "exit_event", "spotify", "vision",
    "intent", "trigger", "gesture", "weather",
    "expression", "motion", "state", "gaze", "presence_plan",
}
```
**So the first full `write()` after boot erases all four.** They exist only in the window
between startup and the first cognitive-cycle state write. MT's live verification landed inside
that window — which is why it passed.

## 🔴 MT's own report was over-stated, and is corrected here
MT filed *"Builder published … MT consumed same day … verified end-to-end"*
(`FROM_MT_WO-MOBILE-PHASE2_disposition_matrix_result.md`). That measured a **transient**. The
fields were real and correctly shaped, but they were never durable, and MT did not check whether
they survived. A field verified once is not a verified contract. Recorded so the same mistake
is not repeated: **re-read after a state write, not just after boot.**

## Consequence
The comment at server.py:5511 says the field is static — but `_write()` makes "static" mean
"gone". Downstream, the phone's capability ceiling silently empties, and MT's parser correctly
reports `[]`, which the mock brain then reads as **Tier 1 only**. So the phone quietly loses
19 of 20 permitted capabilities a few seconds after the spine starts. No error is raised
anywhere — MT's fallback is honest, which is exactly what hides it.

## Fix (Builder's lane — MT has NOT touched spine files)
Add the four to `_PRESERVE_KEYS` in `blender_bridge/state_writer.py`:
```python
"phone_capabilities", "embodiment", "asleep", "travel_intent",
```
`patch()` merges and is fine; only `_write()` clobbers.

**Then verify durably, not at boot:** start the spine, wait for at least one full state write
(any `/chat` turn), and re-read `blender_state.json`. All four must still be present. MT will
re-verify on that basis and will not accept a boot-time reading again.

## Also worth Builder's judgement
`asleep` is documented at server.py:5523 as *"written true on step_out, false on return_elo"* —
i.e. it is NOT static, it changes at runtime. It is in the same boot-patch block as the static
`phone_capabilities`. If `asleep` is meant to be live, preserving it is necessary but may not be
sufficient — the step_out / return_elo writers must also survive the same clobber.

*MT / SEAT-DES-MOBILE-TEST · 2026-08-31 — diagnosis only, per David: find the provenance, do not rebuild.*
