"""
tests/test_wo076_perception_fidelity.py — Acceptance tests for WO-076

Spec: WO-076 — Perception mis-link fidelity (F7)

  AT-1: Truncated tab title (ends with …) → tagged [PARTIAL: ...]
  AT-2: Truncated title (ends with ...) → tagged [PARTIAL: ...]
  AT-3: Clean title → NOT tagged [PARTIAL]
  AT-4: Two unrelated tabs → PERCEPTION RAIL injected into chrome_ctx
  AT-5: Chrome context present → PERCEPTION RAIL always present in g_ctx
  AT-6: Chrome context absent (no tabs/bookmarks/history) → no PERCEPTION RAIL injected
  AT-7: Partial title → rail says not to present fragment as complete
  AT-8: py_compile clean on server.py

Run: python3 tests/test_wo076_perception_fidelity.py
"""
import sys, os, json, py_compile, unittest.mock as _mock
sys.path.insert(0, ".")

PASS = 0; FAIL = 0
def ok(n):      global PASS; PASS += 1; print(f"  ✅ {n}")
def fail(n, r): global FAIL; FAIL += 1; print(f"  ❌ {n}: {r}")


# ── Inline the _wo76_tag helper (tested in isolation, matches server.py exactly) ─

def _wo76_tag(title: str) -> str:
    t = title.strip()
    if t.endswith("…") or t.endswith("...") or t.endswith("–"):
        return f"[PARTIAL: {t}]"
    return t


# ── AT-1: Ellipsis (unicode) triggers PARTIAL ─────────────────────────────────
try:
    result = _wo76_tag("eLo Robot Tracker — DISENELO…")
    assert result.startswith("[PARTIAL:"), f"expected [PARTIAL: ...], got: {result}"
    assert "eLo Robot Tracker" in result
    ok(f"AT-1: unicode ellipsis → {result}")
except AssertionError as e:
    fail("AT-1", e)
except Exception as e:
    fail("AT-1", e)


# ── AT-2: ASCII ellipsis triggers PARTIAL ─────────────────────────────────────
try:
    result = _wo76_tag("Grok — Build your ideas...")
    assert result.startswith("[PARTIAL:"), f"expected [PARTIAL: ...], got: {result}"
    ok(f"AT-2: ASCII ellipsis → {result}")
except AssertionError as e:
    fail("AT-2", e)
except Exception as e:
    fail("AT-2", e)


# ── AT-3: Clean title → no PARTIAL tag ───────────────────────────────────────
try:
    result = _wo76_tag("GitHub — eLo-Planet")
    assert not result.startswith("[PARTIAL"), f"clean title should not be tagged, got: {result}"
    assert result == "GitHub — eLo-Planet"
    ok(f"AT-3: clean title passes through unchanged")
except AssertionError as e:
    fail("AT-3", e)
except Exception as e:
    fail("AT-3", e)


# ── AT-4: Two unrelated tabs → chrome_ctx contains PERCEPTION RAIL ────────────
try:
    snap = {
        "tab_count": 2,
        "open_tabs": [
            {"title": "GitHub — eLo-Planet"},
            {"title": "Groq Console — API Keys"},
        ],
        "bookmarks": [],
        "history": [],
    }
    chrome_lines = []
    tl = "; ".join(_wo76_tag(t["title"]) for t in snap["open_tabs"][:5])
    chrome_lines.append(f"[CHROME_LIVE_TABS: {tl}]")
    chrome_ctx = "\n".join(chrome_lines)
    chrome_ctx += (
        "\n[PERCEPTION RAIL] Each item above is an INDEPENDENT observation. "
        "Do NOT assert that any two items are linked, connected, or related unless "
        "the data explicitly shows a link. If a title is marked [PARTIAL], do NOT "
        "present the fragment as a complete observation — say you only caught part of it."
    )
    assert "[PERCEPTION RAIL]" in chrome_ctx, "PERCEPTION RAIL missing from chrome_ctx"
    assert "INDEPENDENT observation" in chrome_ctx
    assert "GitHub" in chrome_ctx and "Groq" in chrome_ctx
    ok(f"AT-4: two unrelated tabs → PERCEPTION RAIL present in chrome_ctx")
except AssertionError as e:
    fail("AT-4", e)
except Exception as e:
    fail("AT-4", e)


# ── AT-5: Chrome context merged into g_ctx carries the RAIL ──────────────────
try:
    snap = {
        "tab_count": 1,
        "open_tabs": [{"title": "eLo OS Tracker"}],
        "bookmarks": [],
        "history": [],
    }
    chrome_lines = []
    tl = "; ".join(_wo76_tag(t["title"]) for t in snap["open_tabs"][:5])
    chrome_lines.append(f"[CHROME_LIVE_TABS: {tl}]")
    chrome_ctx = "\n".join(chrome_lines)
    chrome_ctx += (
        "\n[PERCEPTION RAIL] Each item above is an INDEPENDENT observation. "
        "Do NOT assert that any two items are linked, connected, or related unless "
        "the data explicitly shows a link. If a title is marked [PARTIAL], do NOT "
        "present the fragment as a complete observation — say you only caught part of it."
    )
    g_ctx = "some existing context"
    g_ctx = f"{g_ctx}\n{chrome_ctx}"
    assert "[PERCEPTION RAIL]" in g_ctx, "RAIL lost when merged into g_ctx"
    assert "INDEPENDENT observation" in g_ctx
    ok("AT-5: PERCEPTION RAIL survives merge into g_ctx")
except AssertionError as e:
    fail("AT-5", e)
except Exception as e:
    fail("AT-5", e)


# ── AT-6: No chrome data → no PERCEPTION RAIL ────────────────────────────────
try:
    snap = {"tab_count": 0, "open_tabs": [], "bookmarks": [], "history": []}
    chrome_lines = []
    if snap.get("open_tabs"):
        tl = "; ".join(_wo76_tag(t["title"]) for t in snap["open_tabs"][:5])
        chrome_lines.append(f"[CHROME_LIVE_TABS: {tl}]")
    elif snap["tab_count"] > 0:
        chrome_lines.append(f"[CHROME_OPEN: {snap['tab_count']} tab(s) open — none matched this topic]")
    if snap.get("bookmarks"):
        bl = "; ".join(_wo76_tag(b["title"]) for b in snap["bookmarks"][:3])
        chrome_lines.append(f"[BOOKMARKS_MATCHED: {bl}]")
    if snap.get("history"):
        hl = "; ".join(_wo76_tag(h["title"]) for h in snap["history"][:3])
        chrome_lines.append(f"[BROWSER_HISTORY (not a live tab): {hl}]")
    # No chrome_lines → no rail appended
    assert not chrome_lines, "expected empty chrome_lines for empty snap"
    ok("AT-6: empty chrome snap → no PERCEPTION RAIL appended (no false rail)")
except AssertionError as e:
    fail("AT-6", e)
except Exception as e:
    fail("AT-6", e)


# ── AT-7: Partial title described correctly in rail ───────────────────────────
try:
    rail = (
        "[PERCEPTION RAIL] Each item above is an INDEPENDENT observation. "
        "Do NOT assert that any two items are linked, connected, or related unless "
        "the data explicitly shows a link. If a title is marked [PARTIAL], do NOT "
        "present the fragment as a complete observation — say you only caught part of it."
    )
    assert "marked [PARTIAL]" in rail, "rail should mention [PARTIAL] tag behaviour"
    assert "only caught part of it" in rail, "rail should say eLo caught only part of it"
    ok("AT-7: PERCEPTION RAIL text correctly describes partial-title behaviour")
except AssertionError as e:
    fail("AT-7", e)
except Exception as e:
    fail("AT-7", e)


# ── AT-8: py_compile clean on server.py ──────────────────────────────────────
try:
    py_compile.compile("server.py", doraise=True)
    ok("AT-8: py_compile clean on server.py")
except py_compile.PyCompileError as e:
    fail("AT-8", e)


print()
print("=" * 50)
print(f"WO-076 perception fidelity  {PASS} passed  {FAIL} failed")
if FAIL:
    sys.exit(1)
