"""
tests/test_ruling_c_assemble_before_decide.py — WO-CANON-VII: Ruling C closure

ATs:
  AT-1: spine._executive_faculty() calls exec_decide directly (not attention["_exec_decision"])
  AT-2: spine.py source ordering — exec_decide call appears AFTER assemble_cognitive_state line
  AT-3: server.py no longer calls exec_decide at the top-of-turn call site
  AT-4: exec_decision dict in server.py is derived from _plan fields (conversation_action → action)
  AT-5: spine.run() returns a plan whose fields populate exec_decision correctly (round-trip)
  AT-6: py_compile clean on spine.py and server.py

Run: python3 tests/test_ruling_c_assemble_before_decide.py
"""
from __future__ import annotations
import os
import py_compile
import sys
import types

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

_passed = _failed = 0
_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def ok(label: str):
    global _passed
    _passed += 1
    print(f"  ✅ {label}")


def fail(label: str, err):
    global _failed
    _failed += 1
    print(f"  ❌ {label}: {err}")


# ── AT-1: _executive_faculty does NOT read attention["_exec_decision"] ────────
try:
    with open(os.path.join(_BASE, "runtime", "spine", "spine.py")) as f:
        spine_src = f.read()

    assert 'attention.get("_exec_decision"' not in spine_src, (
        "_executive_faculty still reads attention['_exec_decision'] — "
        "Ruling C not closed: decision is still taken from pre-assembly injection"
    )
    assert "_exec_decide_fn" in spine_src or "exec_decide_fn" in spine_src, (
        "spine._executive_faculty must call exec_decide directly (via _exec_decide_fn)"
    )
    ok("AT-1: _executive_faculty calls exec_decide directly — not attention['_exec_decision']")
except AssertionError as e:
    fail("AT-1", e)
except Exception as e:
    fail("AT-1", e)

# ── AT-2: source ordering — exec_decide appears AFTER assemble_cognitive_state ─
try:
    lines = spine_src.splitlines()
    assemble_line = next(
        (i for i, ln in enumerate(lines) if "assemble_cognitive_state(" in ln), None
    )
    decide_line = next(
        (i for i, ln in enumerate(lines) if "_exec_decide_fn(" in ln or "exec_decide_fn(" in ln),
        None,
    )
    assert assemble_line is not None, "assemble_cognitive_state( not found in spine.py"
    assert decide_line is not None, "exec_decide_fn( not found in spine.py"
    assert decide_line > assemble_line, (
        f"exec_decide_fn (line {decide_line+1}) precedes "
        f"assemble_cognitive_state (line {assemble_line+1}) — Ruling C still violated"
    )
    ok(f"AT-2: source ordering correct — assemble_cognitive_state L{assemble_line+1} "
       f"< exec_decide_fn L{decide_line+1}")
except AssertionError as e:
    fail("AT-2", e)
except Exception as e:
    fail("AT-2", e)

# ── AT-3: server.py no longer calls exec_decide before spine ──────────────────
try:
    with open(os.path.join(_BASE, "server.py")) as f:
        srv_src = f.read()

    # Find first occurrence of exec_decide( in server.py (excluding the import line)
    srv_lines = srv_src.splitlines()
    call_lines = [
        i for i, ln in enumerate(srv_lines)
        if "exec_decide(" in ln and "import" not in ln
    ]
    # The only remaining exec_decide( call in server.py should be the fallback
    # (inside the `else:` branch when _plan is None) — NOT a standalone top-of-turn call
    for ln_idx in call_lines:
        line_text = srv_lines[ln_idx].strip()
        # The fallback is: exec_decision = exec_decide(attention_model, ...)
        # It must be inside the else branch, not a standalone call
        assert "exec_decision = exec_decide(" in line_text, (
            f"Unexpected exec_decide call at server.py:{ln_idx+1}: {line_text!r}"
        )
    assert len(call_lines) == 1, (
        f"Expected exactly 1 exec_decide call (fallback else-branch); "
        f"found {len(call_lines)} at lines {[i+1 for i in call_lines]}"
    )
    ok(f"AT-3: server.py has exactly 1 exec_decide call — fallback only (L{call_lines[0]+1})")
except AssertionError as e:
    fail("AT-3", e)
except Exception as e:
    fail("AT-3", e)

# ── AT-4: exec_decision dict built from _plan fields (conversation_action → action) ─
try:
    assert "_plan.conversation_action" in srv_src, (
        "server.py must build exec_decision['action'] from _plan.conversation_action"
    )
    assert '"action":        _plan.conversation_action' in srv_src or \
           '"action": _plan.conversation_action' in srv_src, (
        "exec_decision dict must map 'action' from _plan.conversation_action"
    )
    assert '"tone":          _plan.tone' in srv_src or '"tone": _plan.tone' in srv_src, (
        "exec_decision dict must map 'tone' from _plan.tone"
    )
    assert '"cal_reason":    _plan.cal_reason' in srv_src or \
           '"cal_reason": _plan.cal_reason' in srv_src, (
        "exec_decision dict must map 'cal_reason' from _plan.cal_reason"
    )
    ok("AT-4: exec_decision dict derived from _plan fields (conversation_action/tone/cal_reason)")
except AssertionError as e:
    fail("AT-4", e)
except Exception as e:
    fail("AT-4", e)

# ── AT-5: spine.run() round-trip — plan fields survive into exec_decision ──────
try:
    # Stub exec_decide to return a known dict
    _known_exec = {
        "action":        "reflect",
        "cal_reason":    "test_reason",
        "tone":          "CHILDLIKE-WISE",
        "max_sentences": 2,
        "response_goal": "ground",
        "valence":       "warm",
        "momentum":      "building",
        "mode":          "",
        "register":      "",
        "intent":        "conversation",
    }

    _fake_exec_mod = types.ModuleType("runtime.executive")
    _fake_exec_mod.decide = lambda *a, **kw: dict(_known_exec)

    # Stub out heavy deps so spine.run() completes without the full app
    for _mod in ["runtime.router.meaning_engine",
                 "runtime.router.execution_gate",
                 "runtime.capabilities.registry",
                 "runtime.spine.relationship_faculty",
                 "runtime.spine.presence_faculty",
                 "runtime.light_engine.light_engine",
                 "runtime.working_memory",
                 "runtime.cognitive_snapshot",
                 "runtime.contracts",
                 "world.live_world_state",
                 "faculties.perception.perception_faculty"]:
        if _mod not in sys.modules:
            sys.modules[_mod] = types.ModuleType(_mod)

    sys.modules["runtime.executive"] = _fake_exec_mod

    # Fresh spine import after stubs
    for k in list(sys.modules):
        if "runtime.spine.spine" in k:
            del sys.modules[k]

    from runtime.spine.spine import run as _test_spine_run
    _test_plan = _test_spine_run("hello", state={}, attention={}, memory_pack="")

    assert _test_plan is not None, "spine.run() returned None"
    assert _test_plan.conversation_action == "reflect", (
        f"plan.conversation_action should be 'reflect', got {_test_plan.conversation_action!r}"
    )
    assert _test_plan.tone == "CHILDLIKE-WISE", (
        f"plan.tone should be 'CHILDLIKE-WISE', got {_test_plan.tone!r}"
    )
    assert _test_plan.cal_reason == "test_reason", (
        f"plan.cal_reason should be 'test_reason', got {_test_plan.cal_reason!r}"
    )

    # Now verify exec_decision derivation
    _derived = {
        "action":        _test_plan.conversation_action,
        "cal_reason":    _test_plan.cal_reason,
        "tone":          _test_plan.tone,
        "max_sentences": _test_plan.max_sentences,
    }
    assert _derived["action"] == "reflect"
    assert _derived["tone"] == "CHILDLIKE-WISE"
    ok("AT-5: spine.run() round-trip — plan fields match exec_decide output; exec_decision derives correctly")
except AssertionError as e:
    fail("AT-5", e)
except Exception as e:
    fail("AT-5", e)
finally:
    # Restore
    if "runtime.executive" in sys.modules:
        del sys.modules["runtime.executive"]
    for k in list(sys.modules):
        if "runtime.spine.spine" in k:
            del sys.modules[k]

# ── AT-6: py_compile clean ────────────────────────────────────────────────────
try:
    for path in (
        os.path.join(_BASE, "runtime", "spine", "spine.py"),
        os.path.join(_BASE, "server.py"),
    ):
        py_compile.compile(path, doraise=True)
    ok("AT-6: py_compile clean on spine.py and server.py")
except py_compile.PyCompileError as e:
    fail("AT-6", e)
except Exception as e:
    fail("AT-6", e)

# ── Summary ───────────────────────────────────────────────────────────────────
print()
print("=" * 66)
print(f"Ruling C assemble-before-decide     {_passed} passed   {_failed} failed")
if _failed:
    sys.exit(1)
