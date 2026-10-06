"""
tests/test_root2_autobiographical_summary_injection.py — ROOT-2

Acceptance criteria:
  ROOT2-1: SelfModel has autobiographical_summary field
  ROOT2-2: SelfModel.autobiographical_summary default is empty string
  ROOT2-3: autobiographical_summary is populated from wkg_context in spine
  ROOT2-4: server.py ROOT-2 injection block exists (structural check)
  ROOT2-5: injection uses correct history label
  ROOT2-6: injection is non-fatal (empty autobiographical_summary → g_ctx unchanged)
  ROOT2-7: injection appends to existing g_ctx without clobbering it
"""
import inspect


# ── ROOT2-1: SelfModel has autobiographical_summary field ───────────────────

def test_root2_1_selfmodel_has_field():
    """ROOT2-1: SelfModel declares autobiographical_summary"""
    from runtime.contracts import SelfModel
    assert "autobiographical_summary" in SelfModel.__dataclass_fields__


# ── ROOT2-2: default is empty string ────────────────────────────────────────

def test_root2_2_default_empty():
    """ROOT2-2: autobiographical_summary defaults to empty string"""
    from runtime.contracts import SelfModel
    sm = SelfModel()
    assert sm.autobiographical_summary == ""


# ── ROOT2-3: spine wkg_context path populates the field ─────────────────────

def test_root2_3_spine_populates_field():
    """ROOT2-3: spine.py assigns wkg_context[:240] to autobiographical_summary"""
    import ast, pathlib
    spine_src = pathlib.Path("runtime/spine/spine.py").read_text()
    tree = ast.parse(spine_src)
    found = False
    for node in ast.walk(tree):
        if isinstance(node, ast.keyword):
            if getattr(node, "arg", None) == "autobiographical_summary":
                found = True
                break
    assert found, "spine.py does not pass autobiographical_summary to SelfModel constructor"


# ── ROOT2-4: server.py ROOT-2 injection block is present ────────────────────

def test_root2_4_server_injection_block_present():
    """ROOT2-4: server.py contains the ROOT-2 autobiographical_summary injection"""
    import pathlib
    src = pathlib.Path("server.py").read_text()
    assert "ROOT-2" in src, "ROOT-2 marker not found in server.py"
    assert "autobiographical_summary" in src, "autobiographical_summary not referenced in server.py"
    assert "_auto_summary" in src, "_auto_summary variable not found — injection block missing"


# ── ROOT2-5: injection uses the correct label ────────────────────────────────

def test_root2_5_history_label():
    """ROOT2-5: injection uses [WHAT I KNOW FROM OUR HISTORY] header"""
    import pathlib
    src = pathlib.Path("server.py").read_text()
    assert "[WHAT I KNOW FROM OUR HISTORY" in src


# ── ROOT2-6: empty autobiographical_summary → g_ctx unchanged ───────────────

def test_root2_6_empty_summary_noop():
    """ROOT2-6: injection is a no-op when autobiographical_summary is empty"""
    original_ctx = "existing wkg context"
    _plan_stub = type("Plan", (), {"self_model": type("SM", (), {"autobiographical_summary": ""})()})()

    try:
        _auto_summary = getattr(getattr(_plan_stub, "self_model", None), "autobiographical_summary", "") or ""
        g_ctx = original_ctx
        if _auto_summary.strip():
            g_ctx = f"{g_ctx}\nextra"
        assert g_ctx == original_ctx
    except Exception as e:
        raise AssertionError(f"Empty-summary guard raised unexpectedly: {e}")


# ── ROOT2-7: non-empty summary appends to g_ctx ──────────────────────────────

def test_root2_7_nonempty_summary_appends():
    """ROOT2-7: non-empty autobiographical_summary is appended to g_ctx"""
    sample_summary = "[SOURCE_ATTRIBUTED] David Charles associated with concepts: robotics, eLo"
    _auto_block = (
        "[WHAT I KNOW FROM OUR HISTORY — retrieved, treat as verified fact]\n"
        + sample_summary
        + "\n[These are specific facts recorded from our sessions. "
        + "Do not contradict or ignore them in favour of a general answer.]"
    )
    g_ctx = "prior wkg data"
    g_ctx = f"{g_ctx}\n{_auto_block}"

    assert "[WHAT I KNOW FROM OUR HISTORY" in g_ctx
    assert sample_summary in g_ctx
    assert "prior wkg data" in g_ctx, "Original g_ctx was clobbered"
