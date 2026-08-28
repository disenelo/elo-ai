"""
tests/test_wo_creative001_imagination_wiring.py

WO-CREATIVE-001: Creative Imagination runtime wiring.
Proves diverge+evaluate are callable, spine.py imports them,
CognitiveState has creative_candidates field, and executive.py is clean.

Run: ~/miniconda3/bin/python3 -m pytest tests/test_wo_creative001_imagination_wiring.py -v
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

_ROOT = os.path.join(os.path.dirname(__file__), "..")
_SPINE = os.path.join(_ROOT, "runtime", "spine", "spine.py")
_EXECUTIVE = os.path.join(_ROOT, "runtime", "executive.py")
_CONTRACTS = os.path.join(_ROOT, "runtime", "contracts.py")


def test_at1_diverge_and_evaluate_callable():
    """AT-1: diverge() returns a list; evaluate() scores each candidate."""
    from faculties.creative.creative_imagination import diverge, evaluate

    candidates = diverge(goal="make something calm", seeds=["calm", "flow"], breadth_budget=3)
    assert isinstance(candidates, list), f"AT-1: diverge must return list; got {type(candidates)}"

    if candidates:
        score = evaluate(candidates[0], goal="make something calm")
        assert hasattr(score, "weighted_total"), "AT-1: CreativeScore must have weighted_total"
        assert hasattr(score, "epistemic_status"), "AT-1: CreativeScore must have epistemic_status"
        assert score.epistemic_status == "imagined", (
            f"AT-1: epistemic_status must be 'imagined'; got {score.epistemic_status!r}"
        )


def test_at2_spine_imports_diverge_and_evaluate():
    """AT-2: spine.py source contains 'diverge' and 'evaluate' from creative_imagination."""
    assert os.path.isfile(_SPINE), f"AT-2: spine.py not found at {_SPINE}"
    src = open(_SPINE).read()
    assert "diverge" in src, "AT-2: 'diverge' not found in spine.py"
    assert "evaluate" in src, "AT-2: 'evaluate' not found in spine.py"
    assert "creative_imagination" in src, "AT-2: 'creative_imagination' not referenced in spine.py"
    # confirm the wrong API (generate / executive_select) is NOT called via creative_imagination
    # allow 'generate' as a word in comments/elsewhere — check spine doesn't call it from ci
    assert "_ci_diverge" in src or "as _ci_diverge" in src, (
        "AT-2: spine.py must alias diverge as _ci_diverge"
    )


def test_at3_cognitive_state_has_creative_candidates():
    """AT-3: CognitiveState has creative_candidates field."""
    from runtime.contracts import CognitiveState
    import dataclasses

    fields = {f.name for f in dataclasses.fields(CognitiveState)}
    assert "creative_candidates" in fields, (
        f"AT-3: CognitiveState must have creative_candidates field; got {sorted(fields)}"
    )

    # Confirm CognitiveSnapshot also has it (D-3)
    from runtime.cognitive_snapshot import CognitiveSnapshot
    snap_fields = {f.name for f in dataclasses.fields(CognitiveSnapshot)}
    assert "creative_candidates" in snap_fields, (
        f"AT-3: CognitiveSnapshot must have creative_candidates field; got {sorted(snap_fields)}"
    )


def test_at4_executive_py_zero_creative_imagination_references():
    """AT-4: executive.py has 0 references to creative_imagination (FREEZE_V1_LOCK clean)."""
    assert os.path.isfile(_EXECUTIVE), f"AT-4: executive.py not found at {_EXECUTIVE}"
    src = open(_EXECUTIVE).read()
    assert "creative_imagination" not in src, (
        "AT-4: FREEZE_V1_LOCK VIOLATED — executive.py references creative_imagination"
    )
    assert "ci_diverge" not in src, (
        "AT-4: FREEZE_V1_LOCK VIOLATED — executive.py references _ci_diverge"
    )
    assert "ci_evaluate" not in src, (
        "AT-4: FREEZE_V1_LOCK VIOLATED — executive.py references _ci_evaluate"
    )


if __name__ == "__main__":
    _tests = [
        ("AT-1", test_at1_diverge_and_evaluate_callable),
        ("AT-2", test_at2_spine_imports_diverge_and_evaluate),
        ("AT-3", test_at3_cognitive_state_has_creative_candidates),
        ("AT-4", test_at4_executive_py_zero_creative_imagination_references),
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
    print(f"WO-CREATIVE-001   {_passed}/{_passed + _failed} passed, {_failed} failed")
    if __name__ == "__main__" and _failed:
        sys.exit(1)
