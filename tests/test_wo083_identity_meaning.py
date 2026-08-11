"""
tests/test_wo083_identity_meaning.py — WO-083: Identity & Meaning (convergence layer)

Assertions:
  AT-0: derive_tendencies returns [] when state has no evidence (no fabrication)
  AT-1: derive_tendencies returns claims only when thresholds are met
  AT-2: consistency_check flags focal_thread + all-quiet inner_events
  AT-3: flag_value_change routes through personality_drift.propose() — never direct write
  AT-4: server.py wires identity_block; py_compile clean

Run: python3 tests/test_wo083_identity_meaning.py
"""
from __future__ import annotations

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


def _empty_state():
    from self.elo_self_model import EloSelfState
    return EloSelfState(
        mood=0.55,
        focal_thread="",
        inner_events=[],
        lifetime_threads=[],
        recent_behavior={},
    )


# ── AT-0: empty state → no tendencies (verified speech, no fabrication) ───────
try:
    from self.identity_meaning import derive_tendencies

    state = _empty_state()
    result = derive_tendencies(state)
    assert isinstance(result, list), "derive_tendencies must return a list"
    assert result == [], (
        f"derive_tendencies must return [] for empty state, got {result}"
    )
    ok("AT-0: derive_tendencies returns [] for empty state — no fabricated claims")
except AssertionError as e:
    fail("AT-0", e)
except Exception as e:
    fail("AT-0", e)


# ── AT-1: derive_tendencies only claims when thresholds are met ───────────────
try:
    from self.identity_meaning import derive_tendencies

    state = _empty_state()
    # Only 2 occurrences of "creativity" → below _LIFETIME_MIN_COUNT of 3, no claim
    state.lifetime_threads = [["creativity", 2], ["depth", 1]]
    below = derive_tendencies(state)
    assert below == [], (
        f"derive_tendencies must not claim a thread with count < 3, got {below}"
    )

    # Now 3 occurrences → claim should appear
    state.lifetime_threads = [["creativity", 3]]
    above = derive_tendencies(state)
    assert len(above) == 1, (
        f"derive_tendencies should claim exactly one thread at count=3, got {above}"
    )
    assert "creativity" in above[0], (
        f"tendency should mention 'creativity', got {above[0]!r}"
    )

    # Inner events: 3 identical "creative_spark" → one phrase should appear
    state2 = _empty_state()
    state2.inner_events = ["creative_spark", "quiet", "creative_spark", "flat", "creative_spark"]
    above2 = derive_tendencies(state2)
    assert any("light up" in t for t in above2), (
        f"3× creative_spark should produce 'light up' tendency, got {above2}"
    )

    ok("AT-1: derive_tendencies respects thresholds — no under-threshold claims")
except AssertionError as e:
    fail("AT-1", e)
except Exception as e:
    fail("AT-1", e)


# ── AT-2: consistency_check flags focal_thread when all events are flat/quiet ─
try:
    from self.identity_meaning import consistency_check

    # No focal_thread, no flag expected
    state = _empty_state()
    state.inner_events = ["flat", "flat", "flat", "flat"]
    result = consistency_check(state)
    assert result["consistent"] is True, (
        f"no focal_thread + quiet should be consistent, got {result}"
    )

    # focal_thread + all quiet → inconsistency flagged
    state2 = _empty_state()
    state2.focal_thread = "the game world"
    state2.inner_events = ["flat", "quiet", "flat", "quiet"]
    result2 = consistency_check(state2)
    assert result2["consistent"] is False, (
        f"focal_thread + all-quiet should be inconsistent, got {result2}"
    )
    assert result2["flag"] is not None, "inconsistent result must include a flag string"
    assert "the game world" in result2["flag"], (
        f"flag should mention focal_thread, got {result2['flag']!r}"
    )
    ok("AT-2: consistency_check flags focal_thread + all-quiet inner_events")
except AssertionError as e:
    fail("AT-2", e)
except Exception as e:
    fail("AT-2", e)


# ── AT-3: flag_value_change routes through drift gate (no direct write) ────────
try:
    import json
    from unittest.mock import patch

    from self.identity_meaning import flag_value_change

    proposals_captured = []

    def _fake_propose(emotional_history, session_summaries):
        proposals_captured.append({
            "emotional_history": emotional_history,
            "session_summaries": session_summaries,
        })
        return {"status": "pending", "needs_david": True, "deltas": {}, "ts": 0}

    import memory.personality_drift as _pd_mod
    with patch.object(_pd_mod, "propose", side_effect=_fake_propose):
        result = flag_value_change("wonder", 0.01, "identity convergence test")

    assert len(proposals_captured) == 1, (
        f"flag_value_change must call propose() once, called {len(proposals_captured)}"
    )
    assert result.get("status") == "pending", (
        f"returned dict must carry status=pending, got {result}"
    )

    # Personality state file must NOT have been written
    pers_path = os.path.join(_BASE, "memory", "personality_state.json")
    with tempfile.TemporaryDirectory() as td:
        fake_path = os.path.join(td, "personality_state.json")
        with patch("memory.personality_drift._PATH", fake_path):
            _ = flag_value_change("directness", -0.01)
        assert not os.path.exists(fake_path), (
            "flag_value_change must NOT write personality_state.json"
        )
    ok("AT-3: flag_value_change routes through drift gate — no direct personality write")
except AssertionError as e:
    fail("AT-3", e)
except Exception as e:
    fail("AT-3", e)


# ── AT-4: server.py wires identity_block and compiles clean ───────────────────
try:
    server_path = os.path.join(_BASE, "server.py")
    with open(server_path, encoding="utf-8") as f:
        src = f.read()

    assert "identity_meaning" in src, (
        "server.py must import from self.identity_meaning (WO-083 wiring)"
    )
    assert "_im_identity_block" in src, (
        "server.py must call _im_identity_block() (WO-083 injection)"
    )
    assert "WO-083" in src, (
        "server.py must carry WO-083 marker at injection site"
    )

    py_compile.compile(server_path, doraise=True)
    ok("AT-4: server.py wires identity_block with WO-083 marker; py_compile clean")
except AssertionError as e:
    fail("AT-4", e)
except Exception as e:
    fail("AT-4", e)


# ── Summary ───────────────────────────────────────────────────────────────────
print()
print("=" * 62)
print(f"WO-083 identity & meaning   {_passed} passed   {_failed} failed")
if _failed:
    sys.exit(1)
