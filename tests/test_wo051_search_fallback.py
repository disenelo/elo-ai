"""
tests/test_wo051_search_fallback.py — WO-051 honest search fallback

Spec: when SerpAPI fails and DuckDuckGo serves results, eLo must be told so it
      can surface the fallback honestly — never silent degradation. last_source
      tracks which provider served the result; server.py injects SEARCH_NOTE
      when the result came from DDG.

AT-1  last_source='serpapi' when SerpAPI returns results (primary path)
AT-2  last_source='ddg' when SERPAPI_KEY absent — DDG is primary fallback
AT-3  last_source='ddg' when SerpAPI returns empty results → falls through to DDG
AT-4  server.py reads last_source and injects SEARCH_NOTE when source='ddg'
AT-5  SEARCH_NOTE block is gated on _ws_src=='ddg'; not injected for serpapi
AT-6  py_compile clean on server.py + tools/web_search.py
"""
import os
import sys
import py_compile
import unittest.mock as mock

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import tools.web_search as _ws
from tools.web_search import SearchResult, search as _search

_ROOT      = os.path.join(os.path.dirname(__file__), "..")
_SERVER_PY = os.path.join(_ROOT, "server.py")
_WS_PY     = os.path.join(_ROOT, "tools", "web_search.py")

_FAKE_SERP = [SearchResult(title="SerpAPI Result", url="https://example.com", snippet="serp result")]
_FAKE_DDG  = [SearchResult(title="DDG Result", url="https://ddg.co", snippet="ddg result")]
_FAKE_DDG2 = [SearchResult(title="DDG Fallback", url="https://ddg.co/2", snippet="ddg fallback")]


# ── AT-1 ──────────────────────────────────────────────────────────────────────

def test_at1_serpapi_primary_sets_last_source():
    """
    When SerpAPI is available and returns results, last_source must be 'serpapi'.
    This is the happy path — eLo uses the highest-quality provider.
    """
    with (
        mock.patch.dict(os.environ, {"SERPAPI_KEY": "fake_key"}),
        mock.patch.object(_ws, "_serp_search", return_value=_FAKE_SERP),
    ):
        _ws.last_source = ""
        results = _search("python programming")

    assert _ws.last_source == "serpapi", (
        f"AT-1 FAIL: last_source={_ws.last_source!r}, expected 'serpapi'"
    )
    assert results == _FAKE_SERP, (
        f"AT-1 FAIL: results not from SerpAPI mock — got {results!r}"
    )


# ── AT-2 ──────────────────────────────────────────────────────────────────────

def test_at2_no_serpapi_key_falls_to_ddg():
    """
    When SERPAPI_KEY is absent, search must fall through to DuckDuckGo and
    set last_source='ddg'. eLo then knows to surface the fallback honestly.
    """
    env_without_key = {k: v for k, v in os.environ.items() if k != "SERPAPI_KEY"}
    with (
        mock.patch.dict(os.environ, env_without_key, clear=True),
        mock.patch.object(_ws, "_ddg_search", return_value=_FAKE_DDG),
    ):
        _ws.last_source = ""
        results = _search("python programming")

    assert _ws.last_source == "ddg", (
        f"AT-2 FAIL: last_source={_ws.last_source!r}, expected 'ddg' with no key"
    )
    assert results, "AT-2 FAIL: no results from DDG mock"


# ── AT-3 ──────────────────────────────────────────────────────────────────────

def test_at3_serpapi_empty_falls_to_ddg():
    """
    When SerpAPI is configured but returns empty results, the search must fall
    through to DuckDuckGo and record last_source='ddg'. Empty result from a
    provider is a soft failure — don't report it as the source.
    """
    with (
        mock.patch.dict(os.environ, {"SERPAPI_KEY": "bad_key"}),
        mock.patch.object(_ws, "_serp_search", return_value=[]),   # empty → falls to DDG
        mock.patch.object(_ws, "_ddg_search", return_value=_FAKE_DDG2),
    ):
        _ws.last_source = ""
        results = _search("python programming")

    assert _ws.last_source == "ddg", (
        f"AT-3 FAIL: last_source={_ws.last_source!r} after SerpAPI empty — expected 'ddg'"
    )
    assert results, "AT-3 FAIL: no results from DDG mock after SerpAPI empty"


# ── AT-4 ──────────────────────────────────────────────────────────────────────

def test_at4_server_injects_search_note_for_ddg():
    """
    server.py must read last_source and inject a SEARCH_NOTE when source is 'ddg'.
    This is the honest-disclosure mechanism — eLo doesn't claim DDG results
    are from a premium search without saying so.
    """
    src = open(_SERVER_PY, encoding="utf-8").read()
    assert "last_source" in src, "AT-4 FAIL: 'last_source' not referenced in server.py"
    assert "SEARCH_NOTE" in src, "AT-4 FAIL: 'SEARCH_NOTE' not found in server.py"
    assert "_ws_backup" in src or "_ws_src" in src, (
        "AT-4 FAIL: search source variable (_ws_backup/_ws_src) not in server.py"
    )


# ── AT-5 ──────────────────────────────────────────────────────────────────────

def test_at5_search_note_gated_on_ddg_only():
    """
    SEARCH_NOTE must be injected ONLY when the source is DDG — not for SerpAPI.
    The gate must be an explicit equality check on 'ddg', not a truthy check.
    """
    src = open(_SERVER_PY, encoding="utf-8").read()
    assert '"ddg"' in src, "AT-5 FAIL: 'ddg' string not in server.py"
    # The gate must be an explicit equality check
    assert '_ws_src == "ddg"' in src or "_ws_src == 'ddg'" in src, (
        "AT-5 FAIL: exact gate '_ws_src == \"ddg\"' not found — SEARCH_NOTE may fire for non-DDG results"
    )


# ── AT-6 ──────────────────────────────────────────────────────────────────────

def test_at6_py_compile_clean():
    for path in (_SERVER_PY, _WS_PY):
        try:
            py_compile.compile(path, doraise=True)
        except py_compile.PyCompileError as e:
            pytest.fail(f"AT-6 FAIL: {os.path.basename(path)} does not compile: {e}")
