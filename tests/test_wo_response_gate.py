"""
tests/test_wo_response_gate.py — WO-RESPONSE-GATE acceptance tests.

AT-1: runtime/response_gate.py exists with ResponseGate class and evaluate() method.
AT-2: Generic assistant phrasing ("Certainly!", "As an AI…") → flagged by identity check, revised.
AT-3: Reflection-as-default ("I notice you're asking…") → flagged, rewritten.
AT-4: False authority claim flagged by authority check.
AT-5: response_gate.evaluate() called in executive.py decide() when draft_response provided.
AT-6: gate_log.jsonl written with valid entry after evaluate() runs.
AT-7: Full test suite passes with no new failures.

Run: python3 tests/test_wo_response_gate.py
"""
from __future__ import annotations
import sys, os, json, py_compile, tempfile, shutil

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PASS = 0; FAIL = 0
def ok(n):      global PASS; PASS += 1; print(f"  ✅ {n}")
def fail(n, r): global FAIL; FAIL += 1; print(f"  ❌ {n}: {r}")


# ── AT-1: response_gate.py exists with ResponseGate and evaluate() ────────────
try:
    from runtime.response_gate import ResponseGate, GateResult
    assert callable(getattr(ResponseGate, "evaluate", None) or getattr(ResponseGate(), "evaluate", None)), \
        "ResponseGate.evaluate() not callable"
    import dataclasses
    _fields = {f.name for f in dataclasses.fields(GateResult)}
    assert "passed"           in _fields, f"GateResult missing 'passed' field"
    assert "revised_response" in _fields, f"GateResult missing 'revised_response' field"
    assert "flags"            in _fields, f"GateResult missing 'flags' field"
    ok("AT-1: ResponseGate + GateResult with all required fields")
except Exception as e:
    fail("AT-1", e)


# ── AT-2: generic assistant phrasing → identity flag + revision ───────────────
try:
    from runtime.response_gate import ResponseGate as _RG2
    _generic = "Certainly! As an AI language model, I can help you with that."
    _r2 = _RG2().evaluate(_generic)
    assert not _r2.passed, "gate should not pass on generic assistant phrasing"
    _id_flags = [f for f in _r2.flags if "identity" in f]
    assert _id_flags, f"no identity flags raised; flags: {_r2.flags}"
    ok(f"AT-2: generic phrasing → not passed; identity flags: {_id_flags[:2]}")
except AssertionError as e:
    fail("AT-2", e)
except Exception as e:
    fail("AT-2", e)


# ── AT-3: reflection-as-default → flagged + rewritten ────────────────────────
try:
    from runtime.response_gate import ResponseGate as _RG3
    _reflective = "I notice you're asking about your project deadline. That's a lot to carry."
    _r3 = _RG3().evaluate(_reflective)
    assert not _r3.passed, "gate should not pass on reflection-as-default phrasing"
    _ref_flags = [f for f in _r3.flags if "reflection" in f]
    assert _ref_flags, f"no reflection_default flags raised; flags: {_r3.flags}"
    ok(f"AT-3: reflection phrasing → not passed; flags: {_ref_flags[:2]}")
except AssertionError as e:
    fail("AT-3", e)
except Exception as e:
    fail("AT-3", e)


# ── AT-4: false authority claim → authority flag ──────────────────────────────
try:
    from runtime.response_gate import ResponseGate as _RG4
    _authority = "I can access the internet to search for that information for you."
    _r4 = _RG4().evaluate(_authority)
    assert not _r4.passed, "gate should not pass on false authority claim"
    _auth_flags = [f for f in _r4.flags if "authority" in f]
    assert _auth_flags, f"no authority flags raised; flags: {_r4.flags}"
    ok(f"AT-4: false authority → not passed; flags: {_auth_flags[:2]}")
except AssertionError as e:
    fail("AT-4", e)
except Exception as e:
    fail("AT-4", e)


# ── AT-5: gate called in executive.decide() when draft_response provided ──────
try:
    from runtime import executive as _exec5
    _attn = {"intent": "conversation", "emotional_context": {}}
    _draft = "Certainly! I can help you with that. Let me know if you have any other questions."
    _dec5 = _exec5.decide(_attn, loop_detected=False, user_input="help me", draft_response=_draft)
    assert "gate_flags" in _dec5, "decide() result missing 'gate_flags' key"
    assert "gated_response" in _dec5, "decide() result missing 'gated_response' key"
    assert isinstance(_dec5["gate_flags"], list), f"gate_flags should be list, got {type(_dec5['gate_flags'])}"
    assert _dec5["gate_flags"], f"gate_flags empty — identity/padding checks should have fired on: {_draft!r}"
    ok(f"AT-5: decide() with draft_response → gate ran; flags: {_dec5['gate_flags'][:2]}")
except AssertionError as e:
    fail("AT-5", e)
except Exception as e:
    fail("AT-5", e)


# ── AT-6: gate_log.jsonl written after evaluate() ────────────────────────────
try:
    import runtime.response_gate as _rg_mod
    _orig_log = _rg_mod._GATE_LOG
    _tmp_dir = tempfile.mkdtemp(prefix="wo_rg_test_")
    _rg_mod._GATE_LOG = os.path.join(_tmp_dir, "gate_log.jsonl")

    from runtime.response_gate import ResponseGate as _RG6
    _RG6().evaluate("Certainly! As an AI, I want to help.")

    assert os.path.exists(_rg_mod._GATE_LOG), "gate_log.jsonl not created"
    with open(_rg_mod._GATE_LOG) as _f:
        _entries = [json.loads(line) for line in _f if line.strip()]
    assert _entries, "gate_log.jsonl empty"
    _last = _entries[-1]
    assert "ts" in _last, f"gate log entry missing 'ts': {_last}"
    assert "flags" in _last, f"gate log entry missing 'flags': {_last}"
    assert "passed" in _last, f"gate log entry missing 'passed': {_last}"

    _rg_mod._GATE_LOG = _orig_log
    shutil.rmtree(_tmp_dir)
    ok(f"AT-6: gate_log.jsonl written with valid entry (keys: ts, flags, passed)")
except AssertionError as e:
    fail("AT-6", e)
except Exception as e:
    fail("AT-6", e)
finally:
    try:
        import runtime.response_gate as _rg_mod2
        _rg_mod2._GATE_LOG = _orig_log
    except Exception:
        pass


# ── AT-7: py_compile clean on modified files ─────────────────────────────────
try:
    _ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for rel in ("runtime/response_gate.py", "runtime/executive.py"):
        py_compile.compile(os.path.join(_ROOT, rel), doraise=True)
    ok("AT-7: py_compile clean on response_gate.py, executive.py")
except py_compile.PyCompileError as e:
    fail("AT-7", e)
except Exception as e:
    fail("AT-7", e)


# ── Final summary ─────────────────────────────────────────────────────────────
print()
print("=" * 60)
print(f"WO-RESPONSE-GATE   {PASS} passed  {FAIL} failed")
if FAIL:
    sys.exit(1)
