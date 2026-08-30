"""
tests/test_wo_memory_turn_types.py — WO-MEMORY-TURN-TYPES acceptance tests.

AT-1: memory/category_tagger.py exists with tag_turn(turn, intent_output, cognitive_state) -> List[str]
AT-2: "I prefer X to Y" → memory_categories contains "preferences"
AT-3: clothing recommendation → memory_categories contains "contextual_state" AND "preferences"
AT-4: deadline mention → memory_categories contains "projects", "commitments", "plans"
AT-5: cognitive_state.memory_categories non-empty on matching turns
AT-6: vault write triggered for tagged turns (write_interaction called with non-empty categories)
AT-7: existing WKG suite (test_wkg_*.py) and this test suite pass

Run: python3 tests/test_wo_memory_turn_types.py
"""
from __future__ import annotations
import sys, os, py_compile, importlib

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PASS = 0; FAIL = 0
def ok(n):      global PASS; PASS += 1; print(f"  ✅ {n}")
def fail(n, r): global FAIL; FAIL += 1; print(f"  ❌ {n}: {r}")


# ── AT-1: module exists and tag_turn callable ─────────────────────────────────
try:
    from memory.category_tagger import tag_turn
    assert callable(tag_turn), "tag_turn is not callable"
    ok("AT-1: memory/category_tagger.py exists with callable tag_turn()")
except ImportError as e:
    fail("AT-1", f"ImportError: {e}")
except AssertionError as e:
    fail("AT-1", e)
except Exception as e:
    fail("AT-1", e)


# ── AT-2: preference turn → "preferences" in categories ──────────────────────
try:
    cats = tag_turn("I prefer working in the morning to evenings")
    assert "preferences" in cats, f"'preferences' not in categories: {cats}"
    ok(f"AT-2: preference turn → categories include 'preferences' ({cats})")
except AssertionError as e:
    fail("AT-2", e)
except Exception as e:
    fail("AT-2", e)


# ── AT-3: clothing rec → "contextual_state" + "preferences" ──────────────────
try:
    cats = tag_turn("What jacket should I wear today? I prefer layering in cold weather")
    assert "contextual_state" in cats, f"'contextual_state' not in categories: {cats}"
    assert "preferences" in cats, f"'preferences' not in categories: {cats}"
    ok(f"AT-3: clothing rec → contextual_state + preferences ({cats})")
except AssertionError as e:
    fail("AT-3", e)
except Exception as e:
    fail("AT-3", e)


# ── AT-4: deadline turn → "projects" + "commitments" + "plans" ───────────────
try:
    cats = tag_turn("The elo-planet project deadline is next week — we must commit to shipping")
    assert "projects" in cats, f"'projects' not in categories: {cats}"
    assert "commitments" in cats, f"'commitments' not in categories: {cats}"
    assert "plans" in cats, f"'plans' not in categories: {cats}"
    ok(f"AT-4: deadline turn → projects + commitments + plans ({cats})")
except AssertionError as e:
    fail("AT-4", e)
except Exception as e:
    fail("AT-4", e)


# ── AT-5: CognitiveState.memory_categories non-empty on matching turns ────────
try:
    from runtime.spine.spine import assemble_cognitive_state
    language = {"original": "I prefer working late on the project — next week deadline must commit"}
    cs = assemble_cognitive_state(
        language=language,
        memory_result=None,
        attention=None,
        capabilities=[],
        vault_result=None,
        prior_state=None,
    )
    assert hasattr(cs, "memory_categories"), \
        "CognitiveState has no memory_categories field"
    assert len(cs.memory_categories) > 0, \
        f"memory_categories empty for a tagged turn: {cs.memory_categories}"
    ok(f"AT-5: CognitiveState.memory_categories non-empty for matching turn ({list(cs.memory_categories)})")
except AssertionError as e:
    fail("AT-5", e)
except Exception as e:
    fail("AT-5", e)


# ── AT-6: vault write triggered for tagged turn ───────────────────────────────
try:
    import tempfile, json, shutil
    from core.memory_engine import write_interaction
    from memory.category_tagger import tag_turn as _tag_turn

    _TMP = tempfile.mkdtemp(prefix="wo_mtt_test_")
    import core.memory_engine as _me
    orig_store = _me._STORE_PATH
    _me._STORE_PATH = os.path.join(_TMP, "interactions.json")

    turn_text = "I prefer layering in cold weather — wearing my jacket today"
    cats = _tag_turn(turn_text)
    assert cats, f"tag_turn returned empty categories for preference turn: {cats}"
    write_interaction(turn_text, "Got it.", cats, mode="answer")

    with open(_me._STORE_PATH) as f:
        records = json.load(f)
    assert records, "interactions.json empty after write_interaction"
    last = records[-1]
    assert last["memory_categories"] == cats, \
        f"categories mismatch: {last['memory_categories']} vs {cats}"

    _me._STORE_PATH = orig_store
    shutil.rmtree(_TMP)
    ok(f"AT-6: vault write triggered for tagged turn (categories: {cats})")
except AssertionError as e:
    fail("AT-6", e)
except Exception as e:
    fail("AT-6", e)


# ── AT-7: py_compile clean on all modified files ─────────────────────────────
try:
    _ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for rel in ("memory/category_tagger.py", "runtime/spine/spine.py", "runtime/contracts.py"):
        py_compile.compile(os.path.join(_ROOT, rel), doraise=True)
    ok("AT-7: py_compile clean on category_tagger.py, spine.py, contracts.py")
except py_compile.PyCompileError as e:
    fail("AT-7", e)
except Exception as e:
    fail("AT-7", e)


# ── Final summary ─────────────────────────────────────────────────────────────
print()
print("=" * 60)
print(f"WO-MEMORY-TURN-TYPES   {PASS} passed  {FAIL} failed")
if FAIL:
    sys.exit(1)
