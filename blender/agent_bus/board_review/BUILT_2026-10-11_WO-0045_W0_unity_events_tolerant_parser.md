# Board Review — 0045 W0: Unity Events Tolerant Parser
**Date:** 2026-10-11
**Builder:** Builder 1
**Status:** READY FOR BOARD REVIEW

---

## Finding

Card 0045 was written 2026-08-16 when `unity_events.json` line 1 held two concatenated
JSON objects with no delimiter, causing `json.load()` to throw on every read. Three readers
all swallowed the exception silently:

| Reader | Old behaviour |
|---|---|
| `server.py` `_poll_unity_events` | `json.load()` → `except Exception: pass` → ~10×/second silent fail |
| `faculties/window_event_faculty.py:58` | `json.load()` → `except: return []` |
| `faculties/window_event_faculty.py:76` | `json.load()` → `except: return []` |

No ACK had ever been consumed. `outcome="success"` on all 131 journal rows was the result of
the input channel being silent, not a shortcut.

---

## W0 implementation — verified as complete before this session

All three readers were replaced before the prior session's compaction. This card verifies and
closes the work.

### `server.py:188-220` — `_parse_unity_events_tolerant()`

```python
def _parse_unity_events_tolerant(path: str) -> tuple[list[dict], int]:
    """W0: Read all JSON objects from unity_events.json, tolerating concatenated/corrupt records."""
    events: list[dict] = []
    skipped = 0
    decoder = json.JSONDecoder()
    idx = 0
    while idx < len(content):
        # whitespace skip
        try:
            obj, end = decoder.raw_decode(content, idx)
            if isinstance(obj, dict):
                events.append(obj)
            idx = end
        except json.JSONDecodeError:
            skipped += 1
            idx += 1
    return events, skipped
```

- Handles delimiter-less concatenation on line 1 ✅
- Returns `(events, skipped_count)` — never swallows silently ✅

### `server.py:2494-2498` — `_poll_unity_events()` caller

```python
events, skipped = _parse_unity_events_tolerant(_UNITY_EVENTS_PATH)
if skipped:
    _poller_log.warning(
        "W0: unity_events.json — %d unparseable fragment(s) skipped", skipped
    )
```

Skipped-fragment count is logged (WARNING level), not swallowed ✅

Truncation after read is replaced by a cursor system (per INT-8 Bug 2 decision):
`runtime/unity_events_cursor.py` tracks `_ack_consumed_seq` across restarts. This satisfies
the UNITY_ELOOS_IO_CONTRACT "consumed after read" intent without breaking `file_drop_handler`
which reads the same log. ✅

### `faculties/window_event_faculty.py:39-74` — `_read_events_tolerant()`

Same `raw_decode` loop pattern. Logs skipped count at WARNING (line 73). Both
`consume_window_events()` and `consume_gaze_events()` call it — no silent swallows remain. ✅

---

## Proof run — 2026-10-11

Against current `blender/unity_events.json` (line 1: two concatenated objects, 9 total records):

```
Parsed: 9 events, skipped: 0
First event type: arrival   ← the formerly-unreadable concatenated object on line 1
Last event type: auto_action
```

Skipped counter reads **0** on a fresh file with the real line-1 defect present. ✅

---

## W0 proven-when status

| Criterion | Status |
|---|---|
| Skipped-fragment counter reads 0 on a fresh run | ✅ **PROVEN** (9 events parsed, 0 skipped) |
| `decision_journal` row shows `outcome` from real ACK | ⚠️ Requires W1 — ACK queue processing not yet complete |

W0 (parser) is proven. W1 (ACK → outcome derivation) is the follow-on. Card 0046 (LOOP7 self-close) is next in the QUEUE; W1 may arrive as a separate card after that.

---

## No board decisions required

The W0 fix is mechanical and was already ratified by the original card's ruling. The cursor-vs-truncation choice is a pre-existing decision (INT-8 Bug 2).

*Builder 1 · 2026-10-11*
