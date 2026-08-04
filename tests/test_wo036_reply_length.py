"""
tests/test_wo036_reply_length.py — Acceptance tests for WO-036

Spec: WO-036 — Reply length discipline + "I notice" reflex fix.

Tests:
  AT-1: BREVITY RULE present in living_presence_spec.txt
  AT-2: Banned openers include "I notice you..." / "I hear you..." / "I see you..."
  AT-3: "I notice" reflexive mirror in banned behaviours
  AT-4: Style monitor present in server.py (WO-036 comment)
  AT-5: Style monitor checks last 2 replies for banned openers
  AT-6: Style monitor injects [STYLE MONITOR] note into g_ctx when triggered
  AT-7: py_compile clean

Run: python3 tests/test_wo036_reply_length.py
"""
import sys, os
sys.path.insert(0, ".")

PASS = 0; FAIL = 0
def ok(n):      global PASS; PASS += 1; print(f"  \u2705 {n}")
def fail(n, r): global FAIL; FAIL += 1; print(f"  \u274c {n}: {r}")

_spec = open("prompts/living_presence_spec.txt", encoding="utf-8").read()
_server = open("server.py", encoding="utf-8").read()

if "BREVITY RULE" in _spec and "Short inputs get short replies" in _spec:
    ok("AT-1: BREVITY RULE section present in living_presence_spec.txt")
else:
    fail("AT-1", "BREVITY RULE not found in spec")

if "I notice you" in _spec and "I hear you" in _spec and "I see you" in _spec:
    ok("AT-2: banned openers include I notice you / I hear you / I see you")
else:
    fail("AT-2", "banned openers missing")

if "reflexive" in _spec.lower() and "mirror" in _spec.lower():
    ok("AT-3: reflexive mirroring in BANNED behaviours")
else:
    fail("AT-3", "reflexive mirror not in spec")

if "WO-036" in _server and "style monitor" in _server.lower():
    ok("AT-4: Style monitor block in server.py")
else:
    fail("AT-4", "style monitor not found")

if "_recent_elo_replies" in _server and "_cw[-2:]" in _server:
    ok("AT-5: style monitor reads last 2 replies")
else:
    fail("AT-5", "_recent_elo_replies or _cw[-2:] not found")

if "STYLE MONITOR" in _server and "_style_note" in _server:
    ok("AT-6: STYLE MONITOR injected into g_ctx")
else:
    fail("AT-6", "STYLE MONITOR not found")

import py_compile
try:
    py_compile.compile("server.py", doraise=True)
    ok("AT-7: server.py compile clean")
except py_compile.PyCompileError as e:
    fail("AT-7", e)

print()
print("="*50)
print(f"WO-036  {PASS} passed  {FAIL} failed")
if FAIL:
    sys.exit(1)
