"""
tests/test_wo_creative001_imagination_wiring.py — WO-CREATIVE-001
Verify creative_imagination.py is wired into spine.py runtime.
Run: ~/miniconda3/bin/python3 -m pytest tests/test_wo_creative001_imagination_wiring.py -v
"""
import py_compile
import os
import sys
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)


def test_at1_diverge_and_evaluate():
    """AT-1: diverge() returns a list; evaluate() scores candidates."""
    from faculties.creative.creative_imagination import diverge, evaluate
    candidates = diverge(goal="build something", seeds=["build something"], breadth_budget=3)
    assert isinstance(candidates, list), f"Expected list, got {type(candidates)}"
    if candidates:
        scored = evaluate(candidates[0], goal="build something")
        assert scored is not None, "evaluate() returned None"


def test_at2_spine_imports_creative_imagination():
    """AT-2: spine.py imports diverge and evaluate from faculties.creative.creative_imagination."""
    with open(os.path.join(ROOT, "runtime", "spine", "spine.py"), encoding="utf-8") as f:
        src = f.read()
    assert "diverge" in src, "diverge not found in spine.py"
    assert "evaluate" in src, "evaluate not found in spine.py"
    assert "faculties.creative.creative_imagination" in src, \
        "faculties.creative.creative_imagination not imported in spine.py"
    assert "generate" not in src.split("creative_imagination")[0].split("faculties")[-1], \
        "spine.py must import diverge/evaluate, not generate"


def test_at3_cognitive_state_has_creative_candidates():
    """AT-3: CognitiveState (or CognitivePlan) has creative_candidates field."""
    from runtime.spine.plan import CognitivePlan
    plan = CognitivePlan(raw="test")
    assert hasattr(plan, "creative_candidates"), "CognitivePlan missing creative_candidates field"
    assert plan.creative_candidates == () or isinstance(plan.creative_candidates, (list, tuple)), \
        f"Unexpected type: {type(plan.creative_candidates)}"

    # Also check runtime.contracts CognitiveState if present
    try:
        from runtime.contracts import CognitiveState
        assert hasattr(CognitiveState, "__dataclass_fields__"), "CognitiveState is not a dataclass"
        assert "creative_candidates" in CognitiveState.__dataclass_fields__, \
            "CognitiveState missing creative_candidates field"
    except ImportError:
        pass  # CognitiveState may live in spine only


def test_at4_executive_untouched():
    """AT-4: executive.py has 0 references to creative_imagination (FREEZE_V1_LOCK)."""
    exec_path = os.path.join(ROOT, "runtime", "executive.py")
    with open(exec_path, encoding="utf-8") as f:
        src = f.read()
    assert "creative_imagination" not in src, \
        "creative_imagination found in executive.py — violates FREEZE_V1_LOCK"
    py_compile.compile(exec_path, doraise=True)
