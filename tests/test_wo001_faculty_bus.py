"""
tests/test_wo001_faculty_bus.py — Acceptance tests for WO-001: Faculty Bus

Spec: core/faculty_bus.py
5 acceptance tests from ADR-0001 / D-A.

Run: python3 tests/test_wo001_faculty_bus.py
"""
import sys, time
sys.path.insert(0, '.')

PASS = 0; FAIL = 0
def ok(n):  global PASS; PASS += 1; print(f"  ✅ {n}")
def fail(n, r): global FAIL; FAIL += 1; print(f"  ❌ {n}: {r}")

from core.faculty_bus import FacultyBus, make_envelope, get_bus, publish_attention_signal

# ── FT-1: Publish routes to subscriber ───────────────────────────────────────
bus = FacultyBus()
bus.subscribe("Executive")   # filter_fn=None → receives all addressed to it
msgs = []
env1 = make_envelope("Attention", "Executive", "attention_signal",
                     {"intent": "focus", "valence": 0.8, "momentum": 0.5},
                     priority="high", confidence=0.9)
bus.publish(env1)
msgs = bus.get_messages("Executive")
try:
    assert len(msgs) == 1, f"expected 1, got {len(msgs)}"
    assert msgs[0].payload["body"]["intent"] == "focus"
    ok("FT-1: publish routes envelope to subscriber")
except AssertionError as e: fail("FT-1", e)

# ── FT-2: Confidence-only-lowered invariant ───────────────────────────────────
try:
    env2 = make_envelope("Memory", "Executive", "memory_update", {}, confidence=0.7)
    low  = env2.lower_confidence(0.5)
    assert low.confidence == 0.5, f"expected 0.5, got {low.confidence}"
    try:
        env2.lower_confidence(0.9)   # must raise
        fail("FT-2", "raising confidence should raise ValueError")
    except ValueError:
        ok("FT-2: confidence invariant — lower allowed, raising rejected")
except AssertionError as e: fail("FT-2", e)

# ── FT-3: Expired envelope dropped with trace note ────────────────────────────
bus3 = FacultyBus()
bus3.subscribe("Executive")
from datetime import datetime, timezone, timedelta
past_iso = (datetime.now(timezone.utc) - timedelta(seconds=5)).isoformat()
env3 = make_envelope("Emotion", "Executive", "affect_state", {}, expires=past_iso)
result = bus3.publish(env3)
msgs3 = bus3.get_messages("Executive")
try:
    assert not result, "expired envelope should not be delivered"
    assert len(msgs3) == 0, f"expired envelope in queue: {len(msgs3)}"
    assert any("DROPPED" in d["reason"] for d in bus3.dropped_log()), "no DROPPED entry in log"
    ok("FT-3: expired envelope dropped; trace note in dropped_log")
except AssertionError as e: fail("FT-3", e)

# ── ST-1: get_messages pull-and-clear ─────────────────────────────────────────
bus4 = FacultyBus()
bus4.subscribe("Spine")
bus4.publish(make_envelope("Perception", "Spine", "perception_result", {"a": 1}))
bus4.publish(make_envelope("Perception", "Spine", "perception_result", {"b": 2}))
pull1 = bus4.get_messages("Spine")
pull2 = bus4.get_messages("Spine")
try:
    assert len(pull1) == 2, f"expected 2, got {len(pull1)}"
    assert len(pull2) == 0, f"pull-and-clear failed — got {len(pull2)} on second pull"
    ok("ST-1: get_messages pull-and-clear — second pull returns empty")
except AssertionError as e: fail("ST-1", e)

# ── ST-2: Module singleton (get_bus returns same instance) ────────────────────
b1 = get_bus()
b2 = get_bus()
try:
    assert b1 is b2, "get_bus() should return singleton"
    ok("ST-2: get_bus() module singleton — same instance across calls")
except AssertionError as e: fail("ST-2", e)

print(f"\nResult: {PASS}/5 passed, {FAIL} failed")
sys.exit(1 if FAIL else 0)
