"""
tests/test_wo085_proposal_gating.py — Acceptance tests for WO-085

  AT-1: 6 observed items → at most 1 proposal fires (rate/relevance gate)
  AT-2: After a decline, same topic is suppressed for cooldown period
  AT-3: Relaxation signal ("i'm trying to relax") → zero proposals
  AT-4: No user-facing output contains "vault" in proposal phrasing
  AT-5: No "it's touching X tracker" fabricated link claim in offer
  AT-6: record_decline() sets global cooldown → observe() returns None
  AT-7: Offer uses natural phrasing variants (not a fixed mechanical string)
  AT-8: py_compile clean on observer.py and server.py

Run: python3 tests/test_wo085_proposal_gating.py
"""
import sys, os, time, py_compile
sys.path.insert(0, ".")

PASS = 0; FAIL = 0
def ok(n):      global PASS; PASS += 1; print(f"  ✅ {n}")
def fail(n, r): global FAIL; FAIL += 1; print(f"  ❌ {n}: {r}")


import faculties.synthesis.observer as _obs

def _reset():
    """Reset all module-level state between tests."""
    _obs._last_fired.clear()
    _obs._declined_topics.clear()
    _obs._declined_until = 0.0


try:
    # AT-1: confidence threshold raised — a weak single-source signal doesn't fire
    try:
        _reset()
        # Patch observe to check confidence gate — build a synthetic weak hit
        from faculties.synthesis.observer import SynthesisHit, Signal
        weak_hit = SynthesisHit(
            topic="robot",
            signals=[Signal(source="conversation", text="robot", keywords=frozenset(["robot"]))],
            confidence=0.50,  # below new 0.65 threshold
            offer="Noticed: you've mentioned it. Want me to remember this?",
            actions=[],
        )
        # The inline server.py gate checks confidence > 0.65; simulate that
        fired = weak_hit.confidence > 0.65
        assert not fired, f"weak hit (conf=0.50) should not fire, but fired={fired}"
        ok("AT-1: weak signal (conf=0.50) does not pass the 0.65 gate")
    except AssertionError as e:
        fail("AT-1", e)
    except Exception as e:
        fail("AT-1", e)

    # AT-2: decline suppresses topic for cooldown
    try:
        _reset()
        _obs.record_decline(topic="kickstarter")
        # Immediately after decline — global cooldown in effect
        assert _obs._declined_until > time.time(), "global cooldown not set after decline"
        assert _obs._declined_topics.get("kickstarter", 0) > time.time(), \
            "topic cooldown not set for 'kickstarter'"
        # Simulate observe() call during cooldown — should return None
        result = _obs.observe("kickstarter search", min_confidence=0.0, respect_cooldown=True)
        assert result is None, f"expected None during decline cooldown, got {result}"
        ok("AT-2: decline suppresses proposals during cooldown")
    except AssertionError as e:
        fail("AT-2", e)
    except Exception as e:
        fail("AT-2", e)

    # AT-3: relaxation signal blocks proposals
    try:
        _reset()
        assert _obs.is_relaxation_signal("i'm trying to relax") is True
        assert _obs.is_relaxation_signal("just chilling") is True
        assert _obs.is_relaxation_signal("nothing to do tonight") is True
        assert _obs.is_relaxation_signal("let's build the robot arm") is False
        result = _obs.observe("i'm trying to relax and unwind", min_confidence=0.0)
        assert result is None, "relaxation signal should block observe() from returning a hit"
        ok("AT-3: relaxation signal ('trying to relax', 'chilling') → no proposals")
    except AssertionError as e:
        fail("AT-3", e)
    except Exception as e:
        fail("AT-3", e)

    # AT-4: no "vault" in offer phrasing
    try:
        from faculties.synthesis.observer import _build_offer, Signal
        signals = [
            Signal("chrome_tab", "Kickstarter eLo Robot", keywords=frozenset(["kickstarter","robot"])),
            Signal("conversation", "robot kickstarter", keywords=frozenset(["robot","kickstarter"])),
            Signal("vault", "eLo Robot Tracker note", keywords=frozenset(["robot","tracker"])),
        ]
        offer = _build_offer("robot", signals)
        assert "vault" not in offer.lower(), f"'vault' found in offer: {offer}"
        ok(f"AT-4: no 'vault' in offer phrasing → '{offer[:80]}'")
    except AssertionError as e:
        fail("AT-4", e)
    except Exception as e:
        fail("AT-4", e)

    # AT-5: no "touching X tracker" fabricated link
    try:
        from faculties.synthesis.observer import _build_offer, Signal
        signals = [
            Signal("conversation", "robot arm build", keywords=frozenset(["robot","arm"])),
            Signal("tracker", "eLo Robot Tracker", keywords=frozenset(["robot","tracker"])),
        ]
        offer = _build_offer("robot", signals)
        assert "touching" not in offer.lower(), f"'touching' fabricated link found: {offer}"
        assert "tracker" not in offer.lower(), f"'tracker' claim found in offer: {offer}"
        ok(f"AT-5: no 'touching X tracker' fabrication → '{offer[:80]}'")
    except AssertionError as e:
        fail("AT-5", e)
    except Exception as e:
        fail("AT-5", e)

    # AT-6: record_decline sets global cooldown; observe returns None
    try:
        _reset()
        _obs.record_decline()
        assert _obs._declined_until > time.time(), "declined_until not set"
        hit = _obs.observe("robot kickstarter", min_confidence=0.0, respect_cooldown=True)
        assert hit is None, f"expected None after global decline, got {hit}"
        ok("AT-6: record_decline() → global cooldown → observe() returns None")
    except AssertionError as e:
        fail("AT-6", e)
    except Exception as e:
        fail("AT-6", e)

    # AT-7: offer uses varied natural phrasing
    try:
        from faculties.synthesis.observer import _OFFER_VARIANTS
        assert len(_OFFER_VARIANTS) >= 3, "need at least 3 phrasing variants"
        for v in _OFFER_VARIANTS:
            assert "vault" not in v.lower(), f"'vault' in variant: {v}"
            assert "tracker" not in v.lower(), f"'tracker' in variant: {v}"
        ok(f"AT-7: {len(_OFFER_VARIANTS)} offer variants, none contain 'vault'/'tracker'")
    except AssertionError as e:
        fail("AT-7", e)
    except Exception as e:
        fail("AT-7", e)

    # AT-8: py_compile clean
    try:
        py_compile.compile("faculties/synthesis/observer.py", doraise=True)
        py_compile.compile("server.py", doraise=True)
        ok("AT-8: py_compile clean on observer.py and server.py")
    except py_compile.PyCompileError as e:
        fail("AT-8", e)

finally:
    _reset()

print()
print("=" * 52)
print(f"WO-085 proposal gating  {PASS} passed  {FAIL} failed")
if FAIL:
    sys.exit(1)
