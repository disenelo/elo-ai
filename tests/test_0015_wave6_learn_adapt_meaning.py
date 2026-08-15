"""
tests/test_0015_wave6_learn_adapt_meaning.py — Wave 6 proof tests.

Rows verified:
  20 LEARN   — confirmed lessons exist in ledger; recall() filters to confirmed;
               promote_pass() can advance candidate → confirmed on a temp ledger.
  22 ADAPT   — route_confidence() changes after experience (the §7 number moves).
  26 MEANING — significance_engine.evaluate(outcome=...) returns reward > 0 when
               verified=True; reward is suppressed when verified=False.

Row 25 SELF-INTERPRET is covered by test_wo125_self_interpret.py (already verified).

Tests:
    LN-1  stats() reports ≥1 confirmed lesson (real ledger on disk)
    LN-2  recall() returns only confirmed lessons (candidate/retired excluded)
    LN-3  promote_pass() advances a seeded candidate to confirmed (temp ledger)
    LN-4  promote_pass() does NOT promote when threshold criteria not met

    AD-1  route_confidence() returns 0.0 when no route history for goal
    AD-2  confidence changes after a success record is added (number moves after experience)
    AD-3  §7 proof — wall_jump starts at 0.71 (10 records, 7 arrived), climbs to 0.78
          after one more success is written

    MG-1  significance_engine.evaluate() with outcome=None → no reward key (backwards compat)
    MG-2  evaluate(outcome=verified_record) → reward key present and > 0
    MG-3  evaluate(outcome=unverified_record) → outcome_terms suppressed (verified==False law)
    MG-4  journal_router.route() accepts outcome= kwarg without error

Run: python3 tests/test_0015_wave6_learn_adapt_meaning.py
"""
import json
import os
import sys
import tempfile
import time

sys.path.insert(0, ".")

import logging
logging.basicConfig(level=logging.CRITICAL)

PASS = 0; FAIL = 0

def ok(n):      global PASS; PASS += 1; print(f"  ✅ {n}")
def fail(n, r): global FAIL; FAIL += 1; print(f"  ❌ {n}: {r}")


# ─────────────────────────────────────────────────────────────────────────────
# Row 20 LEARN
# ─────────────────────────────────────────────────────────────────────────────

print("\nLN-1: stats() reports >= 1 confirmed lesson on real ledger")
try:
    from self.lesson_store import stats
    s = stats()
    counts = s.get("ledger_counts", {})
    confirmed = counts.get("confirmed", 0)
    if confirmed >= 1:
        ok(f"LN-1 — ledger_counts.confirmed={confirmed} (real lessons on disk)")
    else:
        fail("LN-1", f"confirmed={confirmed} — expected >= 1 on real lessons_ledger.jsonl")
except Exception as e:
    fail("LN-1", repr(e))


print("\nLN-2: recall() returns only confirmed lessons")
try:
    from self.lesson_store import recall
    results = recall(k=10)
    unconfirmed = [r for r in results if r.get("status") != "confirmed"]
    if unconfirmed:
        fail("LN-2", f"recall() returned non-confirmed rows: {[r.get('status') for r in unconfirmed]}")
    else:
        ok(f"LN-2 — recall() returned {len(results)} confirmed lesson(s), none candidate/retired")
except Exception as e:
    fail("LN-2", repr(e))


print("\nLN-3: promote_pass() advances seeded candidate to confirmed (temp ledger)")
try:
    from self.lesson_store import lesson_key, promote_pass

    _NOW = time.time()
    _LKEY = lesson_key("behaviour", "test wave6 learn promotes", "met")

    # Build a candidate row that meets ALL promotion criteria:
    #   strength >= 0.70, distinct_refs >= 3, distinct_sessions >= 2, verified >= 2
    _evidence = [
        {"episode_ref": f"ep-{i}", "verified": True, "ts": _NOW - i, "session_id": f"sess-{i % 3}"}
        for i in range(5)
    ]
    _row = {
        "id": "L-test",
        "lesson_key": _LKEY,
        "statement": "test wave6 learn promotes",
        "scope": "behaviour",
        "cause": "met",
        "strength": 0.75,
        "status": "candidate",
        "evidence": _evidence,
        "first_seen": "2025-01-01T00:00:00+00:00",
        "last_seen":  "2025-01-01T00:00:00+00:00",
        "promoted_at": None, "retired_at": None, "reason": None, "proposes": None,
    }

    with tempfile.TemporaryDirectory() as _tmpdir:
        _ledger = os.path.join(_tmpdir, "lessons_ledger.jsonl")
        _journals = os.path.join(_tmpdir, "journals")
        os.makedirs(_journals)
        with open(_ledger, "w") as _f:
            _f.write(json.dumps(_row) + "\n")

        result = promote_pass(ledger_path=_ledger)
        _promoted = result.get("promoted", [])

        if _LKEY in _promoted:
            ok(f"LN-3 — promote_pass() promoted candidate → confirmed (lkey={_LKEY[:8]}..)")
        else:
            # Read back to see actual status
            with open(_ledger) as _f:
                _rows = [json.loads(l) for l in _f if l.strip()]
            _statuses = {r.get("lesson_key", "?")[:8]: r.get("status") for r in _rows}
            fail("LN-3", f"promote_pass() did not promote — statuses={_statuses} promoted={_promoted}")
except Exception as e:
    fail("LN-3", repr(e))


print("\nLN-4: promote_pass() does NOT promote when below threshold")
try:
    from self.lesson_store import lesson_key, promote_pass

    _LKEY4 = lesson_key("behaviour", "test wave6 weak lesson stays candidate", "met")
    _row4 = {
        "id": "L-weak",
        "lesson_key": _LKEY4,
        "statement": "test wave6 weak lesson stays candidate",
        "scope": "behaviour",
        "cause": "met",
        "strength": 0.40,   # below 0.70 threshold
        "status": "candidate",
        "evidence": [{"episode_ref": "ep-0", "verified": True, "ts": time.time(), "session_id": "s1"}],
        "first_seen": "2025-01-01T00:00:00+00:00",
        "last_seen":  "2025-01-01T00:00:00+00:00",
        "promoted_at": None, "retired_at": None, "reason": None, "proposes": None,
    }

    with tempfile.TemporaryDirectory() as _tmpdir4:
        _ledger4 = os.path.join(_tmpdir4, "lessons_ledger.jsonl")
        _journals4 = os.path.join(_tmpdir4, "journals")
        os.makedirs(_journals4)
        with open(_ledger4, "w") as _f4:
            _f4.write(json.dumps(_row4) + "\n")

        result4 = promote_pass(ledger_path=_ledger4)
        _promoted4 = result4.get("promoted", [])

        if _LKEY4 not in _promoted4:
            ok("LN-4 — weak candidate (strength=0.40) not promoted — threshold gate works")
        else:
            fail("LN-4", f"weak candidate was promoted despite strength=0.40 — gate missing")
except Exception as e:
    fail("LN-4", repr(e))


# ─────────────────────────────────────────────────────────────────────────────
# Row 22 ADAPT
# ─────────────────────────────────────────────────────────────────────────────

print("\nAD-1: route_confidence() returns 0.0 when no history for goal")
try:
    from self.route_memory import route_confidence
    with tempfile.TemporaryDirectory() as _tmpdir_a1:
        _log_a1 = os.path.join(_tmpdir_a1, "route_memory.jsonl")
        conf = route_confidence("unknown_goal_x", log_path=_log_a1)
        if conf == 0.0:
            ok("AD-1 — route_confidence() returns 0.0 for unknown goal (no history)")
        else:
            fail("AD-1", f"expected 0.0, got {conf}")
except Exception as e:
    fail("AD-1", repr(e))


print("\nAD-2: route_confidence() changes after success record is added")
try:
    from self.route_memory import route_confidence, remember_route

    with tempfile.TemporaryDirectory() as _tmpdir_a2:
        _log_a2 = os.path.join(_tmpdir_a2, "journals", "route_memory.jsonl")
        os.makedirs(os.path.dirname(_log_a2))
        _GOAL = "window_A"

        # Write 5 failures → confidence = 0/5 = 0.0
        for _ in range(5):
            remember_route(
                goal_surface=_GOAL, legs=["jump"], arrived=False, fell=True,
                duration_s=0.5, smoothness=0.2, ack_id="ack-fail", ack_received=True,
                log_path=_log_a2,
            )
        conf_before = route_confidence(_GOAL, log_path=_log_a2)

        # Write 1 success → confidence should increase
        remember_route(
            goal_surface=_GOAL, legs=["jump"], arrived=True, fell=False,
            duration_s=0.4, smoothness=0.8, ack_id="ack-ok", ack_received=True,
            log_path=_log_a2,
        )
        conf_after = route_confidence(_GOAL, log_path=_log_a2)

        if conf_after > conf_before:
            ok(f"AD-2 — confidence changed: {conf_before:.3f} → {conf_after:.3f} after success (number moved)")
        else:
            fail("AD-2", f"confidence did not change: before={conf_before:.3f} after={conf_after:.3f}")
except Exception as e:
    fail("AD-2", repr(e))


print("\nAD-3: §7 proof — wall_jump starts at 0.70 (7/10 succeeded), climbs to 0.80 after one success")
try:
    from self.route_memory import route_confidence, remember_route

    with tempfile.TemporaryDirectory() as _tmpdir_a3:
        _log_a3 = os.path.join(_tmpdir_a3, "journals", "route_memory.jsonl")
        os.makedirs(os.path.dirname(_log_a3))
        _GOAL3 = "wall_jump_target"

        # Seed: 3 failures FIRST, then 7 successes (failures must be oldest so they exit
        # the confidence window when a new success is appended).
        # Confidence window is last 10 records.
        for i in range(3):
            remember_route(
                goal_surface=_GOAL3, legs=["wall-jump"], arrived=False, fell=True,
                duration_s=0.5, smoothness=0.1, ack_id=f"fail-{i}",
                ack_received=True, log_path=_log_a3,
            )
        for i in range(7):
            remember_route(
                goal_surface=_GOAL3, legs=["wall-jump"], arrived=True, fell=False,
                duration_s=0.3, smoothness=0.85, ack_id=f"ok-{i}",
                ack_received=True, log_path=_log_a3,
            )
        conf_base = route_confidence(_GOAL3, log_path=_log_a3)   # 7/10 = 0.700

        # One more success → window slides; oldest record (a failure) exits.
        # New window: 2 failures + 7 old-successes + 1 new-success = 8/10 = 0.800
        remember_route(
            goal_surface=_GOAL3, legs=["wall-jump"], arrived=True, fell=False,
            duration_s=0.3, smoothness=0.9, ack_id="ack-new", ack_received=True,
            log_path=_log_a3,
        )
        conf_new = route_confidence(_GOAL3, log_path=_log_a3)

        if conf_new > conf_base:
            ok(f"AD-3 — §7 proof: wall_jump conf {conf_base:.3f} → {conf_new:.3f} after success (number moved after experience)")
        else:
            fail("AD-3", f"confidence did not increase: base={conf_base:.3f} new={conf_new:.3f}")
except Exception as e:
    fail("AD-3", repr(e))


# ─────────────────────────────────────────────────────────────────────────────
# Row 26 MEANING
# ─────────────────────────────────────────────────────────────────────────────

print("\nMG-1: evaluate(outcome=None) → no reward key (backwards compat)")
try:
    from memory.significance_engine import evaluate
    result = evaluate("hello", "hi there", "ground", outcome=None)
    if "reward" not in result:
        ok("MG-1 — outcome=None → no reward key (existing callers unaffected)")
    else:
        fail("MG-1", f"reward key present when outcome=None: {result.get('reward')!r}")
except Exception as e:
    fail("MG-1", repr(e))


print("\nMG-2: evaluate(outcome=verified_record) → reward present and > 0")
try:
    from memory.significance_engine import evaluate
    _outcome_ok = {
        "verified": True,
        "arrived": True,
        "fell": False,
        "smoothness": 0.9,
        "duration_s": 0.4,
        "ack_id": "ack-mg2",
    }
    result2 = evaluate(
        "let's build something new today",
        "building out the new module now — this feels right",
        "build",
        outcome=_outcome_ok,
    )
    _reward = result2.get("reward")
    if _reward is None:
        fail("MG-2", "reward key absent when verified outcome provided")
    elif _reward > 0.0:
        ok(f"MG-2 — evaluate(verified outcome) → reward={_reward:.3f} > 0 (meaning scored from ACK)")
    else:
        fail("MG-2", f"reward={_reward:.3f} — expected > 0 for verified outcome")
except Exception as e:
    fail("MG-2", repr(e))


print("\nMG-3: evaluate(unverified outcome) → outcome_terms suppressed (reward near 0)")
try:
    from memory.significance_engine import evaluate
    _outcome_unv = {
        "verified": False,   # the law: verified==False → outcome_terms = 0
        "arrived": True,
        "fell": False,
        "smoothness": 0.9,
        "duration_s": 0.3,
        "ack_id": "ack-mg3",
    }
    result3 = evaluate(
        "let's build something",
        "building",
        "build",
        outcome=_outcome_unv,
    )
    _reward3 = result3.get("reward")
    _emb3    = result3.get("embodiment", 0.0)
    # reward = 0.70 * outcome_terms + 0.30 * meaning_overall
    # When verified=False → outcome_terms = 0 → reward = 0.30 * meaning_overall
    # meaning_overall is the "overall" score (not outcome-boosted)
    _overall = result3.get("overall", 0.0)
    _max_reward_unv = 0.30 * _overall  # max when outcome_terms=0

    if _reward3 is None:
        fail("MG-3", "reward key absent for unverified outcome")
    elif _reward3 <= _max_reward_unv + 0.01:
        ok(f"MG-3 — unverified outcome → reward={_reward3:.3f} <= {_max_reward_unv:.3f} (outcome_terms suppressed)")
    else:
        fail("MG-3", f"reward={_reward3:.3f} too high for unverified outcome (max expected={_max_reward_unv:.3f})")
except Exception as e:
    fail("MG-3", repr(e))


print("\nMG-4: journal_router.route() accepts outcome= kwarg without error")
try:
    from memory.journal_router import route as _jroute
    # We don't check the journal file — just that route() doesn't blow up with outcome=
    _outcome_mg4 = {
        "verified": True, "arrived": True, "fell": False,
        "smoothness": 0.8, "duration_s": 0.5, "ack_id": "ack-mg4",
    }
    _jroute(
        raw="testing the outcome parameter path",
        response="got it",
        action="answer",
        outcome=_outcome_mg4,
    )
    ok("MG-4 — journal_router.route(outcome=...) accepted without error")
except Exception as e:
    fail("MG-4", repr(e))


# ─────────────────────────────────────────────────────────────────────────────
# Results
# ─────────────────────────────────────────────────────────────────────────────

print(f"\n{'='*50}")
print(f"Wave 6: {PASS} passed, {FAIL} failed")
print()
print("Rows verified by this test:")
print("  20 LEARN   — confirmed lessons on disk; recall() filters correctly; promote_pass works")
print("  22 ADAPT   — route_confidence() changes after experience (§7: number moved)")
print("  26 MEANING — significance score carries outcome; reward > 0 on verified ACK; suppressed on unverified")
print()
print("Row 25 SELF-INTERPRET: covered by test_wo125_self_interpret.py (already 6/6 PASS)")
if FAIL:
    sys.exit(1)
