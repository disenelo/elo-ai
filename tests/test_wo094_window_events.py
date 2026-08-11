"""
tests/test_wo094_window_events.py — WO-094: Window Events / Noticing and Choosing

Assertions:
  AT-0: consume_window_events returns [] on absent/non-window events; returns event on match
  AT-1: decide_window_event returns None for empty state, is_elo_surface, unknown ev_type
  AT-2: user_active=True → peripheral (not full decision); user idle → real decision
  AT-3: route_memory — remember_route writes ONLY on ack_received=True; recall/confidence match
  AT-4: ambient_engine.py wires WO-094; window_event_faculty.py and route_memory.py compile clean

Run: python3 tests/test_wo094_window_events.py
"""
from __future__ import annotations

import json
import os
import py_compile
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

_passed = _failed = 0


def ok(label: str):
    global _passed
    _passed += 1
    print(f"  ✅ {label}")


def fail(label: str, err):
    global _failed
    _failed += 1
    print(f"  ❌ {label}: {err}")


_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# ── AT-0: consume_window_events ───────────────────────────────────────────────
try:
    from faculties.window_event_faculty import consume_window_events

    with tempfile.TemporaryDirectory() as tmp:
        # Absent file → []
        result = consume_window_events(os.path.join(tmp, "missing.json"))
        assert result == [], f"missing file must return [], got {result}"

        # Non-window event → []
        ev_path = os.path.join(tmp, "events.json")
        with open(ev_path, "w") as f:
            json.dump({"type": "user_idle", "idle_secs": 60}, f)
        result = consume_window_events(ev_path)
        assert result == [], f"user_idle must not match as window event, got {result}"

        # Window event → [event]
        with open(ev_path, "w") as f:
            json.dump({"type": "window_opened", "id": "surface_42", "_ts": 100.0}, f)
        result = consume_window_events(ev_path)
        assert len(result) == 1, f"window_opened must return [event], got {result}"
        assert result[0]["type"] == "window_opened", f"type mismatch: {result[0]}"

        ok("AT-0: consume_window_events: absent=[], non-window=[], window=[event]")
except AssertionError as e:
    fail("AT-0", e)
except Exception as e:
    fail("AT-0", e)


# ── AT-1: decide_window_event edge cases ──────────────────────────────────────
try:
    from faculties.window_event_faculty import decide_window_event

    class _FakeState:
        focal_thread = ""
        lifetime_threads: list = []
        inner_events: list = []
        curiosity = 0.50

    # No state → None
    assert decide_window_event({"type": "window_opened"}, state=None) is None, (
        "None state must return None"
    )

    # Empty state (no history) → None
    empty = _FakeState()
    assert decide_window_event({"type": "window_opened"}, state=empty) is None, (
        "Empty state (no focal/threads/events) must return None"
    )

    # is_elo_surface → None (Unity survival handles it)
    rich = _FakeState()
    rich.focal_thread = "code_review"
    assert decide_window_event(
        {"type": "window_closed", "id": "elo_win", "is_elo_surface": True},
        state=rich,
    ) is None, "is_elo_surface must return None"

    # Unknown ev_type → None
    assert decide_window_event({"type": "user_idle"}, state=rich) is None, (
        "Non-window ev_type must return None"
    )

    ok("AT-1: decide_window_event returns None for empty state / elo_surface / unknown type")
except AssertionError as e:
    fail("AT-1", e)
except Exception as e:
    fail("AT-1", e)


# ── AT-2: user_active vs user idle decisions ──────────────────────────────────
try:
    from faculties.window_event_faculty import decide_window_event

    class _RichState:
        focal_thread = "music_production"
        lifetime_threads = [["music", 5], ["code", 3]]
        inner_events = ["wonder", "curiosity", "focus"]
        curiosity = 0.80

    state = _RichState()
    event = {"type": "window_opened", "id": "surface_99", "_ts": 200.0}

    # user_active=True → peripheral
    decision_active = decide_window_event(event, state=state, user_active=True)
    assert decision_active is not None, "user_active must return a decision (peripheral)"
    assert decision_active["action"] == "peripheral", (
        f"user_active must produce 'peripheral', got {decision_active['action']!r}"
    )
    assert decision_active["goal_surface"] is None, "peripheral has no goal_surface"

    # user_active=False + high curiosity → observe
    decision_idle = decide_window_event(event, state=state, user_active=False)
    assert decision_idle is not None, "user idle must return a decision"
    assert decision_idle["action"] in ("observe", "glance"), (
        f"window_opened action must be observe or glance, got {decision_idle['action']!r}"
    )
    assert decision_idle["goal_surface"] == "surface_99", (
        f"goal_surface must match event id, got {decision_idle['goal_surface']!r}"
    )
    assert decision_idle["source"] == "window_event_faculty", (
        "decision must carry source field"
    )
    assert decision_idle["priority"] == "low", "decision must have priority=low"

    ok("AT-2: user_active → peripheral; user idle + high curiosity → observe/glance with correct fields")
except AssertionError as e:
    fail("AT-2", e)
except Exception as e:
    fail("AT-2", e)


# ── AT-3: route_memory — ACK gate + recall + confidence ──────────────────────
try:
    from self.route_memory import remember_route, recall_route, route_confidence

    with tempfile.TemporaryDirectory() as tmp:
        log = os.path.join(tmp, "route_memory.jsonl")

        # No ACK → not written
        wrote = remember_route("surface_A", ["leg1", "leg2"], True, False, 2.5, 0.9,
                                ack_id="ack_001", ack_received=False, log_path=log)
        assert not wrote, "ack_received=False must NOT write the record"
        assert not os.path.exists(log), "log must not be created without ACK"

        # ACK received → written
        wrote = remember_route("surface_A", ["leg1", "leg2"], True, False, 2.5, 0.9,
                                ack_id="ack_001", ack_received=True, log_path=log)
        assert wrote, "ack_received=True must write the record"
        assert os.path.exists(log), "log must be created after successful write"

        # Append-only: second record appended, not overwriting
        remember_route("surface_A", ["leg3"], False, True, 5.0, 0.3,
                       ack_id="ack_002", ack_received=True, log_path=log)
        with open(log) as f:
            lines = [l.strip() for l in f if l.strip()]
        assert len(lines) == 2, f"should be 2 records (append-only), got {len(lines)}"

        # recall_route returns the successful one
        best = recall_route("surface_A", log_path=log)
        assert best is not None, "recall_route must return a record"
        assert best["arrived"] is True, "recall_route must prefer successful route"
        assert best["ack_id"] == "ack_001", "should return the first (successful) route"

        # recall_route for unknown surface → None
        none_result = recall_route("surface_UNKNOWN", log_path=log)
        assert none_result is None, "unknown surface must return None"

        # route_confidence: 1 success out of 2 → 0.5
        conf = route_confidence("surface_A", log_path=log)
        assert conf == 0.5, f"confidence must be 0.5 (1/2 successes), got {conf}"

        # route_confidence for unknown surface → 0.0
        conf_none = route_confidence("surface_UNKNOWN", log_path=log)
        assert conf_none == 0.0, f"unknown surface confidence must be 0.0, got {conf_none}"

        ok("AT-3: route_memory: ACK gate, append-only, recall prefers success, confidence matches")
except AssertionError as e:
    fail("AT-3", e)
except Exception as e:
    fail("AT-3", e)


# ── AT-4: ambient_engine.py wires WO-094; files compile clean ─────────────────
try:
    engine_path = os.path.join(_BASE, "ambient", "ambient_engine.py")
    with open(engine_path, encoding="utf-8") as f:
        src = f.read()

    assert "WO-094" in src, "ambient_engine.py must carry WO-094 marker"
    assert "window_closed" in src, "ambient_engine.py must handle window_closed"
    assert "window_opened" in src, "ambient_engine.py must handle window_opened"
    assert "window_moved" in src, "ambient_engine.py must handle window_moved"
    assert "_handle_window_event" in src, "ambient_engine.py must call _handle_window_event"

    faculty_path = os.path.join(_BASE, "faculties", "window_event_faculty.py")
    route_path   = os.path.join(_BASE, "self", "route_memory.py")

    py_compile.compile(engine_path,   doraise=True)
    py_compile.compile(faculty_path,  doraise=True)
    py_compile.compile(route_path,    doraise=True)

    ok("AT-4: ambient_engine.py wires WO-094; all three files compile clean")
except AssertionError as e:
    fail("AT-4", e)
except Exception as e:
    fail("AT-4", e)


# ── Summary ───────────────────────────────────────────────────────────────────
print()
print("=" * 62)
print(f"WO-094 window events     {_passed} passed   {_failed} failed")
if _failed:
    sys.exit(1)
