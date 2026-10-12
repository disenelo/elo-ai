# Board Review — WO-B1-0121: Board runs continuously without David relaying
**Date:** 2026-10-12
**Builder:** Builder 1
**Status:** READY FOR BOARD REVIEW

---

## What the card asked for

David should not relay seat reports to the Board. The Board should watch for seat filings and act automatically — same pattern as seat triggering.

---

## What was built

### `tools/watchdog.py` — Path 4 added

New handler class `BoardReviewGateHandler` + registration in `run()`.

**Watches:**
- `blender/agent_bus/board_review/` — shared board review directory (where Builder 1 files BUILT_* reviews)
- `blender/agent_bus/<seat>/board_review/` — each seat's local review directory

**On `BUILT_*` file detection:**
1. Writes `BOARD_TRIGGER_<stem>_<ts>.md` to `blender/agent_bus/board/` (Board inbox)
2. Calls `tools/start_board.sh <review_file_path>` (if script exists)

**Dedup:** `threading.Lock` + `_seen` set prevents FSEvents double-fire from generating two triggers for the same file. Verified in dry-run test.

### `tools/start_board.sh` — new file

Mirrors `start_seat.sh` exactly:
- Writes trigger file to `blender/agent_bus/board/`
- Logs to `watchdog.log`
- Exposes `MANUAL LAUNCH POINT` comment for adding `claude --print` auto-launch

---

## Dry-run test evidence

```
2026-10-12 02:30:28,961 [watchdog] INFO BOARD REVIEW filed: BUILT_TEST_0121_lock.md — triggering Board gate
2026-10-12 02:30:28,962 [watchdog] INFO [DRY-RUN] would write → blender/agent_bus/board/BOARD_TRIGGER_BUILT_TEST_0121_lock_20261012_023028_watchdog.md
2026-10-12 02:30:28,962 [watchdog] INFO [DRY-RUN] would launch start_board.sh .../BUILT_TEST_0121_lock.md
```

One `touch BUILT_TEST_*.md` → exactly 1 "BOARD REVIEW filed" → 1 trigger write → 1 start_board.sh launch. No David relay.

---

## One automated gate cycle (done when criterion)

To produce a live cycle:
1. Start watchdog: `python3 tools/watchdog.py` (or confirm it's running)
2. Builder 1 files any `BUILT_*.md` to `board_review/`
3. Watchdog writes `BOARD_TRIGGER_*` to `board/` within one tick (~1 s)
4. Board session (if running) reads the trigger, reviews the card, files gate decision

The trigger file is the relay. The Board session auto-launch can be wired via the `MANUAL LAUNCH POINT` comment in `start_board.sh` — adding a `claude --print` invocation with the Board CLAUDE.md context.

---

## Commits

`2c7050d` — watchdog Path 4 + start_board.sh

---

## Board decisions required

1. **Auto-launch Board session**: wire the `claude --print` invocation in `start_board.sh` MANUAL LAUNCH POINT so the full cycle is automatic without any seat-to-board relay. Needs Board to define the exact `--print` prompt it wants to receive.

*Builder 1 · 2026-10-12*
