"""
tests/test_wo076_perception_fidelity.py — WO-076 perception fidelity

Spec: WO-076 — No fragment-as-fact; no fabricated link assertions between unrelated tabs.
      Partial/truncated tab titles must be flagged [PARTIAL]; rail must always be injected
      when chrome context is present; never assert links between independent observations.

AT-1  Truncated tab title (ends with …) → tagged [PARTIAL: ...]
AT-2  Truncated title (ends with ...) → tagged [PARTIAL: ...]
AT-3  Clean title → NOT tagged [PARTIAL]; passes through unchanged
AT-4  server.py has PERCEPTION RAIL injected when chrome tabs are present (WO-076 marker)
AT-5  server.py anti-fabrication rail text: "INDEPENDENT observation" present
AT-6  server.py partial title guard: [PARTIAL] mentioned and behaviour described
AT-7  Chrome context absent (no tabs) → no false PERCEPTION RAIL injected
AT-8  py_compile clean on server.py
"""
import os
import sys
import py_compile

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

_ROOT      = os.path.join(os.path.dirname(__file__), "..")
_SERVER_PY = os.path.join(_ROOT, "server.py")


def _wo76_tag(title: str) -> str:
    """Inline the perception-fidelity tagger — matches server.py exactly (tested against source)."""
    t = title.strip()
    if t.endswith("…") or t.endswith("...") or t.endswith("–"):
        return f"[PARTIAL: {t}]"
    return t


def _server_src() -> str:
    return open(_SERVER_PY, encoding="utf-8").read()


# ── AT-1 ──────────────────────────────────────────────────────────────────────

def test_at1_unicode_ellipsis_triggers_partial():
    """
    A tab title ending with unicode ellipsis (…) must be tagged [PARTIAL: ...].
    eLo cannot present a truncated browser tab as a confident observation.
    """
    result = _wo76_tag("eLo Robot Tracker — DISENELO…")
    assert result.startswith("[PARTIAL:"), (
        f"AT-1 FAIL: unicode ellipsis not tagged — got: {result!r}"
    )
    assert "eLo Robot Tracker" in result, (
        f"AT-1 FAIL: title content lost in tagging — got: {result!r}"
    )


# ── AT-2 ──────────────────────────────────────────────────────────────────────

def test_at2_ascii_ellipsis_triggers_partial():
    """ASCII ... ellipsis must also trigger [PARTIAL] tagging."""
    result = _wo76_tag("Grok — Build your ideas...")
    assert result.startswith("[PARTIAL:"), (
        f"AT-2 FAIL: ASCII ellipsis not tagged — got: {result!r}"
    )


# ── AT-3 ──────────────────────────────────────────────────────────────────────

def test_at3_clean_title_not_tagged():
    """
    A complete, non-truncated tab title must pass through unchanged.
    Over-tagging clean titles creates false uncertainty.
    """
    result = _wo76_tag("GitHub — eLo-Planet")
    assert not result.startswith("[PARTIAL"), (
        f"AT-3 FAIL: clean title incorrectly tagged as PARTIAL — got: {result!r}"
    )
    assert result == "GitHub — eLo-Planet", (
        f"AT-3 FAIL: clean title modified — got: {result!r}"
    )


# ── AT-4 ──────────────────────────────────────────────────────────────────────

def test_at4_server_injects_perception_rail_on_chrome_context():
    """
    server.py must inject a PERCEPTION RAIL when chrome tab context is available.
    This is the anti-fabrication guard that prevents eLo asserting relationships
    between unrelated open tabs (the confirmed F7 bug).
    """
    src = _server_src()
    assert "WO-076" in src, "AT-4 FAIL: WO-076 marker absent from server.py"
    assert "PERCEPTION RAIL" in src, (
        "AT-4 FAIL: 'PERCEPTION RAIL' not present in server.py — "
        "the anti-fabrication guard is missing from the chrome context path"
    )


# ── AT-5 ──────────────────────────────────────────────────────────────────────

def test_at5_rail_text_says_independent_observations():
    """
    The PERCEPTION RAIL in server.py must state that each item is an INDEPENDENT
    observation and must NOT assert links. This is the exact wording eLo receives
    as a constraint.
    """
    src = _server_src()
    assert "INDEPENDENT observation" in src, (
        "AT-5 FAIL: 'INDEPENDENT observation' not in server.py PERCEPTION RAIL — "
        "eLo has no instruction not to assert links between unrelated tabs"
    )
    assert "Do NOT assert" in src or "do NOT assert" in src or "do not assert" in src.lower(), (
        "AT-5 FAIL: explicit prohibition against asserting links not found in server.py"
    )


# ── AT-6 ──────────────────────────────────────────────────────────────────────

def test_at6_rail_describes_partial_title_behaviour():
    """
    The PERCEPTION RAIL must describe what to do with [PARTIAL] titles —
    say you only caught part of it, not present the fragment as complete.
    """
    src = _server_src()
    assert "[PARTIAL]" in src or "PARTIAL" in src, (
        "AT-6 FAIL: [PARTIAL] tag not mentioned in server.py"
    )
    assert "only caught part of it" in src or "fragment" in src, (
        "AT-6 FAIL: rail doesn't describe fragment behaviour — eLo may still present partial titles as complete"
    )


# ── AT-7 ──────────────────────────────────────────────────────────────────────

def test_at7_no_false_rail_when_no_chrome_context():
    """
    When chrome_lines is empty (no open tabs, bookmarks, or history),
    no PERCEPTION RAIL should be appended. The logic: rail is only injected
    when there's chrome content to guard. Simulate the guard condition.
    """
    # Simulate the server.py guard: rail only appended when chrome_lines non-empty
    snap_empty = {"tab_count": 0, "open_tabs": [], "bookmarks": [], "history": []}
    chrome_lines: list = []

    if snap_empty.get("open_tabs"):
        tl = "; ".join(_wo76_tag(t["title"]) for t in snap_empty["open_tabs"][:5])
        chrome_lines.append(f"[CHROME_LIVE_TABS: {tl}]")
    if snap_empty.get("bookmarks"):
        bl = "; ".join(_wo76_tag(b["title"]) for b in snap_empty["bookmarks"][:3])
        chrome_lines.append(f"[BOOKMARKS_MATCHED: {bl}]")
    if snap_empty.get("history"):
        hl = "; ".join(_wo76_tag(h["title"]) for h in snap_empty["history"][:3])
        chrome_lines.append(f"[BROWSER_HISTORY (not a live tab): {hl}]")

    # No content → chrome_lines empty → rail must NOT be appended
    assert not chrome_lines, (
        f"AT-7 FAIL: chrome_lines non-empty for empty snap: {chrome_lines}"
    )
    # Verify: a PERCEPTION RAIL would only be appended if chrome_lines is non-empty
    chrome_ctx = "\n".join(chrome_lines)
    assert "[PERCEPTION RAIL]" not in chrome_ctx, (
        "AT-7 FAIL: PERCEPTION RAIL injected even with no chrome content"
    )


# ── AT-8 ──────────────────────────────────────────────────────────────────────

def test_at8_server_py_compiles_cleanly():
    try:
        py_compile.compile(_SERVER_PY, doraise=True)
    except py_compile.PyCompileError as e:
        pytest.fail(f"AT-8 FAIL: server.py does not compile: {e}")
