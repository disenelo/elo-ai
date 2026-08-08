"""
tests/test_wo073_pinned_ollama_fallback.py — Acceptance tests for WO-073

Spec: WO-073 — Ollama local floor in pinned-Groq fallback chain.
      Groq → Cerebras → Ollama → Mock  (was: Groq → Cerebras → Mock).
      eLo never drops to the mute mock while a local brain is running.

Tests:
  AT-1: pinned mode, Groq 429 + Cerebras down + Ollama up → returns ("...", "ollama")
  AT-2: pinned mode, Groq succeeds → still "groq" (no regression)
  AT-3: pinned mode, all three down → "mock" (honest fallback unchanged)
  AT-4: active_backend() groq mode, Groq+Cerebras down, Ollama up → "ollama"
  AT-5: active_backend() groq mode, all down → "mock"
  AT-6: py_compile clean

Run: python3 tests/test_wo073_pinned_ollama_fallback.py
"""
import sys, os, time, unittest.mock as _mock
sys.path.insert(0, ".")

PASS = 0; FAIL = 0
def ok(n):      global PASS; PASS += 1; print(f"  ✅ {n}")
def fail(n, r): global FAIL; FAIL += 1; print(f"  ❌ {n}: {r}")

import runtime.backend_router as _br
import urllib.error as _ue


def _make_http_error(code: int):
    """Minimal urllib.error.HTTPError that carries a .code attribute."""
    return _ue.HTTPError(url="", code=code, msg="", hdrs=None, fp=None)


# ── AT-1: Groq 429 + Cerebras down + Ollama up → ollama ─────────────────────
try:
    with (
        _mock.patch.object(_br, "_groq_available",     return_value=True),
        _mock.patch.object(_br, "_groq_call",          side_effect=_make_http_error(429)),
        _mock.patch.object(_br, "_cerebras_available", return_value=False),
        _mock.patch.object(_br, "_ollama_available",   return_value=True),
        _mock.patch.object(_br, "_ollama_call",        return_value="I'm thinking locally."),
        _mock.patch.dict(os.environ, {"ELO_BACKEND": "groq"}),
    ):
        # reset cooldown so Groq block executes
        _br._groq_quota_cooldown_until = 0.0
        result, backend = _br.route("hello", "sys", mode="groq")
        if backend == "ollama":
            ok(f"AT-1: Groq 429 → Ollama floor → backend='{backend}'")
        else:
            fail("AT-1", f"expected 'ollama', got '{backend}' / reply: {result!r}")
except Exception as e:
    fail("AT-1", e)


# ── AT-2: Groq succeeds → still "groq" (no regression) ──────────────────────
try:
    with (
        _mock.patch.object(_br, "_groq_available",     return_value=True),
        _mock.patch.object(_br, "_groq_call",          return_value="All good from Groq."),
        _mock.patch.object(_br, "_ollama_available",   return_value=True),
        _mock.patch.dict(os.environ, {"ELO_BACKEND": "groq"}),
    ):
        _br._groq_quota_cooldown_until = 0.0
        result, backend = _br.route("hello", "sys", mode="groq")
        if backend == "groq":
            ok(f"AT-2: Groq success → backend='{backend}' (Ollama not touched)")
        else:
            fail("AT-2", f"expected 'groq', got '{backend}'")
except Exception as e:
    fail("AT-2", e)


# ── AT-3: Groq + Cerebras + Ollama all down → mock ───────────────────────────
try:
    with (
        _mock.patch.object(_br, "_groq_available",     return_value=False),
        _mock.patch.object(_br, "_cerebras_available", return_value=False),
        _mock.patch.object(_br, "_ollama_available",   return_value=False),
        _mock.patch.dict(os.environ, {"ELO_BACKEND": "groq"}),
    ):
        _br._groq_quota_cooldown_until = 0.0
        result, backend = _br.route("hello", "sys", mode="groq")
        if backend == "mock":
            ok(f"AT-3: all backends down → honest mock fallback")
        else:
            fail("AT-3", f"expected 'mock', got '{backend}'")
except Exception as e:
    fail("AT-3", e)


# ── AT-4: active_backend() groq mode, Groq+Cerebras down, Ollama up ──────────
try:
    with (
        _mock.patch.object(_br, "_groq_available",     return_value=False),
        _mock.patch.object(_br, "_cerebras_available", return_value=False),
        _mock.patch.object(_br, "_ollama_available",   return_value=True),
        _mock.patch.dict(os.environ, {"ELO_BACKEND": "groq"}),
    ):
        b = _br.active_backend()
        if b == "ollama":
            ok(f"AT-4: active_backend() groq mode, cloud down → '{b}'")
        else:
            fail("AT-4", f"expected 'ollama', got '{b}'")
except Exception as e:
    fail("AT-4", e)


# ── AT-5: active_backend() groq mode, all down → mock ────────────────────────
try:
    with (
        _mock.patch.object(_br, "_groq_available",     return_value=False),
        _mock.patch.object(_br, "_cerebras_available", return_value=False),
        _mock.patch.object(_br, "_ollama_available",   return_value=False),
        _mock.patch.dict(os.environ, {"ELO_BACKEND": "groq"}),
    ):
        b = _br.active_backend()
        if b == "mock":
            ok(f"AT-5: active_backend() all down → '{b}'")
        else:
            fail("AT-5", f"expected 'mock', got '{b}'")
except Exception as e:
    fail("AT-5", e)


# ── AT-6: py_compile clean ────────────────────────────────────────────────────
try:
    import py_compile
    py_compile.compile("runtime/backend_router.py", doraise=True)
    ok("AT-6: py_compile clean on backend_router.py")
except py_compile.PyCompileError as e:
    fail("AT-6", e)


print()
print(f"{'='*50}")
print(f"WO-073  {PASS} passed  {FAIL} failed")
if FAIL:
    sys.exit(1)
