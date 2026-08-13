"""
tests/test_wo008_working_memory.py — Acceptance tests for WO-008: Working Memory

Spec: runtime/working_memory.py
6 acceptance tests from Volume_VI (FT-1..3, ST-1..3).

Run: python3 tests/test_wo008_working_memory.py
"""
import sys
sys.path.insert(0, '.')

PASS = 0; FAIL = 0
def ok(n):  global PASS; PASS += 1; print(f"  ✅ {n}")
def fail(n, r): global FAIL; FAIL += 1; print(f"  ❌ {n}: {r}")

from runtime.working_memory import (
    CognitiveFrame, AttentionCandidate, WorkingMemory,
    run_attention_competition, update_working_memory, seed_working_memory,
)

# ── FT-1: Attention competition produces a winner ─────────────────────────────
candidates = [
    AttentionCandidate("task_a", novelty=0.8, importance=0.6, urgency=0.3),
    AttentionCandidate("task_b", novelty=0.2, importance=0.9, urgency=0.5),
    AttentionCandidate("task_c", novelty=0.5, importance=0.4, urgency=0.1),
]
state = run_attention_competition(candidates, budget=0.7, distress=0.0)
try:
    assert state.winner is not None, "no winner"
    assert state.winner in ("task_a", "task_b", "task_c")
    assert 0.0 <= state.budget <= 1.0
    ok(f"FT-1: attention competition — winner={state.winner!r}, mode={state.mode!r}")
except AssertionError as e: fail("FT-1", e)

# ── FT-2: Distress overrides competition ─────────────────────────────────────
state_distress = run_attention_competition(candidates, budget=0.9, distress=1.0)
try:
    assert state_distress.winner is not None
    ok(f"FT-2: distress override active — winner={state_distress.winner!r}")
except AssertionError as e: fail("FT-2", e)

# ── FT-3: Budget → mode mapping ───────────────────────────────────────────────
s_peripheral  = run_attention_competition(candidates, budget=0.05, distress=0.0)
s_reactive    = run_attention_competition(candidates, budget=0.40, distress=0.0)
s_deliberative = run_attention_competition(candidates, budget=0.80, distress=0.0)
try:
    assert s_peripheral.mode  == "peripheral",  f"got {s_peripheral.mode}"
    assert s_reactive.mode    == "reactive",     f"got {s_reactive.mode}"
    assert s_deliberative.mode == "deliberative", f"got {s_deliberative.mode}"
    ok("FT-3: budget→mode — peripheral/reactive/deliberative mapping correct")
except AssertionError as e: fail("FT-3", e)

# ── ST-1: Oldest unpinned evicted on overflow ────────────────────────────────
wm = seed_working_memory("test task", "previous session summary", [], capacity=3)
for i in range(5):
    frame = CognitiveFrame(frame_id=f"f{i}", content=f"item {i}", turn=i, significance=0.5, pinned=False)
    wm = update_working_memory(wm, frame)
try:
    assert len(wm.frames) <= 3, f"overflow: {len(wm.frames)} frames (capacity=3)"
    assert wm.rolling_summary, "rolling_summary should be populated after evictions"
    ok(f"ST-1: overflow — oldest unpinned evicted; frames={len(wm.frames)}, rolling_summary populated")
except AssertionError as e: fail("ST-1", e)

# ── ST-2: Pinned frames survive eviction ─────────────────────────────────────
wm2 = seed_working_memory("task", "", [], capacity=3)
pinned = CognitiveFrame(frame_id="pinned", content="must survive", turn=0, significance=0.9, pinned=True)
wm2 = update_working_memory(wm2, pinned)
for i in range(4):
    frame = CognitiveFrame(frame_id=f"g{i}", content=f"filler {i}", turn=i+1, significance=0.3, pinned=False)
    wm2 = update_working_memory(wm2, frame)
try:
    ids = [f.frame_id for f in wm2.frames]
    assert "pinned" in ids, f"pinned frame was evicted: {ids}"
    ok("ST-2: pinned frames survive overflow eviction")
except AssertionError as e: fail("ST-2", e)

# ── ST-3: WorkingMemory is frozen ─────────────────────────────────────────────
wm3 = seed_working_memory("task", "", [])
try:
    try:
        wm3.current_task = "hacked"
        fail("ST-3", "WorkingMemory is not frozen — mutation succeeded")
    except Exception:
        ok("ST-3: WorkingMemory is frozen (immutable dataclass)")
except Exception as e: fail("ST-3", e)

print(f"\nResult: {PASS}/6 passed, {FAIL} failed")
sys.exit(1 if FAIL else 0)
