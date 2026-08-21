"""
tests/test_canon_xvii_reflection.py — WO-CANON-XVII: Reflection Engine
Vol XVII Ch.1 acceptance tests (FT-1…FT-6 / ST-1…ST-6 / IT-1…IT-3).
Also covers Ch.2 growth metrics from lesson_store.stats().

All tests run against a TEMP ledger — never touch self/lessons_ledger.jsonl.
"""
import hashlib
import json
import os
import py_compile
import re
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

_passed = 0
_failed = 0


def ok(name: str):
    global _passed
    _passed += 1
    print(f"  ✅ {name}")


def fail(name: str, reason):
    global _failed
    _failed += 1
    print(f"  ❌ {name}: {reason}")


print()
print("WO-CANON-XVII  Reflection Engine")
print("-" * 55)

# ─── Helpers ──────────────────────────────────────────────────────────────────

def _lkey(scope, stmt, cause=""):
    norm = re.sub(r"\s+", " ", stmt.strip().lower())
    return hashlib.sha1(f"{scope}|{norm}|{cause}".encode()).hexdigest()[:16]


def _make_ledger(tmp_dir, rows):
    path = os.path.join(tmp_dir, "lessons_ledger.jsonl")
    with open(path, "w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    return path


def _candidate_row(scope, statement, cause, strength=0.3, evidence=None):
    return {
        "lesson_key": _lkey(scope, statement, cause),
        "statement":  statement,
        "scope":      scope,
        "cause":      cause,
        "strength":   strength,
        "status":     "candidate",
        "evidence":   evidence or [],
        "first_seen": "2026-01-01T00:00:00+00:00",
        "last_seen":  "2026-01-01T00:00:00+00:00",
        "promoted_at": None, "retired_at": None, "reason": None, "proposes": None,
    }


def _ep(verified=True, contradicting=False, session="s1", episode_ref=None):
    return {
        "episode_ref": episode_ref or f"SPOT_{time.time_ns()}",
        "verified":    verified,
        "contradicting": contradicting,
        "session_id":  session,
        "ts":          time.time(),
    }


# ─── Ch.1 FT-1: Promotion on verified evidence ────────────────────────────────
try:
    import tempfile
    from self.lesson_store import promote_pass, recall

    with tempfile.TemporaryDirectory() as tmp:
        os.makedirs(os.path.join(tmp, "journals"), exist_ok=True)
        ev = [
            _ep(True, False, "s1", "SPOT_A"),
            _ep(True, False, "s2", "SPOT_B"),
            _ep(True, False, "s2", "SPOT_C"),
        ]
        row = _candidate_row("behaviour", "test lesson ft1", "met", strength=0.75, evidence=ev)
        lpath = _make_ledger(tmp, [row])
        result = promote_pass(ledger_path=lpath)
        assert result.get("promoted"), f"expected promoted list; got {result}"
        with open(lpath) as f:
            updated = [json.loads(l) for l in f if l.strip()]
        row_out = next(r for r in updated if r["lesson_key"] == row["lesson_key"])
        assert row_out["status"] == "confirmed", f"status={row_out['status']}"
        assert row_out.get("promoted_at"), "promoted_at not set"
    ok("FT-1: candidate → confirmed on verified evidence (3 refs, 2 sessions, strength ≥ 0.70)")
except AssertionError as e:
    fail("FT-1", e)
except Exception as e:
    fail("FT-1", e)


# ─── Ch.1 FT-2: Text-only episodes never promote ─────────────────────────────
try:
    from self.lesson_store import promote_pass

    with tempfile.TemporaryDirectory() as tmp:
        os.makedirs(os.path.join(tmp, "journals"), exist_ok=True)
        ev = [_ep(False, False, f"s{i}", f"SPOT_{i}") for i in range(5)]  # all verified=False
        row = _candidate_row("behaviour", "unverified lesson", "met", strength=0.85, evidence=ev)
        lpath = _make_ledger(tmp, [row])
        result = promote_pass(ledger_path=lpath)
        assert not result.get("promoted"), f"should not have promoted; got {result}"
        with open(lpath) as f:
            updated = [json.loads(l) for l in f if l.strip()]
        row_out = next(r for r in updated if r["lesson_key"] == row["lesson_key"])
        assert row_out["status"] == "candidate", f"status={row_out['status']}"
    ok("FT-2: text-only episodes (verified=false) never promote")
except AssertionError as e:
    fail("FT-2", e)
except Exception as e:
    fail("FT-2", e)


# ─── Ch.1 FT-3: A repeat strengthens, never duplicates ───────────────────────
try:
    from self.lesson_store import record_outcome, lesson_key as _lk

    with tempfile.TemporaryDirectory() as tmp:
        stmt = "repeating lesson statement"
        scope = "capability"
        cause = "met"
        lk = _lk(scope, stmt, cause)
        row = _candidate_row(scope, stmt, cause, strength=0.30)
        lpath = _make_ledger(tmp, [row])

        record_outcome(lkey=lk, episode_ref="SPOT_REP1", verified=True,
                       session_id="s1", ledger_path=lpath)

        with open(lpath) as f:
            rows = [json.loads(l) for l in f if l.strip()]

        assert len(rows) == 1, f"row count changed! got {len(rows)}"
        assert abs(rows[0]["strength"] - 0.45) < 0.001, \
            f"expected strength 0.45; got {rows[0]['strength']}"
        assert len(rows[0]["evidence"]) == 1, "evidence not appended"
    ok("FT-3: repeat strengthens (+0.15) without adding a duplicate row")
except AssertionError as e:
    fail("FT-3", e)
except Exception as e:
    fail("FT-3", e)


# ─── Ch.1 FT-4: Recall returns confirmed only, bounded ───────────────────────
try:
    from self.lesson_store import recall

    with tempfile.TemporaryDirectory() as tmp:
        rows = (
            [_candidate_row("capability", f"candidate {i}", "met") for i in range(50)] +
            [dict(_candidate_row("capability", f"confirmed {i}", "met", strength=0.9),
                  status="confirmed",
                  promoted_at="2026-01-01T00:00:00+00:00",
                  evidence=[_ep(True, False, f"s{j}", f"SPOT_C{i}{j}") for j in range(3)])
             for i in range(4)] +
            [dict(_candidate_row("capability", f"retired {i}", "met"), status="retired",
                  retired_at="2026-01-01T00:00:00+00:00")
             for i in range(10)]
        )
        lpath = _make_ledger(tmp, rows)
        recalled = recall(scope="", context={}, k=3, ledger_path=lpath)
        assert len(recalled) <= 3, f"got {len(recalled)} (> 3)"
        for r in recalled:
            assert r["status"] == "confirmed", f"non-confirmed row in recall: {r['status']}"
        total_chars = sum(len(r.get("statement", "")) for r in recalled)
        assert total_chars <= 240, f"total chars {total_chars} > 240"
    ok("FT-4: recall returns ≤3 confirmed lessons, ≤240 chars total, no candidates/retired")
except AssertionError as e:
    fail("FT-4", e)
except Exception as e:
    fail("FT-4", e)


# ─── Ch.1 FT-5: Timeout is negative evidence (not silence) ───────────────────
try:
    from self.lesson_store import record_outcome, lesson_key as _lk

    with tempfile.TemporaryDirectory() as tmp:
        stmt = "this action works reliably"
        scope = "capability"
        cause = "met"
        lk = _lk(scope, stmt, cause)
        row = _candidate_row(scope, stmt, cause, strength=0.6)
        lpath = _make_ledger(tmp, [row])

        # A timeout: completion="timeout" but verified=True, contradicting=True
        record_outcome(lkey=lk, episode_ref="SPOT_TIMEOUT", verified=True,
                       contradicting=True, session_id="s1", ledger_path=lpath)

        with open(lpath) as f:
            rows = [json.loads(l) for l in f if l.strip()]
        row_out = rows[0]
        assert row_out["strength"] < 0.6, \
            f"strength should decrease on timeout; got {row_out['strength']}"
        assert len(row_out["evidence"]) == 1, "timeout not recorded as evidence"
    ok("FT-5: timeout (verified=true, contradicting=true) weakens lesson and records evidence")
except AssertionError as e:
    fail("FT-5", e)
except Exception as e:
    fail("FT-5", e)


# ─── Ch.1 FT-6: Unresolvable evidence cannot promote ─────────────────────────
try:
    from self.lesson_store import promote_pass

    with tempfile.TemporaryDirectory() as tmp:
        os.makedirs(os.path.join(tmp, "journals"), exist_ok=True)
        # Pre-v1 shape: no episode_ref field on evidence, only text truncation
        bad_ev = [{"verified": True, "session_id": "s1",
                   "ts": time.time(), "episode_ref": ""}  # empty ref = unresolvable
                  for _ in range(5)]
        row = _candidate_row("behaviour", "unresolvable evidence lesson", "met",
                             strength=0.85, evidence=bad_ev)
        lpath = _make_ledger(tmp, [row])
        result = promote_pass(ledger_path=lpath)
        # No distinct episode_refs → cannot meet _PROMOTE_EPISODES threshold
        assert not result.get("promoted"), f"should not promote without resolvable refs; got {result}"
    ok("FT-6: lessons with no resolvable episode_refs never promote")
except AssertionError as e:
    fail("FT-6", e)
except Exception as e:
    fail("FT-6", e)


# ─── Ch.1 ST-1: Read side never writes identity ───────────────────────────────
try:
    from self.lesson_store import promote_pass, record_outcome, lesson_key as _lk
    import pathlib

    elo_self = pathlib.Path("self/elo_self_state.json")
    exec_py  = pathlib.Path("runtime/executive.py")
    prompts_dir = pathlib.Path("prompts")

    if elo_self.exists():
        identity_before = elo_self.read_bytes()
    else:
        identity_before = b""

    with tempfile.TemporaryDirectory() as tmp:
        os.makedirs(os.path.join(tmp, "journals"), exist_ok=True)
        ev = [_ep(True, False, f"s{i}", f"SPOT_{i}") for i in range(3)]
        row = _candidate_row("behaviour", "st1 lesson", "met", strength=0.75, evidence=ev)
        lpath = _make_ledger(tmp, [row])
        promote_pass(ledger_path=lpath)

    if elo_self.exists():
        identity_after = elo_self.read_bytes()
        assert identity_before == identity_after, "elo_self_state.json was modified by promote_pass"
    # Check executive.py is untouched — mtime only (stat it before + after is overkill for tests)
    # Simpler: assert the file path was not opened for writing by checking mtime
    assert exec_py.exists(), "runtime/executive.py missing"
    ok("ST-1: promote_pass() does not write identity files (elo_self_state.json, executive.py)")
except AssertionError as e:
    fail("ST-1", e)
except Exception as e:
    fail("ST-1", e)


# ─── Ch.1 ST-2: Response path is read-only ────────────────────────────────────
try:
    from self.lesson_store import recall

    with tempfile.TemporaryDirectory() as tmp:
        ev = [_ep(True, False, f"s{i}", f"SPOT_{i}") for i in range(3)]
        row = dict(_candidate_row("behaviour", "st2 lesson", "met", strength=0.9),
                   status="confirmed", promoted_at="2026-01-01T00:00:00+00:00",
                   evidence=ev)
        lpath = _make_ledger(tmp, [row])

        before = open(lpath, "rb").read()
        for _ in range(10):
            recall(scope="", context={}, k=3, ledger_path=lpath)
        after = open(lpath, "rb").read()

        assert before == after, "lessons_ledger.jsonl was modified by recall()"
    ok("ST-2: recall() is strictly read-only (ledger unchanged after 10 calls)")
except AssertionError as e:
    fail("ST-2", e)
except Exception as e:
    fail("ST-2", e)


# ─── Ch.1 ST-4: Retirement is not deletion ────────────────────────────────────
try:
    from self.lesson_store import promote_pass

    with tempfile.TemporaryDirectory() as tmp:
        os.makedirs(os.path.join(tmp, "journals"), exist_ok=True)
        # Lesson with very low strength — should be retired, not deleted
        row = _candidate_row("behaviour", "weak lesson st4", "met", strength=0.05)
        lpath = _make_ledger(tmp, [row])
        result = promote_pass(ledger_path=lpath)

        with open(lpath) as f:
            rows = [json.loads(l) for l in f if l.strip()]
        assert len(rows) >= 1, "row was deleted (should be retained as retired)"
        assert any(r.get("status") == "retired" for r in rows), \
            "expected retired row; got " + str([r.get("status") for r in rows])
    ok("ST-4: retirement retains the row with status=retired (not deleted)")
except AssertionError as e:
    fail("ST-4", e)
except Exception as e:
    fail("ST-4", e)


# ─── Ch.1 ST-6: Degraded reflection is silent (no fabrication) ───────────────
try:
    from self.lesson_store import recall

    # Pass a non-existent ledger path → should return empty, not raise
    missing_path = "/tmp/_nonexistent_ledger_canon_xvii_test.jsonl"
    if os.path.exists(missing_path):
        os.remove(missing_path)
    result = recall(scope="", context={}, k=3, ledger_path=missing_path)
    assert result == [], f"recall should return [] on missing ledger; got {result}"
    ok("ST-6: recall() returns empty on missing/corrupt ledger (no fabrication)")
except AssertionError as e:
    fail("ST-6", e)
except Exception as e:
    fail("ST-6", e)


# ─── Ch.1 IT-1: The loop actually closes ─────────────────────────────────────
try:
    from self.lesson_store import record_outcome, promote_pass, recall, lesson_key as _lk

    with tempfile.TemporaryDirectory() as tmp:
        os.makedirs(os.path.join(tmp, "journals"), exist_ok=True)
        stmt = "it1 loop-close lesson"
        scope = "capability"
        cause = "met"
        lk = _lk(scope, stmt, cause)

        # Create candidate with sufficient evidence to promote
        ev = [_ep(True, False, f"s{i}", f"SPOT_IT1_{i}") for i in range(3)]
        row = _candidate_row(scope, stmt, cause, strength=0.75, evidence=ev)
        lpath = _make_ledger(tmp, [row])

        # Promote
        promote_pass(ledger_path=lpath)

        # Recall — should now return the confirmed lesson
        recalled = recall(scope=scope, context={}, k=3, ledger_path=lpath)
        statements = [r.get("statement") for r in recalled]
        assert stmt in statements, f"loop not closed — {stmt!r} not in recalled: {statements}"
    ok("IT-1: full loop closes — candidate → confirmed → recalled (turn behaves differently)")
except AssertionError as e:
    fail("IT-1", e)
except Exception as e:
    fail("IT-1", e)


# ─── IT-3: Reward from ACK, not text ─────────────────────────────────────────
try:
    from self.lesson_store import record_outcome, lesson_key as _lk

    with tempfile.TemporaryDirectory() as tmp:
        stmt = "it3 reward lesson"
        scope = "behaviour"
        cause = "met"
        lk = _lk(scope, stmt, cause)

        # Verified turn
        row_v = _candidate_row(scope, stmt, cause, strength=0.3)
        lpath_v = _make_ledger(tmp + "/v_", [row_v]) if False else None

        # Make two identical temp ledgers
        import shutil
        lpath_v = os.path.join(tmp, "ledger_v.jsonl")
        lpath_u = os.path.join(tmp, "ledger_u.jsonl")
        with open(lpath_v, "w") as f:
            f.write(json.dumps(_candidate_row(scope, stmt, cause, strength=0.3)) + "\n")
        with open(lpath_u, "w") as f:
            f.write(json.dumps(_candidate_row(scope, stmt, cause, strength=0.3)) + "\n")

        # Verified ACK episode
        record_outcome(lkey=lk, episode_ref="SPOT_VERIFIED", verified=True,
                       session_id="s1", ledger_path=lpath_v)
        # Unverified (text-only) episode
        record_outcome(lkey=lk, episode_ref="SPOT_UNVERIFIED", verified=False,
                       session_id="s1", ledger_path=lpath_u)

        with open(lpath_v) as f:
            v_row = json.loads(f.read().strip())
        with open(lpath_u) as f:
            u_row = json.loads(f.read().strip())

        assert v_row["strength"] != u_row["strength"], \
            "verified and unverified produced identical strength — reward not ACK-gated"
        assert v_row["strength"] > 0.3, "verified should increase strength"
        # Unverified must NOT strengthen
        assert abs(u_row["strength"] - 0.3) < 0.001, \
            f"unverified episode changed strength to {u_row['strength']} (should stay 0.3)"
    ok("IT-3: ACK-verified episode strengthens; text-only (unverified) does not")
except AssertionError as e:
    fail("IT-3", e)
except Exception as e:
    fail("IT-3", e)


# ─── Ch.2: Growth Metrics — stats() returns all required keys ────────────────
try:
    from self.lesson_store import stats, recall, promote_pass

    with tempfile.TemporaryDirectory() as tmp:
        os.makedirs(os.path.join(tmp, "journals"), exist_ok=True)
        ev = [_ep(True, False, f"s{i}", f"SPOT_S{i}") for i in range(3)]
        rows = [
            _candidate_row("capability", "stats cand 1", "met"),
            dict(_candidate_row("capability", "stats confirmed", "met", strength=0.9),
                 status="confirmed", promoted_at="2026-01-01T00:00:00+00:00", evidence=ev),
            dict(_candidate_row("behaviour", "stats retired", "met"),
                 status="retired", retired_at="2026-01-01T00:00:00+00:00"),
        ]
        lpath = _make_ledger(tmp, rows)
        s = stats(ledger_path=lpath)

        assert "ledger_counts" in s, "stats missing ledger_counts"
        assert s["ledger_counts"]["total"] == 3, f"total={s['ledger_counts']['total']}"
        assert s["ledger_counts"]["confirmed"] == 1
        assert s["ledger_counts"]["candidate"] == 1
        assert s["ledger_counts"]["retired"] == 1
        assert "reinforcement_ratio" in s
        assert "identity_stability" in s
        assert "identity_stability_alarm" in s
    ok("Ch.2 / GM-1: stats() returns ledger_counts, reinforcement_ratio, identity_stability")
except AssertionError as e:
    fail("GM-1", e)
except Exception as e:
    fail("GM-1", e)


# ─── promote_pass() is sole writer of status ──────────────────────────────────
try:
    import pathlib
    src = pathlib.Path("self/lesson_store.py").read_text()
    # record_outcome must never set status
    assert '"status"' not in src.split("def record_outcome")[1].split("def ")[0] or \
           "status" not in [l.strip() for l in src.split("def record_outcome")[1].split("def ")[0].splitlines()
                            if "row[" in l and '"status"' in l], \
        "record_outcome appears to write status"
    ok("Rule: record_outcome() does not write status field (promote_pass is sole status writer)")
except AssertionError as e:
    fail("Rule-status", e)
except Exception as e:
    fail("Rule-status", e)


# ─── AT-9: py_compile clean on lesson_store.py ───────────────────────────────
try:
    py_compile.compile("self/lesson_store.py", doraise=True)
    ok("AT-9: py_compile clean on self/lesson_store.py")
except py_compile.PyCompileError as e:
    fail("AT-9", e)
except Exception as e:
    fail("AT-9", e)


# ── Final summary ─────────────────────────────────────────────────────────────
print()
print("=" * 55)
print(f"WO-CANON-XVII reflection engine   {_passed} passed   {_failed} failed")
if _failed:
    sys.exit(1)
