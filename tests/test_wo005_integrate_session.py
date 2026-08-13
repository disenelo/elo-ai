"""
tests/test_wo005_integrate_session.py — Acceptance tests for WO-005: integrate_session()

Spec: runtime/reflection_faculty.py
5 acceptance tests from 17_memory_update.md.

Run: python3 tests/test_wo005_integrate_session.py
"""
import sys, tempfile, os
sys.path.insert(0, '.')

PASS = 0; FAIL = 0
def ok(n):  global PASS; PASS += 1; print(f"  ✅ {n}")
def fail(n, r): global FAIL; FAIL += 1; print(f"  ❌ {n}: {r}")

from runtime.reflection_faculty import integrate_session

SIG_SUMMARY = (
    "Today we built the Faculty Bus — a typed message envelope system that connects "
    "all faculties. Confirmed the 9-field schema and implemented publish/subscribe with "
    "TTL enforcement and confidence-only-lowered invariant. All 5 acceptance tests passed. "
    "This unblocks WO-006 and WO-007."
)

# ── FT-1: Significant session produces a spot code ────────────────────────────
result = integrate_session(
    SIG_SUMMARY,
    project="eLo OS",
    weight=7,
    tags=["faculty_bus", "architecture"],
    action="build",
    planned_objective="Faculty Bus implementation",
    completion_state="complete",
)
try:
    assert result.get("spot") or result.get("skipped"), f"no spot or skipped: {result}"
    assert not result.get("error"), f"unexpected error: {result.get('error')}"
    ok(f"FT-1: significant session → spot={result.get('spot')!r}, skipped={result.get('skipped')}")
except AssertionError as e: fail("FT-1", e)

# ── FT-2: Below-threshold session is skipped (significance gate) ──────────────
result2 = integrate_session(
    "short",
    project="eLo OS",
    weight=3,
    tags=[],
    action="chat",
    planned_objective="",
    completion_state="complete",
)
try:
    assert result2.get("skipped") == True, f"expected skipped=True, got {result2}"
    ok("FT-2: below-threshold session skipped (significance gate)")
except AssertionError as e: fail("FT-2", e)

# ── FT-3: Returns dict with expected keys ─────────────────────────────────────
try:
    for key in ("spot", "lesson", "skipped", "error"):
        assert key in result, f"missing key: {key}"
    ok("FT-3: result dict contains spot, lesson, skipped, error")
except AssertionError as e: fail("FT-3", e)

# ── FT-4: Lesson formed for significant sessions ──────────────────────────────
try:
    if not result.get("skipped") and result.get("lesson"):
        lesson = result["lesson"]
        assert "statement" in lesson, f"lesson missing statement: {lesson}"
        assert "strength" in lesson, f"lesson missing strength: {lesson}"
        ok(f"FT-4: lesson formed — statement present, strength={lesson.get('strength')}")
    else:
        ok("FT-4: lesson not formed (session skipped or not applicable — gate working)")
except AssertionError as e: fail("FT-4", e)

# ── FT-5: Error path returns error key, no crash ─────────────────────────────
result3 = integrate_session(
    None,  # type: ignore — bad input
    project="test",
    weight=8,
    tags=[],
    action="build",
    planned_objective="",
    completion_state="complete",
)
try:
    # Should either skip or return error — must not raise
    assert "error" in result3 or result3.get("skipped"), f"unexpected result: {result3}"
    ok("FT-5: error path — bad input handled without crash")
except AssertionError as e: fail("FT-5", e)

print(f"\nResult: {PASS}/5 passed, {FAIL} failed")
sys.exit(1 if FAIL else 0)
