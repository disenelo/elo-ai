# BUILDER 1 → BOARD: WO-B1-0112 Autonomous Watchdog — Built
**Date:** 2026-10-10  
**From:** Builder 1  
**To:** Board  
**Commits:** `9d94681` (watchdog.py) + `start_seat.sh` (same session)

---

## What was built

`tools/watchdog.py` — FSEvents watcher on macOS (Python `watchdog` library) running all three trigger paths.

`tools/start_seat.sh` — shell script each seat calls to begin a one-card session.

---

## Three trigger paths implemented

**PATH 1** — `docs/architecture/_intake/` watched. New `.md` file → Board intake prompt dispatched via `start_seat.sh board`.

**PATH 2** — Each seat's `blender/agent_bus/<seat>/` watched. New `FROM_BOARD_*` file → `_launch_seat_session(seat)` fired. Writes a `WATCHDOG_TRIGGER_<ts>.md` to seat inbox AND calls `start_seat.sh <seat>`.

**PATH 3** — `blender/agent_bus/` root watched. New `FROM_BOARD_REQUEST_*` file → Board review session dispatched.

---

## Token efficiency

`start_seat.sh` passes a single one-card prompt: "Read START_HERE. Check inbox for FROM_BOARD files. Do one card. Commit. File to Board. Exit." No idle loops.

---

## Library

`watchdog` Python library installed in `.venv` via `.venv/bin/pip install watchdog`. Verified importable.

---

## Done when criterion

"David drops a test file in `_intake/` → Board session starts within 5 seconds."  
"Board drops a file in a seat inbox → seat session starts within 5 seconds."

**Board must test both paths.** David must launch the watchdog manually first:
```bash
cd ~/elo-ai && .venv/bin/python3 tools/watchdog.py &
```

Or install the launch agent (planned: `tools/install_watchdog_launchagent.sh` — not yet written).
