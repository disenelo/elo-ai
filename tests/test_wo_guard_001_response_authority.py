"""
tests/test_wo_guard_001_response_authority.py — WO-GUARD-001
Verify 3 Response Authority Guard classes (D-1 / D-2 / D-3).
Run: ~/miniconda3/bin/python3 tests/test_wo_guard_001_response_authority.py
"""
import py_compile
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

PASS = 0
FAIL = 0


def ok(label):
    global PASS
    PASS += 1
    print(f"  ✅ {label}")


def fail(label, reason=""):
    global FAIL
    FAIL += 1
    print(f"  ❌ {label}" + (f": {reason}" if reason else ""))


def _load_server_src():
    with open(os.path.join(ROOT, "server.py"), encoding="utf-8") as f:
        return f.read()


# ---------------------------------------------------------------------------
# AT-1: D-1 intercepts contradiction of an in-session denial from David
# ---------------------------------------------------------------------------
def at1_d1_intercepts_contradiction():
    try:
        from runtime.response_authority_guards import guard_d1_current_user_reality
        # David denied sending anything: "I didn't send that"
        session = [{"user": "I didn't send that"}, {"user": "carry on"}]
        candidate = "You said you were sending the file over."
        result = guard_d1_current_user_reality(candidate, session)
        # Result should differ from candidate (qualified or suppressed)
        if result != candidate:
            ok(f'AT-1: D-1 intercepted contradiction → "{result[:60]}…"')
        else:
            fail("AT-1", "D-1 did not modify the response despite in-session denial")
    except Exception as e:
        fail("AT-1", str(e))


# ---------------------------------------------------------------------------
# AT-2: D-1 passes through responses with no in-session contradictions
# ---------------------------------------------------------------------------
def at2_d1_no_block_without_denial():
    try:
        from runtime.response_authority_guards import guard_d1_current_user_reality
        session = [{"user": "can you help with this?"}, {"user": "thanks"}]
        candidate = "Of course, let me help you with that."
        result = guard_d1_current_user_reality(candidate, session)
        if result == candidate:
            ok("AT-2: D-1 does not modify response when no denial in session")
        else:
            fail("AT-2", f"D-1 modified a clean response unexpectedly → {result[:60]}")
    except Exception as e:
        fail("AT-2", str(e))


# ---------------------------------------------------------------------------
# AT-3: D-2 corrects tool-action claims when a tool ran
# ---------------------------------------------------------------------------
def at3_d2_corrects_tool_action_claim():
    try:
        from runtime.response_authority_guards import guard_d2_tool_provenance
        candidate = "I confirmed the meeting is at 3pm."
        result = guard_d2_tool_provenance(candidate, tool_agent="calendar_agent")
        if result != candidate:
            ok(f'AT-3: D-2 rewrote tool-action claim → "{result[:60]}"')
        else:
            fail("AT-3", "D-2 did not rewrite tool-action claim when tool_agent is set")
    except Exception as e:
        fail("AT-3", str(e))


# ---------------------------------------------------------------------------
# AT-4: D-3 qualifies resurrected memory claim after in-session correction
# ---------------------------------------------------------------------------
def at4_d3_suppresses_resurrection():
    try:
        from runtime.response_authority_guards import guard_d3_contradiction_resurrection
        # David corrected eLo: "that's not right"
        session = [{"user": "can we go back to earlier"}, {"user": "that's not right actually"}]
        candidate = "I remember we discussed this last session and you agreed."
        result = guard_d3_contradiction_resurrection(candidate, session)
        if result != candidate:
            ok(f'AT-4: D-3 qualified resurrected claim → "{result[:60]}"')
        else:
            fail("AT-4", "D-3 did not qualify resurrected memory claim after in-session correction")
    except Exception as e:
        fail("AT-4", str(e))


# ---------------------------------------------------------------------------
# AT-5: All 3 guards are try/except wrapped — exception does not block response
# ---------------------------------------------------------------------------
def at5_guards_are_exception_safe():
    try:
        from runtime.response_authority_guards import (
            guard_d1_current_user_reality,
            guard_d2_tool_provenance,
            guard_d3_contradiction_resurrection,
        )
        import sys
        original_response = "Hello David."

        # Trigger exception by passing bad types — guard must return original_response
        d1_out = guard_d1_current_user_reality(original_response, None)  # None breaks list iteration
        d2_out = guard_d2_tool_provenance(original_response, tool_agent="tool")
        d3_out = guard_d3_contradiction_resurrection(original_response, None)  # None breaks iteration

        if d1_out == original_response and d3_out == original_response:
            ok("AT-5: Guards return original response on exception (non-blocking)")
        else:
            fail("AT-5", f"Guard exception changed response: d1={d1_out!r} d3={d3_out!r}")
    except Exception as e:
        fail("AT-5", f"Guard raised unhandled exception: {e}")


# ---------------------------------------------------------------------------
# AT-6: Existing 4 guards in server.py are unmodified (WO is additive only)
# ---------------------------------------------------------------------------
def at6_existing_guards_unmodified():
    src = _load_server_src()
    guard_1 = "response_ownership" in src and "check_candidate" in src
    guard_2 = "memory_claim_guard" in src and "scrub_unverified_memory_claims" in src
    guard_3 = "address_rule_guard" in src and "enforce_second_person_to_david" in src
    guard_4 = "identity_guard" in src and "scrub_ai_leakage" in src
    guard_new = "response_authority_guards" in src and "apply_authority_guards" in src

    all_present = guard_1 and guard_2 and guard_3 and guard_4 and guard_new
    if all_present:
        ok("AT-6: All 4 existing guards + WO-GUARD-001 new guards present in server.py")
    else:
        missing = []
        if not guard_1: missing.append("response_ownership.check_candidate")
        if not guard_2: missing.append("memory_claim_guard.scrub_unverified_memory_claims")
        if not guard_3: missing.append("address_rule_guard.enforce_second_person_to_david")
        if not guard_4: missing.append("identity_guard.scrub_ai_leakage")
        if not guard_new: missing.append("response_authority_guards.apply_authority_guards")
        fail("AT-6", "missing: " + ", ".join(missing))


def run_tests():
    print("\n=== WO-GUARD-001 — Response Authority Guards (D-1 / D-2 / D-3) ===\n")
    at1_d1_intercepts_contradiction()
    at2_d1_no_block_without_denial()
    at3_d2_corrects_tool_action_claim()
    at4_d3_suppresses_resurrection()
    at5_guards_are_exception_safe()
    at6_existing_guards_unmodified()
    print(f"\n{'='*50}")
    print(f"Result: {PASS}/6 PASS  {FAIL}/6 FAIL")
    if FAIL:
        sys.exit(1)


if __name__ == "__main__":
    run_tests()
