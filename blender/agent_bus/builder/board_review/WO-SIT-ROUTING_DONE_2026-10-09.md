# WO-SIT-ROUTING — BUILT
**Date:** 2026-10-09  
**Builder:** Builder 1  
**Commit:** 507c49b

---

## What was done

Added sit phrases to `_ANIM_CMD_MAP` in server.py (L279), so `_detect_anim_cmd()` at L3370 catches them **before the LLM fires** — same routing path as wave/jump/celebrate.

**Phrases now covered:**
- "sit with me" / "sit with me for a bit"
- "come sit with me" / "come sit"
- "sit down" / "just sit"
- "take a seat" / "have a seat" / "can you have a seat"
- "take 5" / "take five"
- "rest a bit"

**Before:** these phrases fell through to `_movement_intent()` at L7431 (after LLM) → full conversational latency, no animation fire guarantee.

**After:** `_detect_anim_cmd()` returns `"sit"` → `anim_fire("sit")` → instant pre-LLM return with `_ANIM_REPLIES` response. Same ACK contract as other anim commands.

---

## Verification needed (Board/David)

- Live test: say "sit with me" to eLo — should get an `_ANIM_REPLIES` response (e.g. "On it.") with no LLM delay, and sit animation fires in Presence.
- `[SPEED]` terminal output should NOT show "LLM fired for 'sit with me'" for this phrase.

---

## Next

Per START_HERE.md: file evidence to Board of what the causal chain is doing on live turns (Track B confirmation). Awaiting Board direction.
