"""
tests/test_0015_unity_events_append_log_cursor.py — Card 0015 · RULING 00d.

Builder half of the unity_events.json append-log ruling:
- Read from the cursor.
- Ack-by-seq (rows above the cursor are unread; rows at/below have been consumed).
- Persist consumed_seq to unity_events_cursor.json so Designer's rotation can warn (Rule 1)
  if it would drop an unread row.

The row that proves it (from the ruling):
- Fire `move_complete` and `gaze_target_changed` in the same tick. Both must arrive.
  Under the previous single-slot file, one was lost. Under the append-log, both rows land
  and both are visible to the cursor consumer.

Additional properties:
- Consume nothing for N events ⇒ they all queue above the cursor; none vanish.
- Cursor file is written after a read batch and can be reloaded to resume.
- Rotation-shaped state (log trimmed at the head) does not confuse the reader: any row
  whose seq exceeds the cursor is yielded exactly once.
"""
from __future__ import annotations

import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


def _append_row(events_path: str, seq: int, ev_type: str, subject: str = "",
                action_id: str = "", payload=None, _ts: float | None = None) -> None:
    row = {
        "seq": seq,
        "type": ev_type,
        "subject": subject,
        "action_id": action_id,
        "payload": payload or {},
        "_ts": _ts if _ts is not None else time.time(),
    }
    with open(events_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(row) + "\n")


# ── AT-0015-1: same-tick move_complete + gaze_target_changed — BOTH arrive ────

def test_move_complete_and_gaze_same_tick_both_arrive(tmp_path):
    """Fire move_complete and gaze_target_changed in the same tick. Both rows must
    be visible to the cursor consumer. Under the previous single-slot file one
    would clobber the other — under the append-log neither is lost."""
    from runtime.unity_events_cursor import iter_events_from

    events_path = str(tmp_path / "unity_events.json")
    same_tick_ts = 1_700_000_000.0

    _append_row(events_path, seq=1, ev_type="move_complete",
                subject="walk", action_id="mv-1",
                payload={"arrived": True}, _ts=same_tick_ts)
    _append_row(events_path, seq=2, ev_type="gaze_target_changed",
                subject="10130",
                payload={"win_id": 10130, "on_window": True,
                         "gaze": {"x": 0.71, "y": 0.35}, "issued_by": "reflex"},
                _ts=same_tick_ts)

    rows = list(iter_events_from(seq_after=-1, events_path=events_path))

    types = [r["type"] for r in rows]
    assert "move_complete" in types, f"move_complete lost — types: {types}"
    assert "gaze_target_changed" in types, f"gaze_target_changed lost — types: {types}"
    assert len(rows) == 2, (
        f"append-log must preserve both same-tick rows, got {len(rows)}: {rows}"
    )
    # order preserved by seq
    assert rows[0]["seq"] == 1 and rows[1]["seq"] == 2


# ── AT-0015-2: consume nothing for N events ⇒ they queue, none vanish ─────────

def test_backlog_queues_no_row_is_lost(tmp_path):
    """The reader consumes nothing for 25 rows. All 25 must be visible when it
    finally reads — the append-log is a delivery buffer, not a state slot."""
    from runtime.unity_events_cursor import iter_events_from, max_seq

    events_path = str(tmp_path / "unity_events.json")
    for n in range(1, 26):
        _append_row(events_path, seq=n, ev_type="gaze_target_changed",
                    payload={"i": n})

    assert max_seq(events_path=events_path) == 25
    rows = list(iter_events_from(seq_after=-1, events_path=events_path))
    assert len(rows) == 25, f"expected 25 rows queued, got {len(rows)}"
    assert [r["seq"] for r in rows] == list(range(1, 26))


# ── AT-0015-3: cursor is persisted and re-readable across processes ──────────

def test_cursor_persistence_roundtrip(tmp_path):
    """After a read batch the Builder writes consumed_seq to unity_events_cursor.json.
    A fresh process/reader can load that value and resume above it — no row re-emitted,
    no row skipped."""
    from runtime.unity_events_cursor import (
        iter_events_from, max_seq, read_cursor, write_cursor,
    )

    events_path = str(tmp_path / "unity_events.json")
    cursor_path = str(tmp_path / "unity_events_cursor.json")

    for n in range(1, 6):
        _append_row(events_path, seq=n, ev_type="move_complete", action_id=f"mv-{n}")

    # First reader consumes everything up to max_seq
    first_cursor = read_cursor(path=cursor_path)   # cold — file absent
    assert first_cursor == -1
    rows = list(iter_events_from(seq_after=first_cursor, events_path=events_path))
    assert len(rows) == 5
    top = max_seq(events_path=events_path)
    assert write_cursor(top, path=cursor_path) is True

    # Second reader — simulating a restart — reads the cursor and sees nothing new
    resumed = read_cursor(path=cursor_path)
    assert resumed == top == 5
    rows2 = list(iter_events_from(seq_after=resumed, events_path=events_path))
    assert rows2 == [], f"already-consumed rows must not re-emit: {rows2}"

    # New rows arrive; only they are yielded
    for n in range(6, 9):
        _append_row(events_path, seq=n, ev_type="gaze_target_changed")
    rows3 = list(iter_events_from(seq_after=resumed, events_path=events_path))
    assert [r["seq"] for r in rows3] == [6, 7, 8]


# ── AT-0015-4: rotation-shaped trim — head trimmed, tail preserved ───────────

def test_survives_head_rotation_of_log(tmp_path):
    """Simulate Designer's bounded rotation: earlier rows drop out of the file,
    but seq keeps climbing. Reader with a cursor at N still sees every row > N
    that survives the rotation. (Discarded-above-cursor is Designer's WARNING;
    the reader itself just yields whatever it finds above its cursor.)"""
    from runtime.unity_events_cursor import iter_events_from

    events_path = str(tmp_path / "unity_events.json")
    # Pre-rotation state: rows 1..10 present
    for n in range(1, 11):
        _append_row(events_path, seq=n, ev_type="gaze_target_changed")

    # Reader consumed up to seq=4
    rows_before = list(iter_events_from(seq_after=4, events_path=events_path))
    assert [r["seq"] for r in rows_before] == [5, 6, 7, 8, 9, 10]

    # Designer rotates: keep only the last 3, and append 11..13
    with open(events_path, "w", encoding="utf-8") as f:
        for n in (8, 9, 10):
            f.write(json.dumps({"seq": n, "type": "gaze_target_changed",
                                "subject": "", "action_id": "",
                                "payload": {}, "_ts": time.time()}) + "\n")
    for n in range(11, 14):
        _append_row(events_path, seq=n, ev_type="move_complete", action_id=f"mv-{n}")

    # Cursor still at 4 — reader sees whatever survived above 4
    rows_after = list(iter_events_from(seq_after=4, events_path=events_path))
    assert [r["seq"] for r in rows_after] == [8, 9, 10, 11, 12, 13]

    # After consuming, cursor advances to 13 — no re-yield
    rows_done = list(iter_events_from(seq_after=13, events_path=events_path))
    assert rows_done == []


# ── AT-0015-5: cursor write is atomic (no partial file on interrupted write) ──

def test_cursor_write_is_atomic(tmp_path):
    """write_cursor uses os.replace on a temp file so a concurrent reader never
    observes a truncated cursor file. We can't easily interrupt the write, but
    we can verify (a) the temp file is not left behind, and (b) the written
    file is valid JSON with an int consumed_seq."""
    from runtime.unity_events_cursor import read_cursor, write_cursor

    cursor_path = str(tmp_path / "unity_events_cursor.json")
    assert write_cursor(42, path=cursor_path) is True

    with open(cursor_path, encoding="utf-8") as f:
        data = json.load(f)
    assert data["consumed_seq"] == 42
    assert isinstance(data.get("_ts"), (int, float))
    assert read_cursor(path=cursor_path) == 42

    # No stragglers in the parent directory
    stragglers = [p for p in os.listdir(str(tmp_path)) if p.startswith(".cursor.")]
    assert stragglers == [], f"temp cursor files left behind: {stragglers}"


# ── Self-runner ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import pathlib
    import tempfile

    tests = [
        ("AT-0015-1", test_move_complete_and_gaze_same_tick_both_arrive),
        ("AT-0015-2", test_backlog_queues_no_row_is_lost),
        ("AT-0015-3", test_cursor_persistence_roundtrip),
        ("AT-0015-4", test_survives_head_rotation_of_log),
        ("AT-0015-5", test_cursor_write_is_atomic),
    ]
    passed = failed = 0
    for label, fn in tests:
        with tempfile.TemporaryDirectory() as td:
            try:
                fn(pathlib.Path(td))
                print(f"  ✅ {label}: {fn.__name__}")
                passed += 1
            except Exception as e:
                print(f"  ❌ {label}: {fn.__name__} — {e}")
                failed += 1
    print()
    print("=" * 62)
    print(f"Card 0015 append-log cursor   {passed}/{passed + failed} passed, {failed} failed")
    if failed:
        sys.exit(1)
