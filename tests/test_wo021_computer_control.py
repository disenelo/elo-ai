"""
WO-021 acceptance tests — Computer Control enable + verify.

AT-1  parse_intent("open Spotify") → {"type": "open", "app": "Spotify"}
AT-2  parse_intent("open the Notes app") → app stripped to "Notes"
AT-3  parse_intent("open Visual Studio Code") → multi-word app preserved
AT-4  describe({"type": "open", "app": "Spotify"}) → "open Spotify"
AT-5  is_enabled() returns False when ELO_COMPUTER_CONTROL not set
AT-6  execute() with flag off → returns disabled message (no action taken)
AT-7  No stale latch: fresh parse_intent call on different target returns new app
AT-8  Non-open intents still return None (reminder, unrelated text)
AT-9  Frozen kernel untouched (executive.py + prompts/ unchanged)
"""
import importlib.util
import os
import sys

_ROOT    = os.path.join(os.path.dirname(__file__), "..")
_CC_PATH = os.path.join(_ROOT, "tools", "computer_control_agent.py")

_spec = importlib.util.spec_from_file_location("computer_control_agent_test", _CC_PATH)
_mod  = importlib.util.module_from_spec(_spec)
sys.modules["computer_control_agent_test"] = _mod
_spec.loader.exec_module(_mod)

parse_intent = _mod.parse_intent
describe     = _mod.describe
execute      = _mod.execute
is_enabled   = _mod.is_enabled


# ── AT-1 ─────────────────────────────────────────────────────────────────────

def test_at1_open_spotify():
    result = parse_intent("open Spotify")
    assert result is not None,          "AT-1 FAIL: returned None"
    assert result["type"] == "open",    f"AT-1 FAIL: type={result['type']}"
    assert result["app"] == "Spotify",  f"AT-1 FAIL: app={result['app']}"
    print(f"AT-1 PASS — parse_intent('open Spotify') → {result}")


# ── AT-2 ─────────────────────────────────────────────────────────────────────

def test_at2_strip_the_app():
    result = parse_intent("open the Notes app")
    assert result is not None,         "AT-2 FAIL: returned None"
    assert result["type"] == "open",   f"AT-2 FAIL: type={result['type']}"
    assert result["app"] == "Notes",   f"AT-2 FAIL: app={result['app']!r} (expected 'Notes')"
    print(f"AT-2 PASS — 'open the Notes app' → app={result['app']!r}")


# ── AT-3 ─────────────────────────────────────────────────────────────────────

def test_at3_multi_word_app():
    result = parse_intent("open Visual Studio Code")
    assert result is not None,                          "AT-3 FAIL: returned None"
    assert result["app"] == "Visual Studio Code",       f"AT-3 FAIL: app={result['app']!r}"
    print(f"AT-3 PASS — multi-word app preserved: {result['app']!r}")


# ── AT-4 ─────────────────────────────────────────────────────────────────────

def test_at4_describe():
    d = describe({"type": "open", "app": "Spotify"})
    assert d == "open Spotify", f"AT-4 FAIL: describe returned {d!r}"
    print(f"AT-4 PASS — describe → {d!r}")


# ── AT-5 ─────────────────────────────────────────────────────────────────────

def test_at5_flag_off_by_default():
    orig = os.environ.pop("ELO_COMPUTER_CONTROL", None)
    try:
        assert not is_enabled(), "AT-5 FAIL: is_enabled() returned True without flag"
    finally:
        if orig is not None:
            os.environ["ELO_COMPUTER_CONTROL"] = orig
    print("AT-5 PASS — is_enabled() False without ELO_COMPUTER_CONTROL")


# ── AT-6 ─────────────────────────────────────────────────────────────────────

def test_at6_execute_disabled():
    orig = os.environ.pop("ELO_COMPUTER_CONTROL", None)
    try:
        result = execute({"type": "open", "app": "Spotify"})
        assert "disabled" in result.lower() or "ELO_COMPUTER_CONTROL" in result, \
            f"AT-6 FAIL: expected disabled message, got: {result!r}"
    finally:
        if orig is not None:
            os.environ["ELO_COMPUTER_CONTROL"] = orig
    print(f"AT-6 PASS — execute() with flag off → {result!r}")


# ── AT-7 ─────────────────────────────────────────────────────────────────────

def test_at7_no_stale_latch():
    r1 = parse_intent("open Spotify")
    r2 = parse_intent("open Safari")
    assert r1["app"] == "Spotify", f"AT-7 FAIL: r1.app={r1['app']}"
    assert r2["app"] == "Safari",  f"AT-7 FAIL: r2.app={r2['app']}"
    assert r1["app"] != r2["app"], "AT-7 FAIL: both calls returned same app (stale latch)"
    print(f"AT-7 PASS — no stale latch: Spotify then Safari → both correct")


# ── AT-8 ─────────────────────────────────────────────────────────────────────

def test_at8_non_open_returns_none():
    cases = [
        "remind me to call mum",
        "how are you doing",
        "what time is it",
    ]
    for c in cases:
        r = parse_intent(c)
        assert r is None or r.get("type") != "open", \
            f"AT-8 FAIL: {c!r} wrongly parsed as open: {r}"
    print("AT-8 PASS — non-open text not misrouted as open")


# ── AT-9 ─────────────────────────────────────────────────────────────────────

def test_at9_frozen_kernel():
    for path in [os.path.join(_ROOT, "runtime", "executive.py")]:
        if not os.path.exists(path):
            continue
        with open(path, "rb") as f:
            content = f.read()
        for token in (b"computer_control_agent", b"_OPEN_RE", b"ELO_COMPUTER_CONTROL"):
            assert token not in content, \
                f"AT-9 FAIL: frozen file {path} contains WO-021 token '{token.decode()}'"
    prompts_dir = os.path.join(_ROOT, "prompts")
    if os.path.isdir(prompts_dir):
        for fname in os.listdir(prompts_dir):
            with open(os.path.join(prompts_dir, fname), "rb") as f:
                content = f.read()
            assert b"ELO_COMPUTER_CONTROL" not in content, \
                f"AT-9 FAIL: prompts/{fname} modified — FREEZE_V1_LOCK violated"
    print("AT-9 PASS — frozen kernel untouched")


# ── runner ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    tests = [
        test_at1_open_spotify,
        test_at2_strip_the_app,
        test_at3_multi_word_app,
        test_at4_describe,
        test_at5_flag_off_by_default,
        test_at6_execute_disabled,
        test_at7_no_stale_latch,
        test_at8_non_open_returns_none,
        test_at9_frozen_kernel,
    ]
    failed = 0
    for t in tests:
        try:
            t()
        except Exception as e:
            print(f"FAIL {t.__name__}: {e}")
            failed += 1
    print(f"\n{'ALL PASS' if not failed else f'{failed} FAILED'} — WO-021 ({len(tests)-failed}/{len(tests)})")
    import sys as _sys
    _sys.exit(failed)
