# Board Review — WO-B1-0115: Ack Before Execute (auto-wired)
**Date:** 2026-10-12
**Builder:** Builder 1
**Status:** READY FOR BOARD REVIEW

---

## What the card asked for

Every tool call in `server.py` must emit a pre-ack phrase BEFORE the tool executes. David should never wait in silence for any tool.

---

## What was built

**`runtime/pre_ack.py`** — extended phrase banks:
- Added: `web_search`, `image_gen`, `model_gen`, `reminder`
- Existing banks unchanged: `document_write`, `device_control`, `spotify_play`, `default`

**`server.py`** — 9 `pre_ack.emit()` injection points added, each wrapped in `try/except` so a TTS failure never degrades the main turn:

| Tool | Location | Bank used |
|------|----------|-----------|
| Spotify | Line ~2860 — after `parse()` detects a Spotify command, before `handle()` executes | `spotify_play` |
| File agent | Line ~3483 — after `_fp_has()` + confirm, before `_fp_exec()` | `document_write` |
| Computer control | Line ~3521 — after `_cc_has()` + confirm, before `_cc_exec()` | `device_control` |
| Image gen | Line ~3856 — after regex match, before `_img_generate()` | `image_gen` |
| Model gen | Line ~3885 — after regex match, before background thread launch | `model_gen` |
| Research (answer_gap) | Line ~4153 — inside the research try block, before `_rs_gap()` | `web_search` |
| Web search (command) | Line ~4178 — after `_ws_resolve()`, before `_ws_lookup()` | `web_search` |
| Web search (intent) | Line ~4220 — after guards pass, before `_wsearch()` | `web_search` |
| Reminder | Line ~4251 — after `is_reminder_intent()` match, before `_set_reminder()` | `reminder` |

For Spotify specifically: `spotify_play.parse(raw)` is called first (fast detection, no API call). Only if it returns non-None is pre_ack fired, then `handle(raw)` executes. This prevents pre_ack firing on unrelated "play" mentions.

---

## Verification

Syntax check passed: `python3 -c "import ast; ast.parse(open('server.py').read())"` → OK.

All 9 injection points confirmed via `grep -n "pre_ack\|_pa_" server.py`.

---

## Board test

Board should test 3 different tool-requiring requests:

1. **"Search for [topic]"** → should hear "Looking that up." / "Give me a second." BEFORE search results arrive
2. **"Play [playlist] on Spotify"** → should hear "One second." / "Let me find that." BEFORE Spotify API response
3. **"Set a reminder for [X]"** → should hear "Setting that." / "On it." BEFORE confirmation

First thing eLo says each time must be the pre-ack phrase, not silence, not the result.

---

## Commit

`0c77a4f`

---

## Board decisions required

None.

*Builder 1 · 2026-10-12*
