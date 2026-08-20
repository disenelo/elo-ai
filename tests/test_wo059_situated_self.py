"""
tests/test_wo059_situated_self.py — WO-052A/059 (Architect-built 2026-08-06)
Sends commands through eLo's ACTUAL self-model logic and shows the answers.
Verifies: (1) update() no longer DROPS the situated fields (the bug); (2) State Ownership —
embodiment answers come from state, not a hardcoded string; (3) capability answers are truthful
from the registry + faculty health; (4) recent_behavior counts.
Run: python3 tests/test_wo059_situated_self.py
"""
import sys, os, py_compile
sys.path.insert(0, ".")
from self.elo_self_model import (
    EloSelfState, apply_turn as update, apply_embodiment, situated_block, can_i, capability_summary, record_behaviour,
)

PASS = 0; FAIL = 0
def ok(n):      global PASS; PASS += 1; print(f"  ✅ {n}")
def bad(n, r):  global FAIL; FAIL += 1; print(f"  ❌ {n}: {r}")

print("── WO-052A/059 Situated Self — commands through eLo's real logic ──")

# 1) BUG FIX: situated fields persist through a conversational update()
s = EloSelfState()
apply_embodiment(s, pose="sitting", surface="bottom edge of Code", location="Code",
                 available_actions=["stand", "sit", "wave"])
before = (s.pose, s.surface, list(s.available_actions))
for _ in range(5):                       # 5 normal conversational turns
    s = update(s, {"action": "answer", "tone": "WITTY", "response": "hey"})
after = (s.pose, s.surface, list(s.available_actions))
if after == before:
    ok(f"update() preserves situated fields across 5 turns (was dropping them) → {after}")
else:
    bad("update() persistence", f"before={before} after={after}")

# 2) STATE OWNERSHIP: 'where are you?' answered from state, not a hardcoded string
print("\n  > command: where are you?")
blk = situated_block(s)
print("   ", blk.replace("\n", "\n    "))
if "bottom edge of Code" in blk and "pose: sitting" in blk:
    ok("situated_block reads location + pose FROM state (State Ownership)")
else:
    bad("State Ownership", "situated_block did not reflect state")

# eLo must NOT claim a surface it isn't on — empty surface says 'not sure'
s2 = EloSelfState()               # fresh: no surface
if "no surface reported" in situated_block(s2):
    ok("empty surface → 'no surface reported' (never fabricates a location)")
else:
    bad("no-invention", "empty surface still asserted a place")

# 3) CAPABILITY TRUTH from the registry
print("\n  > command: can you sit? / wall jump? / fly?")
for verb, expect in [("sit", True), ("wall jump", True), ("fly", False)]:
    okp, reason = can_i(s, verb)
    print(f"    can_i({verb!r}) → {okp}: {reason}")
    if okp == expect: ok(f"can_i({verb!r}) = {okp}")
    else: bad(f"can_i({verb!r})", f"expected {expect}, got {okp}")

# movement degraded → honest 'I know how, but…' (Embodied Truth)
apply_embodiment(s, locomotion_faculty_health="DEGRADED")
okp, reason = can_i(s, "sit")
print(f"    [movement DEGRADED] can_i('sit') → {okp}: {reason}")
if not okp and "degraded" in reason.lower():
    ok("degraded movement → honest 'I know how to sit, but my movement faculty is degraded'")
else:
    bad("degraded honesty", reason)

# 4) recent_behavior — 'you wave a lot' self-reflection data
apply_embodiment(s, locomotion_faculty_health="OK")
for _ in range(3): record_behaviour(s, "wave")
record_behaviour(s, "sit")
print(f"\n  > command: why do you wave so much? → recent_behavior = {s.recent_behavior}")
if s.recent_behavior.get("wave") == 3 and s.recent_behavior.get("sit") == 1:
    ok("recent_behavior counts (wave=3, sit=1) — data for honest self-reflection")
else:
    bad("recent_behavior", s.recent_behavior)

# 5) compile clean
try:
    py_compile.compile("self/elo_self_model.py", doraise=True)
    py_compile.compile("server.py", doraise=True)
    ok("py_compile clean: self/elo_self_model.py + server.py")
except py_compile.PyCompileError as e:
    bad("py_compile", e)

print(f"\n================ WO-052A/059  {PASS} passed  {FAIL} failed ================")
sys.exit(1 if FAIL else 0)
