"""tests/test_card_0020_d1_proposal_loop.py — Card 0020 · D-1 acceptance.

The live-test transcript David ran on 2026-08-19 showed the same 'michael paul -
Google Search' proposal firing five times after being declined twice. WO-085
tests only prove the head keyword is suppressed and only when the exact phrase
matches. This card raises the bar:

  • decline detection includes any leading "no" / "not" / "nope" / "nah";
  • a decline suppresses the ENTIRE subject the last offer was made about — the
    topic + every keyword under it — for the session, not a 5-minute window;
  • the same subject cannot come back under a paraphrase.

Run: python3 tests/test_card_0020_d1_proposal_loop.py
"""
import sys, os, time
sys.path.insert(0, ".")

PASS = 0; FAIL = 0
def ok(n):      global PASS; PASS += 1; print(f"  ✅ {n}")
def fail(n, r): global FAIL; FAIL += 1; print(f"  ❌ {n}: {r}")


import faculties.synthesis.observer as _obs
from faculties.synthesis.observer import (
    SynthesisHit, Signal, is_decline, record_offer, record_decline,
    _declined_topics, _last_offered,
)

def _reset():
    _obs._last_fired.clear()
    _obs._declined_topics.clear()
    _obs._declined_until = 0.0
    _obs._last_offered["topic"]    = ""
    _obs._last_offered["keywords"] = frozenset()
    _obs._last_offered["at"]       = 0.0


# D-1.a — is_decline covers the phrasings from David's live transcript
try:
    _reset()
    for phrase in [
        "No not everything is always worth saving",
        "No Michael Paul",
        "no thanks",
        "nope",
        "nah, leave it",
        "not right now",
        "don't need to save that",
    ]:
        assert is_decline(phrase), f"is_decline() missed {phrase!r}"
    for phrase in [
        "yes please",
        "sure, go ahead",
        "add it",
    ]:
        assert not is_decline(phrase), f"is_decline() false-fired on {phrase!r}"
    ok("D-1.a: is_decline() matches David's live-transcript decline phrasings")
except Exception as e:
    fail("D-1.a", e)


# D-1.b — record_offer + record_decline suppresses every keyword of the offered subject
try:
    _reset()
    hit = SynthesisHit(
        topic="michael",
        signals=[
            Signal(source="history", text="michael paul - Google Search",
                   keywords=frozenset(["michael","paul","google","search"])),
            Signal(source="conversation", text="michael paul",
                   keywords=frozenset(["michael","paul"])),
        ],
        confidence=0.85,
        offer="Noticed: you were looking at 'michael paul - Google Search'. Want me to hold onto that?",
        actions=[],
    )
    record_offer(hit)
    assert _obs._last_offered["topic"] == "michael"
    assert "paul" in _obs._last_offered["keywords"]
    assert "search" in _obs._last_offered["keywords"]

    record_decline()
    _now = time.time()
    # Every keyword of the offered hit is now under a session-length lock.
    for kw in ["michael", "paul", "google", "search"]:
        assert _obs._declined_topics.get(kw, 0) > _now + 60 * 60, \
            f"keyword {kw!r} not locked for the session after decline"
    ok("D-1.b: decline locks the whole offered subject for the session, not just the head token")
except Exception as e:
    fail("D-1.b", e)


# D-1.c — observe() will not surface a hit whose keywords overlap the declined set
try:
    _reset()
    hit = SynthesisHit(
        topic="michael",
        signals=[Signal(
            source="history", text="michael paul - Google Search",
            keywords=frozenset(["michael","paul","google","search"]),
        )],
        confidence=0.85, offer="…", actions=[],
    )
    record_offer(hit)
    record_decline()

    # Fabricate a fresh cluster that shares only ONE keyword with the declined subject —
    # observe() must still reject it, because a paraphrase is still the same subject.
    _obs._last_fired.clear()
    def _fake_chrome():
        return [Signal(source="chrome_tab", text="Michael Paul (Wikipedia)",
                       keywords=frozenset(["michael","wikipedia"])),
                Signal(source="chrome_tab", text="Google Search: paul something",
                       keywords=frozenset(["paul","something"]))]
    def _fake_vault(): return []
    def _fake_tracker(): return []
    def _fake_screen(): return None
    _obs._chrome_signals  = _fake_chrome
    _obs._vault_signals   = _fake_vault
    _obs._tracker_signals = _fake_tracker
    _obs._screen_signal   = _fake_screen
    _obs._declined_until  = 0.0  # bypass the global cooldown to isolate the subject check

    hit2 = _obs.observe("michael paul again", min_confidence=0.0, respect_cooldown=True)
    assert hit2 is None, f"expected None (subject declined); got {hit2}"
    ok("D-1.c: observe() rejects a paraphrase of the declined subject")
except Exception as e:
    fail("D-1.c", e)


print()
print("=" * 52)
print(f"Card 0020 · D-1 proposal loop  {PASS} passed  {FAIL} failed")
if FAIL:
    sys.exit(1)
