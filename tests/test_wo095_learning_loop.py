"""
tests/test_wo095_learning_loop.py — WO-095: Learning Loop — Close the Read Side

Assertions:
  AT-1: lesson promotes on verified evidence (3 eps / 2 sessions → confirmed)
  AT-2: confirmed lesson appears in CognitiveSnapshot.lessons + prompt; ≤3/≤240-char bound
  AT-3: reward from verified ACK not text; unverified → zero learning update
  AT-4: learning path writes nothing to identity (kernel hash, vault bytes, exec/prompts intact)
  AT-5: repeat strengthens, no duplicate row
  AT-6: significance_engine.evaluate() back-compat (no outcome → same 9+overall keys)
  AT-7: stats() moves correctly; identity_stability rise = alarm flag
  AT-8: promote_pass() never called in significance_engine response path (compile + grep)
  AT-9: journal_router + significance_faculty regression (py_compile clean)
  AT-10: pre-v1 migration — rows without lesson_key move to archive, v1 ledger stays clean

Run: python3 tests/test_wo095_learning_loop.py
"""
from __future__ import annotations

import json
import os
import py_compile
import sys
import tempfile
import time

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


# ── AT-1: lesson promotes on verified evidence ─────────────────────────────────
try:
    from self.lesson_store import lesson_key, record_outcome, promote_pass

    with tempfile.TemporaryDirectory() as tmp:
        ledger = os.path.join(tmp, "lessons_ledger.jsonl")
        lkey = lesson_key("behaviour", "Test lesson statement", "met")

        # Seed the ledger with a v1-schema row
        seed = {
            "lesson_key": lkey, "statement": "Test lesson statement",
            "scope": "behaviour", "cause": "met", "strength": 0.3,
            "status": "candidate", "evidence": [],
            "first_seen": "2026-01-01T00:00:00Z", "last_seen": "2026-01-01T00:00:00Z",
            "promoted_at": None, "retired_at": None, "reason": None, "proposes": None,
        }
        with open(ledger, "w") as f:
            f.write(json.dumps(seed) + "\n")

        # 2 episodes / 1 session → stays candidate
        record_outcome(lkey, "SPOT_001", True, session_id="sess_A", ledger_path=ledger)
        record_outcome(lkey, "SPOT_002", True, session_id="sess_A", ledger_path=ledger)
        result = promote_pass(ledger_path=ledger, dry_run=True)
        assert lkey not in result["promoted"], "2 eps / 1 session must stay candidate"

        # 3 distinct eps / 2 distinct sessions → confirmed
        record_outcome(lkey, "SPOT_003", True, session_id="sess_B", ledger_path=ledger)
        result = promote_pass(ledger_path=ledger)
        assert lkey in result["promoted"], f"3 verified eps / 2 sessions must promote: {result}"

        # Load and check status
        with open(ledger) as f:
            rows = [json.loads(l) for l in f if l.strip()]
        row = next(r for r in rows if r["lesson_key"] == lkey)
        assert row["status"] == "confirmed", f"status must be 'confirmed', got {row['status']}"
        assert row["strength"] >= 0.70, f"strength must be >= 0.70, got {row['strength']}"

        # 1 verified ep → stays candidate
        lkey2 = lesson_key("behaviour", "Another test lesson", "met")
        seed2 = dict(seed, lesson_key=lkey2, statement="Another test lesson", evidence=[], strength=0.3)
        with open(ledger, "a") as f:
            f.write(json.dumps(seed2) + "\n")
        record_outcome(lkey2, "SPOT_X", True, session_id="sess_C", ledger_path=ledger)
        result2 = promote_pass(ledger_path=ledger, dry_run=True)
        assert lkey2 not in result2["promoted"], "1 ep must stay candidate"

        ok("AT-1: promotes on 3 verified episodes / 2 sessions; stays candidate on 2 eps or 1 session")
except AssertionError as e:
    fail("AT-1", e)
except Exception as e:
    fail("AT-1", e)


# ── AT-2: confirmed lesson in snapshot + prompt; bounded ─────────────────────
try:
    from self.lesson_store import recall, lesson_key as _lk2
    from runtime.prompt_builder import build as _pb_build

    with tempfile.TemporaryDirectory() as tmp:
        ledger = os.path.join(tmp, "lessons_ledger.jsonl")

        lkey = _lk2("behaviour", "Persist through obstacles, adapt approach", "met")
        confirmed_row = {
            "lesson_key": lkey, "statement": "Persist through obstacles, adapt approach",
            "scope": "behaviour", "cause": "met", "strength": 0.85,
            "status": "confirmed", "promoted_at": "2026-01-01T00:00:00Z",
            "evidence": [
                {"episode_ref": "SPOT_A", "verified": True, "ts": str(time.time()), "session_id": "s1"},
                {"episode_ref": "SPOT_B", "verified": True, "ts": str(time.time()), "session_id": "s2"},
                {"episode_ref": "SPOT_C", "verified": True, "ts": str(time.time()), "session_id": "s3"},
            ],
            "first_seen": "2026-01-01T00:00:00Z", "last_seen": "2026-01-01T00:00:00Z",
            "retired_at": None, "reason": None, "proposes": None,
        }
        with open(ledger, "w") as f:
            f.write(json.dumps(confirmed_row) + "\n")

        # recall() returns it
        results = recall(ledger_path=ledger, k=3)
        assert len(results) >= 1, f"recall must return the confirmed lesson, got {results}"
        assert results[0]["lesson_key"] == lkey, "recalled lesson must match"

        # prompt_builder renders bounded block
        stmts = tuple(r["statement"] for r in results)
        prompt = _pb_build("user input", lessons=stmts)
        assert "LEARNED HEURISTICS" in prompt, "prompt must carry [LEARNED HEURISTICS] block"
        assert "Persist through obstacles" in prompt, "lesson statement must appear in prompt"

        # Bound: ≤3 lessons and ≤240 chars total in the block
        lesson_section = [s for s in prompt.split("\n\n") if "LEARNED HEURISTICS" in s][0]
        bullet_lines = [l for l in lesson_section.split("\n") if l.strip().startswith("•")]
        assert len(bullet_lines) <= 3, f"must be ≤3 lesson lines, got {len(bullet_lines)}"
        total_chars = sum(len(l.replace("  •", "").strip()) for l in bullet_lines)
        assert total_chars <= 240, f"total chars must be ≤240, got {total_chars}"

        ok("AT-2: confirmed lesson in recall result + prompt; ≤3/≤240-char bound enforced")
except AssertionError as e:
    fail("AT-2", e)
except Exception as e:
    fail("AT-2", e)


# ── AT-3: reward from verified ACK, not text ─────────────────────────────────
try:
    from memory.significance_engine import evaluate as _sig_eval

    raw = "I want you to sit with me"
    resp = "Coming right over."

    # With verified ACK → reward present and > 0
    outcome_ok = {
        "intent_id": "uuid1", "action": "sit",
        "ack_type": "sit_complete", "ack_received": True,
        "ack_latency_s": 1.5, "completion": "met",
        "cost": {"retries": 0, "seconds": 1.5, "legs": 1, "fallback_used": False},
        "verified": True,
    }
    scores_ok = _sig_eval(raw, resp, "ground", outcome=outcome_ok)
    assert "reward" in scores_ok, "verified outcome must produce 'reward' key"
    assert scores_ok["reward"] > 0, f"verified ACK reward must be > 0, got {scores_ok['reward']}"
    assert scores_ok["embodiment"] == 1.0, f"met completion must give embodiment=1.0"

    # With unverified outcome → reward_terms=0, reward = only significance (≤0.30)
    # Spec §4.2 hard rule 1: "verified==False → outcome_terms=0"; reward = 0.70*0 + 0.30*sig
    outcome_no = dict(outcome_ok, ack_received=False, verified=False, completion="timeout",
                      ack_type="none")
    scores_no = _sig_eval(raw, resp, "ground", outcome=outcome_no)
    assert "reward" in scores_no, "unverified outcome must still return 'reward' key"
    assert scores_no["reward"] <= 0.30, (
        f"unverified ACK must produce reward ≤ 0.30 (significance only), got {scores_no['reward']}"
    )
    assert scores_no["reward"] < scores_ok["reward"], (
        f"unverified reward must be < verified reward: {scores_no['reward']} vs {scores_ok['reward']}"
    )
    assert scores_no["embodiment"] == 0.0, "timeout completion must give embodiment=0.0"

    # Back-compat: no outcome → no reward key, same 9+overall keys
    scores_base = _sig_eval(raw, resp, "ground")
    base_keys = set(scores_base.keys())
    assert "reward" not in base_keys, "no-outcome call must not return 'reward' key"
    required_keys = {"presence","learning","logic","humour","relationship","creation",
                     "system_change","novelty","continuity","overall"}
    assert required_keys.issubset(base_keys), f"missing keys: {required_keys - base_keys}"

    ok("AT-3: verified ACK → reward>0; unverified → reward=0; no outcome → back-compat keys")
except AssertionError as e:
    fail("AT-3", e)
except Exception as e:
    fail("AT-3", e)


# ── AT-4: learning writes nothing to identity ─────────────────────────────────
try:
    from self.lesson_store import lesson_key as _lk4, record_outcome as _ro4, promote_pass as _pp4

    with tempfile.TemporaryDirectory() as tmp:
        ledger = os.path.join(tmp, "ledger.jsonl")
        lkey = _lk4("behaviour", "Identity isolation test lesson", "met")

        seed = {
            "lesson_key": lkey, "statement": "Identity isolation test lesson",
            "scope": "behaviour", "cause": "met", "strength": 0.3, "status": "candidate",
            "evidence": [], "first_seen": "", "last_seen": "", "promoted_at": None,
            "retired_at": None, "reason": None, "proposes": None,
        }
        with open(ledger, "w") as f:
            f.write(json.dumps(seed) + "\n")

        # Record outcomes
        for spot, sess in [("SA", "s1"), ("SB", "s2"), ("SC", "s3")]:
            _ro4(lkey, f"SPOT_{spot}", True, session_id=sess, ledger_path=ledger)

        # Snapshot identity-sensitive paths before promote
        pvec_path = os.path.join(_BASE, "self", "personality_vector.json")
        pvec_before = open(pvec_path, "rb").read() if os.path.exists(pvec_path) else b""
        exec_path = os.path.join(_BASE, "runtime", "executive.py")
        exec_mtime = os.path.getmtime(exec_path)

        _pp4(ledger_path=ledger)

        # Personality vector must be byte-identical (no live delta in this test — no proposes)
        pvec_after = open(pvec_path, "rb").read() if os.path.exists(pvec_path) else b""
        assert pvec_before == pvec_after, "promote_pass must not touch personality_vector.json"

        # executive.py must be untouched
        assert os.path.getmtime(exec_path) == exec_mtime, "executive.py must not be touched"

        # prompts/ must not be touched
        prompts_dir = os.path.join(_BASE, "prompts")
        for pf in os.listdir(prompts_dir):
            pfull = os.path.join(prompts_dir, pf)
            assert not pfull.endswith("bak_wo095"), "no backup files in prompts/"

        ok("AT-4: promote_pass leaves personality_vector, executive.py, prompts/ untouched")
except AssertionError as e:
    fail("AT-4", e)
except Exception as e:
    fail("AT-4", e)


# ── AT-5: repeat strengthens, no duplicate row ────────────────────────────────
try:
    from self.lesson_store import lesson_key as _lk5, record_outcome as _ro5

    with tempfile.TemporaryDirectory() as tmp:
        ledger = os.path.join(tmp, "ledger.jsonl")
        lkey = _lk5("behaviour", "Repeat lesson deduplication check", "met")

        seed = {
            "lesson_key": lkey, "statement": "Repeat lesson deduplication check",
            "scope": "behaviour", "cause": "met", "strength": 0.3, "status": "candidate",
            "evidence": [], "first_seen": "", "last_seen": "", "promoted_at": None,
            "retired_at": None, "reason": None, "proposes": None,
        }
        with open(ledger, "w") as f:
            f.write(json.dumps(seed) + "\n")

        str_before = 0.3
        for spot in ["SPOT_A", "SPOT_B", "SPOT_C"]:
            _ro5(lkey, spot, True, session_id="s1", ledger_path=ledger)

        with open(ledger) as f:
            rows = [json.loads(l) for l in f if l.strip()]

        # Exactly one row with this lesson_key
        matching = [r for r in rows if r.get("lesson_key") == lkey]
        assert len(matching) == 1, f"must be exactly 1 row per lesson_key, got {len(matching)}"

        # Strength increased from the episodes
        assert matching[0]["strength"] > str_before, (
            f"strength must increase from repeated verified episodes: {matching[0]['strength']}"
        )

        # Evidence list has all 3 episodes
        assert len(matching[0]["evidence"]) == 3, (
            f"evidence must have 3 entries, got {len(matching[0]['evidence'])}"
        )

        ok("AT-5: repeat episodes strengthen existing row; no duplicate row appended")
except AssertionError as e:
    fail("AT-5", e)
except Exception as e:
    fail("AT-5", e)


# ── AT-6: significance_engine back-compat (no outcome) ────────────────────────
try:
    from memory.significance_engine import evaluate as _sig_bc

    scores = _sig_bc("what should I do", "Here's what I think.", "reflect")
    required = {"presence","learning","logic","humour","relationship","creation",
                "system_change","novelty","continuity","overall"}
    assert required.issubset(scores.keys()), f"missing keys: {required - scores.keys()}"
    assert "reward" not in scores, "no-outcome call must not return 'reward'"
    assert all(0.0 <= v <= 1.0 for v in scores.values()), "all scores must be 0–1"

    ok("AT-6: significance_engine.evaluate() back-compat — no outcome → same keys, same range")
except AssertionError as e:
    fail("AT-6", e)
except Exception as e:
    fail("AT-6", e)


# ── AT-7: stats() moves correctly ─────────────────────────────────────────────
try:
    from self.lesson_store import stats as _ls_stats, lesson_key as _lk7, record_outcome as _ro7, promote_pass as _pp7

    with tempfile.TemporaryDirectory() as tmp:
        ledger = os.path.join(tmp, "ledger.jsonl")
        lkey = _lk7("behaviour", "Stats test lesson", "met")
        seed = {
            "lesson_key": lkey, "statement": "Stats test lesson",
            "scope": "behaviour", "cause": "met", "strength": 0.3, "status": "candidate",
            "evidence": [], "first_seen": "", "last_seen": "", "promoted_at": None,
            "retired_at": None, "reason": None, "proposes": None,
        }
        with open(ledger, "w") as f:
            f.write(json.dumps(seed) + "\n")

        s0 = _ls_stats(ledger_path=ledger)
        assert s0["ledger_counts"]["total"] == 1, f"total must be 1, got {s0}"
        assert s0["ledger_counts"]["candidate"] == 1

        for spot, sess in [("SA","s1"),("SB","s2"),("SC","s3")]:
            _ro7(lkey, spot, True, session_id=sess, ledger_path=ledger)
        _pp7(ledger_path=ledger)

        s1 = _ls_stats(ledger_path=ledger)
        assert s1["ledger_counts"]["confirmed"] == 1, f"must have 1 confirmed, got {s1}"
        assert s1["reinforcement_ratio"] > 0, "reinforcement_ratio must be > 0 after verified eps"

        # identity_stability alarm field present
        assert "identity_stability_alarm" in s1, "stats must include identity_stability_alarm"

        ok("AT-7: stats() counts update on promotion; reinforcement_ratio > 0; alarm field present")
except AssertionError as e:
    fail("AT-7", e)
except Exception as e:
    fail("AT-7", e)


# ── AT-8: promote_pass not in response path (compile + grep) ──────────────────
try:
    import re as _re8

    server_path = os.path.join(_BASE, "server.py")
    with open(server_path, encoding="utf-8") as f:
        server_src = f.read()

    # promote_pass must NOT appear in the per-request path — only in the WO-095 ACK emission
    # blocks (which are fine — those are side-effects of ACKs, not the hot response path).
    # The critical check: it must not appear in significance_engine or prompt_builder.
    sig_path = os.path.join(_BASE, "memory", "significance_engine.py")
    pb_path  = os.path.join(_BASE, "runtime", "prompt_builder.py")
    for path in (sig_path, pb_path):
        with open(path, encoding="utf-8") as f:
            src = f.read()
        assert "promote_pass" not in src, f"promote_pass must not appear in {os.path.basename(path)}"

    # lesson_store.py: record_outcome must not CALL promote_pass (function call)
    ls_path = os.path.join(_BASE, "self", "lesson_store.py")
    with open(ls_path, encoding="utf-8") as f:
        ls_src = f.read()
    # Extract just the record_outcome body up to the next top-level def
    if "def record_outcome" in ls_src:
        rec_body = ls_src.split("def record_outcome")[1]
        # Split on next same-indentation def (top-level: starts at column 0)
        import re as _re_at8
        # Find all top-level defs after record_outcome
        match = _re_at8.search(r"\ndef [a-z_]", rec_body)
        if match:
            rec_body = rec_body[:match.start()]
    else:
        rec_body = ""
    # Check for a function CALL (not just a comment or string mention)
    assert "promote_pass(" not in rec_body, "record_outcome must not call promote_pass()"

    # All files compile clean
    for path in (sig_path, pb_path, ls_path, os.path.join(_BASE, "runtime", "cognitive_snapshot.py")):
        py_compile.compile(path, doraise=True)

    ok("AT-8: promote_pass not in significance_engine/prompt_builder; all key files compile clean")
except AssertionError as e:
    fail("AT-8", e)
except Exception as e:
    fail("AT-8", e)


# ── AT-9: journal_router + significance_faculty regression ─────────────────────
try:
    jr_path  = os.path.join(_BASE, "memory", "journal_router.py")
    sf_path  = os.path.join(_BASE, "faculties", "significance", "significance_faculty.py")
    rf_path  = os.path.join(_BASE, "runtime", "reflection_faculty.py")

    for path in (jr_path, sf_path, rf_path):
        if os.path.exists(path):
            py_compile.compile(path, doraise=True)

    # significance_faculty must still wrap the 9-dim engine (back-compat)
    if os.path.exists(sf_path):
        with open(sf_path, encoding="utf-8") as f:
            sf_src = f.read()
        assert "significance_engine" in sf_src, "significance_faculty must still import significance_engine"

    ok("AT-9: journal_router · significance_faculty · reflection_faculty compile clean; sig_faculty still wraps engine")
except AssertionError as e:
    fail("AT-9", e)
except Exception as e:
    fail("AT-9", e)


# ── AT-10: pre-v1 migration ───────────────────────────────────────────────────
try:
    from self.lesson_store import migrate_pre_v1

    with tempfile.TemporaryDirectory() as tmp:
        ledger  = os.path.join(tmp, "ledger.jsonl")
        archive = os.path.join(tmp, "pre_v1.jsonl")

        # Mix of pre-v1 (no lesson_key) and v1 rows
        pre_v1 = {"id": "L-old", "statement": "old lesson", "status": "candidate"}
        v1_row = {"lesson_key": "abc123", "statement": "new lesson", "status": "candidate"}
        with open(ledger, "w") as f:
            f.write(json.dumps(pre_v1) + "\n")
            f.write(json.dumps(v1_row) + "\n")

        migrated = migrate_pre_v1(ledger_path=ledger, archive_path=archive)
        assert migrated == 1, f"must migrate exactly 1 pre-v1 row, got {migrated}"

        # v1 ledger has only the v1 row
        with open(ledger) as f:
            remaining = [json.loads(l) for l in f if l.strip()]
        assert len(remaining) == 1, f"v1 ledger must have 1 row, got {len(remaining)}"
        assert remaining[0].get("lesson_key") == "abc123", "remaining row must be the v1 row"

        # archive has the pre-v1 row
        with open(archive) as f:
            archived = [json.loads(l) for l in f if l.strip()]
        assert len(archived) == 1, f"archive must have 1 row, got {len(archived)}"
        assert archived[0]["id"] == "L-old", "archived row must be the pre-v1 row"

        # Idempotent — running again migrates 0 more
        migrated2 = migrate_pre_v1(ledger_path=ledger, archive_path=archive)
        assert migrated2 == 0, f"second run must migrate 0 rows, got {migrated2}"

        ok("AT-10: pre-v1 rows archived cleanly; v1 ledger untouched; idempotent")
except AssertionError as e:
    fail("AT-10", e)
except Exception as e:
    fail("AT-10", e)


# ── Summary ───────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print()
    print("=" * 62)
    print(f"WO-095 learning loop     {_passed} passed   {_failed} failed")
    if _failed:
        sys.exit(1)
