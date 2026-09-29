"""
tests/test_wo043_bus_isolation.py — WO-043 faculty bus isolation

Spec: WO-043 — Faculty bus isolation; stop "weave it in" fact injection;
      tool outputs must not be asserted as personal truths in the /chat prompt path.

AT-1  Old "use it naturally if the moment feels right" ambient phrase removed from server.py
AT-2  Ambient injection now uses "CURIOUS FACT" framing (not bare "FACT AVAILABLE")
AT-3  ANTI-FABRICATION block covers area-level weather/forecast facts
AT-4  ANTI-FABRICATION block explicitly bans "X in your studio" style assertions
AT-5  py_compile clean on server.py
"""
import os
import sys
import py_compile
import pytest

_ROOT = os.path.join(os.path.dirname(__file__), "..")
_SERVER_PY = os.path.join(_ROOT, "server.py")


def _server_src() -> str:
    return open(_SERVER_PY, encoding="utf-8").read()


# ── AT-1 ──────────────────────────────────────────────────────────────────────

def test_at1_ambient_inject_old_phrase_removed():
    """
    The original bus-contamination phrase "use it naturally in speak if the moment
    feels right" must be absent — it caused eLo to assert tool outputs as personal truths.
    """
    src = _server_src()
    assert "use it naturally in speak if the moment feels right" not in src, (
        "AT-1 FAIL: old ambient injection phrase still present in server.py — "
        "this leaks tool facts into eLo's first-person voice without attribution"
    )


# ── AT-2 ──────────────────────────────────────────────────────────────────────

def test_at2_curious_fact_framing_present():
    """
    Ambient injection must use "CURIOUS FACT" framing so eLo introduces
    external data as a fact it encountered, not a personal observation.
    """
    src = _server_src()
    assert "CURIOUS FACT" in src, (
        "AT-2 FAIL: 'CURIOUS FACT' framing not found in server.py — "
        "ambient injection may still be presented as first-person truth"
    )


# ── AT-3 ──────────────────────────────────────────────────────────────────────

def test_at3_anti_fabrication_covers_area_level_weather():
    """
    ANTI-FABRICATION block must guard against area-level weather/forecast assertions —
    eLo cannot assert "it's raining in Hackney Wick" from a borough-level reading.
    """
    src = _server_src().lower()
    assert "area-level" in src or "area level" in src, (
        "AT-3 FAIL: area-level weather anti-fabrication not found in server.py"
    )


# ── AT-4 ──────────────────────────────────────────────────────────────────────

def test_at4_anti_fabrication_bans_studio_assertions():
    """
    ANTI-FABRICATION block must explicitly prohibit 'X in your studio' assertions.
    The guard must appear within 200 chars of a NEVER/never prohibition.
    """
    src = _server_src()
    idx = src.find("your studio")
    assert idx != -1, "AT-4 FAIL: 'your studio' anti-fabrication guard not found in server.py"

    window = src[max(0, idx - 200):idx + 100]
    assert "NEVER" in window or "never" in window, (
        "AT-4 FAIL: 'your studio' found but no NEVER prohibition within 200 chars"
    )


# ── AT-5 ──────────────────────────────────────────────────────────────────────

def test_at5_server_compiles_cleanly():
    """server.py must compile cleanly — no syntax errors introduced."""
    try:
        py_compile.compile(_SERVER_PY, doraise=True)
    except py_compile.PyCompileError as e:
        pytest.fail(f"AT-5 FAIL: server.py does not compile: {e}")
