# WO-B1-0112 — Autonomous Watchdog + Event-Driven Seat Relay
**Seat:** Builder 1  
**Priority:** P0 — foundational for 20-day sprint  
**Source:** [DAVID 2026-10-10] "Plan it and get automated ways to get it to keep rolling not use too many tokens and I can put things in folders and things move on their own. REALISTIC not old crons and schedules that don't work we want working systems"  
**Date:** 2026-10-10

---

## What

A file-system event watcher (FSEvents on macOS — not polling, not cron) that drives seat activity automatically. David drops a file; things move on their own.

---

## Three trigger paths

### Path 1 — David drops a file in `_intake/`
`docs/architecture/_intake/` watched.  
New file → Board intake session starts → reads file → writes WO → files to correct seat inbox.  
David never has to relay manually.

### Path 2 — Board files to seat inbox
`blender/agent_bus/<seat>/` watched per seat.  
New `FROM_BOARD_*` file → seat's VS Code session resumes or is triggered via shell notification.  
Seat runs: reads inbox → does card → commits → files to Board → exits.

### Path 3 — Seat files to Board
`blender/agent_bus/FROM_BOARD_REQUEST_*/` watched.  
New request file → Board review session starts → tests card → signs off or rejects → exits.

---

## Token efficiency rule (hard)

Each triggered session is ONE CARD only. Read inbox → pick highest priority unstarted card → do it → commit → file to Board → EXIT. No idle. No open-ended loops. Estimated: 10–40k tokens per card. 20 days × 24 hours × seats = hundreds of cards possible at this rate.

---

## Implementation

**`tools/watchdog.py`** — Python script using `watchdog` library (FSEvents backend on macOS, inotify on Linux).

```python
# Core structure (spec — Builder 1 implements)
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class InboxHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.src_path.endswith('.md') and 'FROM_BOARD' in event.src_path:
            trigger_seat_session(seat_from_path(event.src_path))

class IntakeHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.src_path.endswith('.md'):
            trigger_board_intake(event.src_path)
```

Trigger mechanism: write a `.trigger` file or call `open -a "Visual Studio Code" --args <session>`. Seat Claude Code sessions pick up via their START_HERE check at session start.

**`tools/start_seat.sh`** — shell script each seat calls to begin a one-card session:
```bash
#!/bin/bash
SEAT=$1
cd ~/elo-ai
claude --continue --session $SEAT "Read blender/agent_bus/$SEAT/START_HERE.md. Check inbox for new FROM_BOARD files. Do one card. Commit. File to Board. Exit."
```

---

## David's folder drops

David can drop plain text or markdown in `_intake/` with a rough idea. Example:
- `eLo should greet me by name when I haven't talked to him in a while.txt`
→ Watchdog catches it → Board parses it → writes WO → queues to Builder 1

No formatting required from David. The Board cleans it up.

---

## Done when

1. `tools/watchdog.py` runs as background process on David's Mac (launch agent or manual `python3 tools/watchdog.py &`)
2. David drops a test file in `_intake/` → Board session starts within 5 seconds, processes it, files WO to a seat inbox
3. Board drops a file in a seat inbox → seat session starts within 5 seconds
4. Board verifies end-to-end: drop → WO → seat → commit → Board review

File to Board for sign-off. Board tests all three paths.
