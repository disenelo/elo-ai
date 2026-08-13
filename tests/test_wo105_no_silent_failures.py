"""
tests/test_wo105_no_silent_failures.py — WO-105: Kill the silent failures.

AT-1: spine.run() body has zero _log.debug exception swallows.
AT-2: All 9 cognition-path WARNING messages are present in spine.py.
AT-3: shadow_capture.py except handlers use WARNING, not debug.
AT-4: DesktopState.available field exists; failure path sets it False.
AT-5: The 5 g_ctx server.py sites now log WARNING.
AT-6: _startup_faculty_check function defined in server.py.
AT-7: /health endpoint JSON includes spine_degraded field.
AT-LINT: spine.run() has no bare except/pass handlers.
AT-9: All modified files compile clean.
"""
import ast
import os
import py_compile
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


def _src(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
        return f.read()


def _run_func_node(src):
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "run":
            return node
    return None


# ── AT-1: spine.run() — no _log.debug swallows ───────────────────────────────

def test_spine_run_no_debug_swallows():
    src = _src("runtime/spine/spine.py")
    lines = src.splitlines()
    run_func = _run_func_node(src)
    assert run_func is not None, "run() not found in spine.py"

    violations = []
    for node in ast.walk(run_func):
        if not isinstance(node, ast.ExceptHandler):
            continue
        body = node.body
        if len(body) == 1 and isinstance(body[0], ast.Expr):
            expr = body[0].value
            if isinstance(expr, ast.Call):
                func = expr.func
                if isinstance(func, ast.Attribute) and func.attr == "debug":
                    ln = body[0].lineno
                    violations.append(f"spine.py:{ln}  {lines[ln-1].strip()[:80]}")

    assert not violations, (
        "spine.run() still has _log.debug exception swallows — upgrade to WARNING+:\n"
        + "\n".join(violations)
    )


# ── AT-2: spine.py — 9 cognition-path WARNING messages present ───────────────

def test_spine_cognition_warnings_present():
    src = _src("runtime/spine/spine.py")
    expected = [
        "perceive_from_live_state FAILED",
        "assemble_world_state FAILED",
        "working_memory FAILED",
        "build_snapshot FAILED",
        "assemble_cognitive_state FAILED",
        "executive_faculty/enrich FAILED",
        "light_engine/translate FAILED",
        "presence_faculty FAILED",
        "build_embodiment_state FAILED",
    ]
    missing = [m for m in expected if m not in src]
    assert not missing, (
        "Missing WO-105 WARNING messages in spine.py:\n" + "\n".join(missing)
    )


# ── AT-3: shadow_capture.py — no debug swallows ──────────────────────────────

def test_shadow_capture_no_debug_swallows():
    src = _src("runtime/shadow_capture.py")
    tree = ast.parse(src)
    lines = src.splitlines()

    violations = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ExceptHandler):
            continue
        body = node.body
        if len(body) == 1 and isinstance(body[0], ast.Expr):
            expr = body[0].value
            if isinstance(expr, ast.Call):
                func = expr.func
                if isinstance(func, ast.Attribute) and func.attr == "debug":
                    ln = body[0].lineno
                    violations.append(f"shadow_capture.py:{ln}  {lines[ln-1].strip()[:80]}")

    assert not violations, (
        "shadow_capture.py still has _log.debug exception swallows:\n"
        + "\n".join(violations)
    )


# ── AT-4: DesktopState.available field and failure path ──────────────────────

def test_desktop_state_available_field():
    from world.live_world_state import DesktopState
    assert hasattr(DesktopState(), "available"), "DesktopState must have an 'available' field"
    assert DesktopState().available is True, "DesktopState() default: available=True"
    assert DesktopState(available=False).available is False


def test_desktop_failure_path_sets_unavailable():
    src = _src("world/live_world_state.py")
    assert "DesktopState(available=False)" in src, (
        "desktop failure handler must set: desktop = DesktopState(available=False)"
    )


# ── AT-5: server.py g_ctx sites now log WARNING ──────────────────────────────

def test_server_gcxt_no_bare_pass():
    src = _src("server.py")
    expected = [
        "g_ctx/spatial_state FAILED",
        "g_ctx/pos_emit FAILED",
        "g_ctx/synthesis FAILED",
        "g_ctx/chrome FAILED",
        "g_ctx/music FAILED",
    ]
    missing = [m for m in expected if m not in src]
    assert not missing, (
        "Missing WO-105 server.py g_ctx WARNING messages:\n" + "\n".join(missing)
    )


# ── AT-6: startup faculty check defined ──────────────────────────────────────

def test_startup_faculty_check_defined():
    src = _src("server.py")
    assert "def _startup_faculty_check()" in src, (
        "_startup_faculty_check() not found in server.py"
    )
    assert "_startup_faculty_check()" in src.split("def _startup_faculty_check()")[1], (
        "_startup_faculty_check() must be called (after __main__ block)"
    )


# ── AT-7: /health includes spine_degraded ─────────────────────────────────────

def test_health_endpoint_spine_degraded():
    src = _src("server.py")
    assert '"spine_degraded"' in src or "'spine_degraded'" in src, (
        "/health endpoint must include spine_degraded field"
    )
    assert "_spine_degraded" in src, (
        "_spine_degraded module-level variable must exist in server.py"
    )


# ── AT-LINT: spine.run() — no bare except/pass ───────────────────────────────

def test_spine_run_no_bare_pass():
    """Forward-looking lint: any new bare pass in spine.run() fails here."""
    src = _src("runtime/spine/spine.py")
    run_func = _run_func_node(src)
    assert run_func is not None

    violations = []
    for node in ast.walk(run_func):
        if not isinstance(node, ast.ExceptHandler):
            continue
        if len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
            violations.append(f"spine.run():{node.body[0].lineno}")

    assert not violations, (
        "spine.run() has bare except/pass — use WARNING+, raise, or explicit degradation:\n"
        + "\n".join(violations)
    )


# ── AT-9: all modified files compile clean ───────────────────────────────────

def test_compile_clean():
    targets = [
        "runtime/spine/spine.py",
        "runtime/shadow_capture.py",
        "world/live_world_state.py",
        "server.py",
    ]
    for rel in targets:
        py_compile.compile(os.path.join(ROOT, rel), doraise=True)


# ── Self-runner (for wo_test_runner.py subprocess mode) ──────────────────────

if __name__ == "__main__":
    _tests = [
        ("AT-1", test_spine_run_no_debug_swallows),
        ("AT-2", test_spine_cognition_warnings_present),
        ("AT-3", test_shadow_capture_no_debug_swallows),
        ("AT-4", test_desktop_state_available_field),
        ("AT-4b", test_desktop_failure_path_sets_unavailable),
        ("AT-5", test_server_gcxt_no_bare_pass),
        ("AT-6", test_startup_faculty_check_defined),
        ("AT-7", test_health_endpoint_spine_degraded),
        ("AT-LINT", test_spine_run_no_bare_pass),
        ("AT-9", test_compile_clean),
    ]
    _passed = 0; _failed = 0
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
    print(f"WO-105 silent failures   {_passed}/{_passed+_failed} passed, {_failed} failed")
    if _failed:
        sys.exit(1)
