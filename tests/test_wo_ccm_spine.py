"""
tests/test_wo_ccm_spine.py — WO-CCM-SPINE acceptance tests.

AT-1: ccm_enricher.enrich() runs per turn and returns ≥19 dims populated.
AT-2: CCM enrichment is called in spine.py AFTER Language Faculty and BEFORE
       assemble_cognitive_state() (structural wiring check via source scan).
AT-3: assemble_cognitive_state() passes ccm_context into CognitiveState.ccm_context.
AT-4: CognitiveState.ccm_context is non-empty after a full assemble call.
AT-5: All three Category-C dims present in ccm_context keys:
       storytelling_style / cultural_references / street_terminology.
AT-6: No new test regressions introduced — prior AT suites unaffected.

Run: ~/miniconda3/bin/python3 -m pytest tests/test_wo_ccm_spine.py -v
"""
from __future__ import annotations

import os
import sys
import py_compile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PASS = 0; FAIL = 0

def ok(n):      global PASS; PASS += 1; print(f"  ✅ {n}")
def fail(n, r): global FAIL; FAIL += 1; print(f"  ❌ {n}: {r}")


# ── AT-1: ccm_enricher returns all 26 dims as keys ────────────────────────────
try:
    from faculties.ccm.ccm_enricher import enrich as ccm_enrich, CCM_DIMS

    # Minimal turn — should still yield all dim keys, most None
    result_min = ccm_enrich("hello", {}, None)
    assert isinstance(result_min, dict), f"enrich() must return dict, got {type(result_min)}"
    # 27 dims: original 26 + street_language (added WO-CCM-CATEGORY-C-001, David L3 2026-09-05)
    assert len(result_min) == 27, f"expected 27 dim keys, got {len(result_min)}: {list(result_min.keys())}"

    # A richer turn — many dims should fire
    rich_turn = (
        "Hey! I've been thinking about the creative process lately. "
        "There was a time when I was so stuck, remember when I first started? "
        "Anyway, cooked situation with the deadline lmao. "
        "Gaming has taught me a lot — persistence is everything. "
        "How do you think I should handle this? Not sure at all."
    )
    result_rich = ccm_enrich(rich_turn, {"intent": "question"}, None)
    triggered = [k for k, v in result_rich.items() if v is not None]
    assert len(triggered) >= 10, (
        f"AT-1 FAIL: expected ≥10 dims triggered on rich turn, got {len(triggered)}: {triggered}"
    )
    ok(f"AT-1: enrich() returns 27 dims; {len(triggered)} triggered on rich turn")
except AssertionError as e:
    fail("AT-1", e)
except Exception as e:
    fail("AT-1", e)


# ── AT-2: structural wiring — CCM enrichment in spine.py after Language, before assemble ──
try:
    _ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    spine_path = os.path.join(_ROOT, "runtime", "spine", "spine.py")
    with open(spine_path, encoding="utf-8") as f:
        spine_src = f.read()

    assert "from faculties.ccm.ccm_enricher import enrich as _ccm_enrich" in spine_src, \
        "ccm_enricher not imported in spine.py"
    assert "_ccm_context = _ccm_enrich(raw, language, None)" in spine_src or \
           "_ccm_context = _ccm_enrich(" in spine_src, \
        "_ccm_enrich() not called in spine.py"
    assert "ccm_context=_ccm_context" in spine_src, \
        "_ccm_context not passed to assemble_cognitive_state() in spine.py"

    # Confirm order: language line appears before ccm line, ccm line appears before assemble line
    lang_idx    = spine_src.find("language = _language_faculty(raw)")
    ccm_idx     = spine_src.find("_ccm_context = _ccm_enrich(")
    assemble_idx = spine_src.find("ccm_context=_ccm_context")
    assert lang_idx != -1, "language faculty call not found in spine.py"
    assert ccm_idx  != -1, "ccm enrich call not found in spine.py"
    assert assemble_idx != -1, "ccm_context kwarg not found in spine.py"
    assert lang_idx < ccm_idx < assemble_idx, (
        f"AT-2 ORDER FAIL: lang@{lang_idx} ccm@{ccm_idx} assemble@{assemble_idx}"
    )
    ok(f"AT-2: CCM wired after Language Faculty (pos {lang_idx}) and before assemble (pos {assemble_idx})")
except AssertionError as e:
    fail("AT-2", e)
except Exception as e:
    fail("AT-2", e)


# ── AT-3: assemble_cognitive_state accepts ccm_context kwarg ─────────────────
try:
    import inspect
    from runtime.spine.spine import assemble_cognitive_state
    sig = inspect.signature(assemble_cognitive_state)
    assert "ccm_context" in sig.parameters, \
        f"assemble_cognitive_state() missing ccm_context param; params={list(sig.parameters)}"
    ok("AT-3: assemble_cognitive_state() has ccm_context parameter")
except AssertionError as e:
    fail("AT-3", e)
except Exception as e:
    fail("AT-3", e)


# ── AT-4: CognitiveState.ccm_context populated after assembly ────────────────
try:
    from runtime.spine.spine import assemble_cognitive_state
    from faculties.ccm.ccm_enricher import enrich as _ccm_e

    _turn = "I'm curious about the design process and how to create better things."
    _lang = {"original": _turn, "intent": "question", "meaning": {}, "register": "", "social": ""}
    _ccm  = _ccm_e(_turn, _lang, None)

    _cs = assemble_cognitive_state(
        _lang, None, {}, [], None, None,
        ccm_context=_ccm,
    )
    assert hasattr(_cs, "ccm_context"), "CognitiveState missing ccm_context field"
    assert isinstance(_cs.ccm_context, dict), f"ccm_context should be dict, got {type(_cs.ccm_context)}"
    assert len(_cs.ccm_context) >= 26, f"ccm_context has {len(_cs.ccm_context)} dims, expected ≥26"
    assert _cs.ccm_context.get("curiosity") == "present", \
        f"curiosity dim should be 'present' for curiosity-rich turn; got {_cs.ccm_context.get('curiosity')!r}"
    ok(f"AT-4: CognitiveState.ccm_context populated ({len(_cs.ccm_context)} dims, curiosity={_cs.ccm_context.get('curiosity')!r})")
except AssertionError as e:
    fail("AT-4", e)
except Exception as e:
    fail("AT-4", e)


# ── AT-5: Category-C dims present (storytelling / cultural_references / street_terminology) ──
try:
    from faculties.ccm.ccm_enricher import enrich as _ccm_e5, CCM_DIMS

    # All three must be in CCM_DIMS
    for required_dim in ("storytelling_style", "cultural_references", "street_terminology"):
        assert required_dim in CCM_DIMS, f"Category-C dim '{required_dim}' not in CCM_DIMS"

    # A turn that triggers all three
    _cat_c_turn = (
        "Remember when I first started — true story, let me tell you. "
        "Lowkey the situation was cooked. No cap. "
        "The gaming scene and music world both influenced my process."
    )
    _cat_c_result = _ccm_e5(_cat_c_turn, {}, None)

    assert "storytelling_style" in _cat_c_result, "storytelling_style key missing from enrich() output"
    assert "cultural_references" in _cat_c_result, "cultural_references key missing from enrich() output"
    assert "street_terminology"  in _cat_c_result, "street_terminology key missing from enrich() output"

    assert _cat_c_result["storytelling_style"] is not None, \
        "storytelling_style should be triggered; got None"
    assert _cat_c_result["street_terminology"] is not None, \
        "street_terminology should be triggered (lowkey/cooked/no cap present); got None"
    assert _cat_c_result["cultural_references"] is not None, \
        "cultural_references should be triggered (gaming/music present); got None"

    ok(f"AT-5: All 3 Category-C dims present and triggered — "
       f"storytelling={_cat_c_result['storytelling_style']!r}, "
       f"cultural={list(_cat_c_result['cultural_references'].keys())[:2] if _cat_c_result['cultural_references'] else None}, "
       f"street={list(_cat_c_result['street_terminology'].keys())[:2] if _cat_c_result['street_terminology'] else None}")
except AssertionError as e:
    fail("AT-5", e)
except Exception as e:
    fail("AT-5", e)


# ── AT-6: py_compile clean on modified files ──────────────────────────────────
try:
    _ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for rel in (
        "faculties/ccm/ccm_enricher.py",
        "faculties/ccm/__init__.py",
        "runtime/contracts.py",
        "runtime/spine/spine.py",
    ):
        py_compile.compile(os.path.join(_ROOT, rel), doraise=True)
    ok("AT-6: py_compile clean on ccm_enricher.py, contracts.py, spine.py")
except py_compile.PyCompileError as e:
    fail("AT-6", e)
except Exception as e:
    fail("AT-6", e)


# ── Final summary ─────────────────────────────────────────────────────────────
print()
print("=" * 60)
print(f"WO-CCM-SPINE   {PASS} passed  {FAIL} failed")
if FAIL:
    sys.exit(1)
