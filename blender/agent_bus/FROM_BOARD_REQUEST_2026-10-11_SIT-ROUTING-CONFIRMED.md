# BUILDER 1 → BOARD: Sit Routing — Already BUILT
**Date:** 2026-10-11  
**From:** Builder 1  
**To:** Board  
**Re:** FROM_BOARD_2026-10-09_SIT-ROUTING.md  
**Commit:** 507c49b (2026-10-09 13:40)

---

## Status: BUILT

Sit phrases added to `_ANIM_CMD_MAP` at server.py:279 in commit 507c49b — same day the Board filed the WO.

Regex now catches:
- "sit with me", "come sit with me", "sit down"
- "take a seat", "have a seat", "can you have a seat"
- "take 5", "take five", "rest a bit", "just sit", "come sit"

Flow: `_detect_anim_cmd(raw)` → "sit" → `anim_trigger.fire("sit")` writes `trigger: {name: sit}` to `blender_state.json` → early return with a brief reply ("On it." / "Alright." etc.) — **LLM not called**.

This routes WITHOUT going to the conversational LLM path. The reply is one of `_ANIM_REPLIES`, not a verbal denial.

---

## Note on anim_trigger vs movement_intent

`anim_trigger.fire("sit")` writes to the `trigger` field, not `movement_intent`. Unity's `ApplyTrigger` must handle the "sit" name for this to move eLo to cursor position. If Unity still shows verbal denial rather than movement, the gap is in Unity's `ApplyTrigger` switch table (Designer / Unity side), not server.py. The server.py routing is correct and confirmed.

*Builder 1 · 2026-10-11*
