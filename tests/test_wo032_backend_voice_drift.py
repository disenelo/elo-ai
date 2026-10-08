"""
tests/test_wo032_backend_voice_drift.py — Acceptance tests for WO-032

Spec: WO-032 — Groq as voice-consistent primary; "Can't reach my thinking"
      only when ALL providers truly fail; duplicate real response beats mock.

Tests:
  AT-1: _openai_quota_exceeded flag exists in backend_router module
  AT-2: OpenAI block in auto mode respects quota flag (skips when True)
  AT-3: Groq duplicate check returns real response, not mock
  AT-4: Cerebras duplicate check returns real response, not mock
  AT-5: "Can't reach my thinking" path only fires when backend_used == "mock"
  AT-6: py_compile clean

Run: python3 tests/test_wo032_backend_voice_drift.py
"""
import sys, os
sys.path.insert(0, ".")

PASS = 0; FAIL = 0
def ok(n):      global PASS; PASS += 1; print(f"  ✅ {n}")
def fail(n, r): global FAIL; FAIL += 1; print(f"  ❌ {n}: {r}")


# ── AT-1: quota cooldown variable exists ─────────────────────────────────────
# Updated 2026-10-08: was _openai_quota_exceeded (bool); now _openai_quota_cooldown_until (float)
# per David ruling 2026-08-21: "do not snub them out — use what is available to feel out failsafes."
try:
    import runtime.backend_router as _br
    if hasattr(_br, "_openai_quota_cooldown_until"):
        ok("AT-1: _openai_quota_cooldown_until cooldown variable exists in backend_router")
    else:
        fail("AT-1", "_openai_quota_cooldown_until not found in backend_router")
except Exception as e:
    fail("AT-1", e)


# ── AT-2: auto mode block checks the cooldown timer ──────────────────────────
# Updated 2026-10-08: checks for cooldown float pattern instead of old bool flag
try:
    _src = open("runtime/backend_router.py", encoding="utf-8").read()
    if "_openai_quota_cooldown_until" in _src and "time.monotonic() < _openai_quota_cooldown_until" in _src:
        ok("AT-2: auto mode guards OpenAI block with cooldown timer check")
    else:
        fail("AT-2", "cooldown timer guard not found in route() auto block")
except Exception as e:
    fail("AT-2", e)


# ── AT-3: Groq duplicate → returns real response, not mock ───────────────────
try:
    _src = open("runtime/backend_router.py", encoding="utf-8").read()
    # Check that after the Groq duplicate log message, we don't go to _mock_fallback
    _groq_section = _src[_src.find("# WO-032: near-duplicate real response beats a canned mock"):]
    _groq_section_end = _groq_section.find("return normalised, \"groq\"")
    _groq_block = _groq_section[:_groq_section_end + 30]
    if "_mock_fallback" not in _groq_block:
        ok("AT-3: Groq duplicate path returns real response (no mock fallback)")
    else:
        fail("AT-3", "Groq duplicate path still falls to mock")
except Exception as e:
    fail("AT-3", e)


# ── AT-4: Cerebras duplicate → returns real response, not mock ────────────────
try:
    _src = open("runtime/backend_router.py", encoding="utf-8").read()
    _cer_marker = _src.rfind("# WO-032: near-duplicate real response beats a canned mock")
    _cer_section = _src[_cer_marker:]
    _cer_end = _cer_section.find("return normalised, \"cerebras\"")
    _cer_block = _cer_section[:_cer_end + 30]
    if "_mock_fallback" not in _cer_block:
        ok("AT-4: Cerebras duplicate path returns real response (no mock fallback)")
    else:
        fail("AT-4", "Cerebras duplicate path still falls to mock")
except Exception as e:
    fail("AT-4", e)


# ── AT-5: degraded path lets mock through (S1-DEGRADED-HOLDING-LINE) ─────────
# Updated 2026-10-08: "Can't reach my thinking" replacement string was removed.
# S1-DEGRADED-HOLDING-LINE: when _bh_degraded and _agent is None → pass.
# Mock is eLo-voiced by design; the stall-string replacement terminated the turn
# with a promise that was never kept (25% of turns). Let mock through instead.
try:
    _src = open("server.py", encoding="utf-8").read()
    # _bh_degraded must be defined as (backend_used == "mock" ...)
    _bh_def_idx = _src.find("_bh_degraded = (_llm_turn and backend_used == \"mock\"")
    # The guard block must use: if _bh_degraded and _agent is None: ... pass
    _bh_guard_idx = _src.find("if _bh_degraded and _agent is None:")
    # S1-DEGRADED-HOLDING-LINE comment confirms the pass is intentional
    _s1_idx = _src.find("S1-DEGRADED-HOLDING-LINE")
    if _bh_def_idx >= 0 and _bh_guard_idx >= 0 and _s1_idx >= 0:
        ok("AT-5: _bh_degraded tied to backend_used=='mock'; degraded path uses pass (S1-DEGRADED-HOLDING-LINE)")
    else:
        _missing = []
        if _bh_def_idx < 0: _missing.append("_bh_degraded=(backend_used=='mock') definition")
        if _bh_guard_idx < 0: _missing.append("if _bh_degraded and _agent is None guard")
        if _s1_idx < 0: _missing.append("S1-DEGRADED-HOLDING-LINE marker")
        fail("AT-5", f"missing: {', '.join(_missing)}")
except Exception as e:
    fail("AT-5", e)


# ── AT-6: py_compile clean ────────────────────────────────────────────────────
try:
    import py_compile
    py_compile.compile("runtime/backend_router.py", doraise=True)
    py_compile.compile("server.py", doraise=True)
    ok("AT-6: py_compile clean on backend_router.py and server.py")
except py_compile.PyCompileError as e:
    fail("AT-6", e)


# ── Summary ───────────────────────────────────────────────────────────────────
print()
print(f"{'='*50}")
print(f"WO-032  {PASS} passed  {FAIL} failed")
if FAIL:
    sys.exit(1)
