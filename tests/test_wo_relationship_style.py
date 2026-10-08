"""
tests/test_wo_relationship_style.py — WO-RELATIONSHIP-STYLE acceptance tests.

AT-1: NEW mode — no assumed-familiarity callbacks ("as we discussed", etc.) appear
       in style cues; relationship_mode derives correctly from low familiarity.
AT-2: ESTABLISHED mode — no setup/scaffolding phrases in forbidden list; same test
       input with higher session count yields established mode, more direct cues.
AT-3: IN_CONFLICT mode — performative care phrases ("I hear you", "that sounds hard")
       are forbidden; raw conflict signal triggers in_conflict mode.
AT-4: POST_CONFLICT mode — over-apologetic phrases forbidden; repair signal triggers
       post_conflict mode.
AT-5: Core character preserved — style cues never remove; all modes have same fallback
       keys; no mode has an empty get_style() result.

Run: ~/miniconda3/bin/python3 tests/test_wo_relationship_style.py
"""
from __future__ import annotations

import os
import sys
import py_compile
import types

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PASS = 0; FAIL = 0

def ok(n):      global PASS; PASS += 1; print(f"  ✅ {n}")
def fail(n, r): global FAIL; FAIL += 1; print(f"  ❌ {n}: {r}")


# ── AT-1: NEW mode — no assumed-familiarity callbacks; mode derives from familiarity ─
try:
    from kernel.relationship_register import get_style
    from runtime.spine.relationship_faculty import _derive_relationship_mode

    # familiarity 0.20 → NEW
    mode = _derive_relationship_mode("hello, what can you do?", familiarity=0.20)
    assert mode == "new", f"Expected 'new' for familiarity 0.20, got {mode!r}"

    style = get_style("new")
    assert "forbidden" in style, "get_style('new') missing 'forbidden' key"

    assumed_callbacks = ["as we discussed", "remember when", "like last time", "you said"]
    style_forbidden = [f.lower() for f in style["forbidden"]]
    for cb in assumed_callbacks:
        assert cb in style_forbidden, (
            f"AT-1: assumed-familiarity phrase {cb!r} not in forbidden list for 'new' mode"
        )

    ok(f"AT-1: NEW mode — familiarity=0.20 → mode={mode!r}; assumed-familiarity callbacks forbidden")
except AssertionError as e:
    fail("AT-1", e)
except Exception as e:
    fail("AT-1", e)


# ── AT-2: ESTABLISHED mode — setup phrases forbidden; derived from high familiarity ─
try:
    from kernel.relationship_register import get_style as _get_style2
    from runtime.spine.relationship_faculty import _derive_relationship_mode as _drm2

    # familiarity 0.75 → ESTABLISHED
    mode2 = _drm2("write the plan", familiarity=0.75)
    assert mode2 == "established", f"Expected 'established' for familiarity 0.75, got {mode2!r}"

    style2 = _get_style2("established")
    setup_phrases = ["so what you mean is", "just to clarify", "let me explain", "to put it simply"]
    style2_forbidden = [f.lower() for f in style2["forbidden"]]
    for sp in setup_phrases:
        assert sp in style2_forbidden, (
            f"AT-2: setup phrase {sp!r} not in 'established' forbidden list"
        )

    # texture should mention "direct" or "direct"
    assert "direct" in style2.get("texture", "").lower(), (
        f"AT-2: 'established' texture should mention directness; got: {style2.get('texture')!r}"
    )

    ok(f"AT-2: ESTABLISHED mode — familiarity=0.75 → mode={mode2!r}; setup scaffolding forbidden")
except AssertionError as e:
    fail("AT-2", e)
except Exception as e:
    fail("AT-2", e)


# ── AT-3: IN_CONFLICT mode — performative care phrases forbidden; conflict signal triggers ─
try:
    from kernel.relationship_register import get_style as _get_style3
    from runtime.spine.relationship_faculty import _derive_relationship_mode as _drm3

    # Conflict signal in raw → in_conflict regardless of familiarity
    mode3 = _drm3("that's wrong, you keep doing this", familiarity=0.80)
    assert mode3 == "in_conflict", f"Expected 'in_conflict', got {mode3!r}"

    style3 = _get_style3("in_conflict")
    care_phrases = ["i hear you", "that sounds hard", "i understand how you feel",
                    "i'm so sorry", "i apologise for"]
    style3_forbidden = [f.lower() for f in style3["forbidden"]]
    for cp in care_phrases:
        assert cp in style3_forbidden, (
            f"AT-3: performative care phrase {cp!r} not in 'in_conflict' forbidden list"
        )

    ok(f"AT-3: IN_CONFLICT — conflict signal → mode={mode3!r}; performative care phrases forbidden")
except AssertionError as e:
    fail("AT-3", e)
except Exception as e:
    fail("AT-3", e)


# ── AT-4: POST_CONFLICT — over-apologetic phrases forbidden; repair signal triggers ─
try:
    from kernel.relationship_register import get_style as _get_style4
    from runtime.spine.relationship_faculty import _derive_relationship_mode as _drm4

    # Repair signal → post_conflict (checked before familiarity thresholds)
    mode4 = _drm4("it's fine, let's move on", familiarity=0.65)
    assert mode4 == "post_conflict", f"Expected 'post_conflict', got {mode4!r}"

    style4 = _get_style4("post_conflict")
    apology_phrases = ["i promise i'll", "i'll make it up", "never again", "i'm really sorry"]
    style4_forbidden = [f.lower() for f in style4["forbidden"]]
    for ap in apology_phrases:
        assert ap in style4_forbidden, (
            f"AT-4: over-apologetic phrase {ap!r} not in 'post_conflict' forbidden list"
        )

    assert "steady" in style4.get("texture", "").lower() or "over-correction" in style4.get("texture", ""), (
        f"AT-4: 'post_conflict' texture should describe steady/no-over-correction; got: {style4.get('texture')!r}"
    )

    ok(f"AT-4: POST_CONFLICT — repair signal → mode={mode4!r}; over-apologetic phrases forbidden")
except AssertionError as e:
    fail("AT-4", e)
except Exception as e:
    fail("AT-4", e)


# ── AT-5: Core character preserved — all modes have full keys; no mode returns empty ─
try:
    from kernel.relationship_register import get_style as _get_style5, _REGISTRY

    _ALL_MODES = ["new", "developing", "established", "in_conflict", "post_conflict"]
    _REQUIRED_KEYS = {"forbidden", "required", "texture"}

    for m in _ALL_MODES:
        s = _get_style5(m)
        assert s, f"AT-5: get_style({m!r}) returned empty/falsy"
        missing = _REQUIRED_KEYS - set(s.keys())
        assert not missing, f"AT-5: mode {m!r} missing keys: {missing}"
        assert isinstance(s["forbidden"], list), f"AT-5: mode {m!r} 'forbidden' must be list"
        assert isinstance(s["required"], list), f"AT-5: mode {m!r} 'required' must be list"
        assert isinstance(s["texture"], str) and s["texture"], \
            f"AT-5: mode {m!r} 'texture' must be non-empty string"

    # Unknown mode falls back gracefully — does not raise
    fallback = _get_style5("__unknown__")
    assert fallback, "AT-5: unknown mode should fall back to developing, not return empty"

    ok(f"AT-5: Core character preserved — all {len(_ALL_MODES)} modes have full keys; unknown mode falls back cleanly")
except AssertionError as e:
    fail("AT-5", e)
except Exception as e:
    fail("AT-5", e)


# ── AT-6: py_compile clean ────────────────────────────────────────────────────
try:
    _ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for rel in (
        "kernel/relationship_register.py",
        "runtime/spine/relationship_faculty.py",
    ):
        py_compile.compile(os.path.join(_ROOT, rel), doraise=True)
    ok("AT-6: py_compile clean on relationship_register.py and relationship_faculty.py")
except py_compile.PyCompileError as e:
    fail("AT-6", e)
except Exception as e:
    fail("AT-6", e)


# ── Final summary ─────────────────────────────────────────────────────────────
print()
print("=" * 60)
print(f"WO-RELATIONSHIP-STYLE   {PASS} passed  {FAIL} failed")
if FAIL:
    sys.exit(1)
