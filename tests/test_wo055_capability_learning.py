"""
tests/test_wo055_capability_learning.py — Acceptance tests for WO-055

Spec: Capability Learning — track repeated failures, record rule candidates,
propose WO automatically after threshold.

  AT-1: record_failure() increments streak; record_success() resets it
  AT-2: streak >= FAILURE_THRESHOLD creates a rule candidate
  AT-3: rule candidate has required fields (capability_id, streak, rule_draft)
  AT-4: duplicate failures update existing candidate, not add a new one
  AT-5: maybe_propose() writes a proposal when >= PROPOSAL_THRESHOLD candidates
  AT-6: scan_buffer() ingests learning_buffer entries and updates streaks
  AT-7: proposal is written to logs/learning_proposals.jsonl (file exists after write)
  AT-8: py_compile clean on capability_learning.py

Run: python3 tests/test_wo055_capability_learning.py
"""
import sys, os, json, tempfile
sys.path.insert(0, ".")

PASS = 0; FAIL = 0
def ok(n):      global PASS; PASS += 1; print(f"  ✅ {n}")
def fail(n, r): global FAIL; FAIL += 1; print(f"  ❌ {n}: {r}")


def _fresh():
    """Return a fresh copy of the module with reset state."""
    import importlib
    import runtime.capability_learning as _mod
    _mod._failure_streaks.clear()
    _mod._rule_candidates.clear()
    return _mod


# ── AT-1: failure increments / success resets ─────────────────────────────────
try:
    cl = _fresh()
    cl.record_failure("music.spotify", "failed to open app")
    cl.record_failure("music.spotify", "second fail")
    if cl.failure_streak("music.spotify") == 2:
        cl.record_success("music.spotify")
        if cl.failure_streak("music.spotify") == 0:
            ok("AT-1: record_failure() increments streak; record_success() resets to 0")
        else:
            fail("AT-1", f"streak after success = {cl.failure_streak('music.spotify')}")
    else:
        fail("AT-1", f"streak after 2 failures = {cl.failure_streak('music.spotify')}")
except Exception as e:
    fail("AT-1", e)


# ── AT-2: FAILURE_THRESHOLD creates a rule candidate ─────────────────────────
try:
    cl = _fresh()
    for i in range(cl.FAILURE_THRESHOLD):
        cl.record_failure("movement.sit", f"fail {i}")
    candidates = cl.get_candidates()
    if candidates and any(c["capability_id"] == "movement.sit" for c in candidates):
        ok(f"AT-2: {cl.FAILURE_THRESHOLD} failures → rule candidate created "
           f"(streak={cl.failure_streak('movement.sit')})")
    else:
        fail("AT-2", f"no candidate after {cl.FAILURE_THRESHOLD} failures: {candidates}")
except Exception as e:
    fail("AT-2", e)


# ── AT-3: rule candidate has required fields ──────────────────────────────────
try:
    cl = _fresh()
    for i in range(cl.FAILURE_THRESHOLD):
        cl.record_failure("web.search", f"fail {i}")
    candidates = cl.get_candidates()
    cand = next((c for c in candidates if c["capability_id"] == "web.search"), None)
    required_fields = {"capability_id", "streak", "rule_draft", "_ts"}
    if cand and required_fields.issubset(cand.keys()):
        ok(f"AT-3: rule candidate has required fields: {list(cand.keys())}")
    else:
        missing = required_fields - (set(cand.keys()) if cand else set())
        fail("AT-3", f"candidate={cand} missing={missing}")
except Exception as e:
    fail("AT-3", e)


# ── AT-4: duplicate failures update existing candidate ────────────────────────
try:
    cl = _fresh()
    for i in range(cl.FAILURE_THRESHOLD + 2):
        cl.record_failure("tool.timer", f"fail {i}")
    candidates = cl.get_candidates()
    timer_cands = [c for c in candidates if c["capability_id"] == "tool.timer"]
    if len(timer_cands) == 1 and timer_cands[0]["streak"] == cl.FAILURE_THRESHOLD + 2:
        ok(f"AT-4: duplicate failures update existing candidate (no duplicates); "
           f"streak={timer_cands[0]['streak']}")
    else:
        fail("AT-4", f"found {len(timer_cands)} timer candidates with streaks "
             f"{[c['streak'] for c in timer_cands]}")
except Exception as e:
    fail("AT-4", e)


# ── AT-5: maybe_propose() writes proposal at PROPOSAL_THRESHOLD ───────────────
try:
    cl = _fresh()
    with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False, mode="w") as tf:
        _tmp_path = tf.name

    cl._LOG_PATH = _tmp_path

    # Seed PROPOSAL_THRESHOLD distinct candidates
    for cap_id in [f"cap.{i}" for i in range(cl.PROPOSAL_THRESHOLD)]:
        for _ in range(cl.FAILURE_THRESHOLD):
            cl.record_failure(cap_id, "seeded fail")

    proposed = cl.maybe_propose()
    with open(_tmp_path) as f:
        lines = [l.strip() for l in f if l.strip()]
    os.unlink(_tmp_path)

    if proposed and lines:
        entry = json.loads(lines[-1])
        if entry.get("type") == "wo_proposal":
            ok(f"AT-5: maybe_propose() wrote WO proposal ({len(entry['candidates'])} candidates)")
        else:
            fail("AT-5", f"proposal type unexpected: {entry.get('type')}")
    else:
        fail("AT-5", f"proposed={proposed} lines={len(lines)}")
except Exception as e:
    fail("AT-5", e)


# ── AT-6: scan_buffer() ingests learning_buffer entries ──────────────────────
try:
    import unittest.mock as _mock
    cl = _fresh()

    _fake_entries = [
        {"intent": "web.search", "outcome": "failed",  "raw": "search test 1"},
        {"intent": "web.search", "outcome": "failed",  "raw": "search test 2"},
        {"intent": "music.play", "outcome": "success", "raw": "play song"},
        {"intent": "web.search", "outcome": "failed",  "raw": "search test 3"},
    ]

    import runtime.router.learning_buffer as _lb
    with _mock.patch.object(_lb, "recent", return_value=_fake_entries):
        result = cl.scan_buffer()

    streak_after = cl.failure_streak("web.search")
    music_streak = cl.failure_streak("music.play")

    if result["scanned"] == 4 and streak_after >= 3 and music_streak == 0:
        ok(f"AT-6: scan_buffer() scanned={result['scanned']} "
           f"web.search streak={streak_after} music.play reset to {music_streak}")
    else:
        fail("AT-6", f"scanned={result['scanned']} web_streak={streak_after} music_streak={music_streak}")
except Exception as e:
    fail("AT-6", e)


# ── AT-7: proposal written to logs/learning_proposals.jsonl ──────────────────
try:
    cl = _fresh()
    original_path = cl._LOG_PATH

    with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False, mode="w") as tf:
        _tmp_path2 = tf.name
    cl._LOG_PATH = _tmp_path2

    for cap_id in [f"testcap.{i}" for i in range(cl.PROPOSAL_THRESHOLD)]:
        for _ in range(cl.FAILURE_THRESHOLD):
            cl.record_failure(cap_id, "test fail")

    cl.maybe_propose()

    exists = os.path.exists(_tmp_path2) and os.path.getsize(_tmp_path2) > 0
    if exists:
        with open(_tmp_path2) as f:
            line = json.loads(f.readline())
        ok(f"AT-7: proposal written to file ({os.path.getsize(_tmp_path2)} bytes, "
           f"type={line.get('type')})")
    else:
        fail("AT-7", f"file not written or empty: {_tmp_path2}")
    os.unlink(_tmp_path2)
    cl._LOG_PATH = original_path
except Exception as e:
    fail("AT-7", e)


# ── AT-8: py_compile clean ────────────────────────────────────────────────────
try:
    import py_compile
    py_compile.compile("runtime/capability_learning.py", doraise=True)
    ok("AT-8: py_compile clean on capability_learning.py")
except py_compile.PyCompileError as e:
    fail("AT-8", e)


print()
print("=" * 50)
print(f"WO-055  {PASS} passed  {FAIL} failed")
if FAIL:
    sys.exit(1)
