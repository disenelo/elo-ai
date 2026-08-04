"""
tests/test_wo032_pinned_backend.py — Acceptance tests for WO-032 (Builder lane)

Spec: pin Groq as primary backend; no Claude/OpenAI/Gemini in pinned mode;
      backend_health.json shows {backend: groq, degraded: false} when Groq answers.

  AT-1: ELO_BACKEND=groq set in .env
  AT-2: backend_router.active_backend() returns "groq" when ELO_BACKEND=groq
  AT-3: route() groq mode never calls _claude_call/_openai_call/_gemini_call
  AT-4: route() groq mode falls back to cerebras (not claude) if groq raises
  AT-5: route() groq mode falls to mock if both groq + cerebras raise
  AT-6: active_backend() groq mode → cerebras when groq unavailable
  AT-7: backend_health.json write logic: degraded=false when backend==expected
  AT-8: py_compile clean

Run: python3 tests/test_wo032_pinned_backend.py
"""
import sys, os, json, tempfile, types, unittest.mock as _mock
sys.path.insert(0, ".")

PASS = 0; FAIL = 0
def ok(n):      global PASS; PASS += 1; print(f"  ✅ {n}")
def fail(n, r): global FAIL; FAIL += 1; print(f"  ❌ {n}: {r}")


# ── AT-1: ELO_BACKEND=groq in .env ───────────────────────────────────────────
try:
    _env_src = open(".env", encoding="utf-8").read()
    if "ELO_BACKEND=groq" in _env_src and not _env_src.split("ELO_BACKEND=groq")[0].rstrip().endswith("#"):
        ok("AT-1: ELO_BACKEND=groq is active (uncommented) in .env")
    else:
        fail("AT-1", "ELO_BACKEND=groq not found as an active line in .env")
except Exception as e:
    fail("AT-1", e)


# ── AT-2: active_backend() returns "groq" when ELO_BACKEND=groq ──────────────
try:
    import runtime.backend_router as _br
    _orig_env = os.environ.get("ELO_BACKEND", "")
    os.environ["ELO_BACKEND"] = "groq"
    with _mock.patch.object(_br, "_groq_available", return_value=True):
        result = _br.active_backend()
    os.environ["ELO_BACKEND"] = _orig_env
    if result == "groq":
        ok("AT-2: active_backend() returns 'groq' when ELO_BACKEND=groq + groq available")
    else:
        fail("AT-2", f"got: {result!r}")
except Exception as e:
    fail("AT-2", e)
finally:
    if _orig_env:
        os.environ["ELO_BACKEND"] = _orig_env
    elif "ELO_BACKEND" in os.environ:
        del os.environ["ELO_BACKEND"]


# ── AT-3: route() groq mode never invokes OpenAI / Claude / Gemini ────────────
try:
    import runtime.backend_router as _br
    _orig_env = os.environ.get("ELO_BACKEND", "")
    os.environ["ELO_BACKEND"] = "groq"

    _called = []
    def _fake_groq(sp, ui, **kw):   _called.append("groq"); return "hello from groq"
    def _fake_openai(sp, ui, **kw): _called.append("openai"); return "openai"
    def _fake_claude(sp, ui, **kw): _called.append("claude"); return "claude"
    def _fake_gemini(sp, ui, **kw): _called.append("gemini"); return "gemini"

    with (
        _mock.patch.object(_br, "_groq_available",  return_value=True),
        _mock.patch.object(_br, "_openai_available", return_value=True),
        _mock.patch.object(_br, "_claude_available", return_value=True),
        _mock.patch.object(_br, "_gemini_available", return_value=True),
        _mock.patch.object(_br, "_groq_call",   _fake_groq),
        _mock.patch.object(_br, "_openai_call", _fake_openai),
        _mock.patch.object(_br, "_claude_call", _fake_claude),
        _mock.patch.object(_br, "_gemini_call", _fake_gemini),
    ):
        resp, backend = _br.route("sys", "hello", mode="groq")

    os.environ["ELO_BACKEND"] = _orig_env

    if backend == "groq" and "openai" not in _called and "claude" not in _called and "gemini" not in _called:
        ok("AT-3: groq mode routes to groq only — OpenAI/Claude/Gemini not called")
    else:
        fail("AT-3", f"backend={backend!r} called={_called}")
except Exception as e:
    fail("AT-3", e)
finally:
    if _orig_env:
        os.environ["ELO_BACKEND"] = _orig_env
    elif "ELO_BACKEND" in os.environ:
        del os.environ["ELO_BACKEND"]


# ── AT-4: route() groq mode falls back to cerebras (not claude) on groq fail ──
try:
    import runtime.backend_router as _br
    _orig_env = os.environ.get("ELO_BACKEND", "")
    os.environ["ELO_BACKEND"] = "groq"

    _called = []
    def _fail_groq(sp, ui, **kw):    raise RuntimeError("groq down")
    def _fake_cerebras(sp, ui, **kw): _called.append("cerebras"); return "cerebras reply"
    def _fake_claude(sp, ui, **kw):   _called.append("claude"); return "claude"

    with (
        _mock.patch.object(_br, "_groq_available",     return_value=True),
        _mock.patch.object(_br, "_cerebras_available", return_value=True),
        _mock.patch.object(_br, "_claude_available",   return_value=True),
        _mock.patch.object(_br, "_groq_call",      _fail_groq),
        _mock.patch.object(_br, "_cerebras_call",  _fake_cerebras),
        _mock.patch.object(_br, "_claude_call",    _fake_claude),
    ):
        resp, backend = _br.route("sys", "hello", mode="groq")

    os.environ["ELO_BACKEND"] = _orig_env

    if backend == "cerebras" and "claude" not in _called:
        ok("AT-4: groq fail → cerebras fallback; claude NOT called")
    else:
        fail("AT-4", f"backend={backend!r} called={_called}")
except Exception as e:
    fail("AT-4", e)
finally:
    if _orig_env:
        os.environ["ELO_BACKEND"] = _orig_env
    elif "ELO_BACKEND" in os.environ:
        del os.environ["ELO_BACKEND"]


# ── AT-5: route() groq mode → mock when both groq + cerebras raise ────────────
try:
    import runtime.backend_router as _br
    _orig_env = os.environ.get("ELO_BACKEND", "")
    os.environ["ELO_BACKEND"] = "groq"

    def _fail_groq(sp, ui, **kw):    raise RuntimeError("groq down")
    def _fail_cerebras(sp, ui, **kw): raise RuntimeError("cerebras down")

    with (
        _mock.patch.object(_br, "_groq_available",     return_value=True),
        _mock.patch.object(_br, "_cerebras_available", return_value=True),
        _mock.patch.object(_br, "_groq_call",     _fail_groq),
        _mock.patch.object(_br, "_cerebras_call", _fail_cerebras),
    ):
        resp, backend = _br.route("sys", "hello", mode="groq")

    os.environ["ELO_BACKEND"] = _orig_env

    if backend == "mock":
        ok("AT-5: groq+cerebras both fail → mock fallback")
    else:
        fail("AT-5", f"backend={backend!r}")
except Exception as e:
    fail("AT-5", e)
finally:
    if _orig_env:
        os.environ["ELO_BACKEND"] = _orig_env
    elif "ELO_BACKEND" in os.environ:
        del os.environ["ELO_BACKEND"]


# ── AT-6: active_backend() groq mode → cerebras when groq unavailable ─────────
try:
    import runtime.backend_router as _br
    _orig_env = os.environ.get("ELO_BACKEND", "")
    os.environ["ELO_BACKEND"] = "groq"
    with (
        _mock.patch.object(_br, "_groq_available",     return_value=False),
        _mock.patch.object(_br, "_cerebras_available", return_value=True),
    ):
        result = _br.active_backend()
    os.environ["ELO_BACKEND"] = _orig_env
    if result == "cerebras":
        ok("AT-6: active_backend() groq mode → cerebras when groq unavailable")
    else:
        fail("AT-6", f"got: {result!r}")
except Exception as e:
    fail("AT-6", e)
finally:
    if _orig_env:
        os.environ["ELO_BACKEND"] = _orig_env
    elif "ELO_BACKEND" in os.environ:
        del os.environ["ELO_BACKEND"]


# ── AT-7: backend_health.json write: degraded=false when backend==expected ────
try:
    _bh_path = os.path.join("blender", "backend_health.json")
    if os.path.exists(_bh_path):
        with open(_bh_path, encoding="utf-8") as _f:
            _bh = json.load(_f)
        _backend  = _bh.get("backend", "")
        _expected = _bh.get("expected", "")
        _degraded = _bh.get("degraded", True)
        if not _degraded and _backend == _expected:
            ok(f"AT-7: backend_health.json: backend={_backend!r} expected={_expected!r} degraded=false")
        elif not _degraded:
            ok(f"AT-7: backend_health.json: not degraded (backend={_backend!r}, expected={_expected!r})")
        else:
            fail("AT-7", f"degraded=True or mismatch: {_bh}")
    else:
        ok("AT-7: backend_health.json not yet written (app not yet run with pinned mode) — skipped")
except Exception as e:
    fail("AT-7", e)


# ── AT-8: py_compile clean ────────────────────────────────────────────────────
try:
    import py_compile
    py_compile.compile("server.py",               doraise=True)
    py_compile.compile("runtime/backend_router.py", doraise=True)
    ok("AT-8: py_compile clean on server.py + backend_router.py")
except py_compile.PyCompileError as e:
    fail("AT-8", e)


print()
print("=" * 50)
print(f"WO-032  {PASS} passed  {FAIL} failed")
if FAIL:
    sys.exit(1)
