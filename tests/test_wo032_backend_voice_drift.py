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


# ── AT-1: quota flag exists ───────────────────────────────────────────────────
try:
    import runtime.backend_router as _br
    if hasattr(_br, "_openai_quota_exceeded"):
        ok("AT-1: _openai_quota_exceeded flag exists in backend_router")
    else:
        fail("AT-1", "_openai_quota_exceeded not found in backend_router")
except Exception as e:
    fail("AT-1", e)


# ── AT-2: auto mode block checks the quota flag ───────────────────────────────
try:
    _src = open("runtime/backend_router.py", encoding="utf-8").read()
    if "_openai_quota_exceeded" in _src and "not _openai_quota_exceeded" in _src:
        ok("AT-2: auto mode guards OpenAI block with quota flag check")
    else:
        fail("AT-2", "quota flag guard not found in route() auto block")
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


# ── AT-5: "Can't reach" only fires on backend_used == "mock" ─────────────────
# _bh_degraded is defined as (backend_used == "mock" ...) a few lines above the
# message; the guard on the message itself is "if _bh_degraded".
try:
    _src = open("server.py", encoding="utf-8").read()
    # Use "right now" suffix — unique to the code line; the guard comment above uses the
    # shorter form "Can't reach my thinking" without "right now", so find() was hitting
    # the comment (line 2703) instead of the guarded code (line 3011).
    _idx = _src.find("Can't reach my thinking right now")
    if _idx >= 0:
        _window = _src[max(0, _idx - 600):_idx + 100]
        if "_bh_degraded" in _window and "backend_used" in _window:
            ok("AT-5: 'Can't reach my thinking' guarded by _bh_degraded (backend_used == 'mock')")
        else:
            fail("AT-5", f"guard context unexpected: {_window[:200]!r}")
    else:
        fail("AT-5", "'Can't reach my thinking' string not found in server.py")
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
