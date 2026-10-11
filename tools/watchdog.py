"""tools/watchdog.py — WO-B1-0112: Autonomous Watchdog + Event-Driven Seat Relay.

FSEvents-backed (macOS) watcher that drives seat activity automatically.
Three trigger paths:

  Path 1: David drops .md in docs/architecture/_intake/
           → writes FROM_INTAKE_* file to builder inbox (board intake session picks it up)

  Path 2: Board writes FROM_BOARD_* to blender/agent_bus/<seat>/
           → calls tools/start_seat.sh <seat> to trigger a one-card session

  Path 3: Seat writes FROM_BOARD_REQUEST_* to blender/agent_bus/
           → writes TRIGGER_board_review_* to blender/agent_bus/board_review/

Token efficiency rule: each triggered session does ONE CARD ONLY then exits.

Usage:
    python3 tools/watchdog.py             # run in foreground
    python3 tools/watchdog.py &           # background daemon
    python3 tools/watchdog.py --dry-run   # log events without writing trigger files
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path

# Remove this script's own directory from sys.path to prevent it from shadowing
# the pip-installed `watchdog` package when imported as `from watchdog.events import …`
_SELF_DIR = str(Path(__file__).parent.resolve())
if sys.path and sys.path[0] == _SELF_DIR:
    sys.path.pop(0)

from watchdog.events import FileSystemEventHandler, FileCreatedEvent
from watchdog.observers import Observer

# ── paths ─────────────────────────────────────────────────────────────────────
_ROOT = Path(__file__).resolve().parent.parent          # ~/elo-ai
_INTAKE_DIR   = _ROOT / "docs" / "architecture" / "_intake"
_AGENT_BUS    = _ROOT / "blender" / "agent_bus"
_BUILDER_DIR  = _AGENT_BUS / "builder"
_BOARD_DIR    = _AGENT_BUS / "board_review"
_LOG_FILE     = _ROOT / "tools" / "watchdog.log"
_START_SEAT   = _ROOT / "tools" / "start_seat.sh"

# ── logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [watchdog] %(levelname)s %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(_LOG_FILE, mode="a"),
    ],
)
_log = logging.getLogger("elo.watchdog")

# Known seats — extend if more seats are added
_SEATS = ("builder",)


def _ts() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def _write_trigger(directory: Path, prefix: str, body: str, dry_run: bool) -> Path:
    """Write a trigger .md file to `directory`. Returns the path."""
    path = directory / f"{prefix}_{_ts()}_watchdog.md"
    if dry_run:
        _log.info("[DRY-RUN] would write → %s", path)
        return path
    directory.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    _log.info("wrote → %s", path)
    return path


# ── Path 1: intake drop ───────────────────────────────────────────────────────

class IntakeHandler(FileSystemEventHandler):
    """David drops a file in _intake/ → queue board-intake session."""

    def __init__(self, dry_run: bool = False) -> None:
        super().__init__()
        self.dry_run = dry_run

    def on_created(self, event: FileCreatedEvent) -> None:
        if event.is_directory:
            return
        src = Path(event.src_path)
        if src.suffix not in {".md", ".txt"}:
            return
        _log.info("INTAKE drop detected: %s", src.name)
        body = (
            f"# FROM_INTAKE — {src.name}\n"
            f"**Source:** `_intake/{src.name}`\n"
            f"**Detected:** {datetime.now().isoformat()}\n\n"
            f"David dropped a file in `_intake/`. Read it, write a WO card, "
            f"and file to the correct seat inbox.\n\n"
            f"Source path: `{src}`\n"
        )
        _write_trigger(
            _BUILDER_DIR,
            f"FROM_INTAKE_{src.stem[:40].upper().replace(' ', '_')}",
            body,
            self.dry_run,
        )


# ── Path 2: board → seat ──────────────────────────────────────────────────────

class SeatInboxHandler(FileSystemEventHandler):
    """Board writes FROM_BOARD_* to a seat directory → trigger seat session."""

    def __init__(self, seat: str, dry_run: bool = False) -> None:
        super().__init__()
        self.seat = seat
        self.dry_run = dry_run

    def on_created(self, event: FileCreatedEvent) -> None:
        if event.is_directory:
            return
        src = Path(event.src_path)
        if not src.name.startswith("FROM_BOARD") or src.suffix != ".md":
            return
        _log.info("SEAT INBOX event: %s → seat=%s", src.name, self.seat)
        if not self.dry_run and _START_SEAT.exists():
            import subprocess
            try:
                subprocess.Popen(
                    ["bash", str(_START_SEAT), self.seat, str(src)],
                    close_fds=True,
                )
                _log.info("launched start_seat.sh for seat=%s", self.seat)
            except Exception as _e:
                # WO-105: safe to swallow in the observer callback — a launch failure
                # must not crash the watcher loop. Log at WARNING so it is visible.
                _log.warning(
                    "start_seat.sh launch FAILED for seat=%s: %s — "
                    "trigger file is still present for manual pickup", self.seat, _e
                )
        elif self.dry_run:
            _log.info("[DRY-RUN] would launch start_seat.sh %s %s", self.seat, src)


# ── Path 3: seat → board review ───────────────────────────────────────────────

class BoardRequestHandler(FileSystemEventHandler):
    """Seat writes FROM_BOARD_REQUEST_* to agent_bus root → trigger board review."""

    def __init__(self, dry_run: bool = False) -> None:
        super().__init__()
        self.dry_run = dry_run

    def on_created(self, event: FileCreatedEvent) -> None:
        if event.is_directory:
            return
        src = Path(event.src_path)
        if not src.name.startswith("FROM_BOARD_REQUEST") or src.suffix != ".md":
            return
        _log.info("BOARD REQUEST detected: %s", src.name)
        body = (
            f"# TRIGGER board review — {src.name}\n"
            f"**Source:** `{src.name}`\n"
            f"**Detected:** {datetime.now().isoformat()}\n\n"
            f"A seat filed a board request. Read `{src}`, review it, "
            f"sign off or reject, then exit.\n"
        )
        _write_trigger(
            _BOARD_DIR,
            "TRIGGER_board_review",
            body,
            self.dry_run,
        )


# ── Main ──────────────────────────────────────────────────────────────────────

def run(dry_run: bool = False) -> None:
    _log.info("eLo watchdog starting (dry_run=%s)", dry_run)
    _log.info("intake:    %s", _INTAKE_DIR)
    _log.info("agent_bus: %s", _AGENT_BUS)

    observer = Observer()

    # Path 1 — intake
    _INTAKE_DIR.mkdir(parents=True, exist_ok=True)
    observer.schedule(IntakeHandler(dry_run), str(_INTAKE_DIR), recursive=False)

    # Path 2 — seat inboxes
    for seat in _SEATS:
        seat_dir = _AGENT_BUS / seat
        seat_dir.mkdir(parents=True, exist_ok=True)
        observer.schedule(SeatInboxHandler(seat, dry_run), str(seat_dir), recursive=False)

    # Path 3 — board request root
    observer.schedule(BoardRequestHandler(dry_run), str(_AGENT_BUS), recursive=False)

    observer.start()
    _log.info("watchdog running — Ctrl+C to stop")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        _log.info("watchdog stopping")
        observer.stop()
    observer.join()
    _log.info("watchdog stopped")


def main() -> None:
    parser = argparse.ArgumentParser(description="eLo autonomous watchdog")
    parser.add_argument("--dry-run", action="store_true", help="log events without writing trigger files")
    args = parser.parse_args()
    run(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
