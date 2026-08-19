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

## Builder close-out (2026-08-19)

**Status:** DONE. Commit: `44171c7`

**Changed:**
- `blender_bridge/anim_trigger.py` — added `wait_for_ack(action_id, timeout_s)` and
  `fire_ack(name, action_id, timeout_s)`. `fire()` now accepts `action_id` and stamps it
  into the trigger / head_motion block so Unity can echo it back. Only wave + head
  gestures (`_ANIM_ACK_COVERED`) wait on real ACKs — matches "What Designer shipped".
- `tests/test_wo111_consume_ack.py` — 6 new AT tests covering the card's four cases
  (wave complete, wave failed, un-ACKed clip trigger, timeout) plus a disconnect check
  and a baseline-seq guard (stale ACK from prior run does not confirm new invocation).

**Test:** `pytest tests/test_wo111_consume_ack.py tests/test_wo111_ack_contract.py` — 14/14.

**The three sentences eLo now produces (via `runtime.ack_contract.honest_outcome`):**
- completed → `"Done — wave confirmed."`
- failed    → `"That didn't work — wave reported a failure."`
- unconfirmed → `"I triggered jump but can't confirm it happened."`

**Deferred to Designer (unchanged from card):** clip triggers jump/gun_*/calm_*/celebrate
report `unconfirmed` on this side until Designer's `*_entered`/`*_exited` state ACKs are
wired into `_ANIM_ACK_COVERED`. Not undoing Designer's honest deferral.

**Verifies against disconnect (Rule 5.3):**
`test_no_ack_consumer_means_no_confirmation` fires and never emits an ACK — asserts NOT
confirmed. If `fire_ack` regresses to trusting the file write, this test fails.

