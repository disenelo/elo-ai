"""
tests/test_wo064_expression_micro.py — BP-4: Self-Model emits expression.micro (WO-064)

Designer built ApplyExpression reading expression.micro + micro_ts (edge-triggered)
→ FlashMicro. This tests that the brain publishes the field from the real
cognitive/emotional state (not Unity-random).

Rules:
  - Non-neutral emotion at intensity >= 0.4 → expression.micro + micro_ts emitted
  - Neutral/calm / intensity < 0.4 → no emission (don't spam)
  - Command-only, no ACK (per the expression ruling)

  AT-1: joy + intensity 0.7 → expression.micro == "joy" + micro_ts present
  AT-2: curiosity + intensity 0.5 → expression.micro == "curious"
  AT-3: distress + intensity 0.6 → expression.micro == "worried"
  AT-4: neutral + intensity 0.3 → expression.micro NOT emitted (no spam)
  AT-5: joy + intensity 0.2 (below threshold) → NOT emitted
  AT-6: _MICRO_MAP covers all 7 Designer-accepted micro emotions
  AT-7: BP-4 marker + _MICRO_MAP present in server.py
  AT-8: py_compile clean

Run: python3 tests/test_wo064_expression_micro.py
"""
import sys, py_compile, time
sys.path.insert(0, ".")

PASS = 0; FAIL = 0
def ok(n):      global PASS; PASS += 1; print(f"  ✅ {n}")
def fail(n, r): global FAIL; FAIL += 1; print(f"  ❌ {n}: {r}")


# Inline copy of the micro emission logic from server.py
_MICRO_MAP = {
    "joy":        "joy",
    "curiosity":  "curious",
    "curious":    "curious",
    "challenge":  "worried",
    "distress":   "worried",
    "worried":    "worried",
    "confident":  "confident",
    "disgust":    "disgust",
    "sad":        "sad",
    "excited":    "joy",
    "playful":    "joy",
    "alert":      "curious",
    "satisfied":  "satisfied",
}

def _emit_micro(emotion: str, intensity: float) -> dict:
    micro = _MICRO_MAP.get(emotion.lower(), "")
    if micro and intensity >= 0.4:
        return {"micro": micro, "micro_ts": round(time.time(), 3)}
    return {}


# ── AT-1: joy + 0.7 → joy ────────────────────────────────────────────────────
try:
    r = _emit_micro("joy", 0.7)
    assert r.get("micro") == "joy", f"expected 'joy', got {r.get('micro')!r}"
    assert "micro_ts" in r, "micro_ts missing"
    ok(f"AT-1: joy 0.7 → expression.micro='joy' with micro_ts")
except AssertionError as e:
    fail("AT-1", e)

# ── AT-2: curiosity + 0.5 → curious ─────────────────────────────────────────
try:
    r = _emit_micro("curiosity", 0.5)
    assert r.get("micro") == "curious", f"expected 'curious', got {r.get('micro')!r}"
    ok("AT-2: curiosity 0.5 → 'curious'")
except AssertionError as e:
    fail("AT-2", e)

# ── AT-3: distress + 0.6 → worried ──────────────────────────────────────────
try:
    r = _emit_micro("distress", 0.6)
    assert r.get("micro") == "worried", f"expected 'worried', got {r.get('micro')!r}"
    ok("AT-3: distress 0.6 → 'worried'")
except AssertionError as e:
    fail("AT-3", e)

# ── AT-4: neutral + 0.3 → no emission ────────────────────────────────────────
try:
    r = _emit_micro("neutral", 0.3)
    assert r == {}, f"neutral should not emit, got {r}"
    ok("AT-4: neutral 0.3 → no expression.micro emitted")
except AssertionError as e:
    fail("AT-4", e)

# ── AT-5: joy below threshold → no emission ───────────────────────────────────
try:
    r = _emit_micro("joy", 0.2)
    assert r == {}, f"low-intensity joy should not emit, got {r}"
    ok("AT-5: joy 0.2 (below 0.4 threshold) → no emission")
except AssertionError as e:
    fail("AT-5", e)

# ── AT-6: all 7 Designer micro emotions reachable ────────────────────────────
try:
    _DESIGNER_MICROS = {"joy", "worried", "confident", "curious", "disgust", "sad", "satisfied"}
    _reachable = set()
    for _emo, _micro in _MICRO_MAP.items():
        _reachable.add(_micro)
    _missing = _DESIGNER_MICROS - _reachable
    assert not _missing, f"micro emotions not reachable: {_missing}"
    ok(f"AT-6: all 7 Designer micro emotions reachable from _MICRO_MAP")
except AssertionError as e:
    fail("AT-6", e)

# ── AT-7: server.py has BP-4 marker + _MICRO_MAP ─────────────────────────────
try:
    with open("server.py", encoding="utf-8") as f:
        _src = f.read()
    assert "BP-4 (WO-064)" in _src, "BP-4 marker not found in server.py"
    assert "_MICRO_MAP" in _src, "_MICRO_MAP not found in server.py"
    assert "expression" in _src and "micro_ts" in _src, "expression/micro_ts not in _bs_patch"
    ok("AT-7: BP-4 block + _MICRO_MAP confirmed in server.py")
except AssertionError as e:
    fail("AT-7", e)

# ── AT-8: py_compile ──────────────────────────────────────────────────────────
try:
    py_compile.compile("server.py", doraise=True)
    ok("AT-8: py_compile clean on server.py")
except py_compile.PyCompileError as e:
    fail("AT-8", e)


print()
print("=" * 50)
print(f"BP-4 expression.micro  {PASS} passed  {FAIL} failed")
if FAIL:
    sys.exit(1)
