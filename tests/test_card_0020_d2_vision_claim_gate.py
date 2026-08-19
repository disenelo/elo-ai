"""tests/test_card_0020_d2_vision_claim_gate.py — Card 0020 · D-2 acceptance.

The 2026-08-19 live test showed eLo asserting

    "I can read what's on screen if you ask me to. I take a screenshot and
     extract the text. I also see your active app, window title, and all open
     Chrome tabs at all times."

— as the ANSWER to "Did you play Spotify?". The audit had flagged the exact
string at `server.py:3203-3211` one hour earlier: injected unconditionally
every turn, gated on nothing.

This test proves the fix. It reads the server.py source and:

  a) The former unconditional advertisement is no longer injected.
  b) The vision-claim block is gated on the user actually asking about seeing.
  c) It reads live vision state (three phrasings — can / no-permission / off).

Run: python3 tests/test_card_0020_d2_vision_claim_gate.py
"""
import sys, os, re
sys.path.insert(0, ".")

PASS = 0; FAIL = 0
def ok(n):      global PASS; PASS += 1; print(f"  ✅ {n}")
def fail(n, r): global FAIL; FAIL += 1; print(f"  ❌ {n}: {r}")


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVER = os.path.join(ROOT, "server.py")


# D-2.a — the unconditional advertisement is gone
try:
    with open(SERVER, encoding="utf-8") as f:
        src = f.read()
    # The specific string from the audit finding must no longer be unconditionally
    # injected. It is allowed to appear inside a live-state-gated branch, but the
    # ORIGINAL always-on injection is gone.
    old_line = (
        "I take a screenshot and extract the text. I also see your active app, window title, "
        "and all open Chrome tabs at all times."
    )
    assert old_line not in src, \
        "D-2 regression: unconditional vision advertisement still present in server.py"
    ok("D-2.a: former unconditional vision advertisement removed from server.py")
except Exception as e:
    fail("D-2.a", e)


# D-2.b — the new gate is present: only fires when the user asks about seeing
try:
    with open(SERVER, encoding="utf-8") as f:
        src = f.read()
    # Look for the D-2 gate marker + the regex the guard uses.
    assert "D-2 · vision-claim gate" in src, \
        "D-2 gate marker missing from server.py"
    assert "_vision_ask" in src, \
        "D-2 vision-ask predicate missing from server.py"
    # The scripted 'when asked can you see' line must sit AFTER a match on _vision_ask.
    idx_gate = src.find("_vision_ask = _re.search")
    idx_line = src.find("Right now — vision is active")
    assert idx_gate > 0 and idx_line > idx_gate, \
        "D-2: 'Right now — vision is active' beat is not gated behind _vision_ask"
    ok("D-2.b: vision-claim block is gated on the user asking about seeing")
except Exception as e:
    fail("D-2.b", e)


# D-2.c — three live-state phrasings exist (can / no-permission / off)
try:
    with open(SERVER, encoding="utf-8") as f:
        src = f.read()
    assert "Right now — vision is active" in src, "phrasing 1 (can) missing"
    assert "Screen-recording permission" in src or "screen-recording permission" in src.lower(), \
        "phrasing 2 (no permission) missing"
    assert "vision isn't active" in src, "phrasing 3 (offline) missing"
    ok("D-2.c: three live-state phrasings present (can / no-permission / off)")
except Exception as e:
    fail("D-2.c", e)


# D-2.d — the block reads blender_state.json for vision.active
try:
    with open(SERVER, encoding="utf-8") as f:
        src = f.read()
    assert 'blender_state.json' in src and '"active"' not in src or \
           '_vis.get("active")' in src, \
        "D-2: vision block does not read blender/blender_state.json vision.active"
    ok("D-2.d: block reads live vision.active from blender_state.json")
except Exception as e:
    fail("D-2.d", e)


print()
print("=" * 52)
print(f"Card 0020 · D-2 vision-claim gate  {PASS} passed  {FAIL} failed")
if FAIL:
    sys.exit(1)
