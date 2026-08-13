"""
tests/test_wo107_identity_state.py — WO-107: identity as first-class self-model fields.

AT-107-1: EloSelfState has identity_name, core_values, invariants, who_i_am_with
AT-107-2: identity_block() renders from fields — change a field, output changes
AT-107-3: check_identity_drift() returns empty list when prompt contains all values
AT-107-4: check_identity_drift() returns missing values when they're absent from prompt
AT-107-5: Row 11 UNKNOWN — nearby absent → stated as unknown, not silently omitted
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


# ── AT-107-1: EloSelfState has identity fields ───────────────────────────────

def test_elo_self_state_has_identity_fields():
    from self.elo_self_model import EloSelfState
    import dataclasses
    field_names = {f.name for f in dataclasses.fields(EloSelfState)}
    for required in ("identity_name", "core_values", "invariants", "who_i_am_with"):
        assert required in field_names, \
            f"EloSelfState missing identity field: {required} — WO-107 not applied"


def test_identity_defaults_are_non_empty():
    from self.elo_self_model import EloSelfState
    s = EloSelfState()
    assert s.identity_name == "eLo", f"identity_name default: {s.identity_name}"
    assert s.core_values, "core_values is empty — constitutional baseline missing"
    assert s.invariants, "invariants is empty — constitutional baseline missing"
    assert s.who_i_am_with == "David", f"who_i_am_with default: {s.who_i_am_with}"


# ── AT-107-2: identity_block() renders from state — changing a field changes output ─

def test_identity_block_renders_from_fields():
    from self.elo_self_model import EloSelfState, identity_block
    s1 = EloSelfState()
    s2 = EloSelfState(identity_name="eLo-test", core_values=["silent", "watchful"])
    block1 = identity_block(s1)
    block2 = identity_block(s2)
    assert block1 != block2, "identity_block should change when fields change"
    assert "eLo-test" in block2, "identity_name change not reflected in block"
    assert "silent" in block2, "core_values change not reflected in block"
    # Proof: change field → change prompt (one source)
    assert s1.identity_name in block1, "identity_name not rendered in block"
    assert all(v in block1 for v in s1.core_values), "not all core_values in block"


# ── AT-107-3/4: drift guard ───────────────────────────────────────────────────

def test_drift_guard_clean_when_all_values_present():
    from self.elo_self_model import EloSelfState, identity_block, check_identity_drift
    s = EloSelfState()
    block = identity_block(s)  # block contains all core_values by construction
    missing = check_identity_drift(s, block)
    assert not missing, f"Drift guard fires on own output: {missing}"


def test_drift_guard_catches_missing_values():
    from self.elo_self_model import EloSelfState, check_identity_drift
    s = EloSelfState(core_values=["calm", "playful", "secret-trait"])
    prompt_without_secret = "eLo is calm and playful and present."
    missing = check_identity_drift(s, prompt_without_secret)
    assert "secret-trait" in missing, \
        f"Drift guard should catch 'secret-trait' not in prompt; got: {missing}"


# ── AT-107-5: Row 11 UNKNOWN — absence is statable ───────────────────────────

def test_nearby_absence_is_stated_not_omitted():
    from runtime.the_moment import situated_with_epistemic
    from unittest.mock import MagicMock
    state = MagicMock()
    state.embodiment = "desktop"
    state.pose = "perched"
    state.surface = "Terminal"
    state.location = ""
    state.balance = "stable"
    state.size = {"height_cm": 30, "reach_cm": 20, "jump_cm": 40}
    state.available_actions = []
    state.current_action = "idle"
    state.locomotion_faculty_health = "ok"
    state.nearby_surfaces = []   # absent
    state.mood = 0.5
    state.curiosity = 0.5
    state.goal = ""
    state.last_updated = 0.0
    state.recent_behavior = {}
    block = situated_with_epistemic(state)
    # "nearby" must appear EVEN when empty — absence is statable (Row 11 UNKNOWN)
    assert "nearby" in block.lower(), (
        "situated_with_epistemic() omits 'nearby' when empty — absence must be stated. "
        f"Got block:\n{block}"
    )
    assert "unknown" in block.lower(), (
        "situated_with_epistemic() should say 'unknown' for empty nearby_surfaces. "
        f"Got block:\n{block}"
    )
