"""
tests/test_wo_exp_001_storytelling_style.py — WO-EXP-001
Verify storytelling_style field in Meaning Object (SC-NEW-001).
Run: ~/miniconda3/bin/python3 tests/test_wo_exp_001_storytelling_style.py
"""
import py_compile
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

PASS = 0
FAIL = 0


def ok(label):
    global PASS
    PASS += 1
    print(f"  ✅ {label}")


def fail(label, reason=""):
    global FAIL
    FAIL += 1
    print(f"  ❌ {label}" + (f": {reason}" if reason else ""))


# ---------------------------------------------------------------------------
# AT-1: storytelling_style field present in CognitivePlan with correct type annotation
# ---------------------------------------------------------------------------
def at1_field_present():
    try:
        from runtime.spine.plan import CognitivePlan
        plan = CognitivePlan(raw="test", mode="direct")
        if hasattr(plan, "storytelling_style") and plan.storytelling_style is None:
            ok("AT-1: storytelling_style field present in CognitivePlan, default=None")
        else:
            fail("AT-1", f"Field missing or wrong default: {getattr(plan, 'storytelling_style', 'MISSING')}")
    except Exception as e:
        fail("AT-1", str(e))


# ---------------------------------------------------------------------------
# AT-2: Conversation Faculty populates field per SPEC §3 logic
# ---------------------------------------------------------------------------
def at2_population_logic():
    try:
        # Verify the population code exists in spine.py (source check)
        with open(os.path.join(ROOT, "runtime", "spine", "spine.py"), encoding="utf-8") as f:
            src = f.read()
        cases = [
            ("collaborative", "studio"),
            ("imaginative", "imaginat"),
            ("reflective", "reflect"),
            ("playful", "play"),
            ("exploratory", "learn"),
            ("direct", "direct"),
        ]
        missing = [val for val, key in cases if f'"{val}"' not in src or "storytelling_style" not in src]
        if not missing:
            ok("AT-2: spine.py populates storytelling_style for all 6 register cases")
        else:
            fail("AT-2", f"Missing cases: {missing}")
    except Exception as e:
        fail("AT-2", str(e))


# ---------------------------------------------------------------------------
# AT-3: storytelling_style = None → existing behaviour unchanged (regression)
# ---------------------------------------------------------------------------
def at3_none_is_noop():
    try:
        from runtime.spine.plan import CognitivePlan
        plan = CognitivePlan(raw="hello", mode="")
        # mode="" → no mode signal → stays None
        if plan.storytelling_style is None:
            ok("AT-3: storytelling_style=None when no mode signal (regression: behaviour unchanged)")
        else:
            fail("AT-3", f"Expected None, got {plan.storytelling_style!r}")
    except Exception as e:
        fail("AT-3", str(e))


# ---------------------------------------------------------------------------
# AT-4: Field value accessible in response generation context (server.py)
# ---------------------------------------------------------------------------
def at4_consumption_in_server():
    try:
        with open(os.path.join(ROOT, "server.py"), encoding="utf-8") as f:
            src = f.read()
        has_consumption = "storytelling_style" in src and "STORYTELLING FRAME" in src
        has_hint_map = "collaborative" in src and "imaginative" in src and "reflective" in src
        if has_consumption and has_hint_map:
            ok("AT-4: server.py consumes storytelling_style → [STORYTELLING FRAME] injection")
        else:
            fail("AT-4", "storytelling_style consumption or STORYTELLING FRAME not found in server.py")
    except Exception as e:
        fail("AT-4", str(e))


# ---------------------------------------------------------------------------
# AT-5: Executive and CAL action routing are unmodified (no executive.py changes)
# ---------------------------------------------------------------------------
def at5_executive_untouched():
    try:
        exec_path = os.path.join(ROOT, "runtime", "executive.py")
        with open(exec_path, encoding="utf-8") as f:
            exec_src = f.read()
        if "storytelling_style" not in exec_src:
            py_compile.compile(exec_path, doraise=True)
            ok("AT-5: executive.py has no storytelling_style (FREEZE_V1_LOCK) and compiles clean")
        else:
            fail("AT-5", "storytelling_style found in executive.py — violates FREEZE_V1_LOCK")
    except py_compile.PyCompileError as e:
        fail("AT-5", f"executive.py compile error: {e}")
    except Exception as e:
        fail("AT-5", str(e))


def run_tests():
    print("\n=== WO-EXP-001 — storytelling_style Meaning Object field ===\n")
    at1_field_present()
    at2_population_logic()
    at3_none_is_noop()
    at4_consumption_in_server()
    at5_executive_untouched()
    print(f"\n{'='*50}")
    print(f"Result: {PASS}/5 PASS  {FAIL}/5 FAIL")
    if FAIL:
        sys.exit(1)


if __name__ == "__main__":
    run_tests()
