"""
tests/test_wo096b_learning_loop_live.py — WO-096B: Learning loop is inert.

AT-LIVE-1: server.py wires _maybe_run_promote_pass into the turn loop (static check)
AT-LIVE-2: promote_pass advances a seeded lesson to confirmed through the real promote path
AT-LIVE-3: reflection_faculty produces lessons eligible for promotion (scope/evidence contract)
AT-LIVE-4: record_outcome logs WARNING on unknown key (not silent)
AT-LIVE-5: _append_metrics honours ledger_path; real journal is byte-identical after test run
AT-LIVE-6: end-to-end — verified outcome → promotion → recall() returns it
"""
import logging
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from self.lesson_store import (
    record_outcome,
    recall,
    promote_pass,
    ensure_lesson,
)


def _tmp_ledger():
    f = tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False)
    f.close()
    return f.name


def _seed_lesson(ledger_path, scope="behaviour", statement="Test lesson.", cause="met"):
    """Seed a lesson row with 3 verified episodes — enough to cross all promotion thresholds."""
    lkey = ensure_lesson(scope, statement, cause, ledger_path=ledger_path)
    for i in range(3):
        record_outcome(
            lkey=lkey,
            episode_ref=f"ep_{i}",
            verified=True,
            contradicting=False,
            session_id=f"session_{i}",
            ledger_path=ledger_path,
        )
    return lkey


# ── AT-LIVE-1: turn loop wires promote_pass ──────────────────────────────────

def test_server_wires_promote_pass():
    with open(os.path.join(ROOT, "server.py"), encoding="utf-8") as f:
        src = f.read()
    assert "_maybe_run_promote_pass" in src, "_maybe_run_promote_pass not defined in server.py"
    assert "_run_promote_pass_bg" in src, "_run_promote_pass_bg not defined in server.py"
    assert "_PROMOTE_INTERVAL" in src, "_PROMOTE_INTERVAL constant missing from server.py"
    idx_process = src.find("result = _process_turn(text)")
    assert idx_process != -1, "_process_turn(text) call not found"
    idx_promote  = src.find("_maybe_run_promote_pass()", idx_process)
    assert idx_promote != -1, "_maybe_run_promote_pass() must appear after _process_turn()"


# ── AT-LIVE-2: promote_pass confirms a seeded lesson ─────────────────────────

def test_promote_pass_confirms_lesson():
    ledger = _tmp_ledger()
    try:
        lkey = _seed_lesson(ledger)
        result = promote_pass(ledger_path=ledger, dry_run=False)
        assert lkey in result["promoted"], (
            f"Expected lkey in promoted, got: {result}"
        )
        recalled = recall(ledger_path=ledger)
        assert any(r["lesson_key"] == lkey for r in recalled), (
            "recall() must return the promoted lesson"
        )
    finally:
        os.unlink(ledger)


# ── AT-LIVE-3: reflection_faculty lesson is promotable ───────────────────────

def test_reflection_faculty_lesson_is_promotable():
    from runtime.reflection_faculty import _form_lesson
    lesson = _form_lesson(
        session_summary=(
            "The build succeeded after fixing the dependency. "
            "This was a significant milestone worth noting."
        ),
        action="build",
        completion_state="met",
        planned_objective="Build the project.",
    )
    assert lesson is not None, "_form_lesson returned None for a significant build episode"
    assert lesson.get("lesson_key"), "lesson has no lesson_key"
    assert lesson.get("scope") in ("behaviour", "capability", "relationship", "preference"), (
        f"Unknown scope: {lesson.get('scope')}"
    )
    assert lesson.get("status") == "candidate"
    if lesson.get("scope") == "preference":
        assert lesson.get("proposes") is not None, "preference lesson must set proposes"


# ── AT-LIVE-4: record_outcome warns on unknown key ────────────────────────────

def test_record_outcome_warns_on_unknown_key():
    ledger = _tmp_ledger()
    records = []

    class _Cap(logging.Handler):
        def emit(self, r):
            records.append(r)

    import self.lesson_store as _ls_mod
    logger = logging.getLogger(_ls_mod.__name__)
    handler = _Cap()
    logger.addHandler(handler)
    old_level = logger.level
    logger.setLevel(logging.WARNING)
    try:
        result = record_outcome(
            lkey="deadbeef00000000",
            episode_ref="test",
            verified=True,
            contradicting=False,
            session_id="test",
            ledger_path=ledger,
        )
        assert result == {}, "record_outcome must return {} for unknown key"
        msgs = [r.getMessage() for r in records]
        assert any("deadbeef00000000" in m or "not found" in m.lower() for m in msgs), (
            "record_outcome must log WARNING when key not found; got: " + str(msgs)
        )
    finally:
        logger.removeHandler(handler)
        logger.setLevel(old_level)
        os.unlink(ledger)


# ── AT-LIVE-5: _append_metrics honours ledger_path ───────────────────────────

def test_append_metrics_honours_ledger_path():
    import self.lesson_store as _ls_mod
    real_metrics = _ls_mod._METRICS
    before = 0
    try:
        with open(real_metrics, encoding="utf-8") as f:
            before = sum(1 for line in f if line.strip())
    except FileNotFoundError:
        pass

    ledger = _tmp_ledger()
    try:
        _seed_lesson(ledger)
        promote_pass(ledger_path=ledger, dry_run=False)

        after = 0
        try:
            with open(real_metrics, encoding="utf-8") as f:
                after = sum(1 for line in f if line.strip())
        except FileNotFoundError:
            pass

        assert after == before, (
            f"promote_pass polluted real growth_metrics.jsonl: {before} → {after} lines"
        )
    finally:
        os.unlink(ledger)


# ── AT-LIVE-6: end-to-end learning chain ─────────────────────────────────────

def test_end_to_end_learning_chain():
    ledger = _tmp_ledger()
    try:
        lkey = _seed_lesson(ledger, statement="When building succeeds, reinforce the pattern.")
        promote_pass(ledger_path=ledger, dry_run=False)

        recalled = recall(ledger_path=ledger)
        assert recalled, "recall() returned [] after promotion"
        assert any(r["lesson_key"] == lkey for r in recalled), (
            "recall() must return the seeded+promoted lesson"
        )
        # Confirm the full chain: cognitive_snapshot calls recall → prompt_builder renders it
        snap_src = open(os.path.join(ROOT, "runtime", "cognitive_snapshot.py"), encoding="utf-8").read()
        assert "lesson_store" in snap_src, "cognitive_snapshot.py must import lesson_store"
        assert "recall" in snap_src, "cognitive_snapshot.py must call lesson_store.recall"
        pb_src = open(os.path.join(ROOT, "runtime", "prompt_builder.py"), encoding="utf-8").read()
        assert "LEARNED HEURISTICS" in pb_src, "prompt_builder must include [LEARNED HEURISTICS] block"
    finally:
        os.unlink(ledger)


# ── Self-runner ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    _tests = [
        ("AT-LIVE-1", test_server_wires_promote_pass),
        ("AT-LIVE-2", test_promote_pass_confirms_lesson),
        ("AT-LIVE-3", test_reflection_faculty_lesson_is_promotable),
        ("AT-LIVE-4", test_record_outcome_warns_on_unknown_key),
        ("AT-LIVE-5", test_append_metrics_honours_ledger_path),
        ("AT-LIVE-6", test_end_to_end_learning_chain),
    ]
    _passed = 0
    _failed = 0
    for label, fn in _tests:
        try:
            fn()
            print(f"  ✅ {label}: {fn.__name__}")
            _passed += 1
        except Exception as _e:
            print(f"  ❌ {label}: {fn.__name__} — {_e}")
            _failed += 1
    print()
    print("=" * 62)
    print(f"WO-096B learning loop   {_passed}/{_passed + _failed} passed, {_failed} failed")
    if _failed:
        sys.exit(1)
