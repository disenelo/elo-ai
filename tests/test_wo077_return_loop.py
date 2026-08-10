"""
tests/test_wo077_return_loop.py — WO-077: Return loop — own-speech in every turn

Tests that eLo's own recent utterances enter the system prompt each turn so it
can reference what it just said.

  AT-0: py_compile clean on server.py
  AT-1: conversation_matrix.push() stores elo utterances under "elo" key
  AT-2: [RECENT DIALOGUE] block built from last 3 turns with elo entries
  AT-3: block is omitted when no elo entries (e.g. first turn before any reply)
  AT-4: block caps at last 3 turns, not more
  AT-5: WO-077 marker present in server.py

Run: python3 tests/test_wo077_return_loop.py
"""
from __future__ import annotations
import sys, os, py_compile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

_passed = _failed = 0

def ok(label: str):
    global _passed
    _passed += 1
    print(f"  ✅ {label}")

def fail(label: str, err):
    global _failed
    _failed += 1
    print(f"  ❌ {label}: {err}")


# ── AT-0: py_compile clean ────────────────────────────────────────────────────
try:
    _base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    py_compile.compile(os.path.join(_base, "server.py"), doraise=True)
    ok("AT-0: py_compile clean on server.py")
except py_compile.PyCompileError as e:
    fail("AT-0", e)
except Exception as e:
    fail("AT-0", e)


# ── AT-1: push() stores elo utterances under the 'elo' key ────────────────────
try:
    from runtime.router import conversation_matrix as _cm
    _cm._SESSION_WINDOW.clear()

    _cm.push("hello eLo", "Hey David, I'm right here.")
    assert len(_cm._SESSION_WINDOW) == 1
    turn = _cm._SESSION_WINDOW[0]
    assert turn.get("user") == "hello eLo", f"user key wrong: {turn}"
    assert turn.get("elo") == "Hey David, I'm right here.", f"elo key wrong: {turn}"
    ok("AT-1: push() stores user + elo utterance under correct keys")

    _cm._SESSION_WINDOW.clear()
except AssertionError as e:
    fail("AT-1", e)
except Exception as e:
    fail("AT-1", e)


# ── Helper: build the [RECENT DIALOGUE] block the same way server.py does ─────
def _build_dialogue_block(window, n=3):
    """Mirror of the WO-077 server.py logic — returns None if nothing to inject."""
    turns = [t for t in window[-n:] if t.get("elo")]
    if not turns:
        return None
    lines = []
    for t in turns:
        if t.get("user"):
            lines.append(f"David: {t['user'][:120]}")
        lines.append(f"eLo:   {t['elo'][:120]}")
    return (
        "\n\n[RECENT DIALOGUE — last 3 turns, oldest first]\n"
        + "\n".join(lines)
        + "\nThis is what you just said. Reference or continue it when relevant — never fabricate links."
    )


# ── AT-2: block built from last 3 turns with elo entries ─────────────────────
try:
    window = [
        {"user": "turn 1 user", "elo": "turn 1 eLo response"},
        {"user": "turn 2 user", "elo": "turn 2 eLo response"},
    ]
    block = _build_dialogue_block(window)
    assert block is not None, "block should be non-None when turns have elo entries"
    assert "[RECENT DIALOGUE" in block, f"header missing: {block[:80]}"
    assert "turn 1 eLo response" in block, "turn 1 eLo not in block"
    assert "turn 2 eLo response" in block, "turn 2 eLo not in block"
    assert "David: turn 1 user" in block, "user label missing"
    ok("AT-2: [RECENT DIALOGUE] block built correctly from turns with elo entries")
except AssertionError as e:
    fail("AT-2", e)
except Exception as e:
    fail("AT-2", e)


# ── AT-3: block is None when no elo entries ────────────────────────────────────
try:
    window_no_elo = [
        {"user": "first message"},
        {"user": "second message"},
    ]
    block = _build_dialogue_block(window_no_elo)
    assert block is None, f"block should be None when no elo entries; got {block!r}"
    ok("AT-3: block omitted when no elo entries (first turn / user-only window)")
except AssertionError as e:
    fail("AT-3", e)
except Exception as e:
    fail("AT-3", e)


# ── AT-4: only last 3 turns injected, not more ────────────────────────────────
try:
    window_long = [
        {"user": f"u{i}", "elo": f"e{i}"} for i in range(10)
    ]
    block = _build_dialogue_block(window_long)
    assert block is not None
    # Only e7, e8, e9 (last 3) should appear; e6 and earlier should not
    assert "e9" in block and "e8" in block and "e7" in block, \
        f"last 3 turns should appear: {block[-200:]}"
    assert "e6" not in block, \
        f"4th-to-last turn must not appear; got block snippet: {block[-200:]}"
    ok("AT-4: only last 3 turns included in block")
except AssertionError as e:
    fail("AT-4", e)
except Exception as e:
    fail("AT-4", e)


# ── AT-5: WO-077 marker present in server.py ─────────────────────────────────
try:
    _base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(os.path.join(_base, "server.py"), encoding="utf-8") as _f:
        _src = _f.read()
    assert "WO-077" in _src, "WO-077 marker not found in server.py"
    assert "[RECENT DIALOGUE" in _src, "[RECENT DIALOGUE block not found in server.py"
    assert "_cw_077" in _src, "own-speech import variable _cw_077 not found in server.py"
    ok("AT-5: WO-077 marker + [RECENT DIALOGUE] block wired in server.py")
except AssertionError as e:
    fail("AT-5", e)
except Exception as e:
    fail("AT-5", e)


# ── Final summary ─────────────────────────────────────────────────────────────
print()
print("=" * 62)
print(f"WO-077 return loop   {_passed} passed   {_failed} failed")
if _failed:
    sys.exit(1)
