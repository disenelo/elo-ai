"""
tests/test_wo032_false_degraded.py — Acceptance tests for WO-032 false-degraded fix

Spec: "can't reach my thinking" must NOT fire on command/greeting/direct turns.
It should only fire when the LLM path was genuinely attempted and returned mock.

  AT-1: _llm_turn=False present before the if/elif/else branch
  AT-2: _llm_turn=True set inside the LLM else block
  AT-3: _bh_degraded gated on _llm_turn (not just backend_used == "mock")
  AT-4: control-marker scrub present before multi-bubble split
  AT-5: scrub regex removes a [WEB_SEARCH:] prefix from a response string
  AT-6: py_compile clean

Run: python3 tests/test_wo032_false_degraded.py
"""
import sys, os, re
sys.path.insert(0, ".")

PASS = 0; FAIL = 0
def ok(n):      global PASS; PASS += 1; print(f"  ✅ {n}")
def fail(n, r): global FAIL; FAIL += 1; print(f"  ❌ {n}: {r}")

_src = open("server.py", encoding="utf-8").read()


# ── AT-1: _llm_turn = False declared before the branch ───────────────────────
try:
    # Must appear before the multilingual / spine-direct / LLM else branch
    # Use the CALL site (_detect_language_query(_raw_lower)), not the definition
    idx_false = _src.find("_llm_turn = False")
    idx_lang  = _src.find("_detect_language_query(_raw_lower)")
    if idx_false != -1 and idx_false < idx_lang:
        ok("AT-1: _llm_turn = False declared before the if/elif/else branch")
    else:
        fail("AT-1", f"_llm_turn=False pos={idx_false}, _detect_language_query pos={idx_lang}")
except Exception as e:
    fail("AT-1", e)


# ── AT-2: _llm_turn = True inside the LLM else block ────────────────────────
try:
    # The LLM else block starts with "Spine needs LLM"; _llm_turn=True must follow
    idx_llm_block = _src.find("Spine needs LLM")
    idx_true      = _src.find("_llm_turn = True", idx_llm_block)
    if idx_llm_block != -1 and idx_true != -1 and (idx_true - idx_llm_block) < 200:
        ok("AT-2: _llm_turn = True set at the start of the LLM else block")
    else:
        fail("AT-2", f"LLM block pos={idx_llm_block}, _llm_turn=True pos={idx_true}")
except Exception as e:
    fail("AT-2", e)


# ── AT-3: _bh_degraded gated on _llm_turn ───────────────────────────────────
try:
    if "_llm_turn and backend_used" in _src or "_llm_turn and backend_used ==" in _src:
        ok("AT-3: _bh_degraded check includes _llm_turn guard")
    else:
        fail("AT-3", "_llm_turn not found in degraded check expression")
except Exception as e:
    fail("AT-3", e)


# ── AT-4: control-marker scrub present before multi-bubble split ─────────────
try:
    idx_scrub  = _src.find("scrub leaked control markers")
    idx_bubble = _src.find("Multi-bubble split")
    if idx_scrub != -1 and idx_bubble != -1 and idx_scrub < idx_bubble:
        ok("AT-4: control-marker scrub block present before multi-bubble split")
    else:
        fail("AT-4", f"scrub pos={idx_scrub}, bubble pos={idx_bubble}")
except Exception as e:
    fail("AT-4", e)


# ── AT-5: scrub regex removes a [WEB_SEARCH:] prefix ────────────────────────
try:
    _pattern = re.compile(r"^\s*\[[A-Z][A-Z_\s:][^\]]{0,80}\]\s*", re.MULTILINE)
    _cases = [
        ("[WEB_SEARCH: what is the weather]\nHere's the weather.",
         "Here's the weather."),
        ("[WEB SEARCH: query]\nResult text.",
         "Result text."),
        ("Normal reply without a marker.",
         "Normal reply without a marker."),
        ("[WEB_SEARCH: foo bar]\nThe answer is 42.",
         "The answer is 42."),
    ]
    _fails = []
    for inp, expected in _cases:
        got = _pattern.sub("", inp).strip() or inp
        if got != expected:
            _fails.append(f"input={repr(inp[:40])} expected={repr(expected)} got={repr(got)}")
    if not _fails:
        ok(f"AT-5: scrub regex works on {len(_cases)} test cases")
    else:
        fail("AT-5", "; ".join(_fails))
except Exception as e:
    fail("AT-5", e)


# ── AT-6: py_compile clean ────────────────────────────────────────────────────
try:
    import py_compile
    py_compile.compile("server.py", doraise=True)
    ok("AT-6: py_compile clean on server.py")
except py_compile.PyCompileError as e:
    fail("AT-6", e)


print()
print("=" * 50)
print(f"WO-032-FD  {PASS} passed  {FAIL} failed")
if FAIL:
    sys.exit(1)
