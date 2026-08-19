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

---

## Builder close-out — DUPLICATE (2026-08-19)

**Status:** DONE (duplicate). Original work already shipped.

**Original commits:**
- `5118542` — WO-111 ACK contract: `runtime/ack_contract.py` (ActionResult · `honest_outcome`).
- `44171c7` — WO-111 builder half: `blender_bridge/anim_trigger.py` gains `wait_for_ack()` +
  `fire_ack()`; `fire()` stamps `action_id`; only `_ANIM_ACK_COVERED` (wave + head gestures)
  wait on real ACKs; clip triggers (jump/gun_*/calm_*/celebrate/spawn_wave) report `unconfirmed`.

**Canonical DONE stamp:** `DONE/0011_WO-111_consume_anim_complete.md` (already present, dated 2026-08-19).

**Re-verified this pass:** `pytest tests/test_wo111_consume_ack.py` — **6/6 passed** in 1.32s.
That includes the dead-executor guard (`test_no_ack_consumer_means_no_confirmation`) — if
`fire_ack` regresses to trusting the file write, that test fails.

**The three sentences eLo produces (via `runtime.ack_contract.honest_outcome`):**
- completed → `"Done — wave confirmed."`
- failed    → `"That didn't work — wave reported a failure."`
- unconfirmed → `"I triggered jump but can't confirm it happened."`

Duplicate closed to `DONE/0011_WO-111_consume_anim_complete_dup_2026-08-19.md`; canonical DONE preserved.
