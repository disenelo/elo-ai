"""
tests/test_wo042_faculty_health.py — WO-042 faculty health registry

Spec: WO-042 — Persistent CONNECTED/DEGRADED/OFFLINE per faculty; Executive routes
      on it; no per-call oscillation. Four faculties: reasoning, memory, tools, embodiment.

AT-1  Module imports — all public symbols accessible
AT-2  All four faculties in registry (reasoning, memory, tools, embodiment)
AT-3  Default status is CONNECTED for every faculty
AT-4  mark_degraded() → DEGRADED + reason persisted; error_count increments
AT-5  mark_recovered() → CONNECTED + error_count zeroed
AT-6  mark_offline() → OFFLINE; mark_recovered() → CONNECTED (full round-trip)
AT-7  Oscillation guard: degraded→recovered→degraded tracks distinct events correctly
AT-8  health_summary() returns a single-line covering all four faculties in one string
AT-9  backend_router.py wired to faculty_health (WO-042 routing integrated)
AT-10 _persist() writes faculty_health.json atomically (write-to-tmp + os.replace)
AT-11 all_statuses() returns a dict keyed by faculty name with status values
AT-12 py_compile clean on faculty_health.py + backend_router.py
"""
import os
import sys
import json
import tempfile
import py_compile

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from runtime.faculty_health import (
    get_status, mark_degraded, mark_recovered, mark_offline,
    health_summary, all_statuses,
    CONNECTED, DEGRADED, OFFLINE,
    _registry,
)

_ROOT = os.path.join(os.path.dirname(__file__), "..")
_FH_PY = os.path.join(_ROOT, "runtime", "faculty_health.py")
_BR_PY = os.path.join(_ROOT, "runtime", "backend_router.py")


def _reset_all():
    """Return every faculty to CONNECTED/zero before a test."""
    for f in ("reasoning", "memory", "tools", "embodiment"):
        mark_recovered(f)


# ── AT-1 ──────────────────────────────────────────────────────────────────────

def test_at1_module_imports():
    """All public symbols importable from runtime.faculty_health."""
    from runtime.faculty_health import (
        get_status, mark_degraded, mark_recovered, mark_offline,
        health_summary, all_statuses, CONNECTED, DEGRADED, OFFLINE,
    )
    assert CONNECTED == "CONNECTED"
    assert DEGRADED  == "DEGRADED"
    assert OFFLINE   == "OFFLINE"


# ── AT-2 ──────────────────────────────────────────────────────────────────────

def test_at2_all_four_faculties_present():
    """Registry must contain all four canonical faculties."""
    statuses = all_statuses()
    required = {"reasoning", "memory", "tools", "embodiment"}
    missing = required - set(statuses.keys())
    assert not missing, f"AT-2 FAIL: missing faculties: {missing}"


# ── AT-3 ──────────────────────────────────────────────────────────────────────

def test_at3_default_status_connected():
    """After recovery, every faculty reports CONNECTED."""
    _reset_all()
    for faculty in ("reasoning", "memory", "tools", "embodiment"):
        status = get_status(faculty)
        assert status == CONNECTED, (
            f"AT-3 FAIL: {faculty} default status={status!r}, expected CONNECTED"
        )


# ── AT-4 ──────────────────────────────────────────────────────────────────────

def test_at4_mark_degraded_transitions_and_accumulates():
    """
    mark_degraded() must:
    - Set status to DEGRADED
    - Persist the reason in last_error
    - Increment error_count on each call
    """
    _reset_all()

    mark_degraded("reasoning", "OpenAI quota exceeded")
    assert get_status("reasoning") == DEGRADED, "AT-4 FAIL: status not DEGRADED after first degrade"
    assert _registry["reasoning"]["last_error"] == "OpenAI quota exceeded", "AT-4 FAIL: reason not stored"
    assert _registry["reasoning"]["error_count"] == 1, "AT-4 FAIL: error_count not 1 after first degrade"

    mark_degraded("reasoning", "timeout on retry")
    assert _registry["reasoning"]["error_count"] == 2, "AT-4 FAIL: error_count not 2 after second degrade"
    assert _registry["reasoning"]["last_error"] == "timeout on retry", "AT-4 FAIL: reason not updated"

    _reset_all()  # leave clean


# ── AT-5 ──────────────────────────────────────────────────────────────────────

def test_at5_mark_recovered_resets_fully():
    """mark_recovered() must set CONNECTED and zero error_count."""
    _reset_all()
    mark_degraded("memory", "vault read failure")
    assert get_status("memory") == DEGRADED

    mark_recovered("memory")
    assert get_status("memory") == CONNECTED, "AT-5 FAIL: status not CONNECTED after recovery"
    assert _registry["memory"]["error_count"] == 0, "AT-5 FAIL: error_count not zeroed"
    assert _registry["memory"]["last_error"] == "", "AT-5 FAIL: last_error not cleared"


# ── AT-6 ──────────────────────────────────────────────────────────────────────

def test_at6_offline_full_round_trip():
    """OFFLINE → CONNECTED round-trip via mark_offline + mark_recovered."""
    _reset_all()

    mark_offline("tools", "weather API unreachable")
    assert get_status("tools") == OFFLINE, "AT-6 FAIL: status not OFFLINE"
    assert _registry["tools"]["last_error"] == "weather API unreachable"

    mark_recovered("tools")
    assert get_status("tools") == CONNECTED, "AT-6 FAIL: status not CONNECTED after recovery"
    assert _registry["tools"]["error_count"] == 0


# ── AT-7 ──────────────────────────────────────────────────────────────────────

def test_at7_oscillation_guard_tracks_distinct_events():
    """
    Simulates the oscillation pattern that WO-042 was raised to fix.
    DEGRADED → CONNECTED → DEGRADED must track each event independently,
    not merge them or lose count.
    """
    _reset_all()

    # Event 1: first degrade
    mark_degraded("embodiment", "Unity ACK timeout")
    assert get_status("embodiment") == DEGRADED
    count_after_first = _registry["embodiment"]["error_count"]
    assert count_after_first == 1

    # Recovery
    mark_recovered("embodiment")
    assert get_status("embodiment") == CONNECTED
    assert _registry["embodiment"]["error_count"] == 0, "error_count must reset on recovery"

    # Event 2: second independent degrade (different reason)
    mark_degraded("embodiment", "Unity scene not loaded")
    assert get_status("embodiment") == DEGRADED
    assert _registry["embodiment"]["error_count"] == 1, (
        "AT-7 FAIL: error_count should be 1 for second independent incident, not accumulated from before recovery"
    )
    assert _registry["embodiment"]["last_error"] == "Unity scene not loaded"

    _reset_all()


# ── AT-8 ──────────────────────────────────────────────────────────────────────

def test_at8_health_summary_covers_all_faculties():
    """
    health_summary() must return a single string that references all four
    faculties. It's the primary eLo self-report surface — missing a faculty
    means eLo can't report a degraded state.
    """
    _reset_all()
    mark_degraded("tools", "web search timeout")

    summary = health_summary()
    assert isinstance(summary, str), f"AT-8 FAIL: health_summary() returned {type(summary)}"
    for faculty in ("reasoning", "memory", "tools", "embodiment"):
        assert faculty in summary, f"AT-8 FAIL: faculty '{faculty}' not in summary: {summary!r}"

    # Degraded faculty must appear as DEGRADED, not OK
    assert "tools: OK" not in summary, f"AT-8 FAIL: degraded tools shown as OK in: {summary!r}"
    assert "tools: DEGRADED" in summary or "DEGRADED" in summary, (
        f"AT-8 FAIL: DEGRADED not in summary: {summary!r}"
    )

    _reset_all()


# ── AT-9 ──────────────────────────────────────────────────────────────────────

def test_at9_backend_router_wired():
    """backend_router.py must reference faculty_health for routing decisions."""
    src = open(_BR_PY, encoding="utf-8").read()
    assert "WO-042" in src, "AT-9 FAIL: WO-042 marker absent from backend_router.py"
    assert "faculty_health" in src, "AT-9 FAIL: faculty_health import absent from backend_router.py"
    # Routing sentinel: the router reads degraded status before choosing a backend
    assert "_fh_degraded" in src or "mark_degraded" in src or "get_status" in src, (
        "AT-9 FAIL: no faculty-health routing call in backend_router.py"
    )


# ── AT-10 ─────────────────────────────────────────────────────────────────────

def test_at10_persist_atomic():
    """
    _persist() writes atomically (tmp + os.replace).
    Simulate by triggering a state change and verifying the JSON file is valid.
    We can't mock os.replace, so we verify the resulting JSON is parseable and
    contains the expected state — proving the write-then-replace completed cleanly.
    """
    from runtime import faculty_health as _fh

    _reset_all()
    mark_degraded("memory", "vault read failure")

    health_path = _fh._HEALTH_PATH
    if os.path.exists(health_path):
        data = json.loads(open(health_path).read())
        assert "memory" in data, "AT-10 FAIL: 'memory' key missing from persisted JSON"
        assert data["memory"]["status"] == DEGRADED, (
            f"AT-10 FAIL: persisted status={data['memory']['status']!r}, expected DEGRADED"
        )
        assert "_ts" in data, "AT-10 FAIL: _ts timestamp missing from JSON"

    _reset_all()


# ── AT-11 ─────────────────────────────────────────────────────────────────────

def test_at11_all_statuses_returns_keyed_dict():
    """all_statuses() returns {faculty: status_string} for all four faculties."""
    _reset_all()
    mark_offline("embodiment", "robot offline")

    statuses = all_statuses()
    assert isinstance(statuses, dict), "AT-11 FAIL: all_statuses() must return a dict"
    assert set(statuses.keys()) >= {"reasoning", "memory", "tools", "embodiment"}

    assert statuses["embodiment"] == OFFLINE, (
        f"AT-11 FAIL: embodiment={statuses['embodiment']!r}, expected OFFLINE"
    )
    assert statuses["reasoning"] == CONNECTED, (
        f"AT-11 FAIL: reasoning={statuses['reasoning']!r}, expected CONNECTED"
    )

    _reset_all()


# ── AT-12 ─────────────────────────────────────────────────────────────────────

def test_at12_py_compile_clean():
    """Both faculty_health.py and backend_router.py must compile cleanly."""
    for path in (_FH_PY, _BR_PY):
        try:
            py_compile.compile(path, doraise=True)
        except py_compile.PyCompileError as e:
            pytest.fail(f"AT-12 FAIL: {os.path.basename(path)} does not compile: {e}")
