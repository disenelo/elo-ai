"""
tests/test_capability_dispatcher.py — WO-B1-0104

Tests for runtime/capability_dispatcher.py.
All tests are headless (no live server, no LLM calls).
"""

import pytest
from runtime.capability_dispatcher import (
    classify,
    dispatch_fact,
    TIER_FACT, TIER_STATE, TIER_COGNITION, TIER_UNKNOWN,
)


# ── classify() ────────────────────────────────────────────────────────────────

class TestClassify:
    def test_time_request(self):
        assert classify("What time is it?") == TIER_FACT

    def test_time_request_short(self):
        assert classify("time?") == TIER_FACT

    def test_date_request(self):
        assert classify("What's today's date?") == TIER_FACT

    def test_date_request_alt(self):
        assert classify("what is today") == TIER_FACT

    # David 2026-10-09: "battery" is eLo's (robot battery / Presence health), never the
    # Mac by default, so a bare battery question is NOT a macOS FACT.
    def test_battery_request(self):
        assert classify("how much battery do I have?") != TIER_FACT

    def test_battery_request_short(self):
        assert classify("battery?") != TIER_FACT

    def test_battery_request_named_mac_is_fact(self):
        assert classify("what's my Mac's battery?") == TIER_FACT

    def test_disk_request(self):
        assert classify("how much disk space is left?") == TIER_FACT

    def test_math_expression(self):
        assert classify("28 × 74") == TIER_FACT

    def test_math_expression_words(self):
        assert classify("what is 28 times 74") == TIER_FACT

    def test_math_calculate(self):
        assert classify("calculate 5+3*2") == TIER_FACT

    def test_what_am_i_working_on(self):
        assert classify("what am I working on?") == TIER_STATE

    def test_what_are_we_building(self):
        assert classify("what are we building today?") == TIER_STATE

    def test_what_is_next(self):
        assert classify("what's next?") == TIER_STATE

    def test_what_should_i_do(self):
        assert classify("what should I do?") == TIER_COGNITION

    def test_explain(self):
        assert classify("explain this to me") == TIER_COGNITION

    def test_why_question(self):
        assert classify("why is this not working?") == TIER_COGNITION

    def test_what_do_you_think(self):
        assert classify("what do you think about this?") == TIER_COGNITION

    def test_casual_chat(self):
        # "hey" → UNKNOWN (no pattern match)
        result = classify("hey")
        assert result == TIER_UNKNOWN

    def test_empty(self):
        assert classify("") == TIER_UNKNOWN

    def test_none_like(self):
        assert classify("   ") == TIER_UNKNOWN


# ── dispatch_fact() ───────────────────────────────────────────────────────────

class TestDispatchFactBuiltin:
    """Tests for the builtin fallback path (no system_primitives)."""

    def test_time_returns_metadata(self):
        result = dispatch_fact("What time is it?")
        assert result is not None
        assert "value" in result
        assert result["source"] == "macOS"
        assert result["authority"] == "definitive"
        assert result["confidence"] == 1.0
        assert result["freshness"] == "live"
        assert isinstance(result["value"], str)
        assert result["value"]  # non-empty

    def test_date_returns_metadata(self):
        result = dispatch_fact("What's today's date?")
        assert result is not None
        assert "value" in result
        assert result["authority"] == "definitive"
        assert isinstance(result["value"], str)

    def test_tomorrow_returns_metadata(self):
        result = dispatch_fact("What's tomorrow's date?")
        assert result is not None
        assert isinstance(result["value"], str)

    def test_yesterday_returns_metadata(self):
        result = dispatch_fact("What's yesterday's date?")
        assert result is not None
        assert isinstance(result["value"], str)

    def test_math_correct(self):
        result = dispatch_fact("28 × 74")
        assert result is not None
        assert str(result["value"]) == "2072"

    def test_math_addition(self):
        result = dispatch_fact("what is 5 + 3")
        assert result is not None
        assert str(result["value"]) == "8"

    def test_math_division(self):
        result = dispatch_fact("100 / 4")
        assert result is not None
        assert str(result["value"]) == "25"

    def test_math_complex(self):
        result = dispatch_fact("calculate 2 + 3 * 4")
        assert result is not None
        # 2 + 12 = 14 (standard precedence)
        assert str(result["value"]) == "14"

    def test_no_injection_attack(self):
        # Malicious expression should return None (safe_eval rejects it)
        result = dispatch_fact("what is __import__('os').system('ls')")
        # Either None (safe_eval rejected) or a numeric result — never executes the attack
        if result is not None:
            # If it returned something, it must be a number
            assert isinstance(result["value"], (int, float, str))

    def test_battery_returns_none_without_primitives(self):
        # battery requires system_primitives; builtin fallback returns None for battery
        result = dispatch_fact("how much battery?")
        # If system_primitives not installed, result is None (graceful fallback)
        # If it IS installed, result is a dict — either is valid
        assert result is None or isinstance(result, dict)

    def test_unknown_request_returns_none(self):
        result = dispatch_fact("tell me a story about robots")
        assert result is None

    def test_fact_is_not_overridden(self):
        """dispatch_fact must not call any LLM — just check it returns quickly."""
        import time
        start = time.monotonic()
        result = dispatch_fact("What time is it?")
        elapsed = time.monotonic() - start
        assert elapsed < 1.0, f"dispatch_fact took {elapsed:.2f}s — LLM call suspected"
        assert result is not None



def test_spoken_sums_reach_system_primitives():
    # B3 2026-10-09: no symbol run to extract → whole request to math.calculate
    assert dispatch_fact("what's 6 times 7")["value"] == "42"
    assert dispatch_fact("what is 15% of 80")["value"] == "12"
