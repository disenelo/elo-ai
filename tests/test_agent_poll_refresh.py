"""
tests/test_agent_poll_refresh.py

WP_F gap: company_runtime/agent_poll.py + agent_refresh.py — bus sweep and agent diff.
Pure-logic tests avoid calling the live bus (agent_bus.ping_all). All filesystem and
bus interactions are mocked so no BUS directory writes or network calls occur.

Run: ~/miniconda3/bin/python3 -m pytest tests/test_agent_poll_refresh.py -q
"""
import os
import sys
import json
import tempfile
from unittest.mock import patch, mock_open

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from company_runtime.agent_poll import _dispatched_active, REPO_AGENTS


def test_repo_agents_constant():
    """AT-1: REPO_AGENTS contains the 3 canonical repo seat ids."""
    for seat in ("builder", "design", "game"):
        assert seat in REPO_AGENTS, f"AT-1: '{seat}' missing from REPO_AGENTS; got {REPO_AGENTS}"
    assert len(REPO_AGENTS) == 3, f"AT-1: expected 3 REPO_AGENTS; got {len(REPO_AGENTS)}"


def test_dispatched_active_filters_to_active_only():
    """AT-2: _dispatched_active() returns only items with state=='active'."""
    pending = [
        {"wo": "WO-A", "state": "active",    "title": "Do this"},
        {"wo": "WO-B", "state": "ready",     "title": "Next up"},
        {"wo": "WO-C", "state": "blocked",   "title": "Stuck"},
        {"wo": "WO-D", "state": "active",    "title": "Also active"},
        {"wo": "WO-E", "state": "in_review", "title": "With David"},
    ]
    result = _dispatched_active(pending)
    wos = [p["wo"] for p in result]
    assert "WO-A" in wos and "WO-D" in wos, f"AT-2: active items missing; got {wos}"
    assert "WO-B" not in wos, f"AT-2: ready item must not appear; got {wos}"
    assert "WO-C" not in wos, f"AT-2: blocked item must not appear; got {wos}"


def test_dispatched_active_empty_pending():
    """AT-3: _dispatched_active([]) returns []."""
    assert _dispatched_active([]) == [], "AT-3: empty pending must return []"


def test_dispatched_active_none_active():
    """AT-4: _dispatched_active() returns [] when no items have state=='active'."""
    pending = [
        {"wo": "WO-X", "state": "ready"},
        {"wo": "WO-Y", "state": "blocked"},
    ]
    result = _dispatched_active(pending)
    assert result == [], f"AT-4: no active items must return []; got {result}"


def test_sweep_returns_dict_with_agents_key():
    """AT-5: sweep() returns a dict with 'agents' and 'generated' keys (no live bus)."""
    with patch("company_runtime.agent_bus.ping_all"):
        with patch("os.path.exists", return_value=False):
            with patch("json.dump"):
                from company_runtime.agent_poll import sweep
                result = sweep()
    assert isinstance(result, dict), f"AT-5: sweep() must return dict; got {type(result)}"
    assert "agents" in result, f"AT-5: result must have 'agents' key; got {list(result)}"
    assert "generated" in result, f"AT-5: result must have 'generated' key; got {list(result)}"


def test_sweep_empty_bus_produces_empty_agents():
    """AT-6: sweep() with no inbox files returns agents={}."""
    with patch("company_runtime.agent_bus.ping_all"):
        with patch("os.path.exists", return_value=False):
            with patch("json.dump"):
                from company_runtime.agent_poll import sweep
                result = sweep()
    assert result["agents"] == {}, (
        f"AT-6: no inbox files must yield empty agents dict; got {result['agents']}"
    )


def test_sweep_inbox_present_populates_agent_entry():
    """AT-7: sweep() with a mock inbox yields structured agent entry with expected keys."""
    INBOX = {"pending": [{"wo": "WO-1", "state": "active", "title": "Task A", "badge": "P1"}]}
    SNAP = {"wos": []}

    # only builder's paths exist; design/game skip cleanly
    def _exists(path):
        if "builder" in path and ("inbox.json" in path or ".poll_snapshot" in path or "outbox.json" in path):
            return True
        return False

    def _getmtime(path):
        import time
        return time.time() - 3600

    # json.load is called: builder/inbox.json, builder/.poll_snapshot.json
    with patch("company_runtime.agent_bus.ping_all"):
        with patch("os.path.exists", side_effect=_exists):
            with patch("os.path.getmtime", side_effect=_getmtime):
                with patch("json.load", side_effect=[INBOX, SNAP]):
                    with patch("json.dump"):
                        with patch("builtins.open", mock_open()):
                            from company_runtime.agent_poll import sweep
                            result = sweep()

    assert "builder" in result["agents"], (
        f"AT-7: builder entry missing; got {list(result['agents'])}"
    )
    entry = result["agents"]["builder"]
    for key in ("active_dispatched", "new_since_last", "pending", "agent_fresh", "act_eligible"):
        assert key in entry, f"AT-7: agent entry must have '{key}'; got {list(entry)}"


if __name__ == "__main__":
    _tests = [
        ("AT-1", test_repo_agents_constant),
        ("AT-2", test_dispatched_active_filters_to_active_only),
        ("AT-3", test_dispatched_active_empty_pending),
        ("AT-4", test_dispatched_active_none_active),
        ("AT-5", test_sweep_returns_dict_with_agents_key),
        ("AT-6", test_sweep_empty_bus_produces_empty_agents),
        ("AT-7", test_sweep_inbox_present_populates_agent_entry),
    ]
    _passed = _failed = 0
    for label, fn in _tests:
        try:
            fn()
            print(f"  ✅ {label}: {fn.__name__}")
            _passed += 1
        except Exception as _e:
            print(f"  ❌ {label}: {fn.__name__} — {_e}")
            _failed += 1
    print()
    print("=" * 62)
    print(f"agent_poll_refresh   {_passed}/{_passed + _failed} passed, {_failed} failed")
    if _failed:
        sys.exit(1)
