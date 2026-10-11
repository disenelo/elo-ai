#!/usr/bin/env python3
"""
tools/watchdog.py — WO-B1-0112: Autonomous Watchdog + Event-Driven Seat Relay

FSEvents-based (macOS) / inotify-based (Linux) file-system watcher that drives
seat activity automatically. No cron. No polling. David drops a file; things move.

Three trigger paths:
  Path 1 — David drops a file in docs/architecture/_intake/
            → Board intake session triggered
  Path 2 — Board files FROM_BOARD_* in blender/agent_bus/<seat>/
            → That seat's one-card session triggered
  Path 3 — Seat files to blender/agent_bus/FROM_BOARD_REQUEST_*/
            → Board review session triggered

Token efficiency rule: each triggered session is ONE CARD only.
Read inbox → pick highest priority → do it → commit → file to Board → EXIT.

Usage:
  python3 tools/watchdog.py [--root /path/to/elo-ai] [--dry-run]

Run as background process:
  python3 tools/watchdog.py &
  echo $! > tools/.watchdog.pid

Stop:
  kill $(cat tools/.watchdog.pid)

Author: Builder 1 · 2026-10-11
"""
from __future__ import annotations

import argparse
import logging
import os
import subprocess
import sys
import threading
import time
from pathlib import Path

from watchdog.events import FileCreatedEvent, FileSystemEventHandler
from watchdog.observers import Observer

# ── Logging ───────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  WD  %(levelname)s  %(message)s",
    datefmt="%H:%M:%S",
)
_log = logging.getLogger("elo_watchdog")

# ── Config ────────────────────────────────────────────────────────────────────

_ROOT = Path(__file__).parent.parent.resolve()

_INTAKE_DIR  = _ROOT / "docs" / "architecture" / "_intake"
_AGENT_BUS   = _ROOT / "blender" / "agent_bus"
_TOOLS_DIR   = _ROOT / "tools"

# Known seats and their inbox paths
_SEATS: dict[str, Path] = {
    "builder":   _AGENT_BUS / "builder",
    "builder2":  _AGENT_BUS / "builder2",
    "builder3":  _AGENT_BUS / "builder3",
    "board":     _AGENT_BUS / "board",
    "designer":  _AGENT_BUS / "designer",
}

# Debounce: skip duplicate triggers within this window (seconds)
_DEBOUNCE_S: float = 5.0

# ── Debounce registry ─────────────────────────────────────────────────────────

_last_trigger: dict[str, float] = {}
_trigger_lock = threading.Lock()


def _debounced(key: str) -> bool:
    """Return True if this key can fire now (not within debounce window)."""
    now = time.monotonic()
    with _trigger_lock:
        last = _last_trigger.get(key, 0.0)
        if now - last < _DEBOUNCE_S:
            return False
        _last_trigger[key] = now
        return True


# ── Trigger writers ───────────────────────────────────────────────────────────

def _write_trigger(seat: str, reason: str, source_file: str) -> None:
    """
    Write a .trigger file into the seat's inbox so the seat's START_HERE check
    picks it up at next session start. The file is a plain markdown summary.
    """
    seat_dir = _SEATS.get(seat)
    if seat_dir is None:
        _log.warning("Unknown seat: %s — skipping trigger", seat)
        return
    seat_dir.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y-%m-%d_%H%M%S")
    trigger_path = seat_dir / f"TRIGGER_{ts}_{reason[:40].replace(' ', '_')}.md"
    trigger_path.write_text(
        f"# Auto-trigger — {reason}\n"
        f"**Source file:** `{source_file}`\n"
        f"**Triggered:** {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        "Watchdog detected a new file. Read your inbox and pick the highest-priority\n"
        "unstarted card. One card. Commit. File to Board. Exit.\n"
    )
    _log.info("Trigger written → %s (%s)", trigger_path.name, seat)


def _write_board_trigger(reason: str, source_file: str) -> None:
    _write_trigger("board", reason, source_file)


# ── Start-seat launcher (optional, if claude CLI available) ───────────────────

def _launch_seat_session(seat: str, source_file: str, dry_run: bool = False) -> None:
    """
    Optionally launch a Claude Code session for the seat.
    Falls back gracefully if `claude` is not on PATH.

    The primary signal is the .trigger file — this is a convenience shortcut.
    """
    start_script = _TOOLS_DIR / "start_seat.sh"
    if not start_script.exists():
        _log.debug("start_seat.sh not found — trigger file is the signal (ok)")
        return

    cmd = ["bash", str(start_script), seat, source_file]
    _log.info("Launching seat session: %s", " ".join(cmd))
    if dry_run:
        _log.info("[dry-run] would run: %s", " ".join(cmd))
        return
    try:
        subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
    except Exception as _e:
        _log.warning("Could not launch seat session for %s: %s", seat, _e)


# ── Event handlers ────────────────────────────────────────────────────────────

class IntakeHandler(FileSystemEventHandler):
    """Path 1: David drops a file in _intake/ → Board intake."""

    def __init__(self, dry_run: bool = False) -> None:
        self._dry = dry_run

    def on_created(self, event: FileCreatedEvent) -> None:
        if event.is_directory:
            return
        p = Path(event.src_path)
        if not p.suffix in (".md", ".txt"):
            return
        key = f"intake:{p.name}"
        if not _debounced(key):
            return
        _log.info("INTAKE — new file: %s → triggering Board", p.name)
        _write_board_trigger(f"intake_{p.stem[:30]}", str(p))
        _launch_seat_session("board", str(p), dry_run=self._dry)


class SeatInboxHandler(FileSystemEventHandler):
    """Path 2: Board drops FROM_BOARD_* in a seat's inbox → trigger that seat."""

    def __init__(self, seat: str, dry_run: bool = False) -> None:
        self._seat = seat
        self._dry = dry_run

    def on_created(self, event: FileCreatedEvent) -> None:
        if event.is_directory:
            return
        p = Path(event.src_path)
        name = p.name
        # Trigger on FROM_BOARD_* or FROM_ARCHITECT_* markdown files
        if not (name.startswith("FROM_BOARD") or name.startswith("FROM_ARCHITECT")):
            return
        if p.suffix != ".md":
            return
        key = f"seat:{self._seat}:{name}"
        if not _debounced(key):
            return
        _log.info("SEAT INBOX — %s/%s → triggering %s", self._seat, name, self._seat)
        _write_trigger(self._seat, f"new_card_{p.stem[:30]}", str(p))
        _launch_seat_session(self._seat, str(p), dry_run=self._dry)


class BoardRequestHandler(FileSystemEventHandler):
    """Path 3: Seat files FROM_BOARD_REQUEST_* → trigger Board review."""

    def __init__(self, dry_run: bool = False) -> None:
        self._dry = dry_run

    def on_created(self, event: FileCreatedEvent) -> None:
        if event.is_directory:
            return
        p = Path(event.src_path)
        name = p.name
        if not name.startswith("FROM_BOARD_REQUEST"):
            return
        if p.suffix != ".md":
            return
        key = f"board_request:{name}"
        if not _debounced(key):
            return
        _log.info("BOARD REQUEST — %s → triggering Board review", name)
        _write_board_trigger(f"review_{p.stem[:30]}", str(p))
        _launch_seat_session("board", str(p), dry_run=self._dry)


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="eLo-AI autonomous watchdog")
    parser.add_argument("--root", default=str(_ROOT), help="Repo root")
    parser.add_argument("--dry-run", action="store_true", help="Log triggers but do not launch sessions")
    parser.add_argument("--debounce", type=float, default=5.0,
                        help="Debounce window in seconds (default 5.0)")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    intake = root / "docs" / "architecture" / "_intake"
    agent_bus = root / "blender" / "agent_bus"

    # Ensure watched directories exist
    for d in [intake, agent_bus]:
        d.mkdir(parents=True, exist_ok=True)

    observer = Observer()

    # Path 1: _intake/
    observer.schedule(IntakeHandler(dry_run=args.dry_run), str(intake), recursive=False)
    _log.info("Watching INTAKE:  %s", intake)

    # Path 2: each seat inbox
    for seat, seat_dir in _SEATS.items():
        seat_dir.mkdir(parents=True, exist_ok=True)
        observer.schedule(
            SeatInboxHandler(seat=seat, dry_run=args.dry_run),
            str(seat_dir),
            recursive=False,
        )
        _log.info("Watching SEAT:    %s", seat_dir)

    # Path 3: agent_bus root for FROM_BOARD_REQUEST_* files
    observer.schedule(BoardRequestHandler(dry_run=args.dry_run), str(agent_bus), recursive=False)
    _log.info("Watching BUS ROOT: %s", agent_bus)

    if args.dry_run:
        _log.info("[dry-run mode] — triggers logged but sessions not launched")

    observer.start()
    _log.info("Watchdog running (PID %d). Ctrl-C to stop.", os.getpid())

    # Write PID file so the process can be stopped cleanly
    pid_file = root / "tools" / ".watchdog.pid"
    pid_file.parent.mkdir(exist_ok=True)
    pid_file.write_text(str(os.getpid()))

    try:
        while observer.is_alive():
            observer.join(timeout=1.0)
    except KeyboardInterrupt:
        _log.info("Stopping watchdog…")
        observer.stop()
    finally:
        observer.join()
        try:
            pid_file.unlink(missing_ok=True)
        except Exception:
            pass
        _log.info("Watchdog stopped.")


if __name__ == "__main__":
    main()
