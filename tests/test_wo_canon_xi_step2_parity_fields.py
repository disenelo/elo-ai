"""
tests/test_wo_canon_xi_step2_parity_fields.py — WO-CANON-XI-STEP2

AT-1: remember_route with brain_route/unity_route writes both fields to JSONL
AT-2: remember_route without brain_route/unity_route writes explicit null for both
AT-3: ack_received=False → returns False, nothing written (ack gate unchanged)
AT-4: existing signature (no brain_route/unity_route kwargs) → no TypeError
AT-5: parity plumbing — 2 entries (1 matched, 1 mismatched) → count=2, matched=1, rate=50%
"""
import json
import os
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from self.route_memory import remember_route


# ── AT-1: brain_route + unity_route written to JSONL ─────────────────────────

def test_at1_brain_route_unity_route_written(tmp_path):
    log = str(tmp_path / "route_memory.jsonl")
    result = remember_route(
        goal_surface="browser",
        legs=["win-1", "win-2"],
        arrived=True,
        fell=False,
        duration_s=1.5,
        smoothness=0.9,
        ack_id="ack-001",
        ack_received=True,
        goal_win_id=None,
        brain_route=["win-1", "win-2"],
        unity_route=["win-1", "win-2"],
        log_path=log,
    )
    assert result is True, "remember_route should return True on success"
    with open(log, encoding="utf-8") as f:
        record = json.loads(f.readline())
    assert record["brain_route"] == ["win-1", "win-2"], f"brain_route wrong: {record['brain_route']!r}"
    assert record["unity_route"] == ["win-1", "win-2"], f"unity_route wrong: {record['unity_route']!r}"


# ── AT-2: omitted brain_route/unity_route → explicit null ────────────────────

def test_at2_null_fields_when_not_provided(tmp_path):
    log = str(tmp_path / "route_memory.jsonl")
    remember_route(
        goal_surface="code",
        legs=["win-3"],
        arrived=True,
        fell=False,
        duration_s=0.8,
        smoothness=0.95,
        ack_id="ack-002",
        ack_received=True,
        log_path=log,
    )
    with open(log, encoding="utf-8") as f:
        record = json.loads(f.readline())
    assert "brain_route" in record, "brain_route key must be present (not missing)"
    assert "unity_route" in record, "unity_route key must be present (not missing)"
    assert record["brain_route"] is None, f"brain_route should be null, got {record['brain_route']!r}"
    assert record["unity_route"] is None, f"unity_route should be null, got {record['unity_route']!r}"


# ── AT-3: ack_received=False → nothing written ────────────────────────────────

def test_at3_ack_false_nothing_written(tmp_path):
    log = str(tmp_path / "route_memory.jsonl")
    result = remember_route(
        goal_surface="browser",
        legs=["win-1"],
        arrived=False,
        fell=False,
        duration_s=0.5,
        smoothness=0.5,
        ack_id="ack-003",
        ack_received=False,
        brain_route=["win-1"],
        log_path=log,
    )
    assert result is False, "ack_received=False must return False"
    assert not os.path.exists(log), "no JSONL file should be written when ack_received=False"


# ── AT-4: backwards compatibility — existing call signature → no TypeError ────

def test_at4_existing_callers_no_type_error(tmp_path):
    log = str(tmp_path / "route_memory.jsonl")
    try:
        remember_route(
            goal_surface="chat",
            legs=["win-5", "win-6"],
            arrived=True,
            fell=False,
            duration_s=2.1,
            smoothness=0.8,
            ack_id="ack-004",
            ack_received=True,
            goal_win_id=42,
            log_path=log,
        )
    except TypeError as e:
        pytest.fail(f"Existing call signature raised TypeError: {e}")


# ── AT-5: parity plumbing — field counting and match rate ────────────────────

def test_at5_parity_plumbing(tmp_path):
    log = str(tmp_path / "route_memory.jsonl")

    # Entry 1: matched (brain == unity)
    remember_route(
        goal_surface="code",
        legs=["win-1", "win-2"],
        arrived=True,
        fell=False,
        duration_s=1.0,
        smoothness=0.9,
        ack_id="ack-p1",
        ack_received=True,
        brain_route=["win-1", "win-2"],
        unity_route=["win-1", "win-2"],
        log_path=log,
    )

    # Entry 2: mismatched (brain ≠ unity)
    remember_route(
        goal_surface="browser",
        legs=["win-3", "win-4"],
        arrived=True,
        fell=False,
        duration_s=1.2,
        smoothness=0.85,
        ack_id="ack-p2",
        ack_received=True,
        brain_route=["win-3", "win-4"],
        unity_route=["win-4", "win-3"],
        log_path=log,
    )

    entries = []
    with open(log, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                entries.append(json.loads(line))

    parity_entries = [e for e in entries if "brain_route" in e and "unity_route" in e
                      and e["brain_route"] is not None and e["unity_route"] is not None]
    assert len(parity_entries) == 2, f"expected 2 parity entries, got {len(parity_entries)}"

    matched = sum(1 for e in parity_entries if e["brain_route"] == e["unity_route"])
    assert matched == 1, f"expected 1 matched entry, got {matched}"

    rate_pct = round(matched / len(parity_entries) * 100)
    assert rate_pct == 50, f"expected 50% match rate, got {rate_pct}%"
