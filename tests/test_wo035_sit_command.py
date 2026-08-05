"""
tests/test_wo035_sit_command.py — Acceptance tests for WO-035 sit-command fix

Spec: "can you sit?" / "come here" / "sit here" must emit a sit dict from
      presence_faculty.compute() even when tone == SILENCE-AWARE.

  AT-1: signal words run BEFORE SILENCE-AWARE in presence_faculty (code order)
  AT-2: missing sit phrases synced — "can you sit" in _SIGNAL_WORDS
  AT-3: "come and sit" / "sit here" / "sit by me" in _SIGNAL_WORDS
  AT-4: "can you sit?" with SILENCE-AWARE tone → sit dict (not step_out)
  AT-5: "come here" with SILENCE-AWARE tone → sit dict
  AT-6: py_compile clean

Run: python3 tests/test_wo035_sit_command.py
"""
import sys, os, types
sys.path.insert(0, ".")

PASS = 0; FAIL = 0
def ok(n):      global PASS; PASS += 1; print(f"  ✅ {n}")
def fail(n, r): global FAIL; FAIL += 1; print(f"  ❌ {n}: {r}")


# ── AT-1: signal words come BEFORE SILENCE-AWARE in presence_faculty source ──
try:
    _src = open("runtime/spine/presence_faculty.py", encoding="utf-8").read()
    idx_signal   = _src.find("Layer 1 — signal words")
    idx_silence  = _src.find("SILENCE-AWARE" , idx_signal + 1)  # first occurrence after label
    idx_silence2 = _src.find("tone == \"SILENCE-AWARE\"")
    if idx_signal != -1 and idx_signal < idx_silence2:
        ok("AT-1: signal word block comes before SILENCE-AWARE check in source")
    else:
        fail("AT-1", f"signal_words pos={idx_signal}, SILENCE-AWARE pos={idx_silence2}")
except Exception as e:
    fail("AT-1", e)


# ── AT-2: "can you sit" in _SIGNAL_WORDS ─────────────────────────────────────
try:
    import runtime.spine.presence_faculty as _pf
    if "can you sit" in _pf._SIGNAL_WORDS:
        ok("AT-2: 'can you sit' present in _SIGNAL_WORDS")
    else:
        fail("AT-2", "'can you sit' missing from _SIGNAL_WORDS")
except Exception as e:
    fail("AT-2", e)


# ── AT-3: other synced sit phrases present ────────────────────────────────────
try:
    import runtime.spine.presence_faculty as _pf
    _expected = ["come and sit", "sit here", "sit by me", "come over here",
                 "sit beside me", "have a seat", "take a seat", "come sit"]
    _missing = [p for p in _expected if p not in _pf._SIGNAL_WORDS]
    if not _missing:
        ok(f"AT-3: all {len(_expected)} synced sit phrases present in _SIGNAL_WORDS")
    else:
        fail("AT-3", f"missing: {_missing}")
except Exception as e:
    fail("AT-3", e)


# ── AT-4: "can you sit?" + SILENCE-AWARE tone → sit dict, not step_out ───────
try:
    import runtime.spine.presence_faculty as _pf
    from runtime.spine.presence_faculty import CognitivePlan

    _plan = CognitivePlan(raw="can you sit?")
    _plan.tone              = "SILENCE-AWARE"
    _plan.conversation_action = "respond"
    _plan.intent            = "conversation"
    _plan.presence_plan     = {"emotional_state": "comfort"}

    _attention = {
        "emotional_context": {"valence": "neutral", "momentum": "stable", "energy": 0.4},
        "_exec_decision":    {"cognitive_load": "low", "tone": "SILENCE-AWARE",
                              "action": "respond", "intent": "conversation"},
    }

    result = _pf.compute(_plan, _attention)
    mv = result.movement_intent
    if isinstance(mv, dict) and mv.get("name") == "sit":
        ok(f"AT-4: 'can you sit?' + SILENCE-AWARE → sit dict {mv}")
    else:
        fail("AT-4", f"movement_intent={mv!r} (expected sit dict)")
except Exception as e:
    fail("AT-4", e)


# ── AT-5: "come here" + SILENCE-AWARE tone → sit dict ────────────────────────
try:
    import runtime.spine.presence_faculty as _pf
    from runtime.spine.presence_faculty import CognitivePlan

    _plan2 = CognitivePlan(raw="come here")
    _plan2.tone               = "SILENCE-AWARE"
    _plan2.conversation_action = "silence"
    _plan2.intent             = "conversation"
    _plan2.presence_plan      = {"emotional_state": "comfort"}

    _attention2 = {
        "emotional_context": {"valence": "neutral", "momentum": "stable", "energy": 0.4},
        "_exec_decision":    {"cognitive_load": "low", "tone": "SILENCE-AWARE",
                              "action": "silence", "intent": "conversation"},
    }

    result2 = _pf.compute(_plan2, _attention2)
    mv2 = result2.movement_intent
    if isinstance(mv2, dict) and mv2.get("name") == "sit":
        ok(f"AT-5: 'come here' + SILENCE-AWARE → sit dict {mv2}")
    else:
        fail("AT-5", f"movement_intent={mv2!r} (expected sit dict)")
except Exception as e:
    fail("AT-5", e)


# ── AT-6: py_compile clean ────────────────────────────────────────────────────
try:
    import py_compile
    py_compile.compile("runtime/spine/presence_faculty.py", doraise=True)
    ok("AT-6: py_compile clean on presence_faculty.py")
except py_compile.PyCompileError as e:
    fail("AT-6", e)


print()
print("=" * 50)
print(f"WO-035  {PASS} passed  {FAIL} failed")
if FAIL:
    sys.exit(1)
