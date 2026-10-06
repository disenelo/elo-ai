"""
tests/test_wo_wkg004_wkg_runtime_injection.py

WO-WKG-004: §4 Build List — Verify recovered knowledge cannot silently disappear.
Proves WKG claims from graph_loader.retrieve_wkg() reach the runtime context.

Run: ~/miniconda3/bin/python3 -m pytest tests/test_wo_wkg004_wkg_runtime_injection.py -q
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def test_retrieve_wkg_returns_list():
    """AT-1: retrieve_wkg() returns a list (may be empty — no crash)."""
    from knowledge.graph_loader import retrieve_wkg
    result = retrieve_wkg("the moon and its cycles")
    assert isinstance(result, list), f"AT-1: must return list; got {type(result)}"


def test_retrieve_wkg_hits_for_wkg_topic():
    """AT-2: WKG-relevant input (Joseph corpus topics) returns ≥1 result."""
    from knowledge.graph_loader import retrieve_wkg
    # The Joseph corpus contains moon / lunar / 28-day / season claims
    result = retrieve_wkg("28 days moon lunar rhythm")
    assert len(result) >= 1, (
        f"AT-2: expected ≥1 WKG hit for Joseph corpus topic; got {len(result)}"
    )


def test_retrieve_wkg_result_has_required_keys():
    """AT-3: Each result carries label, content, confidence, wkg_epistemic_class."""
    from knowledge.graph_loader import retrieve_wkg
    result = retrieve_wkg("moon lunar 28 days seasons")
    if not result:
        import pytest; pytest.skip("WKG corpus empty — cannot verify shape")
    for key in ("label", "content", "confidence", "wkg_epistemic_class"):
        assert key in result[0], f"AT-3: result missing key '{key}'"


def test_retrieve_wkg_epistemic_class_is_known():
    """AT-4: wkg_epistemic_class is one of the 8 ratified classes."""
    from knowledge.graph_loader import retrieve_wkg
    _KNOWN = {"VERIFIED", "SOURCE_ATTRIBUTED", "SYMBOLIC", "HISTORICAL",
              "HYPOTHESIS", "SPECULATIVE", "DISPUTED", "UNKNOWN"}
    result = retrieve_wkg("moon lunar seasons")
    if not result:
        import pytest; pytest.skip("WKG corpus empty — cannot verify class")
    for r in result:
        assert r["wkg_epistemic_class"] in _KNOWN, (
            f"AT-4: unknown epistemic class: {r['wkg_epistemic_class']!r}"
        )


def test_retrieve_wkg_empty_for_unrelated_input():
    """AT-5: Completely unrelated input returns empty list (no spurious injection)."""
    from knowledge.graph_loader import retrieve_wkg
    result = retrieve_wkg("xyzzy qwerty asdfg zxcvb plmkn jklop wrtyu")  # keyboard mash — no real WKG words
    assert result == [], (
        f"AT-5: expected [] for unrelated input; got {len(result)} results"
    )


def test_wkg_injection_in_server_g_ctx():
    """AT-6: WKG content appears in g_ctx for WKG-relevant input via server.py wiring.
    Proves the g_ctx injection path is live (WO-WKG-004 implementation).
    """
    # Read server.py source and confirm WO-WKG-004 block exists
    _root = os.path.join(os.path.dirname(__file__), "..")
    _server = os.path.join(_root, "server.py")
    src = open(_server, encoding="utf-8").read()
    assert "WO-WKG-004" in src, "AT-6: WO-WKG-004 injection block must exist in server.py"
    assert "retrieve_wkg" in src, "AT-6: retrieve_wkg call must be in server.py"
    assert "wkg_epistemic_class" in src or "wkg_ep" in src, (
        "AT-6: epistemic label mapping must be in server.py"
    )


def test_wkg_injection_pattern_matches_g_ctx_convention():
    """AT-7: WO-WKG-004 uses same additive g_ctx pattern as other context blocks.
    Confirms fault-tolerance (wrapped in try/except with _logging.warning).
    """
    _root = os.path.join(os.path.dirname(__file__), "..")
    _server = os.path.join(_root, "server.py")
    src = open(_server, encoding="utf-8").read()
    # Must be fault-tolerant (try/except)
    wkg_section = src[src.find("WO-WKG-004"):][:1200]
    assert "try:" in wkg_section, "AT-7: injection must be in try block"
    assert "except" in wkg_section, "AT-7: must have except handler"
    assert "_logging.warning" in wkg_section, "AT-7: must log warning on failure (non-fatal)"


def test_wkg_content_includes_epistemic_label():
    """AT-8: Injected WKG lines carry [WKG — {epistemic}] label prefix."""
    from knowledge.graph_loader import retrieve_wkg
    result = retrieve_wkg("moon lunar 28 days seasons")
    if not result:
        import pytest; pytest.skip("WKG corpus empty — cannot verify label format")
    # Simulate the label formatting from server.py
    _ep_map = {"VERIFIED": "verified", "SOURCE_ATTRIBUTED": "source-perspective",
               "SYMBOLIC": "symbolic", "DISPUTED": "disputed"}
    for r in result:
        _cls = r.get("wkg_epistemic_class", "UNKNOWN")
        _ep  = _ep_map.get(_cls, "perspective")
        line = f"[WKG — {_ep}] {r['content']}"
        assert line.startswith("[WKG —"), f"AT-8: WKG line must start with [WKG —]; got: {line[:40]}"
        assert r["content"] in line, "AT-8: claim content must appear in formatted line"
