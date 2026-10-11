#!/usr/bin/env python3
"""
tools/watchdog.py — WO-B1-0112
FSEvents-based file watcher for eLo-AI seat automation.

Three trigger paths (all non-polling, FSEvents on macOS):

  Path 1 — David drops a file in docs/architecture/_intake/
            → Board intake triggered immediately.

  Path 2 — Board drops FROM_BOARD_*.md in a seat inbox
            → Seat session alerted (notification + log entry).

  Path 3 — Seat drops FROM_BOARD_REQUEST_*.md in blender/agent_bus/
            → Board review session alerted.

Token efficiency: each trigger is ONE CARD. The dispatcher (start_seat.sh)
picks the oldest card, surfaces it, moves it to processed/. This script's
job is only to detect new files and write trigger markers — the sessions
do the actual work.

Usage:
    python3 tools/watchdog.py          # runs until Ctrl+C
    python3 tools/watchdog.py --log    # verbose event logging
"""
from __future__ import annotations

import sys
import argparse
import os
import subprocess
import time
from datetime import datetime
from pathlib import Path

# Remove this file's own directory from sys.path so `import watchdog` resolves
# to the installed watchdog package and not this file (name collision).
_self_dir = str(Path(__file__).resolve().parent)
sys.path = [p for p in sys.path if p not in (_self_dir, "")]

from watchdog.events import FileSystemEventHandler, FileCreatedEvent  # noqa: E402
from watchdog.observers import Observer  # noqa: E402

# ── Paths ─────────────────────────────────────────────────────────────────────
REPO_ROOT = Path(__file__).resolve().parent.parent
INTAKE_DIR   = REPO_ROOT / "docs" / "architecture" / "_intake"
AGENT_BUS    = REPO_ROOT / "blender" / "agent_bus"
LOG_FILE     = REPO_ROOT / "data" / "watchdog.log"
TRIGGER_DIR  = REPO_ROOT / "data" / "triggers"

SEAT_INBOXES = {
    "builder":  AGENT_BUS / "builder",
    "builder2": AGENT_BUS / "builder2",
    "builder3": AGENT_BUS / "builder3",
}


def _ts() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _log(msg: str, verbose: bool = False) -> None:
    line = f"[watchdog] {_ts()} {msg}"
    if verbose:
        print(line)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with LOG_FILE.open("a") as f:
        f.write(line + "\n")


def _write_trigger(path: Path, kind: str, src: str) -> None:
    """Write a trigger marker file so sessions can poll data/triggers/ if needed."""
    TRIGGER_DIR.mkdir(parents=True, exist_ok=True)
    slug = f"{kind}_{_ts().replace(' ', '_').replace(':', '')}.trigger"
    marker = TRIGGER_DIR / slug
    marker.write_text(f"kind={kind}\nsrc={src}\nts={_ts()}\n")


def _notify(title: str, body: str) -> None:
    """macOS notification — best-effort; fails silently if blocked."""
    try:
        subprocess.run(
            [
                "osascript", "-e",
                f'display notification "{body}" with title "{title}"',
            ],
            timeout=5,
            check=False,
            capture_output=True,
        )
    except Exception:
        pass


def _trigger_seat(seat: str, card_name: str, verbose: bool) -> None:
    """Alert a seat that new work is waiting. Non-blocking."""
    _log(f"TRIGGER seat={seat} card={card_name}", verbose)
    _write_trigger(TRIGGER_DIR, f"seat_{seat}", card_name)
    _notify(
        f"eLo-AI — {seat} inbox",
        f"New card: {card_name}\nRun: bash tools/start_seat.sh {seat}",
    )


def _trigger_board_intake(intake_file: str, verbose: bool) -> None:
    """Alert Board that David dropped a new file."""
    _log(f"TRIGGER intake={intake_file}", verbose)
    _write_trigger(TRIGGER_DIR, "board_intake", intake_file)
    _notify(
        "eLo-AI — Board intake",
        f"New drop: {Path(intake_file).name}\nBoard: review and write WO.",
    )


def _trigger_board_review(request_file: str, verbose: bool) -> None:
    """Alert Board that a seat filed a review request."""
    _log(f"TRIGGER board_review={request_file}", verbose)
    _write_trigger(TRIGGER_DIR, "board_review", request_file)
    _notify(
        "eLo-AI — Board review",
        f"Seat filed: {Path(request_file).name}",
    )


# ── Handlers ──────────────────────────────────────────────────────────────────

class IntakeHandler(FileSystemEventHandler):
    """Path 1 — David drops files in _intake/."""

    def __init__(self, verbose: bool = False) -> None:
        self._verbose = verbose

    def on_created(self, event: FileCreatedEvent) -> None:
        if event.is_directory:
            return
        p = Path(event.src_path)
        if p.suffix in (".md", ".txt", ".markdown", ""):
            _log(f"INTAKE {p.name}", self._verbose)
            _trigger_board_intake(str(p), self._verbose)


class SeatInboxHandler(FileSystemEventHandler):
    """Path 2 — Board drops FROM_BOARD_*.md in a seat inbox."""

    def __init__(self, seat: str, verbose: bool = False) -> None:
        self._seat = seat
        self._verbose = verbose

    def on_created(self, event: FileCreatedEvent) -> None:
        if event.is_directory:
            return
        p = Path(event.src_path)
        if p.name.startswith("FROM_BOARD_") and p.suffix == ".md":
            _log(f"SEAT_INBOX seat={self._seat} file={p.name}", self._verbose)
            _trigger_seat(self._seat, p.name, self._verbose)


class BoardReviewHandler(FileSystemEventHandler):
    """Path 3 — Seat drops FROM_BOARD_REQUEST_*.md in blender/agent_bus/."""

    def __init__(self, verbose: bool = False) -> None:
        self._verbose = verbose

    def on_created(self, event: FileCreatedEvent) -> None:
        if event.is_directory:
            return
        p = Path(event.src_path)
        if p.name.startswith("FROM_BOARD_REQUEST_") and p.suffix == ".md":
            _log(f"BOARD_REVIEW {p.name}", self._verbose)
            _trigger_board_review(str(p), self._verbose)


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="eLo-AI FSEvents watchdog")
    parser.add_argument("--log", action="store_true", help="Verbose output")
    args = parser.parse_args()
    v = args.log

    # Ensure watched directories exist
    INTAKE_DIR.mkdir(parents=True, exist_ok=True)
    for inbox in SEAT_INBOXES.values():
        inbox.mkdir(parents=True, exist_ok=True)

    observer = Observer()

    # Path 1 — intake
    observer.schedule(IntakeHandler(v), str(INTAKE_DIR), recursive=False)

    # Path 2 — seat inboxes (non-recursive; don't watch QUEUE/ or processed/)
    for seat, inbox in SEAT_INBOXES.items():
        observer.schedule(SeatInboxHandler(seat, v), str(inbox), recursive=False)

    # Path 3 — board review requests
    observer.schedule(BoardReviewHandler(v), str(AGENT_BUS), recursive=False)

    observer.start()
    _log(f"started pid={os.getpid()} repo={REPO_ROOT}", verbose=True)
    print(f"[watchdog] watching — Ctrl+C to stop. Log: {LOG_FILE}")
    print(f"  intake:       {INTAKE_DIR}")
    for seat, inbox in SEAT_INBOXES.items():
        print(f"  {seat:<10s}:  {inbox}")
    print(f"  board_review: {AGENT_BUS}")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        _log("stopped (KeyboardInterrupt)", verbose=True)
    observer.join()


if __name__ == "__main__":
    main()
