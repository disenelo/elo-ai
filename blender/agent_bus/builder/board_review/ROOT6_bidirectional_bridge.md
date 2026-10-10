# ROOT-6 BIDIRECTIONAL BRIDGE — Board Review

**Moved by**: Builder 1  
**Date**: 2026-10-08  
**Commit**: 057df91

---

## Problem

Brain sent movement intents to Presence (swim, jump, stomp, etc.) but never received results back. WKG write is async and keyword-gated — it surfaces only if a later turn mentions the same subject. The brain had no way to know "pool is empty, can't swim" on the VERY NEXT TURN.

---

## What was built

**`ambient/ambient_engine.py`** — extended `_consume_presence_events()` brain_action handler:
- When `brain_action` arrives with `ok=False`, atomically writes `last_movement_result` to `blender/blender_state.json`
- Fields: `{intent, ok: false, reason, ts}`
- Atomic via `os.replace(tmp, blender_state.json)` — no partial writes
- Only records failures (successes need no feedback)
- WKG write still fires as before for memory growth

**`runtime/prompt_builder.py`** — reads `last_movement_result` after `inner_thought_anchor` block:
- Reads `blender_state.json` (already open for `inner_thought_text`)
- If `ok=False` AND fresh (< 30s), injects `[BODY FEEDBACK]` block
- Format: `"My last movement (swim) couldn't happen: pool is empty. Account for this if it's relevant."`
- Freshness gate prevents stale feedback persisting across many turns

---

## Why this approach

`blender_state.json` is already read every turn for `inner_thought_text`. Adding one more key read costs nothing. The 30s freshness gate matches one or two turn cycles — enough for immediate feedback, not so long that it pollutes unrelated turns.

---

## Verification needed

Board/David: confirm that after Presence emits a `brain_action` with `ok=False`, the next turn's prompt contains the `[BODY FEEDBACK]` line. Cannot test against live server from Builder seat.

---

## Status

✅ Code committed  
⚠️ Live verification pending
