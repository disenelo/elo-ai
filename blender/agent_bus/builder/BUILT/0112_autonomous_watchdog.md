# WO-B1-0112 — Autonomous Watchdog + Event-Driven Seat Relay
**Seat:** Builder 1  
**Priority:** P0  
**Date:** 2026-10-11  
**Commit:** 69a5b84

---

## What was built

`tools/watchdog.py` — FSEvents-based file watcher (macOS native events via Python `watchdog` library, not polling, not cron).

### Three trigger paths — all live

**Path 1 — David drops in `_intake/`**  
`docs/architecture/_intake/` (created by watchdog if missing). Any `.md`/`.txt`/`.markdown` file → macOS notification: "Board intake — New drop: {name}". Trigger marker written to `data/triggers/board_intake_*.trigger`.

**Path 2 — Board drops in seat inbox**  
Each seat inbox watched at directory level (non-recursive — doesn't watch QUEUE/ or processed/ subdirs). `FROM_BOARD_*.md` → macOS notification: "eLo-AI — {seat} inbox — New card: {name}. Run: bash tools/start_seat.sh {seat}". Trigger marker: `seat_{seat}_*.trigger`.

**Path 3 — Seat files to Board**  
`blender/agent_bus/` watched (non-recursive). `FROM_BOARD_REQUEST_*.md` → macOS notification: "eLo-AI — Board review — Seat filed: {name}". Trigger marker: `board_review_*.trigger`.

### Self-import guard
File is named `watchdog.py` to match the card spec. Added `sys.path` guard at top to exclude the file's own directory before `from watchdog.events import ...` so the installed package wins over the local file.

### Smoke tested
All three paths fired within 2 seconds in a local test. Log confirmed at `data/watchdog.log`. Trigger files written to `data/triggers/`.

### How to run
```bash
python3 tools/watchdog.py          # silent — macOS notifications only
python3 tools/watchdog.py --log    # verbose stdout + log
```

Background (non-blocking):
```bash
python3 tools/watchdog.py --log &
```

### Not tested (Board verify)
End-to-end: drop a file in `_intake/` → Board processes it → writes WO → files to seat inbox → seat notification fires. That chain requires a Board session to be active.

*Builder 1 · 2026-10-11*
