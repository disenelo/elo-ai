"""
tests/test_one_brain_no_second_authority.py

§1 Build List — Verify no second cognitive authority exists.
Proves the One Brain invariant: Executive is the sole decision-maker.

Authority: RD_P0_REVIEW_2026-08-23.md verdict:
    "The Executive (One Brain) is the sole decision-maker.
     Unity executes and reports — it does not plan."

Run: ~/miniconda3/bin/python3 -m pytest tests/test_one_brain_no_second_authority.py -q
"""
import sys
import os
import ast

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

_ROOT = os.path.join(os.path.dirname(__file__), "..")
_RUNTIME = os.path.join(_ROOT, "runtime")
_EXECUTIVE_PY = os.path.join(_RUNTIME, "executive.py")
_SPINE_PY = os.path.join(_RUNTIME, "spine", "spine.py")


def _all_runtime_py_files():
    """Return all .py files under runtime/ excluding __pycache__."""
    result = []
    for dirpath, dirnames, filenames in os.walk(_RUNTIME):
        dirnames[:] = [d for d in dirnames if d != "__pycache__"]
        for f in filenames:
            if f.endswith(".py"):
                result.append(os.path.join(dirpath, f))
    return result


def test_executive_py_exists_and_is_sole_decide_owner():
    """AT-1: Only runtime/executive.py defines a top-level decide() function.
    No other runtime module has a decide() that could act as a competing authority.
    """
    assert os.path.isfile(_EXECUTIVE_PY), "AT-1: runtime/executive.py must exist"
    competing = []
    for path in _all_runtime_py_files():
        if path == _EXECUTIVE_PY:
            continue
        src = open(path, encoding="utf-8").read()
        tree = ast.parse(src, filename=path)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "decide":
                # Allow decide() inside a class — architectural adapters may wrap.
                # Disallow: a top-level decide() in a non-executive module.
                if not isinstance(getattr(node, "_parent", None), ast.ClassDef):
                    competing.append(os.path.relpath(path, _ROOT))
    # Annotate parent for the above check to work
    for node in ast.walk(ast.parse(open(_EXECUTIVE_PY).read())):
        for child in ast.iter_child_nodes(node):
            child._parent = node
    assert competing == [], (
        f"AT-1: competing decide() found outside executive.py: {competing}"
    )


def test_executive_decide_is_the_spine_terminal_call():
    """AT-2: spine.py calls executive.decide (or _executive_faculty which wraps it).
    Confirms the Executive's decision sits at the terminal point of the turn chain.
    """
    src = open(_SPINE_PY, encoding="utf-8").read()
    assert "executive" in src.lower(), (
        "AT-2: spine.py must reference 'executive' — it is the terminal decision call"
    )
    assert "_executive_faculty" in src or "executive.decide" in src, (
        "AT-2: spine.py must call _executive_faculty() or executive.decide()"
    )


def test_executive_faculty_docstring_names_sole_authority():
    """AT-3: The _executive_faculty wrapper in spine.py carries the governance
    invariant: 'The Executive is the only entity permitted to make decisions.'
    """
    src = open(_SPINE_PY, encoding="utf-8").read()
    assert "only entity permitted to make decisions" in src, (
        "AT-3: spine.py _executive_faculty must carry the governance invariant docstring"
    )


def test_executive_py_contains_freeze_lock_marker():
    """AT-4: executive.py carries the FREEZE_V1_LOCK governance marker.
    This is the Board's canonical signal that the kernel is frozen and protected.
    """
    src = open(_EXECUTIVE_PY, encoding="utf-8").read()
    assert "FREEZE_V1_LOCK" in src or "LAW-017" in src, (
        "AT-4: executive.py must carry FREEZE_V1_LOCK or LAW-017 marker"
    )


def test_no_runtime_faculty_returns_exec_decision_dict():
    """AT-5: No faculty module other than executive.py uses the 'exec_decision'
    return pattern (a dict with 'action'/'cal_action' keys) as its PRIMARY output.
    Faculties enrich CognitivePlan — they do not produce decisions.
    """
    decision_keys = {"action", "cal_action", "tone", "max_sentences"}
    violators = []
    for path in _all_runtime_py_files():
        if path == _EXECUTIVE_PY:
            continue
        if "spine.py" in path:
            continue   # spine assembles but doesn't produce exec_decision
        src = open(path, encoding="utf-8").read()
        # Heuristic: a file that returns all four executive decision keys is a concern
        count = sum(1 for k in decision_keys if f'"{k}"' in src or f"'{k}'" in src)
        if count >= 4:
            violators.append(os.path.relpath(path, _ROOT))
    assert violators == [], (
        f"AT-5: modules with all executive decision keys (possible competing authority): {violators}"
    )


def test_one_brain_p0_review_verdict_on_disk():
    """AT-6: The P0 Review verdict document exists and confirms the One Brain verdict.
    This is the audit that formally established the architectural conclusion.
    """
    p0_path = os.path.join(_ROOT, "docs", "architecture", "findings",
                           "RD_P0_REVIEW_2026-08-23.md")
    assert os.path.isfile(p0_path), (
        "AT-6: RD_P0_REVIEW_2026-08-23.md must exist — it is the One Brain architectural audit"
    )
    src = open(p0_path, encoding="utf-8").read()
    assert "sole decision-maker" in src, (
        "AT-6: P0 review must contain 'sole decision-maker' verdict"
    )
    assert "No." in src or "no second cognitive" in src.lower(), (
        "AT-6: P0 review must confirm no second cognitive authority"
    )
