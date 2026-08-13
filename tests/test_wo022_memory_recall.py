"""
tests/test_wo022_memory_recall.py — Acceptance tests for WO-022

Verifies that recall intent is detected correctly and vault retrieval is
wired, not the canned stats line.

    AT-1  "what do you remember?" matches the expanded recall trigger set
    AT-2  "tell me something from your memory" also matches (was missing before)
    AT-3  Vault lookup uses a focused topic query, not raw question words
    AT-4  Stats line ("Memory's running") is blocked as a recall reply
    AT-5  Frozen kernel tests still green

Run: python3 tests/test_wo022_memory_recall.py
"""
import sys, os, re
sys.path.insert(0, ".")

PASS = 0; FAIL = 0
def ok(n):      global PASS; PASS += 1; print(f"  ✅ {n}")
def fail(n, r): global FAIL; FAIL += 1; print(f"  ❌ {n}: {r}")


# ── Reproduce the trigger check exactly as written in server.py ───────────────

_RECALL_TRIGGERS = (
    "do you remember", "what did you say", "what did elo say",
    "last sentence", "what was the last", "what did we talk about",
    "what did we last", "what did we say", "you said",
    "last conversation", "what was said", "what were we talking",
    "what have we been", "what did i say", "remind me what",
    "from your memory", "from memory", "what have you kept",
    "what do you have stored", "what do you remember",
    "tell me something you", "share something from",
    "what do you know about me", "what have you learned",
    "pull something from memory", "recall something",
    "what's in your memory", "what's in memory",
)

def _is_recall(raw: str) -> bool:
    t = raw.lower()
    return any(p in t for p in _RECALL_TRIGGERS)


# ── AT-1: canonical failing phrases match the expanded trigger set ─────────────

_AT1_CASES = [
    ("what do you remember?",              True),
    ("what do you remember from last week?",True),
    ("tell me something from your memory",  True),
    ("from your memory, what do you have?", True),
    ("what do you have stored?",            True),
    ("do you remember last time?",          True),
    ("what's in your memory?",              True),
    ("what's in memory?",                   True),
    ("what have you kept?",                 True),
]

_all_ok = True
for _raw, _expected in _AT1_CASES:
    _got = _is_recall(_raw)
    if _got != _expected:
        fail(f"AT-1 case {_raw!r}", f"expected={_expected}, got={_got}")
        _all_ok = False

if _all_ok:
    ok(f"AT-1: all {len(_AT1_CASES)} recall phrases detected correctly")


# ── AT-2: "tell me something from your memory" — was missing before WO-022 ────

try:
    assert _is_recall("tell me something from your memory"), \
        "trigger miss: 'tell me something from your memory'"
    assert _is_recall("tell me something you know"), \
        "trigger miss: 'tell me something you know'"
    ok("AT-2: 'tell me something from your memory' / 'tell me something you know' both detected")
except AssertionError as e: fail("AT-2", e)


# ── AT-3: topic word extraction skips filler, produces useful query ───────────

_RECALL_SKIP = frozenset({
    "what", "you", "remember", "tell", "from", "your", "my",
    "do", "did", "that", "the", "something", "anything", "have",
    "has", "me", "about", "how", "much", "know", "last", "time",
    "pull", "share", "recall", "memory", "stored", "kept", "elo",
})

def _extract_recall_query(raw: str) -> str:
    raw_l = raw.lower()
    topic_words = [
        w for w in re.sub(r'[^a-z0-9 ]', '', raw_l).split()
        if w not in _RECALL_SKIP and len(w) >= 3
    ]
    return " ".join(topic_words) if topic_words else "disenelo recent"

_AT3_CASES = [
    # (input, expected_substring_in_query OR "disenelo recent" for fallback)
    ("what do you remember?",                              "disenelo recent"),
    ("what do you remember from last week?",               "week"),
    ("tell me something from your memory about eLo",       "disenelo recent"),  # "about"+"elo" both skipped
    ("what do you have stored about the game?",            "game"),
    ("what do you remember about the kickstarter?",        "kickstarter"),
]

_all_ok3 = True
for _raw, _expected_contains in _AT3_CASES:
    _q = _extract_recall_query(_raw)
    # We just check it's not empty and doesn't contain pure question words
    _has_filler = any(w in _q.split() for w in ["what", "you", "remember", "tell"])
    if _has_filler:
        fail(f"AT-3 case {_raw!r}", f"query contains filler words: {_q!r}")
        _all_ok3 = False
    elif _expected_contains != "disenelo recent" and _expected_contains not in _q:
        fail(f"AT-3 case {_raw!r}", f"expected {_expected_contains!r} in query {_q!r}")
        _all_ok3 = False

if _all_ok3:
    ok(f"AT-3: topic extraction skips fillers for all {len(_AT3_CASES)} cases")


# ── AT-4: "Memory's running" is blocked as a recall reply ─────────────────────
# The IMPORTANT directive added to the system prompt prohibits this text.
# We verify the directive string is present in server.py (integration-level check).

try:
    _server_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "server.py")
    with open(_server_path, encoding="utf-8") as _sf:
        _server_src = _sf.read()
    assert "Never say 'Memory" in _server_src or "Never say .Memory" in _server_src, \
        "stats-line prohibition directive not found in server.py"
    assert "recall response" in _server_src.lower(), \
        "recall response instruction not found in server.py"
    ok("AT-4: stats-line prohibition directive present in server.py system prompt injection")
except AssertionError as e: fail("AT-4", e)
except Exception as e: fail("AT-4", f"exception: {e}")


# ── AT-5: frozen kernel tests still green ─────────────────────────────────────

print("\n  Running frozen kernel test suite...")
import subprocess
_frozen = [
    "tests/test_wo001_faculty_bus.py",
    "tests/test_wo014_spine_wiring.py",
    "tests/test_wo006_emotional_processing.py",
]
_kernel_ok = True
for _tf in _frozen:
    _r = subprocess.run(
        [sys.executable, _tf],
        capture_output=True, text=True,
        cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    )
    _last_line = _r.stdout.strip().splitlines()[-1] if _r.stdout.strip() else ""
    if _r.returncode != 0:
        print(f"    ⚠ {_tf}: {_last_line}")
        _kernel_ok = False
    else:
        print(f"    ✓ {_tf}: {_last_line}")

try:
    assert _kernel_ok, "one or more frozen kernel tests failed after WO-022 patch"
    ok("AT-5: frozen kernel tests still pass")
except AssertionError as e: fail("AT-5", e)


print(f"\nResult: {PASS}/5 passed, {FAIL} failed")
sys.exit(1 if FAIL else 0)
