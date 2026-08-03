"""
tests/test_wo036_reply_length.py — Acceptance tests for WO-036

Spec: WO-036 — brevity discipline in prompts; no filler, no reflexive follow-ups.

Tests:
  AT-1: BREVITY RULE block present in living_presence_spec.txt
  AT-2: banned opener list present ("It feels like", "That's an interesting")
  AT-3: follow-up question rule present (one max, not reflexive)
  AT-4: "match the register" short-input rule present
  AT-5: WO-033 CI guard still passes (no "session" language introduced)

Run: python3 tests/test_wo036_reply_length.py
"""
import sys, os
sys.path.insert(0, ".")

PASS = 0; FAIL = 0
def ok(n):      global PASS; PASS += 1; print(f"  ✅ {n}")
def fail(n, r): global FAIL; FAIL += 1; print(f"  ❌ {n}: {r}")

_SPEC = os.path.join("prompts", "living_presence_spec.txt")
try:
    _content = open(_SPEC, encoding="utf-8").read()
except Exception as e:
    fail("load", e); sys.exit(1)


# ── AT-1: BREVITY RULE block present ─────────────────────────────────────────
if "BREVITY RULE" in _content:
    ok("AT-1: BREVITY RULE block present in living_presence_spec.txt")
else:
    fail("AT-1", "BREVITY RULE block not found")


# ── AT-2: banned opener list present ─────────────────────────────────────────
_banned = ["It feels like", "That's an interesting", "Narrating the user"]
_missing = [b for b in _banned if b not in _content]
if not _missing:
    ok("AT-2: banned opener rules present")
else:
    fail("AT-2", f"missing banned rules: {_missing}")


# ── AT-3: follow-up question cap rule present ─────────────────────────────────
if "ONE follow-up question" in _content or "one follow-up question" in _content.lower():
    ok("AT-3: follow-up question cap rule present")
else:
    fail("AT-3", "follow-up question cap rule not found")


# ── AT-4: register-matching rule present ──────────────────────────────────────
if "Short inputs get short replies" in _content or "short input" in _content.lower():
    ok("AT-4: short-input → short-reply register rule present")
else:
    fail("AT-4", "register-matching rule not found")


# ── AT-5: WO-033 CI guard — no "session" language introduced ─────────────────
# Only check lines added in the BREVITY RULE block
_brevity_start = _content.find("BREVITY RULE")
_brevity_block = _content[_brevity_start:_brevity_start + 1200] if _brevity_start >= 0 else ""
_bad = [l.strip() for l in _brevity_block.splitlines() if "session" in l.lower()]
if not _bad:
    ok("AT-5: BREVITY RULE block introduces no 'session' language")
else:
    fail("AT-5", f"'session' found in brevity block: {_bad}")


# ── Summary ───────────────────────────────────────────────────────────────────
print()
print(f"{'='*50}")
print(f"WO-036  {PASS} passed  {FAIL} failed")
if FAIL:
    sys.exit(1)
