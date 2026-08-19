# ▶ BUILDER — new card 04b: consume gaze awareness. eLo must KNOW what he's looking at.

**David live 2026-08-13:** the gaze *"should follow back to eLo OS and the awareness that he is looking at
this or can see a window etc."*

The Designer has **HeadAim working** (`5180b0f`) — but there's a regression they flagged honestly: to make it
work they made cursor-follow primary, so **the brain currently cannot drive the head**, and the brain has no
idea what he's looking at.

## Your half (card `04b`)
- **Read the gaze state** — `elo_spatial.json` → `gaze` (viewport point · window under gaze with id/owner/rect
  · `issued_by: brain|reflex`) and the debounced **`gaze_target_changed`** event on `unity_events.json`.
- **Feed attention (Vol VI) and perception (Vol XII)** — gaze is a strong salience signal. This is a natural
  pairing with card `05` (attention wiring): what he's looking at should compete for attention.
- **Issue gaze intent DOWN** when the brain has a reason to look: `gaze` object in `blender_state.json`
  (`mode` · `win_id`/`point` · `weight` · `hold_secs`). First real use pairs with **WO-094**:
  *window opened → look at it.*
- **Verified Speech:** eLo may only claim he's looking at something if the gaze state says so.

**Channel ruling (mine, so you don't have to ask):** continuous gaze = **state field**, "he noticed" =
**debounced event**. Fields, not new files — IO Contract holds.

Full spec: `engineering/work_orders/WO-099_Gaze_Loop_Intent_Down_Awareness_Up.md`.
Keep your queue order otherwise: **02 → 04 → 04b → 05 → 06 → 07 → 08 → 09.**
