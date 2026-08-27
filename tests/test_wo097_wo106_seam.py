"""
tests/test_wo097_wo106_seam.py — WO-097 + WO-106: embodiment ordering + seam opening.

AT-097-1: _conversation_faculty appears BEFORE build_embodiment_state in spine.run() (static)
AT-097-2: ordering test fails if swapped back (guard against regression)
AT-106-1: _executive_faculty call site passes world/working_memory/cognitive_state/affordances
AT-106-2: plan.world absent → WARNING emitted (disconnection test — not silent)
AT-106-3: plan.world present → world_state key in enriched attention dict
AT-106-4: working_memory present → wm_winner/wm_mode/wm_budget in enriched attention dict
AT-106-5: _executive_faculty signature accepts new params (no TypeError)
"""
import ast
import logging
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


def _src(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
        return f.read()


def _run_func_node(src, name="run"):
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    return None


# ── AT-097-1: conversation before embodiment (static) ────────────────────────

def test_conversation_before_embodiment_static():
    src = _src("runtime/spine/spine.py")
    idx_conv = src.find("_conversation_faculty(plan)")
    idx_emb  = src.find("build_embodiment_state(plan")
    assert idx_conv != -1, "_conversation_faculty(plan) not found in spine.py"
    assert idx_emb  != -1, "build_embodiment_state(plan...) not found in spine.py"
    assert idx_conv < idx_emb, (
        "ORDERING DEFECT: build_embodiment_state runs before _conversation_faculty — "
        "WO-097 reorder not applied"
    )


# ── AT-097-2: regression guard — swap back fails ─────────────────────────────

def test_embodiment_ordering_regression_guard():
    src = _src("runtime/spine/spine.py")
    # Must contain WO-097 comment marking the reorder
    assert "WO-097" in src, "WO-097 reorder comment missing from spine.py"
    # And the comment for conversation-before-embodiment must appear before embodiment call
    idx_wo097_note = src.find("WO-097: conversation runs FIRST")
    idx_emb        = src.find("build_embodiment_state(plan")
    assert idx_wo097_note != -1, "WO-097 ordering comment not found"
    assert idx_wo097_note < idx_emb, "WO-097 comment must appear before embodiment call"


# ── AT-106-1: call site passes assembled state ────────────────────────────────

def test_executive_faculty_call_site_passes_assembled_state():
    src = _src("runtime/spine/spine.py")
    assert "world=_world" in src, \
        "_executive_faculty() call site must pass world=_world"
    assert "working_memory=_wm" in src, \
        "_executive_faculty() call site must pass working_memory=_wm"
    assert "cognitive_state=_cognitive_state" in src, \
        "_executive_faculty() call site must pass cognitive_state=_cognitive_state"
    assert "affordances=" in src, \
        "_executive_faculty() call site must pass affordances="


# ── AT-106-2: disconnection test — absent world → WARNING ────────────────────

def test_world_absent_logs_warning():
    from runtime.spine.spine import _executive_faculty
    import runtime.spine.spine as _spine_mod

    records = []
    class _Cap(logging.Handler):
        def emit(self, r):
            records.append(r)

    logger = logging.getLogger(_spine_mod.__name__)
    handler = _Cap()
    logger.addHandler(handler)
    old_level = logger.level
    logger.setLevel(logging.WARNING)
    try:
        # Call with world=None (explicitly absent) — must log WARNING
        _executive_faculty(
            raw="hello",
            language={"meaning": "hello", "intent": "conversation", "register": "", "social": "", "confidence": 0.7},
            attention={},
            capabilities=[],
            system_det=None,
            world=None,   # ← absent
        )
        msgs = [r.getMessage() for r in records]
        assert any("world" in m.lower() and ("absent" in m.lower() or "without" in m.lower()) for m in msgs), (
            "executive_faculty must log WARNING when plan.world is absent; got: " + str(msgs)
        )
    finally:
        logger.removeHandler(handler)
        logger.setLevel(old_level)


# ── AT-106-3: world present → world_state in enriched attention ──────────────

def test_world_state_reaches_enriched_attention():
    src = _src("runtime/spine/spine.py")
    # Verify the merge code exists
    assert '"world_state"' in src or "'world_state'" in src, \
        "spine.py must set world_state key in enriched attention dict"
    assert "_attention_in" in src, \
        "_attention_in dict must exist in _executive_faculty()"
    # Verify _attention_in is passed to exec_decide
    assert "_exec_decide_fn(_attention_in," in src, \
        "exec_decide must receive _attention_in, not raw attention"


# ── AT-106-4: working_memory → wm_winner in enriched attention ───────────────

def test_wm_winner_reaches_enriched_attention():
    src = _src("runtime/spine/spine.py")
    assert '"wm_winner"' in src or "'wm_winner'" in src, \
        "spine.py must set wm_winner key from working_memory.attention.winner"
    assert '"wm_mode"' in src or "'wm_mode'" in src, \
        "spine.py must set wm_mode key from working_memory.attention.mode"
    assert '"wm_budget"' in src or "'wm_budget'" in src, \
        "spine.py must set wm_budget key from working_memory.attention.budget"


# ── AT-106-5: _executive_faculty signature accepts new params ────────────────

def test_executive_faculty_accepts_new_params():
    from runtime.spine.spine import _executive_faculty
    import inspect
    sig = inspect.signature(_executive_faculty)
    params = set(sig.parameters.keys())
    for expected in ("world", "cognitive_state", "working_memory", "affordances"):
        assert expected in params, (
            f"_executive_faculty() missing param: {expected}; got: {params}"
        )


# ── Self-runner ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    _tests = [
        ("AT-097-1", test_conversation_before_embodiment_static),
        ("AT-097-2", test_embodiment_ordering_regression_guard),
        ("AT-106-1", test_executive_faculty_call_site_passes_assembled_state),
        ("AT-106-2", test_world_absent_logs_warning),
        ("AT-106-3", test_world_state_reaches_enriched_attention),
        ("AT-106-4", test_wm_winner_reaches_enriched_attention),
        ("AT-106-5", test_executive_faculty_accepts_new_params),
    ]
    _passed = 0
    _failed = 0
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
    print(f"WO-097+106 seam   {_passed}/{_passed + _failed} passed, {_failed} failed")
    if _failed:
        sys.exit(1)
