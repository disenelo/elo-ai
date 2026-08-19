# 0011 — ⚡ **Row 13 hand-off: Designer's ACKs are live. Stop trusting the file write.**

**Seat:** builder · **Priority:** P1, small · **Gate?** none · **Designer commit `c571f59`**

## What Designer shipped
- **`anim_complete`** — wave + head gestures ACK on **real completion**
- **`anim_failed`** — failures ACK too, with a reason
- Deferred honestly: **animator-clip triggers (jump/gun/calm) are NOT ACKed yet** — they said outright that
  faking completion would be *"the dishonesty this row fixes."* Correct call.

## Your half
`blender_bridge/anim_trigger.py:34` currently **returns `True` on a file write**. Replace it:
1. **Read `anim_complete` / `anim_failed`** from `unity_events.json`; resolve against the `action_id`.
2. **A write is not a completion.** The trigger call returns *pending* until an ACK arrives.
3. **`anim_failed` ⇒ eLo says it didn't work.** Route through the honesty layer.
4. **Timeout ⇒ reported failure**, never silence.
5. **The un-ACKed clip triggers (jump/gun/calm) must report `unconfirmed`, not success.** Do not let them
   inherit the old `True`. Designer deferred them honestly; don't undo that on this side.

## Test (without David)
- Wave that completes ⇒ ACK matched, eLo may claim it.
- Wave that fails ⇒ `anim_failed` ⇒ **eLo says it didn't work** (assert the wording).
- A clip trigger with no ACK path ⇒ status `unconfirmed`, **not** success.
- Timeout ⇒ reported failure.

## Done when
Committed. **Outbox: the sentence eLo produces for each of completed / failed / unconfirmed.**
Row 13 goes VERIFIED when a broken executor makes him say so — not before.
