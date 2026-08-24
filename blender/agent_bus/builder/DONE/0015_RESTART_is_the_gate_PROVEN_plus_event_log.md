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

---

## Result — Builder half of the event-log ruling (step 3)

**Commit:** `2805f57` — *0015 builder: unity_events append-log cursor — Builder half of RULING 00d*

### What changed
- **`runtime/unity_events_cursor.py`** (new). `read_cursor` / `write_cursor` for
  `unity_events_cursor.json`; `iter_events_from(seq_after, path)` yields NDJSON rows with
  `seq > seq_after`; `max_seq(path)` returns the highest seq in the file. Cursor write is
  atomic (`mkstemp` + `os.replace`); no straggler temp files on failure.
- **`server.py::_poll_unity_events`** — loads the persisted cursor at start (survives
  restart because Designer keeps `seq` monotonic across relaunch, per
  `FROM_DESIGN_2026-08-15_unity_events_append_log_schema.md`) and writes it after each
  read batch. Designer now has a live watermark and won't need to warn conservatively on
  every rotation.
- **`tests/test_0015_unity_events_append_log_cursor.py`** (5/5).

### Test — the row-13 hardening
- **AT-0015-1** — same-tick `move_complete` + `gaze_target_changed` both arrive. Under the
  old single slot one was lost; under the append-log both rows land and both are visible
  to the cursor consumer.
- **AT-0015-2** — consume nothing for 25 rows: all 25 are visible (backlog queues, none
  vanish). This is the "delivery buffer, not state slot" property.
- **AT-0015-3** — persistence roundtrip: after writing `consumed_seq`, a fresh reader
  loads it and sees nothing already-consumed; only new rows are yielded.
- **AT-0015-4** — head-rotation trim: reader with cursor at N still sees every surviving
  row above N (discarded-above-cursor is Designer's WARNING; the reader stays sane).
- **AT-0015-5** — cursor write is atomic; no `.cursor.*` stragglers, valid JSON on read.

### Non-regression
- `test_int8_event_consumers.py` 2/2 · `test_int8a_file_drop_roundtrip.py` 9/9 ·
  `test_wo099b_gaze_consume.py` 7/7 · `test_wo111_consume_ack.py` 6/6.

### Handshake state
Cursor file will appear at `blender/unity_events_cursor.json` on the next backend restart
(the ACK poller writes it after the first read batch). Once present, Designer's rotation
warns only when a truly unread row would be discarded.

### Not in scope (deliberately)
- Step 1 (backend restart → rows 23/25) — mechanical, not code-shaped.
- Step 2 (three actions across two sessions → row 20/22) — belongs to card `0014`.
- Step 4 (`0010_WO-122` → row 14) — its own card.

