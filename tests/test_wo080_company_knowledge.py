"""
tests/test_wo080_company_knowledge.py — WO-080: Company Knowledge Interface

Assertions:
  AT-0: query_active_wos returns only non-done/blocked WOs; empty state = []
  AT-1: build_deep_brief varies with state (different state → different content)
  AT-2: check_permitted returns True for permitted actions, False for L3-required
  AT-3: missing data yields honest_gap, not a fabricated answer
  AT-4: company_state_writer.py wires deep brief; py_compile clean

Run: python3 tests/test_wo080_company_knowledge.py
"""
from __future__ import annotations

import os
import py_compile
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

_passed = _failed = 0


def ok(label: str):
    global _passed
    _passed += 1
    print(f"  ✅ {label}")


def fail(label: str, err):
    global _failed
    _failed += 1
    print(f"  ❌ {label}: {err}")


_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _make_state(board=None, regressions=None, permitted=None, milestone="") -> dict:
    return {
        "board": board or [],
        "regressions": regressions or [],
        "permitted_actions": permitted or [],
        "company_focus": {"milestone": milestone},
        "waiting_for_approval": [],
    }


# ── AT-0: query_active_wos — only non-done/blocked; empty = [] ───────────────
try:
    from company_runtime.company_knowledge import query_active_wos

    # Empty state → []
    result = query_active_wos({})
    assert result == [], f"empty state must return [], got {result}"

    # Board with mix of done/active/blocked
    state = _make_state(board=[
        {"id": "WO-001", "title": "Build thing", "status": "WORKING", "pri": "P1"},
        {"id": "WO-002", "title": "Done thing",  "status": "DONE",    "pri": "P2"},
        {"id": "WO-003", "title": "Blocked",      "status": "BLOCKED", "pri": "P3"},
        {"id": "WO-004", "title": "Review",       "status": "REVIEW",  "pri": "P2"},
    ])
    active = query_active_wos(state)
    ids = [w["id"] for w in active]
    assert "WO-001" in ids, f"WORKING WO must be active, got {ids}"
    assert "WO-004" in ids, f"REVIEW WO must be active, got {ids}"
    assert "WO-002" not in ids, f"DONE WO must be excluded, got {ids}"
    assert "WO-003" not in ids, f"BLOCKED WO must be excluded, got {ids}"

    # Each result carries required fields
    for item in active:
        assert "id" in item and "title" in item and "status" in item and "priority" in item, (
            f"result missing required fields: {item}"
        )

    ok(f"AT-0: query_active_wos returns {len(active)} active (done/blocked excluded); empty state = []")
except AssertionError as e:
    fail("AT-0", e)
except Exception as e:
    fail("AT-0", e)


# ── AT-1: build_deep_brief varies with state ──────────────────────────────────
try:
    from company_runtime.company_knowledge import build_deep_brief

    # State A: active WOs
    state_a = _make_state(board=[
        {"id": "WO-080", "title": "Company Knowledge", "status": "WORKING", "pri": "P2"},
        {"id": "WO-081", "title": "Emergent Cognition", "status": "REVIEW", "pri": "P2"},
    ])
    brief_a = build_deep_brief("what tasks are we on", state_a)
    assert "WO-080" in brief_a or "WO-081" in brief_a, (
        f"brief should mention active WO IDs, got: {brief_a!r}"
    )

    # State B: different WOs → different reply
    state_b = _make_state(board=[
        {"id": "WO-099", "title": "Something else", "status": "WORKING", "pri": "P1"},
    ])
    brief_b = build_deep_brief("what tasks are we on", state_b)
    assert brief_a != brief_b, (
        "brief must vary with state — different WOs should produce different text"
    )
    assert "WO-099" in brief_b, f"brief_b should mention WO-099, got: {brief_b!r}"

    ok("AT-1: build_deep_brief varies with state — different WOs produce different output")
except AssertionError as e:
    fail("AT-1", e)
except Exception as e:
    fail("AT-1", e)


# ── AT-2: check_permitted gate ────────────────────────────────────────────────
try:
    from company_runtime.company_knowledge import check_permitted, _L3_REQUIRED

    state_with_perms = _make_state(permitted=["assemble_review_pack", "query_active_wos"])

    # Permitted action → True
    assert check_permitted("assemble_review_pack", state_with_perms) is True, (
        "assemble_review_pack should be permitted"
    )
    assert check_permitted("query_active_wos", state_with_perms) is True, (
        "query_active_wos should be permitted"
    )

    # Unlisted action → False
    assert check_permitted("unknown_action_xyz", state_with_perms) is False, (
        "unlisted action should not be permitted"
    )

    # L3-required action → always False, even if in permitted_actions
    l3_state = _make_state(permitted=["commit", "send"])  # trying to sneak them in
    assert check_permitted("commit", l3_state) is False, (
        "commit must always be False (L3 required)"
    )
    assert check_permitted("send", l3_state) is False, (
        "send must always be False (L3 required)"
    )

    # Empty action → False
    assert check_permitted("", state_with_perms) is False, (
        "empty action string must return False"
    )

    ok("AT-2: check_permitted enforces permitted list and L3 wall")
except AssertionError as e:
    fail("AT-2", e)
except Exception as e:
    fail("AT-2", e)


# ── AT-3: missing data → honest gap (no fabrication) ─────────────────────────
try:
    from company_runtime.company_knowledge import build_deep_brief, honest_gap

    # Empty state → honest gap
    result_empty = build_deep_brief("what tasks are we on", {})
    assert "don't have" in result_empty.lower() or "no data" in result_empty.lower(), (
        f"empty state must return honest gap, got: {result_empty!r}"
    )

    # State with no active WOs → honest gap for tasks query
    state_done = _make_state(board=[
        {"id": "WO-001", "title": "Done", "status": "DONE", "pri": "P1"}
    ])
    result_none = build_deep_brief("what work orders are active", state_done)
    assert "don't have" in result_none.lower() or "board" in result_none.lower(), (
        f"no-active-WO state must yield honest gap or board reference, got: {result_none!r}"
    )

    # honest_gap helper returns useful text
    gap = honest_gap("sprint data")
    assert "sprint data" in gap, f"honest_gap must name the missing topic: {gap!r}"
    assert "board" in gap.lower() or "dispatch" in gap.lower(), (
        f"honest_gap must reference the board: {gap!r}"
    )

    ok("AT-3: missing data → honest gap, never fabrication")
except AssertionError as e:
    fail("AT-3", e)
except Exception as e:
    fail("AT-3", e)


# ── AT-4: company_state_writer.py wires deep brief; py_compile clean ──────────
try:
    writer_path = os.path.join(_BASE, "company_runtime", "company_state_writer.py")
    with open(writer_path, encoding="utf-8") as f:
        src = f.read()

    assert "company_knowledge" in src, (
        "company_state_writer.py must import from company_knowledge (WO-080 wiring)"
    )
    assert "is_deep_company_query" in src, (
        "company_state_writer.py must call is_deep_company_query() (WO-080)"
    )
    assert "build_deep_brief" in src, (
        "company_state_writer.py must call build_deep_brief() (WO-080)"
    )
    assert "WO-080" in src, (
        "company_state_writer.py must carry WO-080 marker at integration point"
    )

    py_compile.compile(writer_path, doraise=True)
    knowledge_path = os.path.join(_BASE, "company_runtime", "company_knowledge.py")
    py_compile.compile(knowledge_path, doraise=True)
    ok("AT-4: company_state_writer.py wires deep brief with WO-080 marker; both files compile clean")
except AssertionError as e:
    fail("AT-4", e)
except Exception as e:
    fail("AT-4", e)


# ── Summary ───────────────────────────────────────────────────────────────────
print()
print("=" * 62)
print(f"WO-080 company knowledge   {_passed} passed   {_failed} failed")
if _failed:
    sys.exit(1)
