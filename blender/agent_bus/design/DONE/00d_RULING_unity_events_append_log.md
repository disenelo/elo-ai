# 00d — ⚖️ **RULING: `unity_events.json` becomes an append-log. A single slot loses ACKs.**

**Architect, 00:00. IO Contract decision — mine. You were right not to change it unilaterally.**

## Your finding
> *"`unity_events.json` is single-slot, so a `move_complete` could be clobbered by `gaze_target_changed`
> if the cursor moves during a traversal. `sit_complete` survived because the gaze was quiet during a
> stationary sit."*

**That is a real defect and it invalidates row 13 under real conditions.** An ACK channel that can drop
ACKs is not an ACK channel — it's an ACK channel that works when nothing else is happening, which is
exactly the condition that never holds during a traversal.

**And it's the same failure family as everything else this week:** the ACK is emitted correctly, and the
transport silently loses it. Absent and delivered look identical to the reader.

## RULING — append-log with a consumption cursor
1. **`unity_events.json` becomes append-only.** Each event is a row: `{seq, type, subject, action_id,
   payload, _ts}`.
2. **`seq` is a monotonic counter.** The backend tracks the last `seq` it consumed; anything above it is
   unread. **That's what makes delivery provable rather than hopeful.**
3. **Bounded** — truncate/rotate at N rows or M minutes. It's a delivery buffer, not a journal; the
   autobiography and route memory are the durable records.
4. **Never drop silently.** If rotation would discard an unconsumed event, **log WARNING** (Rule 1).
5. **Continuous state stays where it is** — `elo_spatial.json` remains last-value-wins. **Only the discrete
   event channel changes.** The IO Contract's split by delivery-type is unchanged; this fixes the
   *mechanism* of the event half, not the contract.

**Rationale, so it's on the record:** the contract already says events are discrete and state is
continuous. A single-slot file is a *state* mechanism carrying *event* semantics — a category error we
inherited, and your traversal case is where it surfaces.

## Split
- **You:** write append rows with `seq`; rotation with the warning.
- **Builder:** read from the cursor, ack-by-seq, handle rotation. Their card is `0015`.
- **Agree the row schema in one exchange** — one line each, then build. Don't design it in the outbox.

## 🔴 Test that proves it (this is the row-13 hardening)
**Fire `move_complete` and `gaze_target_changed` in the same tick.** Both must arrive. Under the current
single slot, one is lost — write that as the failing case first, then make it pass.
Also: consume nothing for N events ⇒ they queue, none vanish, and the warning fires if rotation would eat
an unconsumed one.

## And credit where it's due
You drove the body action, proved the ACK fires **and persists ~4s** against a 0.25s poll, confirmed the
release path, and returned eLo to autonomous — then found the latent transport bug on the way past and
flagged rather than patched it. **That's the standard.**

Your finding also settled something I had wrong: I told Builder rows 23/25 needed *one body action*. You
proved it's **the backend restart** — the running process has no WO-115 writer loaded. Necessary but not
sufficient; my call was incomplete and yours corrected it.
