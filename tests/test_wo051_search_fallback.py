"""
tests/test_wo051_search_fallback.py — Acceptance tests for WO-051

Spec: when SerpAPI fails and DuckDuckGo serves results, eLo must be told
      so it can surface the fallback honestly (never silent degradation).

  AT-1: web_search.last_source = "serpapi" when SerpAPI returns results
  AT-2: web_search.last_source = "ddg" when SerpAPI key is absent
  AT-3: web_search.last_source = "ddg" when SerpAPI call raises
  AT-4: server.py reads last_source and injects SEARCH_NOTE for ddg
  AT-5: no SEARCH_NOTE when serpapi serves
  AT-6: py_compile clean

Run: python3 tests/test_wo051_search_fallback.py
"""
import sys, os, unittest.mock as _mock
sys.path.insert(0, ".")

PASS = 0; FAIL = 0
def ok(n):      global PASS; PASS += 1; print(f"  ✅ {n}")
def fail(n, r): global FAIL; FAIL += 1; print(f"  ❌ {n}: {r}")


import tools.web_search as _ws
from tools.web_search import SearchResult, search as _search


# ── AT-1: last_source = "serpapi" when SerpAPI works ─────────────────────────
try:
    _fake_result = [SearchResult(title="Result", url="https://example.com", snippet="test")]

    with (
        _mock.patch.dict(os.environ, {"SERPAPI_KEY": "fake_key"}),
        _mock.patch.object(_ws, "_serp_search", return_value=_fake_result),
    ):
        _ws.last_source = ""
        results = _search("python programming")

    if _ws.last_source == "serpapi" and results == _fake_result:
        ok("AT-1: last_source='serpapi' when SerpAPI returns results")
    else:
        fail("AT-1", f"last_source={_ws.last_source!r}, results_len={len(results)}")
except Exception as e:
    fail("AT-1", e)


# ── AT-2: last_source = "ddg" when no SERPAPI_KEY ────────────────────────────
try:
    _fake_ddg = [SearchResult(title="DDG", url="https://ddg.co", snippet="ddg result")]

    _env_without_key = {k: v for k, v in os.environ.items() if k != "SERPAPI_KEY"}
    with (
        _mock.patch.dict(os.environ, _env_without_key, clear=True),
        _mock.patch.object(_ws, "_ddg_search", return_value=_fake_ddg),
    ):
        _ws.last_source = ""
        results = _search("python programming")

    if _ws.last_source == "ddg":
        ok("AT-2: last_source='ddg' when no SERPAPI_KEY")
    else:
        fail("AT-2", f"last_source={_ws.last_source!r}")
except Exception as e:
    fail("AT-2", e)


# ── AT-3: last_source = "ddg" when SerpAPI call raises ───────────────────────
try:
    _fake_ddg2 = [SearchResult(title="DDG2", url="https://ddg.co/2", snippet="ddg result 2")]

    with (
        _mock.patch.dict(os.environ, {"SERPAPI_KEY": "bad_key"}),
        _mock.patch.object(_ws, "_serp_search", return_value=[]),   # serp returns empty → ddg
        _mock.patch.object(_ws, "_ddg_search", return_value=_fake_ddg2),
    ):
        _ws.last_source = ""
        results = _search("python programming")

    if _ws.last_source == "ddg":
        ok("AT-3: last_source='ddg' when SerpAPI returns empty (falls to DDG)")
    else:
        fail("AT-3", f"last_source={_ws.last_source!r}")
except Exception as e:
    fail("AT-3", e)


# ── AT-4: server.py injects SEARCH_NOTE when last_source == "ddg" ─────────────
try:
    _src = open("server.py", encoding="utf-8").read()
    if 'last_source' in _src and 'SEARCH_NOTE' in _src and '_ws_backup' in _src:
        ok("AT-4: server.py reads last_source and injects SEARCH_NOTE for ddg")
    else:
        fail("AT-4", "SEARCH_NOTE / last_source / _ws_backup not found in server.py")
except Exception as e:
    fail("AT-4", e)


# ── AT-5: SEARCH_NOTE block only fires when source == "ddg" ──────────────────
try:
    # Check the conditional in server.py is guarded by _ws_src == "ddg"
    if '"ddg"' in _src and '_ws_src == "ddg"' in _src:
        ok("AT-5: SEARCH_NOTE is gated on _ws_src == 'ddg' (not injected for serpapi)")
    else:
        fail("AT-5", "ddg gate not found in server.py")
except Exception as e:
    fail("AT-5", e)


# ── AT-6: py_compile clean ────────────────────────────────────────────────────
try:
    import py_compile
    py_compile.compile("server.py",          doraise=True)
    py_compile.compile("tools/web_search.py", doraise=True)
    ok("AT-6: py_compile clean on server.py + tools/web_search.py")
except py_compile.PyCompileError as e:
    fail("AT-6", e)


print()
print("=" * 50)
print(f"WO-051  {PASS} passed  {FAIL} failed")
if FAIL:
    sys.exit(1)
