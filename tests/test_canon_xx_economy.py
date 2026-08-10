"""
tests/test_canon_xx_economy.py — WO-CANON-XX: Cognitive Economy

Tests for:
  Ch.1 — tier constants, priority order, scarcity rules
  Ch.2 — token budget, mode chains, escalation logging, tier→budget
  Ch.3 — mock-honesty gate, degradation-honesty, backend_name truthful

Spec ref: engineering/work_orders/WO-CANON-XX.md
"""
from __future__ import annotations
import sys, os, py_compile, logging, io

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ── pass/fail helpers ─────────────────────────────────────────────────────────
_passed = _failed = 0

def ok(label: str):
    global _passed
    _passed += 1
    print(f"  ✅ {label}")

def fail(label: str, err):
    global _failed
    _failed += 1
    print(f"  ❌ {label}: {err}")


# ── import target ─────────────────────────────────────────────────────────────
try:
    from runtime.backend_router import (
        _TIER_REFLEX, _TIER_CONVERSATIONAL, _TIER_REASONING, _TIER_DEEP,
        _COST_FREE_LOCAL, _COST_CHEAP_CLOUD, _COST_PREMIUM_CLOUD,
        _PROVIDER_COST_CLASS,
        _TIER_PROVIDER_ORDER,
        _TIER_BUDGET,
        _ACTION_PRIORITY,
        _action_priority,
        _is_factual_request,
        _action_default_tier,
        _token_budget,
        _HONEST_DEGRADATION_MSG,
        route,
    )
    _import_ok = True
except ImportError as _e:
    _import_ok = False
    print(f"  [import failed: {_e}]")


# ── Ch.1/FT-1: tier constants defined and ordered ─────────────────────────────
try:
    assert _import_ok
    assert _TIER_REFLEX == 0
    assert _TIER_CONVERSATIONAL == 1
    assert _TIER_REASONING == 2
    assert _TIER_DEEP == 3
    assert _TIER_REFLEX < _TIER_CONVERSATIONAL < _TIER_REASONING < _TIER_DEEP
    ok("Ch.1/FT-1: tier constants defined and ordered (0<1<2<3)")
except AssertionError as e:
    fail("Ch.1/FT-1", e)
except Exception as e:
    fail("Ch.1/FT-1", e)


# ── Ch.1/FT-2: cost classes defined ──────────────────────────────────────────
try:
    assert _import_ok
    assert _COST_FREE_LOCAL == "free-local"
    assert _COST_CHEAP_CLOUD == "cheap-cloud"
    assert _COST_PREMIUM_CLOUD == "premium-cloud"
    # providers mapped
    assert _PROVIDER_COST_CLASS["ollama"] == _COST_FREE_LOCAL
    assert _PROVIDER_COST_CLASS["mock"]   == _COST_FREE_LOCAL
    assert _PROVIDER_COST_CLASS["groq"]   == _COST_CHEAP_CLOUD
    assert _PROVIDER_COST_CLASS["openai"] == _COST_PREMIUM_CLOUD
    assert _PROVIDER_COST_CLASS["claude"] == _COST_PREMIUM_CLOUD
    ok("Ch.1/FT-2: cost classes defined (free-local / cheap-cloud / premium-cloud)")
except AssertionError as e:
    fail("Ch.1/FT-2", e)
except Exception as e:
    fail("Ch.1/FT-2", e)


# ── Ch.1/FT-3: priority order — safety never yields, dream yields first ───────
try:
    assert _import_ok
    assert _action_priority("safety") == 0, "safety must be priority 0 (highest)"
    assert _action_priority("dream") == 9, "dream must be priority 9 (yields first)"
    assert _action_priority("optimise") == 9, "optimise must be priority 9"
    # user interaction < 2 → higher than planning (2)
    assert _action_priority("celebrate") < _action_priority("build"), \
        "user interaction celebrates before build (lower value = higher priority)"
    ok("Ch.1/FT-3: priority order — safety never yields, dream yields first")
except AssertionError as e:
    fail("Ch.1/FT-3", e)
except Exception as e:
    fail("Ch.1/FT-3", e)


# ── Ch.1/ST-1: scarcity yields low-priority first ─────────────────────────────
try:
    assert _import_ok
    # priority values: lower = higher priority = never yield under scarcity
    priorities = [_action_priority(a) for a in
                  ("safety", "celebrate", "build", "reflect", "deep", "dream")]
    assert priorities == sorted(priorities), \
        "priority order must be monotone (safety→dream)"
    ok("Ch.1/ST-1: scarcity priority monotone — safety first, dream yields first")
except AssertionError as e:
    fail("Ch.1/ST-1", e)
except Exception as e:
    fail("Ch.1/ST-1", e)


# ── Ch.1/ST-2: Tier 0 (reflex) → 0 budget (never reaches router) ─────────────
try:
    assert _import_ok
    # tier 0 is not in _TIER_BUDGET — budget falls through to action-based
    assert _TIER_REFLEX not in _TIER_BUDGET, "Tier 0 must not have a token budget"
    ok("Ch.1/ST-2: Tier 0 not in _TIER_BUDGET — reflex never reaches router")
except AssertionError as e:
    fail("Ch.1/ST-2", e)
except Exception as e:
    fail("Ch.1/ST-2", e)


# ── Ch.2/FT-4: _token_budget() tier-primary, action-secondary ─────────────────
try:
    assert _import_ok
    # tier-primary: tier=1 → 180, tier=2 → 400, tier=3 → 600
    assert _token_budget("celebrate", tier=1) == 180
    assert _token_budget("celebrate", tier=2) == 400
    assert _token_budget("celebrate", tier=3) == 600
    # action-secondary (no tier): build/challenge → 600, celebrate → 280
    assert _token_budget("build", tier=0) == 600
    assert _token_budget("celebrate", tier=0) == 280
    ok("Ch.2/FT-4: _token_budget() tier-primary (1→180, 2→400, 3→600); action-fallback")
except AssertionError as e:
    fail("Ch.2/FT-4", e)
except Exception as e:
    fail("Ch.2/FT-4", e)


# ── Ch.2/ST-5: live token budgets verbatim (no regression) ────────────────────
try:
    assert _import_ok
    for act in ("build", "challenge", "reflect", "plan", "deep", "diagnose"):
        assert _token_budget(act) == 600, f"{act} must be 600"
    for act in ("celebrate", "connect", "ground", "navigate", "witness", "silence", "answer", ""):
        assert _token_budget(act) == 280, f"{act} must be 280"
    ok("Ch.2/ST-5: live token budgets unchanged (build/deep=600, celebrate/answer=280)")
except AssertionError as e:
    fail("Ch.2/ST-5", e)
except Exception as e:
    fail("Ch.2/ST-5", e)


# ── Ch.2/FT-5: tier→provider ordering — Tier 1 cheapest-first ────────────────
try:
    assert _import_ok
    tier1_order = _TIER_PROVIDER_ORDER[_TIER_CONVERSATIONAL]
    tier3_order = _TIER_PROVIDER_ORDER[_TIER_DEEP]
    # Tier 1: Ollama (free-local) must come before OpenAI (premium-cloud)
    assert tier1_order.index("ollama") < tier1_order.index("openai"), \
        "Tier 1 must route ollama before openai"
    # Tier 3: OpenAI (premium-cloud) must come before Ollama (free-local)
    assert tier3_order.index("openai") < tier3_order.index("ollama"), \
        "Tier 3 must route openai before ollama"
    ok("Ch.2/FT-5: tier provider order — Tier 1 cheapest-first, Tier 3 premium-first")
except AssertionError as e:
    fail("Ch.2/FT-5", e)
except Exception as e:
    fail("Ch.2/FT-5", e)


# ── Ch.2/ST-6: escalation logged when tier > action default ───────────────────
try:
    assert _import_ok
    # action default tier for 'celebrate' is CONVERSATIONAL (1)
    assert _action_default_tier("celebrate") == _TIER_CONVERSATIONAL
    # action default tier for 'build' is REASONING (2)
    assert _action_default_tier("build") == _TIER_REASONING
    # action default tier for 'diagnose' is DEEP (3)
    assert _action_default_tier("diagnose") == _TIER_DEEP

    # Capture the escalation log message
    log_capture = io.StringIO()
    handler = logging.StreamHandler(log_capture)
    handler.setLevel(logging.DEBUG)
    logger = logging.getLogger("runtime.backend_router")
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)

    # Call route() in mock mode with tier escalation to trigger the log
    os.environ["ELO_BACKEND"] = "mock"
    try:
        route("sp", "hello world", mode="mock", action="celebrate", tier=3)
    except Exception:
        pass
    finally:
        os.environ.pop("ELO_BACKEND", None)

    logger.removeHandler(handler)
    logged = log_capture.getvalue()
    assert "escalated=true" in logged, f"Expected 'escalated=true' in log; got: {logged!r}"
    ok("Ch.2/ST-6: escalation logged when Executive tier > action default (escalated=true)")
except AssertionError as e:
    fail("Ch.2/ST-6", e)
except Exception as e:
    fail("Ch.2/ST-6", e)


# ── Ch.2/ST-7: _action_default_tier fallback → CONVERSATIONAL ────────────────
try:
    assert _import_ok
    assert _action_default_tier("unknown_action") == _TIER_CONVERSATIONAL, \
        "Unknown action must default to CONVERSATIONAL"
    assert _action_default_tier("") == _TIER_CONVERSATIONAL, \
        "Empty action must default to CONVERSATIONAL"
    ok("Ch.2/ST-7: unknown/empty action defaults to CONVERSATIONAL tier")
except AssertionError as e:
    fail("Ch.2/ST-7", e)
except Exception as e:
    fail("Ch.2/ST-7", e)


# ── Ch.3/FT-6: mock must not fabricate for factual requests (G-1) ─────────────
try:
    assert _import_ok
    # factual patterns → _is_factual_request = True
    assert _is_factual_request("what time is it?")
    assert _is_factual_request("what is the weather like?")
    assert _is_factual_request("how does memory work?")
    assert _is_factual_request("explain this concept")
    # social/ambient → False
    assert not _is_factual_request("yo")
    assert not _is_factual_request("hey eLo")
    ok("Ch.3/FT-6: _is_factual_request() — factual patterns detected, social cleared")
except AssertionError as e:
    fail("Ch.3/FT-6", e)
except Exception as e:
    fail("Ch.3/FT-6", e)


# ── Ch.3/ST-8: honest limitation message (G-4) ───────────────────────────────
try:
    assert _import_ok
    assert _HONEST_DEGRADATION_MSG, "Honest degradation message must be non-empty"
    assert "offline" in _HONEST_DEGRADATION_MSG.lower() or "can't" in _HONEST_DEGRADATION_MSG.lower(), \
        "Honest degradation must acknowledge inability, not fabricate"
    ok(f"Ch.3/ST-8: honest degradation message non-empty and honest ({_HONEST_DEGRADATION_MSG[:40]!r})")
except AssertionError as e:
    fail("Ch.3/ST-8", e)
except Exception as e:
    fail("Ch.3/ST-8", e)


# ── Ch.3/FT-7: mock returns honest limitation for factual request ─────────────
try:
    assert _import_ok
    # In mock mode, a factual request must return the honest limitation, not a canned presence line
    os.environ["ELO_BACKEND"] = "mock"
    try:
        response, backend = route("sp", "what time is it?", mode="mock", action="answer")
        assert backend == "mock"
        assert response == _HONEST_DEGRADATION_MSG, \
            f"Factual + mock must return honest limitation; got: {response!r}"
        ok("Ch.3/FT-7: mock returns honest limitation for factual request (not fabrication)")
    finally:
        os.environ.pop("ELO_BACKEND", None)
except AssertionError as e:
    fail("Ch.3/FT-7", e)
except Exception as e:
    fail("Ch.3/FT-7", e)


# ── Ch.3/ST-9: mock may use canned presence for social turns ─────────────────
try:
    assert _import_ok
    os.environ["ELO_BACKEND"] = "mock"
    try:
        response, backend = route("sp", "hey", mode="mock", action="celebrate")
        assert backend == "mock"
        # social turns (celebrate) are NOT factual — mock is allowed to use canned presence
        # (response != HONEST_DEGRADATION_MSG is not asserted — it's allowed to vary)
        ok(f"Ch.3/ST-9: social turn (celebrate) — mock allowed canned presence ({response[:40]!r})")
    finally:
        os.environ.pop("ELO_BACKEND", None)
except Exception as e:
    fail("Ch.3/ST-9", e)


# ── Ch.3/ST-10: silence beats fabrication (G-4 — silence is honest too) ────────
try:
    assert _import_ok
    # _HONEST_DEGRADATION_MSG is not a fabricated factual answer
    assert "eLo" not in _HONEST_DEGRADATION_MSG, \
        "Honest degradation must not impersonate eLo's voice (avoid fabrication)"
    ok("Ch.3/ST-10: honest degradation msg does not fabricate an eLo response")
except AssertionError as e:
    fail("Ch.3/ST-10", e)
except Exception as e:
    fail("Ch.3/ST-10", e)


# ── AT-9: py_compile clean on backend_router.py ───────────────────────────────
try:
    _f = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      "runtime", "backend_router.py")
    py_compile.compile(_f, doraise=True)
    ok("AT-9: py_compile clean on runtime/backend_router.py")
except py_compile.PyCompileError as e:
    fail("AT-9", e)
except Exception as e:
    fail("AT-9", e)


# ── Final summary ─────────────────────────────────────────────────────────────
print()
print("=" * 62)
print(f"WO-CANON-XX cognitive economy   {_passed} passed   {_failed} failed")
if _failed:
    sys.exit(1)
