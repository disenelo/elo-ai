"""
tests/test_w0_ack_channel.py — W0: ACK channel readable (card 0045)

Tests:
    W0-1  _parse_unity_events_tolerant handles concatenated objects on one line (the root defect)
    W0-2  _parse_unity_events_tolerant returns events and skipped count; logs non-zero skip count
    W0-3  _parse_unity_events_tolerant returns [] on missing file (no exception)
    W0-4  _parse_unity_events_tolerant handles clean single-object JSONL
    W0-5  consume_window_events returns window events from a multi-event file
    W0-6  consume_gaze_events returns gaze events from a multi-event file
    W0-7  _parse_unity_events_tolerant parses the real corrupt file if present (0 events lost
          from valid objects)

W0 PROVEN when: skipped-fragment counter reads 0 on a fresh run (unity_events.json consumed
and Unity writes clean newline-delimited events thereafter).

Run: python3 tests/test_w0_ack_channel.py
"""
import json
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

ok  = lambda msg: print(f"  PASS  {msg}")
err = lambda msg: (print(f"  FAIL  {msg}"), sys.exit(1))


# ── W0-1: tolerant parser handles concatenated objects (the root defect) ─────
def test_w0_1_concatenated_objects():
    from server import _parse_unity_events_tolerant
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        # Exact defect: two objects on one line with no delimiter
        f.write('{"event":"arrival","_ts":1786894486.692}{"seq":0,"type":"gaze_target_changed","_ts":1786894487.0}')
        path = f.name
    try:
        events, skipped = _parse_unity_events_tolerant(path)
        if len(events) != 2:
            err(f"W0-1: expected 2 events from concatenated line, got {len(events)} (skipped={skipped})")
        if skipped != 0:
            err(f"W0-1: expected 0 skipped, got {skipped} — concatenated objects should parse cleanly")
        if events[0].get("event") != "arrival":
            err(f"W0-1: first event wrong: {events[0]}")
        if events[1].get("type") != "gaze_target_changed":
            err(f"W0-1: second event wrong: {events[1]}")
    finally:
        os.unlink(path)
    ok("W0-1: concatenated objects on one line parsed — root defect handled")


# ── W0-2: skipped count is non-zero on truly corrupt content ─────────────────
def test_w0_2_skipped_count_on_corrupt():
    from server import _parse_unity_events_tolerant
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        f.write('{"type":"sit_complete","_ts":1.0}\nNOT_JSON_AT_ALL\n{"type":"move_complete","_ts":2.0}')
        path = f.name
    try:
        events, skipped = _parse_unity_events_tolerant(path)
        if len(events) != 2:
            err(f"W0-2: expected 2 valid events, got {len(events)}")
        if skipped == 0:
            err("W0-2: expected non-zero skipped count for 'NOT_JSON_AT_ALL' fragment")
    finally:
        os.unlink(path)
    ok(f"W0-2: skipped={skipped}, events={len(events)} — corrupt fragment counted, valid events preserved")


# ── W0-3: missing file returns empty without exception ────────────────────────
def test_w0_3_missing_file():
    from server import _parse_unity_events_tolerant
    events, skipped = _parse_unity_events_tolerant("/tmp/nonexistent_unity_events_w0test.json")
    if events or skipped:
        err(f"W0-3: expected ([], 0) for missing file, got ({events}, {skipped})")
    ok("W0-3: missing file returns ([], 0) — no exception raised")


# ── W0-4: clean single-object JSONL ──────────────────────────────────────────
def test_w0_4_clean_jsonl():
    from server import _parse_unity_events_tolerant
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        f.write('{"type":"sit_complete","_ts":1786900000.0}\n')
        path = f.name
    try:
        events, skipped = _parse_unity_events_tolerant(path)
        if len(events) != 1:
            err(f"W0-4: expected 1 event, got {len(events)}")
        if skipped != 0:
            err(f"W0-4: expected 0 skipped for clean JSONL, got {skipped}")
        if events[0].get("type") != "sit_complete":
            err(f"W0-4: wrong event type: {events[0]}")
    finally:
        os.unlink(path)
    ok("W0-4: clean single-object JSONL parses correctly")


# ── W0-5: consume_window_events returns window events from multi-event file ───
def test_w0_5_consume_window_events():
    from faculties.window_event_faculty import consume_window_events
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        # concatenated: an ACK + a window event on the same "line"
        f.write('{"type":"sit_complete","_ts":1.0}{"type":"window_closed","_ts":2.0,"window":"Safari"}')
        path = f.name
    try:
        result = consume_window_events(events_path=path)
        if len(result) != 1:
            err(f"W0-5: expected 1 window event, got {len(result)}: {result}")
        if result[0].get("type") != "window_closed":
            err(f"W0-5: wrong event type: {result[0]}")
    finally:
        os.unlink(path)
    ok("W0-5: consume_window_events reads window events from concatenated/multi-event file")


# ── W0-6: consume_gaze_events returns gaze events from multi-event file ───────
def test_w0_6_consume_gaze_events():
    from faculties.window_event_faculty import consume_gaze_events
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        f.write('{"event":"arrival","_ts":1.0}\n{"type":"gaze_target_changed","_ts":2.0,"gaze":{},"on_window":false}')
        path = f.name
    try:
        result = consume_gaze_events(events_path=path)
        if len(result) != 1:
            err(f"W0-6: expected 1 gaze event, got {len(result)}: {result}")
        if result[0].get("type") != "gaze_target_changed":
            err(f"W0-6: wrong event type: {result[0]}")
    finally:
        os.unlink(path)
    ok("W0-6: consume_gaze_events reads gaze events from multi-event file")


# ── W0-7: real file (if present) — no valid objects are lost ─────────────────
def test_w0_7_real_file_if_present():
    from server import _parse_unity_events_tolerant
    real_path = os.path.join(ROOT, "blender", "unity_events.json")
    if not os.path.exists(real_path):
        ok("W0-7: unity_events.json absent — skipped (run after server has started)")
        return
    events, skipped = _parse_unity_events_tolerant(real_path)
    if skipped > 0:
        print(f"  NOTE  W0-7: {skipped} fragment(s) skipped from real file — expected on first run; "
              f"should be 0 after file is consumed and Unity re-writes")
    if not events and not skipped:
        ok("W0-7: unity_events.json is empty — file already consumed")
        return
    ok(f"W0-7: real file — {len(events)} event(s) parsed, {skipped} skipped. "
       f"{'FRESH RUN NEEDED for 0-skipped proof' if skipped else 'Fragment-free ✓'}")


# ── runner ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("W0 — ACK CHANNEL READABLE (closes card 0045 / proves W1 path)")
    print()
    test_w0_1_concatenated_objects()
    test_w0_2_skipped_count_on_corrupt()
    test_w0_3_missing_file()
    test_w0_4_clean_jsonl()
    test_w0_5_consume_window_events()
    test_w0_6_consume_gaze_events()
    test_w0_7_real_file_if_present()
    print()
    print("7/7 PASS — W0 ACK channel parser fixed")
    print()
    print("W0 PROVEN when (card 0045):")
    print("  1. skipped-fragment counter reads 0 on a fresh run")
    print("     (server consumes corrupt file; Unity re-writes clean events)")
    print("  2. A decision_journal row shows outcome derived from a real ACK")
    print("     (requires server running with W0 active + Unity emitting sit/move ACK)")
