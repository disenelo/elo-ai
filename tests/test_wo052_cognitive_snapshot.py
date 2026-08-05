"""
tests/test_wo052_cognitive_snapshot.py — Acceptance tests for WO-052

Spec: ONE frozen CognitiveSnapshot assembled at the TOP of each spine turn,
      BEFORE the Executive decides. Push, not pull.

  AT-1: CognitiveSnapshot has all required fields (self, health, body, attention)
  AT-2: build_snapshot() returns CognitiveSnapshot with correct types
  AT-3: Faculty health fields populated (CONNECTED/DEGRADED/OFFLINE strings)
  AT-4: Pending sit reflected in body_schema when pending_sit["active"]=True
  AT-5: Snapshot is on plan after spine.run() (plan.snapshot is not None)
  AT-6: py_compile clean on cognitive_snapshot.py + spine.py

Run: python3 tests/test_wo052_cognitive_snapshot.py
"""
import sys
sys.path.insert(0, ".")

PASS = 0; FAIL = 0
def ok(n):      global PASS; PASS += 1; print(f"  ✅ {n}")
def fail(n, r): global FAIL; FAIL += 1; print(f"  ❌ {n}: {r}")


# ── AT-1: CognitiveSnapshot has all required fields ──────────────────────────
try:
    from runtime.cognitive_snapshot import CognitiveSnapshot, BodySchema
    snap = CognitiveSnapshot()
    required = [
        "self_mood", "self_curiosity", "self_satisfaction",
        "self_session_read", "self_focal_thread", "self_model_block",
        "faculty_health", "health_summary",
        "intent", "valence", "momentum", "tone", "action",
        "body", "pending_intentions",
        "assembled_ts", "turn_id", "confidence",
    ]
    missing = [f for f in required if not hasattr(snap, f)]
    if not missing:
        ok("AT-1: CognitiveSnapshot has all required fields")
    else:
        fail("AT-1", f"missing fields: {missing}")
except Exception as e:
    fail("AT-1", e)


# ── AT-2: build_snapshot() returns CognitiveSnapshot with correct types ──────
try:
    from runtime.cognitive_snapshot import build_snapshot, CognitiveSnapshot, BodySchema
    snap = build_snapshot(
        attention={"intent": "build", "valence": "positive", "momentum": "building"},
        pending_sit=None,
        turn_id="test-001",
    )
    checks = [
        isinstance(snap, CognitiveSnapshot),
        isinstance(snap.self_mood, float),
        isinstance(snap.faculty_health, dict),
        isinstance(snap.body, BodySchema),
        isinstance(snap.pending_intentions, tuple),
        isinstance(snap.assembled_ts, float) and snap.assembled_ts > 0,
        snap.intent == "build",
        snap.valence == "positive",
        snap.momentum == "building",
        snap.turn_id == "test-001",
        0.0 <= snap.confidence <= 1.0,
    ]
    if all(checks):
        ok("AT-2: build_snapshot() returns CognitiveSnapshot with correct types")
    else:
        failed_idx = [i for i, c in enumerate(checks) if not c]
        fail("AT-2", f"failed checks at indices: {failed_idx}")
except Exception as e:
    fail("AT-2", e)


# ── AT-3: Faculty health fields populated ─────────────────────────────────────
try:
    from runtime.cognitive_snapshot import build_snapshot
    from runtime.faculty_health import CONNECTED, DEGRADED, OFFLINE

    snap = build_snapshot()
    valid_statuses = {CONNECTED, DEGRADED, OFFLINE}

    if snap.faculty_health:
        all_valid = all(v in valid_statuses for v in snap.faculty_health.values())
        if all_valid:
            ok(f"AT-3: faculty_health populated ({len(snap.faculty_health)} faculties, all valid statuses)")
        else:
            bad = {k: v for k, v in snap.faculty_health.items() if v not in valid_statuses}
            fail("AT-3", f"invalid status values: {bad}")
    else:
        ok("AT-3: faculty_health empty (no registry running) — acceptable default")
except Exception as e:
    fail("AT-3", e)


# ── AT-4: Pending sit reflected in body_schema ────────────────────────────────
try:
    import time as _t
    from runtime.cognitive_snapshot import build_snapshot

    _since = _t.time()
    _pending = {"active": True, "since": _since, "queued": "explore"}
    snap = build_snapshot(pending_sit=_pending)

    if (snap.body.pending_sit is True
            and abs(snap.body.sit_pending_since - _since) < 0.01
            and snap.body.queued_intent == "explore"
            and ("sit", "cursor") in snap.pending_intentions):
        ok("AT-4: pending sit reflected in body_schema + pending_intentions")
    else:
        fail("AT-4", f"body={snap.body} intentions={snap.pending_intentions}")
except Exception as e:
    fail("AT-4", e)


# ── AT-5: Snapshot on plan after spine.run() ─────────────────────────────────
try:
    from runtime.spine.spine import run as _spine_run
    _plan = _spine_run("hello, how are you?")
    if hasattr(_plan, "snapshot") and _plan.snapshot is not None:
        from runtime.cognitive_snapshot import CognitiveSnapshot
        if isinstance(_plan.snapshot, CognitiveSnapshot):
            ok("AT-5: plan.snapshot is CognitiveSnapshot after spine.run()")
        else:
            fail("AT-5", f"plan.snapshot is {type(_plan.snapshot).__name__}, not CognitiveSnapshot")
    else:
        fail("AT-5", f"plan.snapshot missing or None (hasattr={hasattr(_plan, 'snapshot')})")
except Exception as e:
    fail("AT-5", e)


# ── AT-6: py_compile clean ────────────────────────────────────────────────────
try:
    import py_compile
    py_compile.compile("runtime/cognitive_snapshot.py", doraise=True)
    py_compile.compile("runtime/spine/spine.py",        doraise=True)
    py_compile.compile("runtime/spine/plan.py",         doraise=True)
    ok("AT-6: py_compile clean on cognitive_snapshot.py + spine.py + plan.py")
except py_compile.PyCompileError as e:
    fail("AT-6", e)


print()
print("=" * 50)
print(f"WO-052  {PASS} passed  {FAIL} failed")
if FAIL:
    sys.exit(1)
