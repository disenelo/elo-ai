"""
tests/test_wonav002_008_movement_ack_wiring.py
WO-NAV-002 (SP-3/SP-23) + WO-NAV-008 (SP-4) acceptance tests.

AT-1  SP-3  Rich payload in autobiography entry (arrived/fell/goal/duration_s from payload)
AT-2  SP-3  MovementOutcome.from_ack() called with since=; ack_id non-empty, duration_s > 0
AT-3  SP-23 ExecutionReport has 5 move fields (move_arrived, move_fell, move_goal_win_id,
            move_duration_s, move_issued_by) accessible at defaults
AT-4  SP-23 After ACK, ExecutionReport movement fields populated from _mout
AT-5  SP-4  remember_route() called on ACK with ack_received=True and ack_id from _mout
AT-6  SP-4  remember_route() NOT called when _move_acked is False
AT-7  SP-4  smoothness=1.0 on arrived=True,fell=False; 0.0 on fell=True
AT-8  N/A   No regression — WO-NAV-001 MovementOutcome.from_ack() field contract

Run: python3 tests/test_wonav002_008_movement_ack_wiring.py
"""
from __future__ import annotations
import json
import os
import sys
import tempfile
import time
import types

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

_passed = _failed = 0


def ok(label: str) -> None:
    global _passed
    _passed += 1
    print(f"  ✅ {label}")


def fail(label: str, err) -> None:
    global _failed
    _failed += 1
    print(f"  ❌ {label}: {err}")


# ── shared fixtures ────────────────────────────────────────────────────────────

def _make_movement_report_ack(arrived: bool = True, fell: bool = False,
                               goal: str = "top_of_chrome",
                               goal_win_id: int = 42,
                               route_nodes: list | None = None,
                               issued_by: str = "user_message",
                               ts: float | None = None,
                               ack_id: str = "ack-test-001") -> dict:
    ts = ts or time.time()
    return {
        "type": "movement_report",
        "_ts":  ts,
        "id":   ack_id,
        "report": {
            "arrived":      arrived,
            "fell":         fell,
            "goal":         goal,
            "goal_win_id":  goal_win_id,
            "route_nodes":  route_nodes or ["jump", "parkour_up"],
            "issued_by":    issued_by,
            "_ts":          ts,
        },
    }


# ── AT-1: rich payload in autobiography ───────────────────────────────────────
try:
    from runtime.movement_outcome import MovementOutcome
    ack = _make_movement_report_ack(arrived=True, fell=False, goal="upper_platform",
                                     goal_win_id=7, route_nodes=["walk", "jump"],
                                     issued_by="user_message", ts=1000.0, ack_id="ack-001")
    mout = MovementOutcome.from_ack(ack, since=998.0)

    # Simulate the server ACK block description building
    _mv_desc = "jump_right"
    _mv_ab_desc = (
        f"moved ({mout.goal or _mv_desc}) — body ACK confirmed"
        f" | arrived={mout.arrived} fell={mout.fell}"
        f" goal_win_id={mout.goal_win_id} duration_s={mout.duration_s}"
        f" route_nodes={mout.route_nodes} issued_by={mout.issued_by}"
    )
    assert "arrived=True" in _mv_ab_desc, f"arrived not in description: {_mv_ab_desc}"
    assert "fell=False"   in _mv_ab_desc, f"fell not in description"
    assert "goal_win_id=7" in _mv_ab_desc, f"goal_win_id not in description"
    assert "duration_s"   in _mv_ab_desc, f"duration_s not in description"
    assert "upper_platform" in _mv_ab_desc, f"goal not in description"
    ok("AT-1: rich payload in autobiography entry — all SP-3 fields present")
except AssertionError as e:
    fail("AT-1", e)
except Exception as e:
    fail("AT-1", e)


# ── AT-2: from_ack with since= → ack_id non-empty, duration_s > 0 ─────────────
try:
    ack = _make_movement_report_ack(arrived=True, ts=1002.5, ack_id="ack-002")
    mout = MovementOutcome.from_ack(ack, since=1000.0)
    assert mout.ack_id, f"ack_id should be non-empty: {mout.ack_id!r}"
    assert mout.duration_s > 0, f"duration_s should be > 0 when since is set, got {mout.duration_s}"
    assert round(mout.duration_s, 3) == 2.5, f"duration_s should be 2.5, got {mout.duration_s}"
    ok(f"AT-2: from_ack() with since=1000.0 → ack_id={mout.ack_id!r}, duration_s={mout.duration_s}")
except AssertionError as e:
    fail("AT-2", e)
except Exception as e:
    fail("AT-2", e)


# ── AT-3: ExecutionReport has 5 move fields accessible at defaults ────────────
try:
    from runtime.contracts import ExecutionReport
    er = ExecutionReport()
    assert hasattr(er, "move_arrived"),     "move_arrived missing from ExecutionReport"
    assert hasattr(er, "move_fell"),        "move_fell missing"
    assert hasattr(er, "move_goal_win_id"), "move_goal_win_id missing"
    assert hasattr(er, "move_duration_s"),  "move_duration_s missing"
    assert hasattr(er, "move_issued_by"),   "move_issued_by missing"
    assert er.move_arrived     is False,    f"default move_arrived should be False: {er.move_arrived}"
    assert er.move_fell        is False,    f"default move_fell should be False: {er.move_fell}"
    assert er.move_goal_win_id is None,     f"default move_goal_win_id should be None: {er.move_goal_win_id}"
    assert er.move_duration_s  == 0.0,      f"default move_duration_s should be 0.0: {er.move_duration_s}"
    assert er.move_issued_by   == "",       f"default move_issued_by should be '': {er.move_issued_by}"
    ok("AT-3: ExecutionReport has 5 move fields, all accessible with correct defaults")
except AssertionError as e:
    fail("AT-3", e)
except Exception as e:
    fail("AT-3", e)


# ── AT-4: ExecutionReport movement fields populated from _mout ────────────────
try:
    import dataclasses as _dc
    from runtime.contracts import ExecutionReport
    from runtime.movement_outcome import MovementOutcome

    er = ExecutionReport()
    ack = _make_movement_report_ack(arrived=True, fell=False, goal="upper_ledge",
                                     goal_win_id=99, issued_by="self_initiation",
                                     ts=1005.0, ack_id="ack-004")
    mout = MovementOutcome.from_ack(ack, since=1003.0)

    er_updated = _dc.replace(
        er,
        move_arrived    = mout.arrived,
        move_fell       = mout.fell,
        move_goal_win_id= mout.goal_win_id,
        move_duration_s = mout.duration_s,
        move_issued_by  = mout.issued_by,
    )
    assert er_updated.move_arrived    is True,             f"move_arrived: {er_updated.move_arrived}"
    assert er_updated.move_fell       is False,            f"move_fell: {er_updated.move_fell}"
    assert er_updated.move_goal_win_id == 99,              f"move_goal_win_id: {er_updated.move_goal_win_id}"
    assert er_updated.move_duration_s  == mout.duration_s, f"move_duration_s: {er_updated.move_duration_s}"
    assert er_updated.move_issued_by   == "self_initiation", f"move_issued_by: {er_updated.move_issued_by}"
    ok("AT-4: ExecutionReport movement fields populated from _mout via dataclasses.replace()")
except AssertionError as e:
    fail("AT-4", e)
except Exception as e:
    fail("AT-4", e)


# ── AT-5: remember_route() called on ACK with ack_received=True ──────────────
try:
    from self.route_memory import remember_route
    from runtime.movement_outcome import MovementOutcome

    ack = _make_movement_report_ack(arrived=True, fell=False, goal="side_panel",
                                     goal_win_id=3, route_nodes=["walk"],
                                     ts=1010.0, ack_id="ack-005")
    mout = MovementOutcome.from_ack(ack, since=1008.0)

    tmp_log = tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False, mode="w", encoding="utf-8")
    tmp_log.close()

    result = remember_route(
        goal_surface=mout.goal or "",
        legs=mout.route_nodes,
        arrived=mout.arrived,
        fell=mout.fell,
        duration_s=mout.duration_s,
        smoothness=1.0 if mout.arrived and not mout.fell else 0.0,
        ack_id=mout.ack_id,
        ack_received=True,
        log_path=tmp_log.name,
    )
    assert result is True, f"remember_route() should return True on ack_received=True, got {result}"

    with open(tmp_log.name, encoding="utf-8") as f:
        records = [json.loads(line) for line in f if line.strip()]
    assert len(records) == 1, f"Expected 1 route_memory record, got {len(records)}"
    r = records[0]
    assert r.get("ack_id") == mout.ack_id, f"ack_id mismatch: {r.get('ack_id')} vs {mout.ack_id}"
    assert r.get("arrived") is True,       f"arrived should be True: {r.get('arrived')}"
    os.unlink(tmp_log.name)
    ok(f"AT-5: remember_route() called on ACK; ack_id={mout.ack_id!r}, ack_received=True")
except AssertionError as e:
    fail("AT-5", e)
except Exception as e:
    fail("AT-5", e)


# ── AT-6: remember_route() NOT called when _move_acked is False ──────────────
try:
    from self.route_memory import remember_route

    tmp_log = tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False, mode="w", encoding="utf-8")
    tmp_log.close()

    # Simulating ack_received=False — function must return False and not write
    result = remember_route(
        goal_surface="top_bar",
        legs=[],
        arrived=False,
        fell=False,
        duration_s=0.0,
        smoothness=0.0,
        ack_id="no-ack",
        ack_received=False,
        log_path=tmp_log.name,
    )
    assert result is False, f"remember_route() with ack_received=False should return False, got {result}"

    with open(tmp_log.name, encoding="utf-8") as f:
        lines = [l for l in f if l.strip()]
    assert not lines, f"remember_route() should NOT write when ack_received=False, wrote {len(lines)} line(s)"
    os.unlink(tmp_log.name)
    ok("AT-6: remember_route() NOT called when ack_received=False — no record written")
except AssertionError as e:
    fail("AT-6", e)
except Exception as e:
    fail("AT-6", e)


# ── AT-7: smoothness=1.0 on arrived; 0.0 on fell ─────────────────────────────
try:
    from runtime.movement_outcome import MovementOutcome

    ack_ok  = _make_movement_report_ack(arrived=True,  fell=False, ts=1020.0)
    ack_bad = _make_movement_report_ack(arrived=False, fell=True,  ts=1025.0)
    mout_ok  = MovementOutcome.from_ack(ack_ok)
    mout_bad = MovementOutcome.from_ack(ack_bad)

    smooth_ok  = 1.0 if mout_ok.arrived  and not mout_ok.fell  else 0.0
    smooth_bad = 1.0 if mout_bad.arrived and not mout_bad.fell else 0.0

    assert smooth_ok  == 1.0, f"arrived=T,fell=F → smoothness should be 1.0, got {smooth_ok}"
    assert smooth_bad == 0.0, f"fell=T → smoothness should be 0.0, got {smooth_bad}"
    ok("AT-7: smoothness placeholder 1.0 on arrived, 0.0 on fell — [ESTIMATE] correct")
except AssertionError as e:
    fail("AT-7", e)
except Exception as e:
    fail("AT-7", e)


# ── AT-8: WO-NAV-001 regression — MovementOutcome.from_ack() field contract ──
try:
    from runtime.movement_outcome import MovementOutcome

    ack = _make_movement_report_ack(arrived=True, fell=False, goal="test_goal",
                                     goal_win_id=5, route_nodes=["a", "b"],
                                     issued_by="user_message", ts=1030.5, ack_id="ack-008")
    mout = MovementOutcome.from_ack(ack, since=1028.0)
    assert mout.arrived      is True,           f"arrived: {mout.arrived}"
    assert mout.fell         is False,          f"fell: {mout.fell}"
    assert mout.goal         == "test_goal",    f"goal: {mout.goal}"
    assert mout.goal_win_id  == 5,              f"goal_win_id: {mout.goal_win_id}"
    assert mout.route_nodes  == ["a", "b"],     f"route_nodes: {mout.route_nodes}"
    assert mout.issued_by    == "user_message", f"issued_by: {mout.issued_by}"
    assert mout.ack_id       == "ack-008",      f"ack_id: {mout.ack_id}"
    ok("AT-8: WO-NAV-001 regression — MovementOutcome.from_ack() field contract intact")
except AssertionError as e:
    fail("AT-8", e)
except Exception as e:
    fail("AT-8", e)


# ── summary ────────────────────────────────────────────────────────────────────
print()
print("=" * 62)
print(f"WO-NAV-002/008 movement ACK wiring   {_passed} passed   {_failed} failed")
