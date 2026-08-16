"""
tests/test_w6_lesson_attribution.py — W6: Lesson Attribution closes LOOP-7

Tests:
    W6-1  CognitivePlan has lesson_id field defaulting to ""
    W6-2  decision_journal.record() accepts learning param and writes it (not hardcoded "")
    W6-3  _executive_faculty amends cal_reason to "lesson: <stmt>" when default routing + lesson recalled
    W6-4  _executive_faculty leaves cal_reason untouched when no lessons recalled
    W6-5  _executive_faculty leaves cal_reason untouched when real signal exists (not default)
    W6-6  plan.lesson_id is set to lesson_key when lesson recalled; "" when not
    W6-7  decision_journal.record() backward-compat: learning defaults to ""

Run: python3 tests/test_w6_lesson_attribution.py
"""
import json
import os
import sys
import tempfile
import unittest.mock as mock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

ok  = lambda msg: print(f"  PASS  {msg}")
err = lambda msg: (print(f"  FAIL  {msg}"), sys.exit(1))


# ── W6-1: CognitivePlan has lesson_id ────────────────────────────────────────
def test_w6_1_plan_has_lesson_id():
    from runtime.spine.plan import CognitivePlan
    p = CognitivePlan()
    if not hasattr(p, "lesson_id"):
        err("W6-1: CognitivePlan missing lesson_id field")
    if p.lesson_id != "":
        err(f"W6-1: lesson_id default should be '' — got {p.lesson_id!r}")
    ok("W6-1: CognitivePlan.lesson_id exists, defaults to ''")


# ── W6-2: decision_journal.record() writes learning param ────────────────────
def test_w6_2_record_writes_learning():
    import inspect
    from self import decision_journal as dj
    sig = inspect.signature(dj.record)
    if "learning" not in sig.parameters:
        err("W6-2: decision_journal.record() missing 'learning' parameter")

    with tempfile.TemporaryDirectory() as tmp:
        j_path = os.path.join(tmp, "journals", "decision_journal.jsonl")
        r_path = os.path.join(tmp, "journals", "action_reliability.json")
        os.makedirs(os.path.dirname(j_path))

        with mock.patch.object(dj, "_JOURNAL", j_path), \
             mock.patch.object(dj, "_RELIABILITY", r_path):
            dj.record(
                turn="test input",
                action="reflect",
                exec_decision={"cal_reason": "lesson: test stmt", "intent": "conversation"},
                backend="mock",
                outcome="spoke",
                learning="abc123lessonkey",
            )

        with open(j_path) as f:
            row = json.loads(f.read().strip())

        if row.get("learning") != "abc123lessonkey":
            err(f"W6-2: expected learning='abc123lessonkey' got {row.get('learning')!r}")

    ok("W6-2: decision_journal.record() writes learning param to journal row")


# ── W6-3: cal_reason amended when default + lesson recalled ──────────────────
def test_w6_3_cal_reason_amended_on_default():
    from runtime.spine.spine import _executive_faculty

    fake_lesson = {
        "lesson_key": "sha1testkey",
        "statement": "David's sitting ACK is always positive",
        "status": "confirmed",
        "strength": 0.90,
        "scope": "behaviour",
        "evidence": [],
    }

    # "indeed" + conversation/neutral/stable always falls through to
    # the default branch in _conversation_action() — returns cal_reason =
    # "default — no stronger signal".  Confirmed by tracing executive.py.
    with mock.patch("self.lesson_store.recall", return_value=[fake_lesson]):
        plan = _executive_faculty(
            raw="indeed",
            language={
                "meaning": "indeed",
                "intent": "conversation",
                "register": "",
                "social": "",
                "confidence": 0.7,
                "intent_chain": [],
            },
            attention={
                "intent": "conversation",
                "emotional_context": {"valence": "neutral", "momentum": "stable"},
            },
            capabilities=[],
            system_det=None,
        )

    if not plan.cal_reason.startswith("lesson:"):
        err(f"W6-3: cal_reason should start with 'lesson:' when Executive defaults and lesson recalled — got {plan.cal_reason!r}")
    if "David's sitting" not in plan.cal_reason:
        err(f"W6-3: lesson stmt not in cal_reason — got {plan.cal_reason!r}")
    ok(f"W6-3: cal_reason amended to {plan.cal_reason!r} — LOOP-7 trigger path confirmed")


# ── W6-4: cal_reason untouched when no lessons recalled ──────────────────────
def test_w6_4_cal_reason_untouched_when_no_lessons():
    from runtime.spine.spine import _executive_faculty

    with mock.patch("self.lesson_store.recall", return_value=[]):
        plan = _executive_faculty(
            raw="what is your name?",
            language={
                "meaning": "what is your name?",
                "intent": "inquiry",
                "register": "",
                "social": "",
                "confidence": 0.9,
                "intent_chain": [],
            },
            attention={"intent": "inquiry", "emotional_context": {}},
            capabilities=[],
            system_det=None,
        )

    if plan.cal_reason.startswith("lesson:"):
        err(f"W6-4: cal_reason should NOT start with 'lesson:' when no lessons recalled — got {plan.cal_reason!r}")
    if plan.lesson_id != "":
        err(f"W6-4: lesson_id should be '' when no lessons — got {plan.lesson_id!r}")
    ok(f"W6-4: cal_reason untouched ({plan.cal_reason!r}), lesson_id='' when no lessons recalled")


# ── W6-5: real signal preserved even when lesson recalled ────────────────────
def test_w6_5_real_signal_not_replaced():
    from runtime.spine.spine import _executive_faculty

    fake_lesson = {
        "lesson_key": "sha1testkey2",
        "statement": "some lesson statement",
        "status": "confirmed",
        "strength": 0.80,
        "scope": "behaviour",
        "evidence": [],
    }

    with mock.patch("self.lesson_store.recall", return_value=[fake_lesson]):
        plan = _executive_faculty(
            raw="what is your name?",
            language={
                "meaning": "what is your name?",
                "intent": "inquiry",
                "register": "",
                "social": "",
                "confidence": 0.9,
                "intent_chain": [],
            },
            attention={"intent": "inquiry", "emotional_context": {}},
            capabilities=[],
            system_det=None,
        )

    # Executive should return "capability question" or "factual question" for "what is your name?"
    # In both cases, cal_reason should NOT be replaced with a lesson
    if plan.cal_reason.startswith("lesson:"):
        err(f"W6-5: real signal should NOT be replaced by lesson — got {plan.cal_reason!r}")
    ok(f"W6-5: real signal preserved ({plan.cal_reason!r}) even when lesson recalled. lesson_id={plan.lesson_id!r}")


# ── W6-6: plan.lesson_id set correctly ───────────────────────────────────────
def test_w6_6_lesson_id_set():
    from runtime.spine.spine import _executive_faculty

    fake_lesson = {
        "lesson_key": "thekey123",
        "statement": "test lesson",
        "status": "confirmed",
        "strength": 0.85,
        "scope": "behaviour",
        "evidence": [],
    }

    with mock.patch("self.lesson_store.recall", return_value=[fake_lesson]):
        plan = _executive_faculty(
            raw="",
            language={
                "meaning": "",
                "intent": "conversation",
                "register": "",
                "social": "",
                "confidence": 0.7,
                "intent_chain": [],
            },
            attention={"intent": "conversation", "emotional_context": {}},
            capabilities=[],
            system_det=None,
        )

    if plan.lesson_id != "thekey123":
        err(f"W6-6: expected lesson_id='thekey123' got {plan.lesson_id!r}")
    ok(f"W6-6: plan.lesson_id={plan.lesson_id!r} correctly threaded from recalled lesson")


# ── W6-7: backward compat — learning defaults to "" ──────────────────────────
def test_w6_7_learning_backward_compat():
    import inspect
    from self import decision_journal as dj
    sig = inspect.signature(dj.record)
    param = sig.parameters.get("learning")
    if param is None:
        err("W6-7: learning param missing from record()")
    if param.default != "":
        err(f"W6-7: learning param default should be '' — got {param.default!r}")
    ok("W6-7: decision_journal.record() backward-compat — learning defaults to '' (existing callers unaffected)")


# ── runner ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("W6 — LESSON ATTRIBUTION (closes LOOP-7)")
    print()
    test_w6_1_plan_has_lesson_id()
    test_w6_2_record_writes_learning()
    test_w6_3_cal_reason_amended_on_default()
    test_w6_4_cal_reason_untouched_when_no_lessons()
    test_w6_5_real_signal_not_replaced()
    test_w6_6_lesson_id_set()
    test_w6_7_learning_backward_compat()
    print()
    print("7/7 PASS — W6 lesson attribution wired")
    print()
    print("LOOP-7 closes when:")
    print("  1. Server runs a turn where Executive defaults AND lessons are recalled")
    print("  2. trigger field = 'lesson: <statement>'")
    print("  3. Re-run tests/test_loop_one_brain.py — LOOP-7 goes green")
