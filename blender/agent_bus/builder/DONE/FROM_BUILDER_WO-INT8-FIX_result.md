# BUILDER RESULT — WO-INT8-FIX
Date: 2026-09-11
Status: ALREADY DONE — both bugs fixed in prior sessions; this card is the missing verification record

---

## Bug 1 — file_drop_handler.py (fixed, verified)

**Diagnosis (FROM_DESIGN_2026-08-21_INT8):** `json.load(f)` reads file as single JSON; `event.get("path")` reads top-level path. Append-log schema puts path in `payload.path`.

**Current state:** `desktop/file_drop_handler.py:197-238` — `_poll_loop()` is correctly implemented:
- Line 198: comment `# INT-8 Bug 1: read NDJSON line-by-line; seq cursor; path from payload.path`
- Line 204: `lines = f.readlines()` (line-by-line, not `json.load`)
- Line 212: `event = json.loads(line)` (parse each line)
- Line 219-224: seq cursor (`_last_seq`) dedup
- Line 232: `raw_path = (event.get("payload") or {}).get("path") or event.get("path", "")` (payload.path first)

Bug 1: **FIXED** ✅

---

## Bug 2 — ACK-poller truncation (fixed, verified)

**Diagnosis (FROM_DESIGN_2026-08-21_INT8):** `server.py _poll_unity_events` truncated `unity_events.json` via `open(path, "w")` after reading. Polling every 0.1s destroyed events before file_drop_handler (polling 0.5s) could read them.

**Current state:** `server.py:1997-2089` — `_poll_unity_events()`:
- Line 1997-2003: imports `runtime.unity_events_cursor` (cursor-based consumption)
- Line 2006: `_ack_consumed_seq: int = _rc()` — reads persisted cursor
- Line 2017: `if _ev_seq is not None and _ev_seq <= _ack_consumed_seq: continue` — seq-based dedup, no delete
- Line 2081-2083: advances cursor, writes to `unity_events_cursor.json` — never touches the events file
- Line 2084: `# never truncate — file_drop_handler reads the same append-log via its own cursor`

Bug 2: **FIXED** ✅

---

## Residual (not a regression — legacy `sit_ended` handler)

`server.py:3562-3576` — legacy `sit_ended` single-slot consumer still uses `json.load` + truncate on the events file. This is a separate code path for the pose `sit_ended` event and was not part of INT-8 scope. It pre-dates the append-log. Not fixing here — separate WO if needed.

---

## DoD

- [x] Bug 1 (file_drop_handler.py parse format) — FIXED in prior session, verified ✅
- [x] Bug 2 (ACK-poller truncation → cursor-based) — FIXED in prior session, verified ✅
- [x] `runtime/unity_events_cursor.py` exists and is imported correctly ✅
- [x] file_drop_handler.py uses seq cursor + payload.path schema ✅
- [x] No changes made — already correct; this card records the missing verification

FREEZE check:
- `runtime/executive.py`: NOT TOUCHED ✅
- `prompts/living_presence_spec.txt`: NOT TOUCHED ✅

— Builder · 2026-09-11
