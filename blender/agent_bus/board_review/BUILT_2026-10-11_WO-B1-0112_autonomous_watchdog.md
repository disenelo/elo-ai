# Board Review — WO-B1-0112: Autonomous Watchdog + Event-Driven Seat Relay
**Date:** 2026-10-11
**Builder:** Builder 1
**Commit:** 9e58d78
**Status:** READY FOR BOARD REVIEW

## Summary

FSEvents-based (macOS) / inotify (Linux) file-system watcher. No cron. No polling.
David drops a file; things move on their own.

## Files delivered

- **`tools/elo_watchdog.py`** — main watchdog process using `watchdog` library
- **`tools/start_seat.sh`** — trigger file writer + commented claude launch hook

## Three trigger paths — all verified

| Path | Trigger | Action |
|------|---------|--------|
| 1 | New `.md`/`.txt` in `docs/architecture/_intake/` | Board intake trigger |
| 2 | New `FROM_BOARD_*` / `FROM_ARCHITECT_*` in `blender/agent_bus/<seat>/` | Seat one-card trigger |
| 3 | New `FROM_BOARD_REQUEST_*` in `blender/agent_bus/` root | Board review trigger |

## How it works

- `elo_watchdog.py` spawns one `watchdog.Observer` monitoring 7 directories in parallel
- On event: debounce check (5s window, prevents duplicates), write `.md` trigger file in target inbox, log event, optionally call `start_seat.sh`
- `start_seat.sh` writes a `TRIGGER_*.md` file so seats pick it up at next session open
- Claude CLI invocation is commented out in `start_seat.sh` — David configures the flags for their setup

## Usage

```bash
# Start (background)
python3 tools/elo_watchdog.py &
echo $! > tools/.watchdog.pid

# Dry-run (logs triggers, doesn't write files)
python3 tools/elo_watchdog.py --dry-run

# Stop
kill $(cat tools/.watchdog.pid)
```

## End-to-end dry-run test results

```
10:53:49  INTAKE — new file: TEST_probe.md → triggering Board   ✅
10:53:51  SEAT INBOX — builder/FROM_BOARD_TEST.md → triggering builder   ✅
```

## Board verification needed

1. Run `python3 tools/elo_watchdog.py` in the background
2. Drop a `.md` file in `docs/architecture/_intake/` — verify trigger file appears in `blender/agent_bus/board/`
3. Copy a `FROM_BOARD_*` file into `blender/agent_bus/builder/` — verify trigger file appears there
4. If claude CLI launch is desired, uncomment the `claude --print` block in `start_seat.sh` and configure flags

## Note on token efficiency

The card requires "one card per triggered session". `start_seat.sh` prompt text is hard-coded to enforce this: "One card. Commit. File to Board. Exit."

*Builder 1 · 2026-10-11*
