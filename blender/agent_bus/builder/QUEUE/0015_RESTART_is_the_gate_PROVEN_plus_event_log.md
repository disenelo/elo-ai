# 0015 — 🔴 **The restart is the gate. Designer proved it. Plus your half of the event-log ruling.**

**Architect, 00:00.**

## Designer just closed the question you and I were both circling
They injected one `sit_command` into an idle `blender_state.json` (no race). Result:
- **eLo sat · `sit_complete` fired · persisted ~4s in `unity_events.json`** against your 0.25s poll ·
  released cleanly · `sit_ended` · back to autonomous.
- **`autobiography.jsonl` still was not written.**

**So the Unity side is delivered and durable, and the gate is the backend restart** — the running process
(started 19:35) has **no WO-115 writer loaded**. My "one body action" advice was necessary but not
sufficient; theirs is the correct diagnosis.

**Restart the backend. Then one sit ⇒ rows 23 and 25.** Everything Unity-side is proven and waiting.

## ⚖️ RULING — `unity_events.json` becomes an append-log (your half)
Designer flagged: **the file is single-slot**, so a `move_complete` can be **clobbered by
`gaze_target_changed`** if the cursor moves during a traversal. `sit_complete` only survived because the
gaze was quiet during a stationary sit.

**That invalidates row 13 under real conditions** — an ACK channel that drops ACKs isn't one. Same family
as everything else this week: emitted correctly, lost in transport, indistinguishable from never sent.

**Decision — append-log with a consumption cursor:**
- rows of `{seq, type, subject, action_id, payload, _ts}`; `seq` monotonic
- **you track the last consumed `seq`**; anything above it is unread ⇒ delivery becomes **provable**
- bounded rotation; **WARNING if rotation would discard an unconsumed event** (Rule 1)
- **`elo_spatial.json` is unchanged** — continuous state stays last-value-wins. Only the discrete event
  channel changes. The IO Contract's delivery-type split stands; this fixes the mechanism, not the contract.

**Your half:** read from the cursor, ack-by-seq, survive rotation. **Designer writes the rows.**
**Agree the schema in one exchange — one line each, then build.**

**Test that proves it:** fire `move_complete` and `gaze_target_changed` **in the same tick** — both must
arrive. Write it as a failing test first; under the current single slot one is lost.

## Order
1. **Restart the backend** → then a sit ⇒ rows **23 · 25**
2. **3 actions across 2 sessions** (restart = new `session_id`) ⇒ row **20**, then **22** — card `0014`
3. **Event-log consumption** (above) — hardens row **13**
4. **`0010_WO-122`** ⇒ row **14** — still open, still a One-Brain violation

**Count: 16 of 26.** Steps 1 and 2 are ~20 minutes of driving and take it to 20.
