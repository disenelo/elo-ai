"""
company_runtime/scheduling_faculty.py — EA2-4 Scheduling Faculty.

Reorder / move Work Order rows on the dispatch board (DISPATCH_BOARD.md).
ADDITIVE ONLY — a net-new faculty. Does NOT touch server.py, runtime/*, core/*,
or the frozen cognitive kernel (LAW-017 / FREEZE_V1_LOCK). It only rewrites data
rows in the markdown board, preserving headers, separators and row content.

Reuses the board-row parsing approach from company_state_writer (`_ROW_RE`,
`_norm_status`, `_WO_PREFIXES`) — imported, not reinvented.

Public API (each returns {"ok": bool, "reason": str, "moved": list}):
  move_wo(wo_id, before=None, after=None)        — move a row before/after another WO
  set_priority(wo_id, priority)                  — change only a WO's priority cell (P0..P3)
  reorder_section(section_marker, wo_ids_in_order) — reorder a set of rows within a section

Every write is: (1) a `.bak` backup of the original board first, then (2) an
atomic write (`.tmp` → `os.replace`). Nothing is written unless the whole
operation validates, so a malformed / unknown wo_id can never corrupt the board.
"""
from __future__ import annotations

import logging
import os
import re

# Reuse the canonical board-row parsing from the state writer — do not reinvent.
from company_runtime.company_state_writer import (
    _ROW_RE,          # noqa: F401  (row regex — canonical shape)
    _norm_status,     # noqa: F401  (status normaliser — canonical vocab)
    _WO_PREFIXES,
    _BOARD_PATH,
)

_logger = logging.getLogger(__name__)

_VALID_PRIORITIES = ("P0", "P1", "P2", "P3")


# ── Result helpers ────────────────────────────────────────────────────────────

def _ok(reason: str, moved: list) -> dict:
    return {"ok": True, "reason": reason, "moved": moved}


def _err(reason: str) -> dict:
    _logger.info("scheduling_faculty: %s", reason)
    return {"ok": False, "reason": reason, "moved": []}


# ── Board IO (lossless split/join on '\n'; never touches content beyond rows) ──

def _read_lines(board_path: str):
    """Return the board as a list of lines (lossless on '\\n'), or None if absent."""
    try:
        with open(board_path, encoding="utf-8") as f:
            text = f.read()
    except FileNotFoundError:
        return None
    return text.split("\n")


def _backup(board_path: str) -> None:
    """Write a `.bak` copy of the current board BEFORE any change."""
    try:
        with open(board_path, encoding="utf-8") as f:
            original = f.read()
        with open(board_path + ".bak", "w", encoding="utf-8") as f:
            f.write(original)
    except Exception as exc:  # best-effort; never blocks the caller
        _logger.error("scheduling_faculty: backup failed: %s", exc)


def _atomic_write_lines(board_path: str, lines: list) -> bool:
    """Atomic write: build text, write to `.tmp`, then os.replace into place."""
    try:
        tmp = board_path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        os.replace(tmp, board_path)
        return True
    except Exception as exc:
        _logger.error("scheduling_faculty: atomic write failed: %s", exc)
        return False


# ── Row identification (via the shared _ROW_RE / _WO_PREFIXES) ─────────────────

def _row_wo_id(line: str):
    """
    Return the WO id if `line` is a WO *data* row, else None.

    A data row is one whose first cell matches a known WO prefix. Header rows
    ("| WO | Title |") and separator rows ("|----|") fail the prefix / regex
    test and are correctly skipped — so we never move or edit them.
    """
    m = _ROW_RE.match(line.strip())
    if not m:
        return None
    wo_id = m.group(1).strip()
    if not any(wo_id.startswith(pfx) for pfx in _WO_PREFIXES):
        return None
    return wo_id


def _find_row(lines: list, wo_id: str):
    """Index of the (first) data-row line for wo_id, or None."""
    for i, line in enumerate(lines):
        if _row_wo_id(line) == wo_id:
            return i
    return None


def _block_bounds(lines: list, idx: int):
    """
    (start, end) inclusive of the contiguous markdown-table block containing
    line `idx`. A table block is a maximal run of lines that begin with '|'.
    Used so a move stays inside its own table section (never leaks across a
    heading / blank line into another table).
    """
    start = idx
    while start > 0 and lines[start - 1].lstrip().startswith("|"):
        start -= 1
    end = idx
    while end + 1 < len(lines) and lines[end + 1].lstrip().startswith("|"):
        end += 1
    return start, end


# ── move_wo ───────────────────────────────────────────────────────────────────

def move_wo(wo_id: str, before: str | None = None, after: str | None = None,
            board_path: str = _BOARD_PATH) -> dict:
    """
    Move the WO row `wo_id` to sit immediately before/after another WO's row,
    within the SAME table section. Row content is preserved exactly — only the
    line's position changes.
    """
    wo_id = (wo_id or "").strip()
    before = (before or "").strip() or None
    after = (after or "").strip() or None

    if not wo_id:
        return _err("move_wo: missing wo_id")
    if not before and not after:
        return _err("move_wo: must supply before= or after=")
    if before and after:
        return _err("move_wo: supply only one of before= / after=")

    target = before or after
    if target == wo_id:
        return _err("move_wo: cannot move a WO relative to itself")

    lines = _read_lines(board_path)
    if lines is None:
        return _err(f"move_wo: board not found: {board_path}")

    src = _find_row(lines, wo_id)
    if src is None:
        return _err(f"move_wo: wo_id not found: {wo_id}")
    tgt = _find_row(lines, target)
    if tgt is None:
        return _err(f"move_wo: target not found: {target}")

    if _block_bounds(lines, src) != _block_bounds(lines, tgt):
        return _err(f"move_wo: {wo_id} and {target} are not in the same table section")

    # Validated — safe to mutate. Backup first, then rebuild the line list.
    _backup(board_path)
    row = lines.pop(src)
    tgt2 = _find_row(lines, target)          # index shifts after the pop
    insert_at = tgt2 if before else tgt2 + 1
    lines.insert(insert_at, row)

    if not _atomic_write_lines(board_path, lines):
        return _err("move_wo: atomic write failed (board unchanged)")

    where = f"before {target}" if before else f"after {target}"
    return _ok(f"move_wo: {wo_id} moved {where}", [wo_id])


# ── set_priority ──────────────────────────────────────────────────────────────

def set_priority(wo_id: str, priority: str, board_path: str = _BOARD_PATH) -> dict:
    """Change ONLY the priority cell (4th column) of a WO row. priority ∈ P0..P3."""
    wo_id = (wo_id or "").strip()
    priority = (priority or "").strip().upper()

    if not wo_id:
        return _err("set_priority: missing wo_id")
    if priority not in _VALID_PRIORITIES:
        return _err(f"set_priority: invalid priority {priority!r} (want one of {_VALID_PRIORITIES})")

    lines = _read_lines(board_path)
    if lines is None:
        return _err(f"set_priority: board not found: {board_path}")

    idx = _find_row(lines, wo_id)
    if idx is None:
        return _err(f"set_priority: wo_id not found: {wo_id}")

    # Split the single row on pipes. parts[1]=id, [2]=title, [3]=agent, [4]=pri, [5]=status...
    parts = lines[idx].split("|")
    if len(parts) < 6:
        return _err(f"set_priority: row for {wo_id} is malformed (too few cells) — refused")

    parts[4] = f" {priority} "            # only the priority cell changes
    lines[idx] = "|".join(parts)

    _backup(board_path)
    if not _atomic_write_lines(board_path, lines):
        return _err("set_priority: atomic write failed (board unchanged)")

    return _ok(f"set_priority: {wo_id} → {priority}", [wo_id])


# ── reorder_section ───────────────────────────────────────────────────────────

def reorder_section(section_marker: str, wo_ids_in_order: list,
                    board_path: str = _BOARD_PATH) -> dict:
    """
    Reorder the given WO rows within the first table section that follows
    `section_marker` (a substring of the section's heading / intro line), so
    they appear in `wo_ids_in_order`. Rows not in the list keep their positions;
    only the listed rows' contents are re-slotted into the positions they
    already occupy — so the table stays intact and no row is lost.
    """
    section_marker = (section_marker or "").strip()
    wo_ids_in_order = [w.strip() for w in (wo_ids_in_order or []) if w and w.strip()]

    if not section_marker:
        return _err("reorder_section: missing section_marker")
    if len(wo_ids_in_order) < 2:
        return _err("reorder_section: need at least 2 wo_ids to reorder")

    lines = _read_lines(board_path)
    if lines is None:
        return _err(f"reorder_section: board not found: {board_path}")

    # Locate the marker line.
    marker_idx = next((i for i, ln in enumerate(lines) if section_marker in ln), None)
    if marker_idx is None:
        return _err(f"reorder_section: section marker not found: {section_marker!r}")

    # First table block at/after the marker.
    tbl_idx = next((i for i in range(marker_idx, len(lines))
                    if lines[i].lstrip().startswith("|")), None)
    if tbl_idx is None:
        return _err(f"reorder_section: no table found after {section_marker!r}")
    b_start, b_end = _block_bounds(lines, tbl_idx)

    # Data rows within the block, in board order.
    data_rows = [(i, _row_wo_id(lines[i])) for i in range(b_start, b_end + 1)
                 if _row_wo_id(lines[i])]
    present = {wo for _, wo in data_rows}

    missing = [w for w in wo_ids_in_order if w not in present]
    if missing:
        return _err(f"reorder_section: wo_ids not in this section: {missing}")

    wanted = set(wo_ids_in_order)
    positions = [i for i, wo in data_rows if wo in wanted]     # slots to fill, in board order
    line_for = {wo: lines[i] for i, wo in data_rows if wo in wanted}
    contents = [line_for[wo] for wo in wo_ids_in_order]        # desired order

    if len(positions) != len(contents):                       # defensive; should not happen
        return _err("reorder_section: position/content count mismatch — refused")

    _backup(board_path)
    for pos, content in zip(positions, contents):
        lines[pos] = content

    if not _atomic_write_lines(board_path, lines):
        return _err("reorder_section: atomic write failed (board unchanged)")

    return _ok(f"reorder_section: reordered {len(wo_ids_in_order)} rows under {section_marker!r}",
               list(wo_ids_in_order))
