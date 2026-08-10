"""
tests/test_wo032b_groq_backend.py — WO-032b: Real Groq backend via stdlib urllib

Spec: with GROQ_API_KEY set → _groq_call builds the right request and parses the completion;
      active_backend() reports 'groq'; _groq_quota_cooldown_until clears after 60s window.

  AT-1:  _groq_call POSTs correct endpoint, auth header, model, messages — via stubbed urllib
  AT-2:  _groq_call parses completion text from response dict
  AT-3:  active_backend() returns 'groq' when ELO_BACKEND=groq and key present
  AT-4:  active_backend() returns 'mock' when ELO_BACKEND=groq and key absent
  AT-5:  _groq_quota_cooldown_until starts at 0.0 (not latched)
  AT-6:  Groq 429 sets cooldown for ~60 s; subsequent call skips _groq_call
  AT-7:  Groq cooldown clears naturally after window expires
  AT-8:  Successful Groq call after cooldown clears cooldown_until to 0.0
  AT-9:  _json_post builds correct Request object (url, method, Content-Type)
  AT-10: _json_post raises urllib.error.HTTPError on non-2xx (passthrough)
  AT-11: _cerebras_call uses _json_post (no httpx import)
  AT-12: py_compile clean on backend_router.py

Run: python3 tests/test_wo032b_groq_backend.py
"""
import sys, os, json, io, py_compile, time, unittest.mock as mock
sys.path.insert(0, ".")

PASS = 0; FAIL = 0
def ok(n):      global PASS; PASS += 1; print(f"  ✅ {n}")
def fail(n, r): global FAIL; FAIL += 1; print(f"  ❌ {n}: {r}")


# ── helpers ────────────────────────────────────────────────────────────────────

_GROQ_RESPONSE = {
    "choices": [{"message": {"content": "Hello from Groq stub."}}]
}

def _make_mock_urlopen(response_dict):
    """Return a context-manager mock that yields a file-like with JSON body."""
    encoded = json.dumps(response_dict).encode()
    cm = mock.MagicMock()
    cm.__enter__ = lambda s: io.BytesIO(encoded)
    cm.__exit__  = mock.MagicMock(return_value=False)
    return cm


# ── AT-1: _groq_call builds correct request via stubbed urllib ─────────────────
try:
    import urllib.request as _ur, urllib.error as _ue, runtime.backend_router as br

    captured_req = {}

    def _fake_urlopen(req, timeout=None):
        captured_req["url"]     = req.full_url
        captured_req["method"]  = req.get_method()
        captured_req["headers"] = {k.lower(): v for k, v in req.headers.items()}
        captured_req["body"]    = json.loads(req.data)
        cm = mock.MagicMock()
        cm.__enter__ = lambda s: io.BytesIO(json.dumps(_GROQ_RESPONSE).encode())
        cm.__exit__  = mock.MagicMock(return_value=False)
        return cm

    with mock.patch.dict(os.environ, {"GROQ_API_KEY": "test-key-123",
                                       "ELO_GROQ_MODEL": "llama-3.3-70b-versatile"}):
        with mock.patch("urllib.request.urlopen", _fake_urlopen):
            br._groq_call("sys prompt", "hello")

    assert "groq.com" in captured_req["url"], f"wrong endpoint: {captured_req['url']}"
    assert captured_req["method"] == "POST", f"wrong method: {captured_req['method']}"
    auth = captured_req["headers"].get("authorization", "")
    assert "test-key-123" in auth, f"auth header missing key: {auth}"
    body = captured_req["body"]
    assert body["model"] == "llama-3.3-70b-versatile", f"wrong model: {body.get('model')}"
    assert any(m["role"] == "system" for m in body["messages"]), "no system message"
    assert any(m["role"] == "user"   for m in body["messages"]), "no user message"
    ok("AT-1: _groq_call POSTs correct endpoint, auth header, model, messages")
except AssertionError as e:
    fail("AT-1", e)
except Exception as e:
    fail("AT-1", e)


# ── AT-2: _groq_call parses completion text ────────────────────────────────────
try:
    def _fake_urlopen2(req, timeout=None):
        cm = mock.MagicMock()
        cm.__enter__ = lambda s: io.BytesIO(json.dumps(_GROQ_RESPONSE).encode())
        cm.__exit__  = mock.MagicMock(return_value=False)
        return cm

    with mock.patch.dict(os.environ, {"GROQ_API_KEY": "test-key"}):
        with mock.patch("urllib.request.urlopen", _fake_urlopen2):
            result = br._groq_call("sys", "hello")

    assert result == "Hello from Groq stub.", f"unexpected result: {result!r}"
    ok("AT-2: _groq_call parses completion text from response")
except AssertionError as e:
    fail("AT-2", e)
except Exception as e:
    fail("AT-2", e)


# ── AT-3: active_backend() = 'groq' when key present + mode pinned ────────────
try:
    with mock.patch.dict(os.environ, {"ELO_BACKEND": "groq", "GROQ_API_KEY": "test-key"},
                         clear=False):
        backend = br.active_backend()
    assert backend == "groq", f"expected 'groq', got {backend!r}"
    ok("AT-3: active_backend() = 'groq' when ELO_BACKEND=groq + key present")
except AssertionError as e:
    fail("AT-3", e)
except Exception as e:
    fail("AT-3", e)


# ── AT-4: active_backend() = 'ollama'|'mock' when groq/cerebras key absent ────
# WO-073 added ollama as a local floor in the groq fallback chain.
# Expected: "ollama" when Ollama is running, "mock" when it's not.
try:
    env_no_key = {k: v for k, v in os.environ.items()
                  if k not in ("GROQ_API_KEY", "CEREBRAS_API_KEY", "ELO_BACKEND")}
    env_no_key["ELO_BACKEND"] = "groq"
    with mock.patch.dict(os.environ, env_no_key, clear=True):
        backend = br.active_backend()
    assert backend in ("ollama", "mock"), \
        f"expected 'ollama' or 'mock' when key absent; got {backend!r}"
    ok(f"AT-4: active_backend() = {backend!r} when groq key absent (WO-073: ollama floor)")
except AssertionError as e:
    fail("AT-4", e)
except Exception as e:
    fail("AT-4", e)


# ── AT-5: _groq_quota_cooldown_until starts at 0.0 ────────────────────────────
try:
    import importlib, runtime.backend_router as br2
    importlib.reload(br2)
    assert br2._groq_quota_cooldown_until == 0.0, \
        f"expected 0.0, got {br2._groq_quota_cooldown_until}"
    ok("AT-5: _groq_quota_cooldown_until initialises to 0.0 (not latched)")
except AssertionError as e:
    fail("AT-5", e)
except Exception as e:
    fail("AT-5", e)


# ── AT-6: Groq 429 sets cooldown ~60 s ────────────────────────────────────────
try:
    import urllib.error as _ue2
    br._groq_quota_cooldown_until = 0.0  # reset

    def _fake_429(req, timeout=None):
        raise _ue2.HTTPError(req.full_url, 429, "Too Many Requests", {}, None)

    with mock.patch.dict(os.environ, {"GROQ_API_KEY": "test-key", "ELO_BACKEND": "groq"}):
        with mock.patch("urllib.request.urlopen", _fake_429):
            br.route("test", "hello", action="answer")

    cooldown = br._groq_quota_cooldown_until
    assert cooldown > 0, f"cooldown not set after 429 (still 0)"
    remaining = cooldown - time.monotonic()
    assert 50 < remaining < 70, f"cooldown should be ~60s, got {remaining:.1f}s remaining"
    ok(f"AT-6: Groq 429 sets {remaining:.0f}s cooldown (expected ~60 s)")
except AssertionError as e:
    fail("AT-6", e)
except Exception as e:
    fail("AT-6", e)


# ── AT-7: Cooldown clears naturally after window ───────────────────────────────
try:
    br._groq_quota_cooldown_until = time.monotonic() - 1.0  # already expired

    calls = []
    def _fake_success(req, timeout=None):
        calls.append(req.full_url)
        cm = mock.MagicMock()
        cm.__enter__ = lambda s: io.BytesIO(json.dumps(_GROQ_RESPONSE).encode())
        cm.__exit__  = mock.MagicMock(return_value=False)
        return cm

    with mock.patch.dict(os.environ, {"GROQ_API_KEY": "test-key", "ELO_BACKEND": "groq"}):
        with mock.patch("urllib.request.urlopen", _fake_success):
            _, used = br.route("test", "hello", action="answer")

    assert used == "groq", f"expected groq after cooldown expiry, got {used!r}"
    assert calls, "Groq was not called after cooldown expired"
    ok("AT-7: expired cooldown → Groq call fires normally")
except AssertionError as e:
    fail("AT-7", e)
except Exception as e:
    fail("AT-7", e)


# ── AT-8: Successful call clears cooldown_until to 0.0 ────────────────────────
try:
    assert br._groq_quota_cooldown_until == 0.0, \
        f"successful call should have cleared cooldown; got {br._groq_quota_cooldown_until}"
    ok("AT-8: successful Groq call resets cooldown_until to 0.0")
except AssertionError as e:
    fail("AT-8", e)
except Exception as e:
    fail("AT-8", e)


# ── AT-9: _json_post builds correct Request ────────────────────────────────────
try:
    from runtime.backend_router import _json_post

    captured_req2 = {}
    def _fake_urlopen3(req, timeout=None):
        captured_req2["url"]    = req.full_url
        captured_req2["method"] = req.get_method()
        captured_req2["ct"]     = req.get_header("Content-type")
        captured_req2["body"]   = req.data
        cm = mock.MagicMock()
        cm.__enter__ = lambda s: io.BytesIO(b'{"result": "ok"}')
        cm.__exit__  = mock.MagicMock(return_value=False)
        return cm

    with mock.patch("urllib.request.urlopen", _fake_urlopen3):
        _json_post("https://example.com/v1/test",
                   payload={"key": "value"},
                   headers={"Content-Type": "application/json"})

    assert captured_req2["url"] == "https://example.com/v1/test", \
        f"wrong url: {captured_req2['url']}"
    assert captured_req2["method"] == "POST", f"wrong method"
    parsed_body = json.loads(captured_req2["body"])
    assert parsed_body == {"key": "value"}, f"wrong body: {parsed_body}"
    ok("AT-9: _json_post builds Request with correct url, method, JSON body")
except AssertionError as e:
    fail("AT-9", e)
except Exception as e:
    fail("AT-9", e)


# ── AT-10: _json_post passes HTTPError through ────────────────────────────────
try:
    import urllib.error as _ue3
    def _fake_500(req, timeout=None):
        raise _ue3.HTTPError(req.full_url, 500, "Server Error", {}, None)

    raised = None
    try:
        with mock.patch("urllib.request.urlopen", _fake_500):
            _json_post("https://example.com/fail", {}, {"Content-Type": "application/json"})
    except _ue3.HTTPError as ex:
        raised = ex

    assert raised is not None, "_json_post swallowed HTTPError"
    assert raised.code == 500, f"expected 500, got {raised.code}"
    ok("AT-10: _json_post raises HTTPError on non-2xx (passthrough)")
except AssertionError as e:
    fail("AT-10", e)
except Exception as e:
    fail("AT-10", e)


# ── AT-11: _cerebras_call uses _json_post (no httpx import in source) ─────────
try:
    with open("runtime/backend_router.py", encoding="utf-8") as _f:
        _src = _f.read()
    # _cerebras_call must not contain bare 'import httpx'
    import ast
    tree = ast.parse(_src)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name == "_cerebras_call":
                for child in ast.walk(node):
                    if isinstance(child, ast.Import):
                        for alias in child.names:
                            assert alias.name != "httpx", \
                                "_cerebras_call still imports httpx directly"
    # WO-032b marker present
    assert "WO-032b" in _src, "WO-032b comment marker not in backend_router.py"
    ok("AT-11: _cerebras_call uses _json_post (no bare httpx import); WO-032b marker present")
except AssertionError as e:
    fail("AT-11", e)
except Exception as e:
    fail("AT-11", e)


# ── AT-12: py_compile clean ────────────────────────────────────────────────────
try:
    py_compile.compile("runtime/backend_router.py", doraise=True)
    ok("AT-12: py_compile clean on backend_router.py")
except py_compile.PyCompileError as e:
    fail("AT-12", e)


print()
print("=" * 55)
print(f"WO-032b groq backend  {PASS} passed  {FAIL} failed")
if FAIL:
    sys.exit(1)
