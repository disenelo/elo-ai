"""
tests/test_wo039_f6_mirror_scrub.py — WO-039-F6: mirror-scrub extension

Spec: WO-036b opener scrub catches "I notice/see/hear" forms but NOT
      "You said 'X'…" or "Your typo 'hwow'…" (F6 live findings).
      Added to _MIRROR_OPENERS: "you said ", "you typed ", "you wrote ",
      "your typo", "i noticed your typo", "i noticed a typo".

  AT-1: "You said 'Interesting to know'…" opener → tail kept, opener stripped
  AT-2: "Your typo 'hwow' slipped in…" opener → tail kept, opener stripped
  AT-3: "You typed 'hwow' earlier…" opener → tail kept, opener stripped
  AT-4: "You wrote 'interesting' back there…" opener → tail kept
  AT-5: "I noticed a typo in your message…" opener → tail kept
  AT-6: Bare "You said 'no'." (no substantive tail) — reply not destroyed
  AT-7: "you said" NOT mid-reply — "Everything you said makes sense." → unchanged
  AT-8: All F6 pattern tokens present in _MIRROR_OPENERS block of server.py
  AT-9: py_compile clean on server.py

Run: python3 tests/test_wo039_f6_mirror_scrub.py
"""
import sys, os, re, py_compile
sys.path.insert(0, ".")

PASS = 0; FAIL = 0
def ok(n):      global PASS; PASS += 1; print(f"  ✅ {n}")
def fail(n, r): global FAIL; FAIL += 1; print(f"  ❌ {n}: {r}")


# Replicate the scrub logic from server.py for isolated testing
_MIRROR_OPENERS = (
    "i notice you", "i see you", "i hear you", "i notice that you",
    "you've been", "you're offering", "you seem to be", "you seem ",
    "it seems you", "it sounds like you", "it feels like you",
    "i can see you", "i can feel you",
    "you said ", "you typed ", "you wrote ",
    "your typo", "i noticed your typo", "i noticed a typo",
)


def _apply_scrub(response: str) -> str:
    resp_stripped = response.lstrip()
    resp_lower    = resp_stripped.lower()
    for mo in _MIRROR_OPENERS:
        if resp_lower.startswith(mo):
            end = next(
                (i for i, c in enumerate(resp_stripped) if c in ".?!" and i > 8),
                -1,
            )
            tail = resp_stripped[end + 1:].lstrip(" —,\n") if end > 0 else ""
            if len(tail) >= 8:
                return tail
            break
    return response


# ── AT-1: "You said 'X'…" opener stripped ────────────────────────────────────
try:
    inp = "You said 'Interesting to know' — that really resonated. Let's keep going."
    out = _apply_scrub(inp)
    assert "You said" not in out[:20], f"opener not stripped: {out!r}"
    assert "Let's keep going" in out, f"tail lost: {out!r}"
    ok(f"AT-1: 'You said…' opener stripped → {out!r}")
except AssertionError as e:
    fail("AT-1", e)


# ── AT-2: "Your typo '…'" opener stripped ────────────────────────────────────
try:
    inp = "Your typo 'hwow' slipped in there. What did you mean to say?"
    out = _apply_scrub(inp)
    assert not out.startswith("Your typo"), f"opener not stripped: {out!r}"
    assert "What did you mean" in out, f"tail lost: {out!r}"
    ok(f"AT-2: 'Your typo…' opener stripped → {out!r}")
except AssertionError as e:
    fail("AT-2", e)


# ── AT-3: "You typed '…'" opener stripped ────────────────────────────────────
try:
    inp = "You typed 'hwow' — I'm guessing that's 'how'? Anyway, here's my take."
    out = _apply_scrub(inp)
    assert not out.startswith("You typed"), f"opener not stripped: {out!r}"
    assert "here's my take" in out, f"tail lost: {out!r}"
    ok(f"AT-3: 'You typed…' opener stripped → {out!r}")
except AssertionError as e:
    fail("AT-3", e)


# ── AT-4: "You wrote '…'" opener stripped ────────────────────────────────────
try:
    inp = "You wrote 'interesting' back there. I want to pick that apart a bit."
    out = _apply_scrub(inp)
    assert not out.startswith("You wrote"), f"opener not stripped: {out!r}"
    ok(f"AT-4: 'You wrote…' opener stripped → {out!r}")
except AssertionError as e:
    fail("AT-4", e)


# ── AT-5: "I noticed a typo…" opener stripped ────────────────────────────────
try:
    inp = "I noticed a typo in your message. Moving on — what were you trying to say?"
    out = _apply_scrub(inp)
    assert not out.lower().startswith("i noticed a typo"), f"opener not stripped: {out!r}"
    ok(f"AT-5: 'I noticed a typo…' opener stripped → {out!r}")
except AssertionError as e:
    fail("AT-5", e)


# ── AT-6: bare "You said 'no'." with no substantive tail — reply not destroyed ─
try:
    inp = "You said 'no'."
    out = _apply_scrub(inp)
    # tail < 8 chars → reply kept as-is (don't destroy a short reply)
    assert out == inp, f"short reply should be kept: {out!r}"
    ok(f"AT-6: bare short 'You said no.' — reply kept intact (tail < 8 chars guard)")
except AssertionError as e:
    fail("AT-6", e)


# ── AT-7: mid-sentence "you said" is NOT stripped (scrub is opener-only) ──────
try:
    inp = "Everything you said makes complete sense to me."
    out = _apply_scrub(inp)
    assert out == inp, f"mid-sentence 'you said' must NOT be stripped: {out!r}"
    ok("AT-7: 'Everything you said…' — mid-sentence 'you said' is NOT stripped")
except AssertionError as e:
    fail("AT-7", e)


# ── AT-8: F6 tokens present in server.py _MIRROR_OPENERS block ──────────────
try:
    with open("server.py", encoding="utf-8") as f:
        src = f.read()
    for token in ("you said ", "your typo", "you typed ", "you wrote "):
        assert token in src, f"F6 token {token!r} missing from server.py"
    assert "WO-039-F6" in src, "WO-039-F6 marker not in server.py"
    ok("AT-8: All F6 tokens + WO-039-F6 marker present in server.py _MIRROR_OPENERS")
except AssertionError as e:
    fail("AT-8", e)
except Exception as e:
    fail("AT-8", e)


# ── AT-9: py_compile clean ────────────────────────────────────────────────────
try:
    py_compile.compile("server.py", doraise=True)
    ok("AT-9: py_compile clean on server.py")
except py_compile.PyCompileError as e:
    fail("AT-9", e)


print()
print("=" * 60)
print(f"WO-039-F6 mirror-scrub ext  {PASS} passed  {FAIL} failed")
if FAIL:
    sys.exit(1)
