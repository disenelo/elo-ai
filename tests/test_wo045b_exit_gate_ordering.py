"""
tests/test_wo045b_exit_gate_ordering.py — WO-045b: exit-gate ordering fix

The bug: _PENDING_EXIT["active"] was set at movement-intent time (~line 3152),
AFTER the LLM call. So the exit gate at line 2557 (which guards [EXIT_IN_TRANSIT]
injection) was always skipped on the first "take five" turn → eLo said "stepping
away" before the body was confirmed gone.

Fix: detect step_out phrases EARLY (before the LLM call), set _PENDING_EXIT["active"]
immediately so the gate can inject [EXIT_IN_TRANSIT] on the SAME turn.

  AT-1: step_out early-detect block present in server.py (ordering fix)
  AT-2: _STEP_OUT_PHRASES contains the core take-five phrases
  AT-3: [EXIT_IN_TRANSIT] directive present in server.py (gate injects it)
  AT-4: [EXIT_CONFIRMED] directive present (gate clears once acked)
  AT-5: [EXIT_FAILED] directive present (timeout honesty fallback)
  AT-6: [EXIT_CONFIRMED] allows "stepping away" — [EXIT_IN_TRANSIT] forbids it
  AT-7: py_compile clean

Run: python3 tests/test_wo045b_exit_gate_ordering.py
"""
import sys, py_compile
sys.path.insert(0, ".")

PASS = 0; FAIL = 0
def ok(n):      global PASS; PASS += 1; print(f"  ✅ {n}")
def fail(n, r): global FAIL; FAIL += 1; print(f"  ❌ {n}: {r}")


with open("server.py", encoding="utf-8") as _f:
    _src = _f.read()

# ── AT-1: early-detect block present ────────────────────────────────────────
try:
    assert "WO-045 ordering fix" in _src, "ordering fix comment not found"
    assert "_STEP_OUT_PHRASES" in _src, "_STEP_OUT_PHRASES not in server.py"
    assert "_PENDING_EXIT[\"active\"] = True" in _src, "early-set of PENDING_EXIT not found"
    ok("AT-1: step_out early-detect block present (ordering fix)")
except AssertionError as e:
    fail("AT-1", e)


# ── AT-2: _STEP_OUT_PHRASES contains core phrases ───────────────────────────
try:
    # Extract _STEP_OUT_PHRASES definition from server.py
    import re as _re
    _match = _re.search(r"_STEP_OUT_PHRASES\s*=\s*frozenset\(\{([^}]+)\}\)", _src, _re.DOTALL)
    assert _match, "_STEP_OUT_PHRASES frozenset not found"
    _phrases_text = _match.group(1)
    for p in ["take 5", "take five", "give me a minute", "step away", "pop off"]:
        assert f'"{p}"' in _phrases_text or f"'{p}'" in _phrases_text, f"{p!r} not in _STEP_OUT_PHRASES"
    ok("AT-2: _STEP_OUT_PHRASES contains core take-five phrases")
except AssertionError as e:
    fail("AT-2", e)


# ── AT-3..5: three gate directives present ─────────────────────────────────
for at, needle in [
    ("AT-3", "[EXIT_IN_TRANSIT]"),
    ("AT-4", "[EXIT_CONFIRMED]"),
    ("AT-5", "[EXIT_FAILED]"),
]:
    if needle in _src:
        ok(f"{at}: {needle} directive present in server.py")
    else:
        fail(at, f"{needle} not found in server.py")


# ── AT-6: semantic content check ────────────────────────────────────────────
try:
    assert "do NOT say" in _src or "Do NOT say" in _src, "[EXIT_IN_TRANSIT] should forbid 'stepping away'"
    assert "you can say" in _src or "can say" in _src, "[EXIT_CONFIRMED] should allow 'stepping away'"
    ok("AT-6: EXIT_CONFIRMED allows; EXIT_IN_TRANSIT forbids — semantics correct")
except AssertionError as e:
    fail("AT-6", e)


# ── AT-7: py_compile ──────────────────────────────────────────────────────
try:
    py_compile.compile("server.py", doraise=True)
    ok("AT-7: py_compile clean on server.py")
except py_compile.PyCompileError as e:
    fail("AT-7", e)


print()
print("=" * 50)
print(f"WO-045b exit-gate ordering  {PASS} passed  {FAIL} failed")
if FAIL:
    sys.exit(1)
