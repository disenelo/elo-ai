# Board Review — WO-0112: Autonomous Watchdog + Event-Driven Seat Relay
**Date:** 2026-10-11
**Builder:** Builder 1
**Status:** READY FOR BOARD REVIEW

---

## Card scope

FSEvents-backed file-system watcher (not polling, not cron) that drives seat activity
automatically. David drops a file; things move on their own.

Three trigger paths:
1. `docs/architecture/_intake/` — `.md`/`.txt` drop → `FROM_INTAKE_*` written to builder inbox
2. `blender/agent_bus/<seat>/` — `FROM_BOARD_*.md` → `tools/start_seat.sh <seat>` launched
3. `blender/agent_bus/` root — `FROM_BOARD_REQUEST_*.md` → `TRIGGER_board_review_*` in board_review/

Token efficiency: one card per triggered session. Each session reads inbox, does one card,
commits, files to board, exits.

---

## Implementation

**`tools/watchdog.py`** (new) — `IntakeHandler`, `SeatInboxHandler`, `BoardRequestHandler`,
`_write_trigger()`. Fixes self-shadowing: removes `tools/` from `sys.path[0]` so `import watchdog`
resolves the pip package, not the script itself. `--dry-run` flag for safe testing.

**`tools/start_seat.sh`** — already existed (pre-built for this card).

Run: `python3 tools/watchdog.py` (foreground) or `python3 tools/watchdog.py &` (daemon)

---

## Commit

- `422ab2d` — WO-0112: autonomous watchdog — FSEvents file-drop relay

---

## Tests — `tests/test_watchdog.py`

```
python3 -m pytest tests/test_watchdog.py -v
→ 12 passed in 0.17s
```

| Test | Result |
|------|--------|
| intake md triggers write | ✅ |
| intake txt triggers write | ✅ |
| intake ignores non-md | ✅ |
| intake ignores directories | ✅ |
| intake dry-run | ✅ |
| seat inbox FROM_BOARD triggers start_seat | ✅ |
| seat inbox ignores non-FROM_BOARD | ✅ |
| seat inbox dry-run no Popen | ✅ |
| board request triggers review | ✅ |
| board request ignores non-request | ✅ |
| write_trigger creates file | ✅ |
| write_trigger dry-run no file | ✅ |

WO-105 lint passes (no new silent failures in watchdog.py).

---

## Board decisions required

None. Board should test the end-to-end path: drop a file in `_intake/`,
confirm FROM_INTAKE_* appears in `blender/agent_bus/builder/`.

*Builder 1 · 2026-10-11*
