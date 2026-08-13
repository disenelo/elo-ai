"""
tests/test_wo072_intent_gatekeeper.py — Acceptance tests for WO-072

Spec: WO-072 — Intent Gatekeeper (rules-first, LLM normalizer fallback).

  AT-1: "anything we can press on with? that needs my attention?" → conversation
  AT-2: "No but it takes time to build you" → conversation (NOT cancel)
  AT-3: "Strange reply what does that mean?" → conversation (NOT tool)
  AT-4: "come sit" → sit (real command still routes)
  AT-5: "how's the company" → company
  AT-6: "what's the weather" → weather
  AT-7: confidence gate — ambiguous short fragment → conversation
  AT-8: degrade (use_llm=False, low-conf rules) → conversation, no crash
  AT-9: fast path — clean command ("come sit") does NOT call LLM normalizer
  AT-10: cancel guard — "no but..." NOT classified as cancel
  AT-11: chaos-text — "No but it takes time to build you" NOT cancel (full chaos scenario)
  AT-12: py_compile clean on intent_gatekeeper.py and server.py

Run: python3 tests/test_wo072_intent_gatekeeper.py
"""
import sys, os, py_compile, unittest.mock as _mock
sys.path.insert(0, ".")

PASS = 0; FAIL = 0
def ok(n):      global PASS; PASS += 1; print(f"  ✅ {n}")
def fail(n, r): global FAIL; FAIL += 1; print(f"  ❌ {n}: {r}")

from faculties.intent_gatekeeper import classify, _rules_classify, _llm_normalize


# ── AT-1: transcript misroute #1 → conversation ───────────────────────────────
try:
    r = classify("anything we can press on with? that needs my attention?", use_llm=False)
    assert r["intent"] == "conversation", f"expected conversation, got {r['intent']!r}"
    assert r["confidence"] >= 0.85, f"confidence too low: {r['confidence']}"
    ok(f"AT-1: 'anything we can press on with?' → intent={r['intent']!r} conf={r['confidence']:.2f}")
except AssertionError as e:
    fail("AT-1", e)
except Exception as e:
    fail("AT-1", e)


# ── AT-2: transcript misroute #2 — "No but..." → conversation (NOT cancel) ───
try:
    r = classify("No but it takes time to build you", use_llm=False)
    assert r["intent"] == "conversation", f"expected conversation, got {r['intent']!r}"
    assert r["intent"] != "cancel", "must NOT classify 'No but...' as cancel"
    ok(f"AT-2: 'No but it takes time...' → intent={r['intent']!r} (not cancel)")
except AssertionError as e:
    fail("AT-2", e)
except Exception as e:
    fail("AT-2", e)


# ── AT-3: transcript misroute #3 — meta-question → conversation (NOT tool) ───
try:
    r = classify("Strange reply what does that mean?", use_llm=False)
    assert r["intent"] == "conversation", f"expected conversation, got {r['intent']!r}"
    assert not r["intent"].startswith("tool:"), "must NOT fire a tool on meta-question"
    ok(f"AT-3: 'Strange reply what does that mean?' → intent={r['intent']!r}")
except AssertionError as e:
    fail("AT-3", e)
except Exception as e:
    fail("AT-3", e)


# ── AT-4: real sit command still routes ───────────────────────────────────────
try:
    r = classify("come sit", use_llm=False)
    assert r["intent"] == "sit", f"expected sit, got {r['intent']!r}"
    assert r["confidence"] >= 0.85, f"sit confidence too low: {r['confidence']}"
    ok(f"AT-4: 'come sit' → intent={r['intent']!r} conf={r['confidence']:.2f}")
except AssertionError as e:
    fail("AT-4", e)
except Exception as e:
    fail("AT-4", e)


# ── AT-5: company query routes correctly ──────────────────────────────────────
try:
    r = classify("how's the company", use_llm=False)
    assert r["intent"] == "company", f"expected company, got {r['intent']!r}"
    ok(f"AT-5: 'how\\'s the company' → intent={r['intent']!r}")
except AssertionError as e:
    fail("AT-5", e)
except Exception as e:
    fail("AT-5", e)


# ── AT-6: weather query routes correctly ──────────────────────────────────────
try:
    r = classify("what's the weather", use_llm=False)
    assert r["intent"] == "weather", f"expected weather, got {r['intent']!r}"
    ok(f"AT-6: 'what\\'s the weather' → intent={r['intent']!r}")
except AssertionError as e:
    fail("AT-6", e)
except Exception as e:
    fail("AT-6", e)


# ── AT-7: confidence gate — ambiguous fragment → conversation ─────────────────
try:
    r = classify("hmm the grok tab thing", use_llm=False)
    assert r["intent"] == "conversation", f"expected conversation, got {r['intent']!r}"
    ok(f"AT-7: 'hmm the grok tab thing' → intent={r['intent']!r} (ambiguous → conversation)")
except AssertionError as e:
    fail("AT-7", e)
except Exception as e:
    fail("AT-7", e)


# ── AT-8: degrade gracefully — use_llm=False, low-conf rules → conversation ──
try:
    r = classify("the invoice for client X looks weird", use_llm=False)
    assert r["intent"] in ("conversation",), \
        f"low-conf input should default to conversation, got {r['intent']!r}"
    assert "intent" in r and "confidence" in r and "cleaned_text" in r, \
        f"envelope missing keys: {r}"
    ok(f"AT-8: low-conf input degrades to conversation without crash")
except AssertionError as e:
    fail("AT-8", e)
except Exception as e:
    fail("AT-8", e)


# ── AT-9: fast path — clean command does NOT call LLM normalizer ──────────────
try:
    _llm_called = []
    with _mock.patch("faculties.intent_gatekeeper._llm_normalize",
                     side_effect=lambda t: _llm_called.append(t) or None):
        r = classify("come sit with me", use_llm=True)
    assert r["intent"] == "sit", f"expected sit, got {r['intent']!r}"
    assert len(_llm_called) == 0, \
        f"LLM was called on a high-confidence command — should be rules-only: {_llm_called}"
    ok(f"AT-9: 'come sit with me' → rules fast path, LLM NOT called")
except AssertionError as e:
    fail("AT-9", e)
except Exception as e:
    fail("AT-9", e)


# ── AT-10: cancel guard — "no but..." is NOT cancel ──────────────────────────
try:
    for phrase in (
        "No but it takes time to build you",
        "no but we should think about this",
        "no but actually that's wrong",
    ):
        r = classify(phrase, use_llm=False)
        assert r["intent"] != "cancel", \
            f"'{phrase}' classified as cancel — must be conversation"
    ok("AT-10: 'no but...' variants → not cancel in any case")
except AssertionError as e:
    fail("AT-10", e)
except Exception as e:
    fail("AT-10", e)


# ── AT-11: chaos scenario — venting is conversation ───────────────────────────
try:
    r = classify("I'm tired and nothing's working", use_llm=False)
    assert r["intent"] == "conversation", f"expected conversation, got {r['intent']!r}"
    ok(f"AT-11: 'I\\'m tired and nothing\\'s working' → conversation (eLo grounds, doesn't command)")
except AssertionError as e:
    fail("AT-11", e)
except Exception as e:
    fail("AT-11", e)


# ── AT-12: py_compile clean ───────────────────────────────────────────────────
try:
    py_compile.compile("faculties/intent_gatekeeper.py", doraise=True)
    py_compile.compile("server.py", doraise=True)
    ok("AT-12: py_compile clean on intent_gatekeeper.py and server.py")
except py_compile.PyCompileError as e:
    fail("AT-12", e)


print()
print("=" * 50)
print(f"WO-072 intent gatekeeper  {PASS} passed  {FAIL} failed")
if FAIL:
    sys.exit(1)
