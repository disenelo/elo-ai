"""
tests/test_wo_pres004_failed_navigation.py — WO-PRES-004

AT-1: handle_navigate() produces navigation_failed outcome when no reachable route exists.
AT-2: [NAVIGATE_OUTCOME] distinguishes success from failure — no silent failure path.
AT-3: Failure outcome does not produce a repeated loop — _PENDING_MOVE cleared on failure.
AT-4: Executive receives and processes the failed_navigation trigger without crashing.
AT-5: Failure outcome appears in the capability result chain (visible to consequence consumers).
"""
import importlib
import json
import os
import sys
import tempfile
import types

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ── AT-1: handle_navigate returns navigation_failed when reachable=False ──────

def test_at1_navigation_failed_outcome_when_not_reachable():
    """D-1: reachable=False → named navigation_failed outcome dict."""
    from runtime.backend_router import handle_navigate
    result = handle_navigate({"goal_win_id": 42}, reachable=False)
    assert isinstance(result, dict), "Expected dict outcome, got None"
    assert result.get("outcome") == "navigation_failed"
    assert result.get("reason") == "no_reachable_route"
    assert result.get("goal_win_id") == 42


def test_at1_success_path_unmodified():
    """Original path untouched — reachable=True (default) still returns movement intent."""
    from runtime.backend_router import handle_navigate
    result = handle_navigate({"goal_win_id": 7})
    assert isinstance(result, dict)
    assert result.get("name") == "move"
    assert result.get("goal_win_id") == 7


def test_at1_none_still_returned_on_no_signal():
    """No nav signal + reachable=True → still None (AT-5 backward compat)."""
    from runtime.backend_router import handle_navigate
    result = handle_navigate({})
    assert result is None


# ── AT-2: server.py [NAVIGATE_OUTCOME] distinguishes success from failure ─────

def test_at2_navigate_outcome_block_in_server_source():
    """NAVIGATION_FAILED block must be distinct from [NAVIGATE_OUTCOME] in server.py."""
    server_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "server.py")
    with open(server_path, encoding="utf-8") as f:
        src = f.read()
    assert "[NAVIGATION_FAILED]" in src, "server.py missing [NAVIGATION_FAILED] distinct block"
    assert "navigation_failed" in src, "server.py missing navigation_failed outcome reference"
    assert "EVALUATE_BEAT" in src, "server.py missing [EVALUATE_BEAT] settle directive"
    # Success path still present
    assert "ARRIVED" in src and "FELL" in src, "server.py success/fell paths must remain"


# ── AT-3: failure is one-shot — PENDING_MOVE cleared, no loop ─────────────────

def test_at3_pending_move_cleared_on_failure_in_source():
    """D-3: server.py must clear _PENDING_MOVE["active"] = False in the FAILED branch."""
    server_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "server.py")
    with open(server_path, encoding="utf-8") as f:
        src = f.read()
    # The NAVIGATION_FAILED block and PENDING_MOVE clear must co-occur
    nav_failed_idx = src.index("[NAVIGATION_FAILED]")
    # Find next occurrence of _PENDING_MOVE["active"] = False after [NAVIGATION_FAILED]
    clear_idx = src.find('_PENDING_MOVE["active"] = False', nav_failed_idx)
    assert clear_idx != -1, (
        "_PENDING_MOVE['active'] = False must appear after [NAVIGATION_FAILED] block"
    )
    # Ensure it appears before the next elif/else block (not from a different branch)
    between = src[nav_failed_idx:clear_idx]
    assert len(between) < 2000, "Clear statement is too far from NAVIGATION_FAILED block"


# ── AT-4: failed_navigation trigger reaches Executive without crash ───────────

def test_at4_handle_navigate_reachable_false_does_not_crash():
    """D-2: reachable=False path is safe — no exception, returns dict."""
    from runtime.backend_router import handle_navigate
    for goal in [1, 99, None, "bad"]:
        result = handle_navigate({"goal_win_id": goal}, reachable=False)
        assert isinstance(result, dict), f"Expected dict for goal={goal!r}"
        assert result["outcome"] == "navigation_failed"


def test_at4_failed_navigation_block_provides_evaluate_beat():
    """D-2: [EVALUATE_BEAT] in the NAVIGATION_FAILED block gives Executive settle directive."""
    server_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "server.py")
    with open(server_path, encoding="utf-8") as f:
        src = f.read()
    nav_failed_idx = src.index("[NAVIGATION_FAILED]")
    block_end = src.find("g_ctx", nav_failed_idx)
    block = src[nav_failed_idx:block_end]
    assert "EVALUATE_BEAT" in block, "[EVALUATE_BEAT] must be inside NAVIGATION_FAILED block"
    assert "settle" in block.lower(), "settle directive must appear in NAVIGATION_FAILED block"


# ── AT-5: failure logged to capability result chain ───────────────────────────

def test_at5_capability_result_recording_in_source():
    """D-4: server.py must call record_capability_result for the navigation_failed case."""
    server_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "server.py")
    with open(server_path, encoding="utf-8") as f:
        src = f.read()
    nav_failed_idx = src.index("[NAVIGATION_FAILED]")
    # record_capability_result must appear after [NAVIGATION_FAILED] and before next elif
    after = src[nav_failed_idx:nav_failed_idx + 2500]
    assert "record_capability_result" in after, (
        "record_capability_result must be called in NAVIGATION_FAILED block"
    )
    assert "succeeded=False" in after, "capability result must record succeeded=False"
    assert "failure_reason" in after, "capability result must include failure_reason"


def test_at5_record_capability_result_importable():
    """self.capability_memory.record_capability_result is importable and callable."""
    from self.capability_memory import record_capability_result
    import inspect
    sig = inspect.signature(record_capability_result)
    params = list(sig.parameters)
    assert "capability" in params
    assert "succeeded" in params
    assert "failure_reason" in params


def test_at5_capability_result_writes_on_failure(tmp_path):
    """record_capability_result with succeeded=False writes a JSONL record."""
    from self.capability_memory import record_capability_result
    log = tmp_path / "cap.jsonl"
    record_capability_result(
        capability="navigate",
        experience_id="test-xid",
        goal_surface="goal_win_id=42",
        result_summary="navigation_failed: no_reachable_route",
        result_typed={"outcome": "navigation_failed", "reason": "no_reachable_route", "goal_win_id": 42},
        succeeded=False,
        failure_reason="no_reachable_route",
        log_path=str(log),
    )
    assert log.exists(), "JSONL log file must be created"
    with open(log) as f:
        record = json.loads(f.readline())
    assert record["capability"] == "navigate"
    assert record["succeeded"] is False
    assert record["failure_reason"] == "no_reachable_route"
