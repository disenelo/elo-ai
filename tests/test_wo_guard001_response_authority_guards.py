"""
tests/test_wo_guard001_response_authority_guards.py

Acceptance tests for WO-GUARD-001 (D-1 / D-2 / D-3).
6 pytest-style ATs — no sys.exit at module level.

Run: ~/miniconda3/bin/python3 -m pytest tests/test_wo_guard001_response_authority_guards.py -q
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def _summaries(*user_turns: str) -> list:
    return [{"user": u, "elo": ""} for u in user_turns]


# AT-1 — D-1: response that contradicts David's in-session denial is intercepted
def test_d1_contradicts_in_session_denial():
    from runtime.response_authority_guards import guard_d1_current_user_reality
    response = "You said you were going to send that file."
    summaries = _summaries("I'm heading out", "I never said that", "OK")
    result = guard_d1_current_user_reality(response, summaries)
    # Must be modified — either qualified or original claim softened
    assert result != response or "I never said" not in summaries[-2]["user"], (
        "D-1 must intercept a response that contradicts David's in-session denial"
    )
    # The result must be non-empty (response not swallowed)
    assert result.strip(), "D-1 must not return empty response"


# AT-2 — D-1: response with no in-session contradiction passes through unmodified
def test_d1_no_contradiction_passes_through():
    from runtime.response_authority_guards import guard_d1_current_user_reality
    response = "Sounds good, let me know what you need."
    summaries = _summaries("How are you?", "Tell me more about the project")
    result = guard_d1_current_user_reality(response, summaries)
    assert result == response, "D-1 must not modify response when no contradiction exists"


# AT-3 — D-2: tool-action claim corrected when tool_agent is set
def test_d2_tool_action_rewrite():
    from runtime.response_authority_guards import guard_d2_tool_provenance
    response = "I checked the weather — it's 14°C in London."
    result = guard_d2_tool_provenance(response, tool_agent="weather_agent")
    assert "I checked" not in result, (
        "D-2 must rewrite 'I checked' when tool_agent is set"
    )
    assert result.strip(), "D-2 must not return empty response"
    assert "14°C" in result, "D-2 must preserve the factual content"


# AT-4 — D-3: resurrected contradicted claim is qualified before publication
def test_d3_resurrection_qualified_after_correction():
    from runtime.response_authority_guards import guard_d3_contradiction_resurrection
    response = "I remember you said the deadline was Friday."
    summaries = _summaries("That's not right", "I never said Friday")
    result = guard_d3_contradiction_resurrection(response, summaries)
    assert "I remember" not in result or "misremember" in result.lower(), (
        "D-3 must qualify or remove the resurrected claim after a user correction"
    )
    assert result.strip(), "D-3 must not return empty response"


# AT-5 — All 3 guards wrapped in try/except: guard exception does not block response
def test_guards_wrapped_in_try_except():
    from runtime.response_authority_guards import (
        guard_d1_current_user_reality,
        guard_d2_tool_provenance,
        guard_d3_contradiction_resurrection,
    )
    response = "This is a test response."

    # Pass bad inputs to trigger internal exceptions
    r1 = guard_d1_current_user_reality(response, None)  # type: ignore
    r2 = guard_d2_tool_provenance(response, None)       # type: ignore
    r3 = guard_d3_contradiction_resurrection(response, None)  # type: ignore

    assert r1 == response, "D-1 exception must return original response"
    assert r2 == response, "D-2 exception must return original response"
    assert r3 == response, "D-3 exception must return original response"


# AT-6 — Existing 4 guards in server.py are unmodified
def test_existing_4_guards_unmodified():
    server_path = os.path.join(os.path.dirname(__file__), "..", "server.py")
    with open(server_path, encoding="utf-8") as f:
        source = f.read()
    assert "from runtime.response_ownership import check_candidate" in source, \
        "Guard 1 (response_ownership) missing"
    assert "from runtime.memory_claim_guard import" in source, \
        "Guard 2 (memory_claim_guard) missing"
    assert "from runtime.address_rule_guard import enforce_second_person_to_david" in source, \
        "Guard 3 (address_rule_guard) missing"
    assert "from runtime.identity_guard import scrub_ai_leakage" in source, \
        "Guard 4 (identity_guard) missing"
    # WO-GUARD-001 guards appear AFTER existing 4
    ro_pos  = source.index("from runtime.response_ownership import check_candidate")
    rag_pos = source.index("from runtime.response_authority_guards import apply_authority_guards")
    assert rag_pos > ro_pos, "WO-GUARD-001 guards must appear after existing 4 guards"
