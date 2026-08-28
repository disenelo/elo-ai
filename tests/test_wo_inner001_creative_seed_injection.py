"""
tests/test_wo_inner001_creative_seed_injection.py

WO-INNER-001 — Inner-child expression: creative seed injection
Authority: BUILD LIST §5 (inner-child expression, no dedicated WO) · RTR-015 (Jupiter=Expansion)

AT-1: runtime/spine/plan.py has creative_candidates field with tuple default
AT-2: runtime/spine/spine.py contains plan.creative_candidates assignment (LOOP-8 propagation)
AT-3: server.py contains [CREATIVE SEED] injection reading _plan.creative_candidates
AT-4: executive.py has 0 references to creative_candidates (FREEZE_V1_LOCK clean)
AT-5: CognitivePlan.creative_candidates defaults to empty tuple (non-None safe)

Run: ~/miniconda3/bin/python3 -m pytest tests/test_wo_inner001_creative_seed_injection.py -v
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

_REPO = Path(__file__).parent.parent


def test_at1_plan_has_creative_candidates_field():
    """AT-1: plan.py CognitivePlan has creative_candidates field."""
    plan_src = (_REPO / "runtime" / "spine" / "plan.py").read_text()
    assert "creative_candidates" in plan_src, (
        "AT-1 FAIL: creative_candidates field not found in runtime/spine/plan.py"
    )
    assert "default_factory=tuple" in plan_src, (
        "AT-1 FAIL: creative_candidates must have default_factory=tuple"
    )
    # Verify it actually imports properly
    from runtime.spine.plan import CognitivePlan
    plan = CognitivePlan(raw="test", meaning="test")
    assert hasattr(plan, "creative_candidates"), (
        "AT-1 FAIL: CognitivePlan instance missing creative_candidates attribute"
    )
    assert isinstance(plan.creative_candidates, tuple), (
        "AT-1 FAIL: creative_candidates default must be a tuple"
    )
    assert plan.creative_candidates == (), (
        "AT-1 FAIL: creative_candidates must default to empty tuple"
    )


def test_at2_spine_propagates_creative_candidates_to_plan():
    """AT-2: spine.py assigns creative_candidates from LOOP-8 onto plan."""
    spine_src = (_REPO / "runtime" / "spine" / "spine.py").read_text()
    assert "plan.creative_candidates" in spine_src, (
        "AT-2 FAIL: spine.py does not contain 'plan.creative_candidates' assignment"
    )
    assert "WO-INNER-001" in spine_src, (
        "AT-2 FAIL: spine.py missing WO-INNER-001 D-2 label"
    )


def test_at3_server_injects_creative_seed():
    """AT-3: server.py contains [CREATIVE SEED] injection block reading _plan.creative_candidates."""
    server_src = (_REPO / "server.py").read_text()
    assert "[CREATIVE SEED" in server_src, (
        "AT-3 FAIL: server.py missing [CREATIVE SEED] injection string"
    )
    assert "_plan.creative_candidates" in server_src or "_ci_srv_candidates" in server_src, (
        "AT-3 FAIL: server.py does not read plan.creative_candidates for injection"
    )
    assert "WO-INNER-001" in server_src, (
        "AT-3 FAIL: server.py missing WO-INNER-001 D-3 label"
    )


def test_at4_executive_not_touched():
    """AT-4: executive.py has no reference to creative_candidates (FREEZE_V1_LOCK clean)."""
    exec_src = (_REPO / "runtime" / "executive.py").read_text()
    assert "creative_candidates" not in exec_src, (
        "AT-4 FAIL: FREEZE_V1_LOCK VIOLATION — executive.py references creative_candidates"
    )
    assert "WO-INNER-001" not in exec_src, (
        "AT-4 FAIL: FREEZE_V1_LOCK VIOLATION — executive.py references WO-INNER-001"
    )


def test_at5_creative_candidates_tuple_safe():
    """AT-5: plan.creative_candidates=() is falsy; non-empty tuple is truthy — safe branch in server.py."""
    from runtime.spine.plan import CognitivePlan
    plan_empty = CognitivePlan(raw="hi", meaning="hi")
    assert not plan_empty.creative_candidates, (
        "AT-5 FAIL: empty creative_candidates must be falsy for safe server.py branch"
    )
    plan_with = CognitivePlan(
        raw="hi", meaning="hi",
        creative_candidates=({"candidate": {"metaphor": "eLo is light"}, "score": {}},),
    )
    assert plan_with.creative_candidates, (
        "AT-5 FAIL: non-empty creative_candidates must be truthy"
    )
    assert plan_with.creative_candidates[0]["candidate"]["metaphor"] == "eLo is light", (
        "AT-5 FAIL: creative_candidates content mismatch"
    )
