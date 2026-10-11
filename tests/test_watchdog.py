"""tests/test_watchdog.py — WO-B1-0112: Autonomous Watchdog tests.

Tests handler logic directly (no real FSEvents loop needed).
"""
from __future__ import annotations

import sys
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# ── helpers ───────────────────────────────────────────────────────────────────

def _fake_event(path: str, is_directory: bool = False) -> MagicMock:
    ev = MagicMock()
    ev.src_path = path
    ev.is_directory = is_directory
    return ev


# ── IntakeHandler ─────────────────────────────────────────────────────────────

def test_intake_handler_md_triggers_write(tmp_path):
    """Path 1: .md drop in _intake/ → trigger written to builder inbox."""
    from tools.watchdog import IntakeHandler, _BUILDER_DIR
    handler = IntakeHandler(dry_run=False)
    intake_file = tmp_path / "my_idea.md"
    intake_file.write_text("eLo should greet me by name.", encoding="utf-8")

    written: list[Path] = []
    def _fake_write(directory, prefix, body, dry_run):
        p = directory / f"{prefix}_fake.md"
        written.append(p)
        return p

    with patch("tools.watchdog._write_trigger", side_effect=_fake_write):
        handler.on_created(_fake_event(str(intake_file)))

    assert len(written) == 1
    assert "FROM_INTAKE" in written[0].name


def test_intake_handler_txt_triggers_write(tmp_path):
    """Path 1: .txt drop also triggers (David might not know to use .md)."""
    from tools.watchdog import IntakeHandler
    handler = IntakeHandler(dry_run=False)
    src = tmp_path / "idea.txt"
    src.write_text("idea", encoding="utf-8")

    written: list[Path] = []
    with patch("tools.watchdog._write_trigger", side_effect=lambda d, p, b, dr: written.append(d / p) or d / p):
        handler.on_created(_fake_event(str(src)))
    assert len(written) == 1


def test_intake_handler_ignores_non_md(tmp_path):
    """Path 1: non-md/txt files ignored (e.g. .DS_Store)."""
    from tools.watchdog import IntakeHandler
    handler = IntakeHandler(dry_run=True)
    with patch("tools.watchdog._write_trigger") as mock_wt:
        handler.on_created(_fake_event(str(tmp_path / "file.png")))
    mock_wt.assert_not_called()


def test_intake_handler_ignores_directories():
    """Path 1: directory creation events are ignored."""
    from tools.watchdog import IntakeHandler
    handler = IntakeHandler(dry_run=True)
    with patch("tools.watchdog._write_trigger") as mock_wt:
        handler.on_created(_fake_event("/some/dir", is_directory=True))
    mock_wt.assert_not_called()


def test_intake_handler_dry_run(tmp_path):
    """Path 1 dry-run: no file written."""
    from tools.watchdog import IntakeHandler
    handler = IntakeHandler(dry_run=True)
    src = tmp_path / "idea.md"
    src.write_text("x")
    with patch("tools.watchdog._write_trigger") as mock_wt:
        mock_wt.return_value = tmp_path / "trigger.md"
        handler.on_created(_fake_event(str(src)))
    mock_wt.assert_called_once()
    # dry_run=True was passed through
    assert mock_wt.call_args[0][3] is True


# ── SeatInboxHandler ──────────────────────────────────────────────────────────

def test_seat_inbox_handler_from_board_triggers_start(tmp_path):
    """Path 2: FROM_BOARD_*.md in seat dir → start_seat.sh launched."""
    from tools.watchdog import SeatInboxHandler
    handler = SeatInboxHandler("builder", dry_run=False)
    md_file = tmp_path / "FROM_BOARD_TEST_001.md"
    md_file.write_text("board filing", encoding="utf-8")

    # Patch _START_SEAT to a path that exists (/bin/bash on macOS) and mock Popen
    with patch("tools.watchdog._START_SEAT", new=Path("/bin/bash")):
        with patch("subprocess.Popen") as mock_popen:
            handler.on_created(_fake_event(str(md_file)))
    mock_popen.assert_called_once()
    args = mock_popen.call_args[0][0]
    assert "builder" in args


def test_seat_inbox_handler_ignores_non_from_board(tmp_path):
    """Path 2: files not prefixed FROM_BOARD are ignored."""
    from tools.watchdog import SeatInboxHandler
    handler = SeatInboxHandler("builder", dry_run=True)
    md_file = tmp_path / "TRIGGER_watchdog.md"
    with patch("subprocess.Popen") as mock_popen:
        handler.on_created(_fake_event(str(md_file)))
    mock_popen.assert_not_called()


def test_seat_inbox_handler_dry_run(tmp_path):
    """Path 2 dry-run: no Popen launched."""
    from tools.watchdog import SeatInboxHandler
    handler = SeatInboxHandler("builder", dry_run=True)
    md_file = tmp_path / "FROM_BOARD_TEST.md"
    md_file.write_text("x")
    with patch("subprocess.Popen") as mock_popen:
        handler.on_created(_fake_event(str(md_file)))
    mock_popen.assert_not_called()


# ── BoardRequestHandler ───────────────────────────────────────────────────────

def test_board_request_handler_triggers_review(tmp_path):
    """Path 3: FROM_BOARD_REQUEST_*.md → trigger written to board_review/."""
    from tools.watchdog import BoardRequestHandler
    handler = BoardRequestHandler(dry_run=False)
    src = tmp_path / "FROM_BOARD_REQUEST_SEAT_001.md"
    src.write_text("seat card", encoding="utf-8")

    written: list[Path] = []
    with patch("tools.watchdog._write_trigger", side_effect=lambda d, p, b, dr: written.append(d / p) or d / p):
        handler.on_created(_fake_event(str(src)))
    assert len(written) == 1
    assert "TRIGGER_board_review" in written[0].name


def test_board_request_handler_ignores_non_request(tmp_path):
    """Path 3: files not prefixed FROM_BOARD_REQUEST are ignored."""
    from tools.watchdog import BoardRequestHandler
    handler = BoardRequestHandler(dry_run=True)
    src = tmp_path / "FROM_BOARD_OTHER.md"
    with patch("tools.watchdog._write_trigger") as mock_wt:
        handler.on_created(_fake_event(str(src)))
    mock_wt.assert_not_called()


# ── write_trigger ─────────────────────────────────────────────────────────────

def test_write_trigger_creates_file(tmp_path):
    """_write_trigger writes a .md file to the target directory."""
    from tools.watchdog import _write_trigger
    result = _write_trigger(tmp_path, "TEST_PREFIX", "body text", dry_run=False)
    assert result.exists()
    assert result.read_text(encoding="utf-8") == "body text"
    assert result.name.startswith("TEST_PREFIX_")


def test_write_trigger_dry_run_no_file(tmp_path):
    """_write_trigger dry_run=True: returns path but does NOT create the file."""
    from tools.watchdog import _write_trigger
    result = _write_trigger(tmp_path, "DRY_PREFIX", "body", dry_run=True)
    assert not result.exists()
