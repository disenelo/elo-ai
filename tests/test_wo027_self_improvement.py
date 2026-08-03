"""
tests/test_wo027_self_improvement.py — Acceptance tests for WO-027

Spec: WO-027 eLo Self-Improvement Loop — golden set + LLM-judge + correction-memory (ICL)

Tests:
  AT-1: golden_set.json is loadable and has ≥8 cases with required keys
  AT-2: score_response returns a dict with score/verdict/reason
  AT-3: should_escalate returns True below threshold, False above
  AT-4: store_correction blocks red-tier without reviewed=True
  AT-5: store_correction accepts green-tier without review flag
  AT-6: inject_corrections prepends the correction block into the system prompt
  AT-7: search_corrections returns [] on empty ledger without crashing
  AT-8: get_corrected_response returns a non-empty string (or original on failure)

Run: python3 tests/test_wo027_self_improvement.py
"""
import sys, os, json, tempfile
sys.path.insert(0, ".")

PASS = 0; FAIL = 0
def ok(n):      global PASS; PASS += 1; print(f"  ✅ {n}")
def fail(n, r): global FAIL; FAIL += 1; print(f"  ❌ {n}: {r}")


# ── AT-1: golden_set.json loads and has required keys ────────────────────────

try:
    _gs_path = os.path.join("self_improvement", "golden_set.json")
    with open(_gs_path, encoding="utf-8") as _f:
        _golden = json.load(_f)
    _required_keys = {"id", "input", "eval_criteria"}
    _bad = [c for c in _golden if not _required_keys.issubset(c)]
    if len(_golden) >= 8 and not _bad:
        ok("AT-1: golden_set.json loads with ≥8 cases and required keys")
    else:
        fail("AT-1", f"cases={len(_golden)}, missing-key cases={len(_bad)}")
except Exception as e:
    fail("AT-1", e)


# ── AT-2: score_response returns structured dict ──────────────────────────────

try:
    from self_improvement.evaluator import score_response
    _result = score_response(
        input_text="what is eLo planet?",
        response="eLo Planet is a game by DISENELO where eLo navigates a world full of overcharged enemies.",
        eval_criteria=["mentions the game", "does not deflect"],
    )
    assert isinstance(_result, dict), "not a dict"
    for _k in ("score", "verdict", "reason"):
        assert _k in _result, f"missing key '{_k}'"
    assert isinstance(_result["score"], float), "score not float"
    assert _result["verdict"] in ("pass", "fail"), "verdict invalid"
    ok("AT-2: score_response returns {score, verdict, reason}")
except Exception as e:
    fail("AT-2", e)


# ── AT-3: should_escalate threshold logic ────────────────────────────────────

try:
    from self_improvement.evaluator import should_escalate
    _low  = should_escalate({"score": 0.4, "verdict": "fail"})
    _high = should_escalate({"score": 0.9, "verdict": "pass"})
    _edge = should_escalate({"score": 0.65, "verdict": "pass"})
    assert _low  is True,  "low score (0.4) should escalate"
    assert _high is False, "high score (0.9) should not escalate"
    assert _edge is False, "edge case (0.65) is at threshold — should not escalate"
    ok("AT-3: should_escalate threshold correct at 0.65")
except Exception as e:
    fail("AT-3", e)


# ── AT-4/AT-5: store_correction review gate ──────────────────────────────────

try:
    import self_improvement.correction_store as _cs
    _orig_path = _cs._LEDGER_PATH
    with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as _tf:
        _tmp_ledger = _tf.name
    _cs._LEDGER_PATH = _tmp_ledger

    # AT-4: red-tier blocked without reviewed=True
    _blocked = _cs.store_correction(
        "wagwan elo", "safe g", "register: south london tone",
        reviewed=False,
    )
    assert _blocked is False, "red-tier should be blocked without reviewed=True"
    ok("AT-4: red-tier correction blocked without reviewed=True")

    # AT-5: green-tier auto-accepted
    _accepted = _cs.store_correction(
        "what is the eLo planet game?",
        "eLo Planet is a DISENELO game about a world of overcharged creatures.",
        "answer was evasive — should state the game premise directly",
        reviewed=False,
    )
    assert _accepted is True, "green-tier should be accepted without reviewed flag"
    ok("AT-5: green-tier correction accepted without reviewed flag")

    _cs._LEDGER_PATH = _orig_path
    os.unlink(_tmp_ledger)
except Exception as e:
    fail("AT-4/AT-5", e)


# ── AT-6: inject_corrections prepends ICL block ───────────────────────────────

try:
    from self_improvement.correction_store import inject_corrections
    _corrections = [
        {
            "input":              "my speakers are not working",
            "corrected_response": "Try checking your system audio settings — start there.",
            "why":                "previous response deflected instead of helping",
        }
    ]
    _base = "You are eLo, a creative AI companion."
    _enriched = inject_corrections(_corrections, _base)
    assert _enriched != _base, "inject_corrections returned unchanged prompt"
    assert "[PAST CORRECTIONS" in _enriched, "correction block header missing"
    assert "my speakers are not working" in _enriched, "correction input missing"
    assert _base in _enriched, "original system prompt missing from enriched"
    ok("AT-6: inject_corrections prepends ICL block, original prompt preserved")
except Exception as e:
    fail("AT-6", e)


# ── AT-7: search_corrections on empty ledger ─────────────────────────────────

try:
    import self_improvement.correction_store as _cs
    _orig_path = _cs._LEDGER_PATH
    with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as _tf:
        _tmp = _tf.name
    _cs._LEDGER_PATH = _tmp

    _results = _cs.search_corrections("wagwan elo", top_k=3)
    assert isinstance(_results, list), "should return a list"
    assert len(_results) == 0, f"empty ledger should return no corrections, got {len(_results)}"
    ok("AT-7: search_corrections returns [] on empty ledger")

    _cs._LEDGER_PATH = _orig_path
    os.unlink(_tmp)
except Exception as e:
    fail("AT-7", e)


# ── AT-8: get_corrected_response returns a string ────────────────────────────

try:
    from self_improvement.evaluator import get_corrected_response
    _original = "I cannot help with that."
    _corrected = get_corrected_response(
        input_text="what is eLo planet?",
        failed_response=_original,
        failure_reason="evasion detected",
    )
    assert isinstance(_corrected, str), "should return a string"
    assert len(_corrected) > 0, "should return non-empty string"
    # On LLM failure the fallback is the original — both outcomes are acceptable
    ok(f"AT-8: get_corrected_response returned a string ({len(_corrected)} chars)")
except Exception as e:
    fail("AT-8", e)


# ── Summary ───────────────────────────────────────────────────────────────────

print()
print(f"{'='*50}")
print(f"WO-027  {PASS} passed  {FAIL} failed")
if FAIL:
    sys.exit(1)
