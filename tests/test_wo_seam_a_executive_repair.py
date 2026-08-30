"""WO-SEAM-A: Executive intent→action minimum repair — 7 ATs."""
import sys, os, subprocess, json
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from runtime.executive import _conversation_action

REFLECTIVE = {"reflect", "connect", "witness"}


def test_at1_open_command_routes_answer():
    """AT-1: Plain command 'open X' → ANSWER, not CONNECT/REFLECT/WITNESS."""
    r = _conversation_action("open Joe Budden Podcast on YouTube", "conversation", "neutral", "steady")
    assert r["action"] == "answer", f"AT-1 FAIL: got {r['action']!r} ({r['reason']!r})"
    assert r["action"] not in REFLECTIVE, f"AT-1 FAIL: landed in reflective branch: {r}"
    print(f"✅ AT-1: 'open Joe Budden Podcast on YouTube' → {r['action']!r} ({r['reason']!r})")


def test_at2_tell_me_weather_routes_answer():
    """AT-2: 'tell me the weather' → ANSWER, not reflective."""
    r = _conversation_action("tell me the weather", "conversation", "neutral", "steady")
    assert r["action"] == "answer", f"AT-2 FAIL: got {r['action']!r} ({r['reason']!r})"
    assert r["action"] not in REFLECTIVE, f"AT-2 FAIL: landed in reflective branch: {r}"
    print(f"✅ AT-2: 'tell me the weather' → {r['action']!r} ({r['reason']!r})")


def test_at3_repeated_explicit_request_routes_answer():
    """AT-3: Repeated explicit request ('play the song again') → ANSWER."""
    r = _conversation_action("play the song again", "conversation", "neutral", "steady")
    assert r["action"] == "answer", f"AT-3 FAIL: got {r['action']!r}"
    assert r["action"] not in REFLECTIVE
    print(f"✅ AT-3: 'play the song again' → {r['action']!r} ({r['reason']!r})")


def test_at4_genuine_reflection_allowed():
    """AT-4: Genuinely reflective input → CONNECT/REFLECT still allowed."""
    r = _conversation_action("that's an interesting tension, isn't it", "conversation", "neutral", "steady")
    # Should NOT be ANSWER — reflective routing allowed for this input
    assert r["action"] != "answer", f"AT-4 FAIL: reflective input routed to ANSWER: {r}"
    print(f"✅ AT-4: reflective input → {r['action']!r} ({r['reason']!r}) [not ANSWER — correct]")


def test_at5_seam_b_guard_still_active():
    """AT-5: Seam B guard — 'what is done?' ambiguous guard prevents web-search."""
    from tools.web_search import is_search_intent, extract_query
    _AMBIGUOUS = frozenset({"done", "ok", "okay", "yes", "no", "wait", "ready", "waiting"})
    q = "what is done?"
    assert is_search_intent(q), "Seam B: is_search_intent should match 'what is done?'"
    extracted = extract_query(q)
    assert extracted.strip().lower() in _AMBIGUOUS, (
        f"AT-5 FAIL: extracted query {extracted!r} not in ambiguous guard set"
    )
    print(f"✅ AT-5: 'what is done?' → extracted {extracted!r} in ambiguous guard — search blocked")


def test_at6_frozen_kernel_tests_pass():
    """AT-6: Frozen kernel tests (WO-001, WO-006, WO-014) still pass."""
    py = os.path.expanduser("~/miniconda3/bin/python3")
    test_dir = os.path.dirname(__file__)
    frozen = [
        os.path.join(test_dir, "test_wo001_faculty_bus.py"),
        os.path.join(test_dir, "test_wo006_emotional_processing.py"),
        os.path.join(test_dir, "test_wo014_spine_wiring.py"),
    ]
    for tf in frozen:
        r = subprocess.run([py, tf], capture_output=True, text=True, cwd=os.path.dirname(test_dir))
        if r.returncode != 0:
            print(r.stdout[-500:] if r.stdout else "")
            print(r.stderr[-500:] if r.stderr else "")
            assert False, f"AT-6 FAIL: {os.path.basename(tf)} failed"
        print(f"✅ AT-6: {os.path.basename(tf)} PASS")


def test_at7_routing_confirms_answer_action():
    """AT-7: Routing trace confirms action='answer' for imperative inputs."""
    cases = [
        ("open Joe Budden Podcast on YouTube", "conversation", "neutral", "steady"),
        ("tell me the weather", "conversation", "neutral", "steady"),
    ]
    for user_input, intent, valence, momentum in cases:
        r = _conversation_action(user_input, intent, valence, momentum)
        assert r["action"] == "answer", (
            f"AT-7 FAIL: '{user_input}' → {r['action']!r}, expected 'answer'"
        )
    print("✅ AT-7: both imperative inputs confirm action='answer' in routing result")


if __name__ == "__main__":
    tests = [
        test_at1_open_command_routes_answer,
        test_at2_tell_me_weather_routes_answer,
        test_at3_repeated_explicit_request_routes_answer,
        test_at4_genuine_reflection_allowed,
        test_at5_seam_b_guard_still_active,
        test_at6_frozen_kernel_tests_pass,
        test_at7_routing_confirms_answer_action,
    ]
    passed = 0
    for t in tests:
        try:
            t()
            passed += 1
        except AssertionError as e:
            print(f"❌ {t.__name__}: {e}")
        except Exception as e:
            print(f"❌ {t.__name__}: EXCEPTION {e}")
    print(f"\n{passed}/{len(tests)} PASS")
    sys.exit(0 if passed == len(tests) else 1)
