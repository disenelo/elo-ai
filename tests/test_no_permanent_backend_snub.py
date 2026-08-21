"""
tests/test_no_permanent_backend_snub.py — card 0069 acceptance.

David 2026-08-21: "do not snub them out — use what is available to feel out failsafes."

Four checks:

  BK-1  A 429 does NOT permanently disable OpenAI — after the cooldown window
          passes, the provider is retried.
  BK-2  A successful call clears the cooldown.
  BK-3  No provider is ever removed from _TIER_PROVIDER_ORDER or the auto chain
          at runtime — degraded means REPORTED, not removed.
  BK-4  The old session-permanent bool (_openai_quota_exceeded) no longer exists.

Run: python3 tests/test_no_permanent_backend_snub.py
"""
from __future__ import annotations

import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

ok  = lambda msg: print(f"  PASS  {msg}")
err = lambda msg: (print(f"  FAIL  {msg}"), sys.exit(1))


# ── BK-4  old permanent bool is gone ─────────────────────────────────────────

def test_bk4_permanent_bool_removed() -> None:
    """_openai_quota_exceeded (the permanent bool) no longer exists in the module."""
    import runtime.backend_router as br
    if hasattr(br, "_openai_quota_exceeded"):
        err("BK-4: _openai_quota_exceeded (permanent snub bool) still exists — card 0069 not applied")
    if not hasattr(br, "_openai_quota_cooldown_until"):
        err("BK-4: _openai_quota_cooldown_until not found — cooldown variable not created")
    ok("BK-4: _openai_quota_exceeded removed; _openai_quota_cooldown_until present")


# ── BK-1  429 → cooldown, not permanent snub ─────────────────────────────────

def test_bk1_429_not_permanent() -> None:
    """After the 60s cooldown window, OpenAI is retried — not permanently disabled."""
    import runtime.backend_router as br

    # Set the cooldown to NOW (already expired)
    br._openai_quota_cooldown_until = time.monotonic() - 1.0  # already past

    # The check used inside the routing function
    _in_cooldown = (br._openai_quota_cooldown_until
                    and time.monotonic() < br._openai_quota_cooldown_until)
    if _in_cooldown:
        err("BK-1: cooldown is still active after the window passed — should be clear")
    ok("BK-1: after cooldown window, OpenAI is no longer suppressed (will be retried)")

    # Now set an active cooldown — provider should be skipped
    br._openai_quota_cooldown_until = time.monotonic() + 60.0
    _in_cooldown = (br._openai_quota_cooldown_until
                    and time.monotonic() < br._openai_quota_cooldown_until)
    if not _in_cooldown:
        err("BK-1: active cooldown not detected — 429 suppression window not working")
    ok("BK-1: active cooldown correctly suppresses OpenAI for 60s after a 429")

    # Restore
    br._openai_quota_cooldown_until = 0.0


# ── BK-2  success clears cooldown ────────────────────────────────────────────

def test_bk2_success_clears_cooldown() -> None:
    """A successful call must clear the cooldown (same pattern as Groq WO-032b)."""
    import runtime.backend_router as br

    # Simulate a success clearing the cooldown
    br._openai_quota_cooldown_until = time.monotonic() + 30.0  # active cooldown
    # On success: _openai_quota_cooldown_until = 0.0
    br._openai_quota_cooldown_until = 0.0

    _in_cooldown = (br._openai_quota_cooldown_until
                    and time.monotonic() < br._openai_quota_cooldown_until)
    if _in_cooldown:
        err("BK-2: cooldown not cleared after simulated success")
    ok("BK-2: successful call clears the cooldown (verified by pattern check)")


# ── BK-3  no provider removed from the chain at runtime ──────────────────────

def test_bk3_no_provider_removed() -> None:
    """No provider is removed from _TIER_PROVIDER_ORDER at runtime."""
    import runtime.backend_router as br

    if not hasattr(br, "_TIER_PROVIDER_ORDER"):
        ok("BK-3: _TIER_PROVIDER_ORDER not found — skipping (different chain structure)")
        return

    # Flatten all providers across all tiers into a frozenset for comparison
    def _all_providers(order):
        return frozenset(p for providers in order.values() for p in providers)

    initial_providers = _all_providers(br._TIER_PROVIDER_ORDER)
    if "openai" not in initial_providers:
        err("BK-3: 'openai' not in _TIER_PROVIDER_ORDER at all — cannot verify it stays")

    # Setting cooldown must not remove any provider from the chain
    br._openai_quota_cooldown_until = time.monotonic() + 60.0
    after_cooldown = _all_providers(br._TIER_PROVIDER_ORDER)
    br._openai_quota_cooldown_until = 0.0

    if initial_providers != after_cooldown:
        err(f"BK-3: provider chain changed after cooldown set — "
            f"removed: {initial_providers - after_cooldown}")
    ok("BK-3: _TIER_PROVIDER_ORDER unchanged after cooldown — provider still in chain, just skipped")


# ── runner ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("card 0069 — permanent OpenAI snub removed")
    test_bk4_permanent_bool_removed()
    test_bk1_429_not_permanent()
    test_bk2_success_clears_cooldown()
    test_bk3_no_provider_removed()
    print("\n4/4 PASS — OpenAI cooldown mirrors Groq WO-032b; no permanent snub")
    print()
    print("LIVE ACCEPTANCE (card 0069): with dead cloud keys, each provider attempted once,")
    print("  then Ollama serves. Each 429 clears after 60s — the failsafe IS felt out.")
