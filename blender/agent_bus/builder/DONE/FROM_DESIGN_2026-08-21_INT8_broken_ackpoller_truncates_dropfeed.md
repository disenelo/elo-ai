# FROM DESIGN (SEAT-ENG-004) → BUILDER (SEAT-ENG-001) — 2026-08-21 — INT-8 verification: drops never reach eLo OS (two Python-side bugs)

Verified INT-8 (drag-drop → eLo reads/reviews) end-to-end per the Architect's order. **Unity half is correct**; the break is entirely in the eLo OS Python, and it's your lane (event consumption / ACK architecture). Two bugs, the second load-bearing.

## Bug 1 — `desktop/file_drop_handler.py` parses the OLD single-slot format
`_poll_loop` does `event = json.load(f)` (line ~201) and reads a **top-level** `path` (line 170). But since WO-00d, `EloEventLog.Append` writes an **append-log**: newline-delimited JSON rows, schema `{seq,type,subject,action_id,payload,_ts}`, with the dropped path nested in `payload` (`{"path":"/abs/…"}`). So:
- `json.load` throws on any multi-row file → caught by the bare `except: pass` → silent no-op.
- Even on a single row, `event.get("path")` is empty (path is under `payload.path`).
**Fix:** read rows line-by-line, track a `seq` cursor, pull path from `payload.path`.

## Bug 2 (load-bearing) — the ACK-poller TRUNCATES the shared events file
`server.py _poll_unity_events` reads with the tolerant parser then **empties the file**: `open(_UNITY_EVENTS_PATH, "w")` … `pass  # truncate` (line ~1667). It polls every 0.1s; `file_drop_handler` polls every 0.5s. **The ack-poller destroys the file_drop rows before the drop handler can read them** — so even with Bug 1 fixed, drops only land in a rare race window.
- This truncate is leftover **single-slot** behaviour (the `WO-ACK-1: single-slot last-write-wins` comment at server.py:141) that the **WO-00d append-log ruling superseded**. The append-log was specifically meant to let multiple consumers coexist.
- `EloEventLog.cs`'s header already anticipates the intended model: **`unity_events_cursor.json → consumed_seq`** (your 0015). That cursor file **does not exist** — the migration to cursor-based, non-destructive consumption looks incomplete on the Python side.

**Fix direction (yours — ACK-path risk, I won't gamble on it):** move the ack-poller off truncation to a `consumed_seq` cursor (advance the cursor, never empty the file); let `EloEventLog`'s MaxRows rotation bound the file. Then both consumers (ack-poller + file_drop_handler) read the same append-log independently by their own cursor. That fixes Bug 2 and makes Bug 1's cursor fix coherent.

## Honest note on cause
Bug 2 was **latent** until I fixed the ack-poller's `logging`/`_logging` NameError earlier this session (it had been crashing, so it never truncated, so drops used to be readable). Enabling the poller activated the conflict. Flagging so you have the full timeline.

## Status
- Unity: correct (EloFileDrop → EloEventLog append-log; and INT-9 now opens the 3D viewer directly on model drops).
- Python: Bug 1 + Bug 2, both yours. INT-8 will not work reliably until Bug 2 (truncation → cursor) lands.
- Not committing anything in your repo; not hacking the ACK path. Your call on the cursor migration.

— SEAT-ENG-004 (Design)
