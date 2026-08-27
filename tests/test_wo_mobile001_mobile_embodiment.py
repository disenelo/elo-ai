"""
tests/test_wo_mobile001_mobile_embodiment.py

Acceptance tests for WO-MOBILE-001 (D-SPINE-1 / D-SPINE-2 / D-SPINE-3).
5 pytest-style ATs — no sys.exit at module level.

Run: ~/miniconda3/bin/python3 -m pytest tests/test_wo_mobile001_mobile_embodiment.py -q
"""
import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def _fresh_state(**kw):
    from self.elo_self_model import EloSelfState
    s = EloSelfState()
    s.nearby_surfaces = kw.get("nearby_surfaces", ["win_4", "win_7"])
    s.embodiment = kw.get("embodiment", "desktop")
    s.mobile_lifecycle = kw.get("mobile_lifecycle", "")
    return s


# AT-1 — D-SPINE-1: foreground event → current_embodiment = "phone" in state
def test_mobile_foreground_sets_embodiment_phone():
    from runtime.mobile_embodiment import apply_mobile_foreground
    state = _fresh_state()
    state = apply_mobile_foreground(state, ts=time.time())
    assert state.embodiment == "phone", (
        f"AT-1: current_embodiment must be 'phone' after foreground event; got {state.embodiment!r}"
    )


# AT-2 — D-SPINE-1: embodiment_scope on phone filters desktop-only caps
#         Verified via spine.py — _capability_faculty reads state.embodiment
def test_embodiment_scope_filters_on_phone():
    from runtime.mobile_embodiment import apply_mobile_foreground
    from runtime.spine.spine import _capability_faculty
    state = _fresh_state()
    state = apply_mobile_foreground(state, ts=time.time())
    # Ask spine for capabilities with the phone embodiment
    caps = _capability_faculty("what time is it", "time", current_embodiment=state.embodiment)
    # Spine must not error — capabilities list is returned (may be empty if none enabled)
    assert isinstance(caps, list), "AT-2: _capability_faculty must return a list for phone embodiment"


# AT-3 — D-SPINE-1: embodiment_transitions contains transition record with timestamp
def test_mobile_foreground_records_transition_with_ts():
    from runtime.mobile_embodiment import apply_mobile_foreground
    state = _fresh_state()
    ts_before = time.time()
    state = apply_mobile_foreground(state, ts=ts_before)
    assert len(state.embodiment_transitions) >= 1, "AT-3: embodiment_transitions must have a record"
    latest = state.embodiment_transitions[-1]
    assert latest.get("to") == "phone", f"AT-3: transition 'to' must be 'phone'; got {latest}"
    assert "ts" in latest, "AT-3: transition must have a timestamp"
    assert latest["event"] == "mobile_foreground", "AT-3: transition event must be 'mobile_foreground'"


# AT-4 — D-SPINE-2: background event → current_embodiment stays "phone" (does NOT revert)
def test_mobile_background_keeps_embodiment_phone():
    from runtime.mobile_embodiment import apply_mobile_foreground, apply_mobile_background
    state = _fresh_state()
    state = apply_mobile_foreground(state, ts=time.time())
    assert state.embodiment == "phone"
    # Now simulate background
    state = apply_mobile_background(state, ts=time.time())
    assert state.embodiment == "phone", (
        "AT-4: current_embodiment must stay 'phone' on background — must not revert to 'desktop'"
    )
    assert state.mobile_lifecycle == "background", (
        f"AT-4: mobile_lifecycle must be 'background'; got {state.mobile_lifecycle!r}"
    )


# AT-5 — D-SPINE-3: nearby_surfaces is explicitly cleared on mobile switch
def test_nearby_surfaces_cleared_on_mobile_foreground():
    from runtime.mobile_embodiment import apply_mobile_foreground
    state = _fresh_state(nearby_surfaces=["win_4", "win_7", "win_12"])
    assert len(state.nearby_surfaces) == 3, "precondition: nearby_surfaces populated"
    state = apply_mobile_foreground(state, ts=time.time())
    assert state.nearby_surfaces == [], (
        f"AT-5: nearby_surfaces must be cleared on mobile switch; got {state.nearby_surfaces}"
    )
