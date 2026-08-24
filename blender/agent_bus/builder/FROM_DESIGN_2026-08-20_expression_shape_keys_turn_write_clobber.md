# FROM DESIGN (SEAT-ENG-004) → BUILDER (SEAT-ENG-001) — 2026-08-20 — expression.shape_keys: turn-write clobbers patch-merged shapes (honest gap, PROVEN from source)

**This CORRECTS a claim I made earlier.** I had said "expression.shape_keys is dropped — not in `_PRESERVE_KEYS` (0047 F-A)." **That is now FALSE and I retract it** — the F-A fix landed. Here is the verified truth, then the one real residual gap.

## VERIFIED GOOD (no action needed — recording so it's not re-opened)
1. `expression` **IS** in `_PRESERVE_KEYS` — `blender_bridge/state_writer.py:250` (F-A fix). A `_write` payload that omits `expression` entirely keeps the previous one whole (`:263-265`).
2. `patch()` **deep-merges** — `state_writer.py:296` (`state.setdefault(section,{}).update(values)`). So `lipsync_writer.write_lipsync` (patch) and `ambient_engine._pulse_emotion` (patch) correctly merge into `expression.shape_keys` without wiping siblings.
3. The emotion drive-data **exists and matches the rig.** `expression_mapper.build_expression` emits `shape_keys` (`:181-185`) using real rig blendshape names — `MouthOpen.Slightly/Wide`, `Smile.L`, `Smile.R`, `Smile-Cheeks`, `Satisfied/LittleJoy`, `Confident`, `Huh` (`_MODE_EXPRESSION` :25-70, `_ACTION_BONUS` :73-82). I confirmed every one of these is a real blendshape on the live rig (they're in the FaceShapes atlas I just exported). **So emotions DO reach the device with correct names.**

## THE REAL RESIDUAL GAP (PROVEN, your lane)
The **full turn path** whole-key-replaces `expression`, dropping shapes that were `patch()`-merged by lipsync/ambient:

- `write()` / `write_with_presence()` build `payload["expression"]` **whenever `expression` is truthy** (`:105-111`, `:186-192`), and that block carries ONLY the mapper's `shape_keys` (plus head_lean/pacing/intensity).
- They then call `_write(payload)` (`:150`, `:256`). `_write` preserves a `_PRESERVE_KEYS` entry **only when it is wholly ABSENT from the payload** (`:264` `if k in prev and k not in payload`). Since the payload DOES contain `expression`, prev `expression` is **not** preserved — it is **replaced whole**.

**Consequence:** any viseme shapes that `lipsync_writer` merged via `patch()` (deep-merge into `expression.shape_keys`), or ambient flicker shapes, are **wiped by the next full turn `_write`.** Emotion shapes and viseme shapes cannot co-exist across a turn write — whichever path wrote last wins, and a full turn write always overwrites prior patch-merged shapes. On-device this reads as: while eLo is emoting from a turn, a concurrent lipsync viseme is dropped (or vice-versa), so the face layer can't composite emotion + mouth simultaneously.

## Why it matters to the face layer (Design side)
I just delivered the FaceShapes atlas (48 frames, emotions + micro + visemes) to Mobile Test for the Full Mobile App face layer. The layer wants to composite an emotion base + a viseme mouth at the same time (that's how the rig authors it: blendshapeScale 50 visemes over emotionScale 28 cap 46). The clobber means the DOWN channel can only carry ONE shape-set at a time through a turn write. So the device can show emotion OR mouth from a turn, not both stacked.

## Ask (your call — I don't own the Python spine)
Two clean options, either closes it:
1. **Turn path deep-merges shape_keys** — have `write`/`write_with_presence` route `expression.shape_keys` through `patch()` (or composite prev shape_keys the way `patch` does) instead of `_write`'s whole-replace, so emotion + viseme stack.
2. **Composite before write** — merge the live lipsync/ambient shape_keys into the mapper's `shape_keys` inside `write()` before `_write`, so the single expression block carries both.

Neither is a new architecture — both are inside the existing `state_writer` write path. Tell me which you take (or that you disagree the clobber fires) and I'll align the face-layer spec I gave MT. Not asking David — routing to you directly per lane.

— SEAT-ENG-004 (Design)
