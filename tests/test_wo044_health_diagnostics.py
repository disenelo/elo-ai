"""
tests/test_wo044_health_diagnostics.py — WO-044 runtime health diagnostics API

Spec: GET /health returns per-faculty status dict; [FACULTY HEALTH] wired into
      capability injection; eLo self-reports health on relevant queries.

AT-1  faculty_health module imports with all required symbols
AT-2  all_statuses() returns all four faculties
AT-3  mark_degraded → all_statuses reflects DEGRADED; reflected in health_summary
AT-4  mark_recovered → all_statuses reflects CONNECTED
AT-5  health_summary() covers all four faculties in one string
AT-6  server.py /health route present and wired to all_statuses (WO-044)
AT-7  [FACULTY HEALTH] block wired into capability injection path
AT-8  py_compile clean on faculty_health.py + server.py
"""
import os
import sys
import py_compile
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from runtime.faculty_health import (
    mark_degraded, mark_recovered, mark_offline,
    get_status, all_statuses, health_summary,
    CONNECTED, DEGRADED, OFFLINE,
)

_ROOT       = os.path.join(os.path.dirname(__file__), "..")
_SERVER_PY  = os.path.join(_ROOT, "server.py")
_FH_PY      = os.path.join(_ROOT, "runtime", "faculty_health.py")


def _reset_all():
    for f in ("reasoning", "memory", "tools", "embodiment"):
        mark_recovered(f)


# ── AT-1 ──────────────────────────────────────────────────────────────────────

def test_at1_module_imports():
    from runtime.faculty_health import (
        mark_degraded, mark_recovered, mark_offline,
        get_status, all_statuses, health_summary,
        CONNECTED, DEGRADED, OFFLINE,
    )
    assert CONNECTED and DEGRADED and OFFLINE


# ── AT-2 ──────────────────────────────────────────────────────────────────────

def test_at2_all_four_faculties_in_statuses():
    statuses = all_statuses()
    required = {"reasoning", "memory", "tools", "embodiment"}
    missing = required - set(statuses.keys())
    assert not missing, f"AT-2 FAIL: missing faculties: {missing}"


# ── AT-3 ──────────────────────────────────────────────────────────────────────

def test_at3_degraded_reflected_in_all_statuses_and_summary():
    """
    mark_degraded → all_statuses shows DEGRADED AND health_summary reflects it.
    This is the /health endpoint contract — the summary is what eLo reports to David.
    """
    _reset_all()

    mark_degraded("tools", "web search timeout")

    statuses = all_statuses()
    assert statuses.get("tools") == DEGRADED, (
        f"AT-3 FAIL: all_statuses shows tools={statuses.get('tools')!r}, expected DEGRADED"
    )

    summary = health_summary()
    assert "DEGRADED" in summary, f"AT-3 FAIL: DEGRADED not in health_summary: {summary!r}"
    assert "tools" in summary, f"AT-3 FAIL: 'tools' not in health_summary: {summary!r}"

    _reset_all()


# ── AT-4 ──────────────────────────────────────────────────────────────────────

def test_at4_recovered_reflected_in_all_statuses():
    """mark_recovered → /health endpoint returns CONNECTED for that faculty."""
    _reset_all()
    mark_degraded("memory", "vault read failure")
    assert all_statuses().get("memory") == DEGRADED

    mark_recovered("memory")
    statuses = all_statuses()
    assert statuses.get("memory") == CONNECTED, (
        f"AT-4 FAIL: memory={statuses.get('memory')!r} after recovery, expected CONNECTED"
    )


# ── AT-5 ──────────────────────────────────────────────────────────────────────

def test_at5_health_summary_covers_all_faculties():
    """health_summary() must include all four faculty names in one string."""
    _reset_all()
    summary = health_summary()
    assert isinstance(summary, str), "AT-5 FAIL: health_summary() must return str"
    for faculty in ("reasoning", "memory", "tools", "embodiment"):
        assert faculty in summary, (
            f"AT-5 FAIL: '{faculty}' missing from health_summary: {summary!r}"
        )


# ── AT-6 ──────────────────────────────────────────────────────────────────────

def test_at6_health_route_in_server():
    """
    server.py must declare a /health route that calls all_statuses.
    This is the runtime diagnostics endpoint David (and the board) can query.
    """
    src = open(_SERVER_PY, encoding="utf-8").read()
    assert '"/health"' in src or "'/health'" in src, (
        "AT-6 FAIL: /health route not found in server.py"
    )
    assert "all_statuses" in src, "AT-6 FAIL: all_statuses not called in server.py"
    assert "WO-044" in src, "AT-6 FAIL: WO-044 marker absent from server.py"


# ── AT-7 ──────────────────────────────────────────────────────────────────────

def test_at7_faculty_health_wired_into_capability_injection():
    """
    [FACULTY HEALTH] block must appear in the capability injection path in
    server.py — this surfaces health in eLo's self-report when David asks
    "are you working right?".
    """
    src = open(_SERVER_PY, encoding="utf-8").read()
    assert "FACULTY HEALTH" in src, (
        "AT-7 FAIL: [FACULTY HEALTH] block absent from server.py capability injection"
    )
    assert "health_summary" in src, (
        "AT-7 FAIL: health_summary() not called in server.py"
    )
    assert "are you working right" in src or "working right" in src, (
        "AT-7 FAIL: 'are you working right' trigger not in server.py capability injection"
    )


# ── AT-8 ──────────────────────────────────────────────────────────────────────

def test_at8_py_compile_clean():
    for path in (_FH_PY, _SERVER_PY):
        try:
            py_compile.compile(path, doraise=True)
        except py_compile.PyCompileError as e:
            pytest.fail(f"AT-8 FAIL: {os.path.basename(path)} does not compile: {e}")
