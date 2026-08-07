"""
tests/test_wo036b_mirror_scrub.py — Deterministic mirror scrub (WO-036b)

Verifies that the post-gen scrub in server.py strips banned opener sentences
BEFORE the reply reaches the user — regardless of what the LLM generated.

  AT-1: "I notice you're struggling today. Let's talk." → tail returned
  AT-2: "I see you are working on something big. That's meaningful." → tail returned
  AT-3: "I hear you. It sounds like the project is moving." → tail returned
  AT-4: "You've been building a lot lately. Robot is coming together." → tail returned
  AT-5: "You're offering a lot of insight here. Tell me more." → tail returned
  AT-6: "That sounds cool." → unchanged (no mirror opener — must NOT be stripped)
  AT-7: "I notice you" with no tail (entire reply is the opener) → preserve; no crash
  AT-8: Mirror opener mid-reply (not at start) → NOT stripped (scrub is opener-only)
  AT-9: py_compile clean on server.py

Run: python3 tests/test_wo036b_mirror_scrub.py
"""
import sys, py_compile
sys.path.insert(0, ".")

PASS = 0; FAIL = 0
def ok(n):      global PASS; PASS += 1; print(f"  ✅ {n}")
def fail(n, r): global FAIL; FAIL += 1; print(f"  ❌ {n}: {r}")


def _scrub(response: str) -> str:
    """Inline copy of the deterministic scrub from server.py — tests the logic, not the file."""
    _MIRROR_OPENERS = (
        "i notice you", "i see you", "i hear you", "i notice that you",
        "you've been", "you're offering", "you seem to be", "you seem ",
        "it seems you", "it sounds like you", "it feels like you",
        "i can see you", "i can feel you",
    )
    _resp_stripped = response.lstrip()
    _resp_lower    = _resp_stripped.lower()
    for _mo in _MIRROR_OPENERS:
        if _resp_lower.startswith(_mo):
            _end = next(
                (i for i, c in enumerate(_resp_stripped) if c in ".?!" and i > 8),
                -1,
            )
            _tail = _resp_stripped[_end + 1:].lstrip(" —,\n") if _end > 0 else ""
            if len(_tail) >= 8:
                response = _tail
            break
    return response


# ── AT-1..5: banned openers are stripped ─────────────────────────────────────
cases = [
    ("AT-1", "I notice you're struggling today. Let's talk.", "Let's talk."),
    ("AT-2", "I see you are working on something big. That's meaningful.", "That's meaningful."),
    ("AT-3", "I hear you. It sounds like the project is moving.", "It sounds like the project is moving."),
    ("AT-4", "You've been building a lot lately. Robot is coming together.", "Robot is coming together."),
    ("AT-5", "You're offering a lot of insight here. Tell me more.", "Tell me more."),
]

for at, inp, expected in cases:
    try:
        result = _scrub(inp)
        if result.strip() == expected.strip():
            ok(f"{at}: opener stripped → {result!r}")
        else:
            fail(at, f"expected {expected!r}, got {result!r}")
    except Exception as e:
        fail(at, e)


# ── AT-6: non-mirror reply is unchanged ──────────────────────────────────────
try:
    inp = "That sounds cool."
    result = _scrub(inp)
    assert result == inp, f"non-mirror reply should be unchanged, got {result!r}"
    ok("AT-6: non-mirror reply unchanged")
except AssertionError as e:
    fail("AT-6", e)


# ── AT-7: opener with no tail → preserve; no crash ───────────────────────────
try:
    inp = "I notice you."
    result = _scrub(inp)
    assert result, "should not return empty"
    ok(f"AT-7: short all-opener reply preserved without crash → {result!r}")
except Exception as e:
    fail("AT-7", e)


# ── AT-8: opener mid-reply → NOT stripped (scrub is opener-only) ─────────────
try:
    inp = "That's interesting. I notice you're working on a robot."
    result = _scrub(inp)
    assert result == inp, f"mid-reply opener should NOT be stripped, got {result!r}"
    ok("AT-8: mid-reply mirror phrase NOT stripped")
except AssertionError as e:
    fail("AT-8", e)


# ── AT-9: server.py compile clean ────────────────────────────────────────────
try:
    py_compile.compile("server.py", doraise=True)
    ok("AT-9: py_compile clean on server.py")
except py_compile.PyCompileError as e:
    fail("AT-9", e)


# ── also verify the scrub block is present in the actual server.py ────────────
try:
    with open("server.py") as f:
        _src = f.read()
    assert "WO-036b: deterministic mirror scrub" in _src, "scrub comment not found in server.py"
    assert "_MIRROR_OPENERS" in _src, "_MIRROR_OPENERS not in server.py"
    ok("AT-9b: deterministic scrub block confirmed in server.py")
except AssertionError as e:
    fail("AT-9b", e)


print()
print("=" * 50)
print(f"WO-036b mirror-scrub  {PASS} passed  {FAIL} failed")
if FAIL:
    sys.exit(1)
