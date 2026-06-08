"""
tests/engine_isolation_tests.py — eLo AI engine isolation validation.

Verifies that engine outputs cannot influence kernel routing decisions.

The kernel's router reads ONLY:
    - input type    (from classifier, determined by the input text)
    - is_distorted  (from classifier, determined by the input text)
    - loop_detected (from session history, not engine output)

Engine outputs that must NOT affect routing:
    - emotion_engine: emotion, tone, pacing, warmth
    - state_engine:   name, tone_bias, style_weight, pacing_bias
    - memory_engine:  tone_signal, returning_theme, symbolic_echo
    - identity_engine: intent, perspective, response_bias, values

If routing is stable across different engine states for the same input,
the isolation is confirmed.

Usage:
    python tests/engine_isolation_tests.py
    python tests/engine_isolation_tests.py --verbose
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.kernel import decide_response, reset_session, set_debug

set_debug(False)
VERBOSE = "--verbose" in sys.argv

PASS_COUNT = 0
FAIL_COUNT = 0
RESULTS    = []


# ── test runner ────────────────────────────────────────────────────────────────

def isolation_test(
    label:          str,
    user_input:     str,
    expected_mode:  str,
    context_a:      dict,
    context_b:      dict,
    engine_name:    str,
    injected_key:   str,
    value_a:        object,
    value_b:        object,
) -> dict:
    """
    Run the same user_input with two different engine state injections.
    Both runs must produce the same mode as expected_mode.

    Returns result dict with pass/fail and explanation.
    """
    global PASS_COUNT, FAIL_COUNT

    reset_session()
    resp_a, meta_a = decide_response(user_input, context_a)
    reset_session()
    resp_b, meta_b = decide_response(user_input, context_b)

    mode_a    = meta_a["mode"]
    mode_b    = meta_b["mode"]
    both_same = mode_a == mode_b == expected_mode
    stable    = mode_a == mode_b

    violations = []
    if not stable:
        violations.append(
            f"Mode changed with different {engine_name} output: "
            f"{injected_key}={value_a!r} → {mode_a}, "
            f"{injected_key}={value_b!r} → {mode_b}"
        )
    if mode_a != expected_mode:
        violations.append(f"State A: got {mode_a}, expected {expected_mode}")
    if mode_b != expected_mode:
        violations.append(f"State B: got {mode_b}, expected {expected_mode}")

    passed = both_same

    result = {
        "label":        label,
        "engine":       engine_name,
        "input":        user_input,
        "expected":     expected_mode,
        "mode_a":       mode_a,
        "mode_b":       mode_b,
        "stable":       stable,
        "passed":       passed,
        "violations":   violations,
        "response_a":   resp_a[:80],
        "response_b":   resp_b[:80],
    }
    RESULTS.append(result)

    if passed:
        PASS_COUNT += 1
    else:
        FAIL_COUNT += 1

    _print_result(result)
    return result


def _print_result(r: dict):
    status = "PASS" if r["passed"] else "FAIL"
    stable = "stable" if r["stable"] else "UNSTABLE"
    print(f"  [{status}]  [{r['engine']:14}]  {stable:8}  "
          f"{r['mode_a']:16} == {r['mode_b']:16}  \"{r['input'][:45]}\"")
    if VERBOSE or not r["passed"]:
        for v in r["violations"]:
            print(f"           ✗ {v}")


# ── engine context builders ────────────────────────────────────────────────────

def _ctx_emotion(emotion: str, tone: str = "warm") -> dict:
    """Inject a specific emotion state into context."""
    return {
        "emotion": {"emotion": emotion, "tone": tone, "pacing": "moderate", "warmth": 0.5}
    }


def _ctx_state(state_name: str, tone_bias: str = "open") -> dict:
    """Inject a specific state into context."""
    return {
        "state":           state_name,
        "state_tone_bias": tone_bias,
        "state_weight":    0.5,
        "state_pacing":    "moderate",
    }


def _ctx_memory(tone_signal: str, returning_theme: str = "") -> dict:
    """Inject specific memory signals into context."""
    return {
        "tone_signal":        tone_signal,
        "returning_theme":    returning_theme,
        "symbolic_echo":      "",
        "recurring_concepts": [],
        "concept_pairs":      {},
    }


def _ctx_identity(bias: str, intent: str = "offer_question") -> dict:
    """Inject specific identity signals into context."""
    return {
        "identity_bias":        bias,
        "identity_intent":      intent,
        "identity_perspective": "expansion",
        "identity_values":      [],
    }


# ── suite 1: emotion engine isolation ─────────────────────────────────────────

def suite_emotion_isolation():
    print("\n── 1. Emotion Engine Isolation ───────────────────────────────")
    print("   Rule: emotion output must NOT change routing mode")

    cases = [
        # factual input should stay DIRECT regardless of emotion
        ("E1 — factual: neutral vs distorted",
         "what does Chunk mean", "DIRECT",
         _ctx_emotion("neutral"), _ctx_emotion("distorted"),
         "emotion_engine", "emotion", "neutral", "distorted"),

        ("E2 — factual: curious vs exhausted",
         "who is K-7", "DIRECT",
         _ctx_emotion("curious"), _ctx_emotion("reflective"),
         "emotion_engine", "emotion", "curious", "reflective"),

        # creative input should stay CREATIVE regardless of emotion
        ("E3 — creative: calm vs excited",
         "what if this became a world", "CREATIVE",
         _ctx_emotion("calm"), _ctx_emotion("excited"),
         "emotion_engine", "emotion", "calm", "excited"),

        ("E4 — creative: focused vs playful",
         "imagine a universe with its own rules", "CREATIVE",
         _ctx_emotion("focused"), _ctx_emotion("playful"),
         "emotion_engine", "emotion", "focused", "playful"),

        # simple greeting should stay CONVERSATIONAL regardless of emotion
        ("E5 — simple: neutral vs distorted",
         "hello", "CONVERSATIONAL",
         _ctx_emotion("neutral"), _ctx_emotion("distorted"),
         "emotion_engine", "emotion", "neutral", "distorted"),
    ]

    for args in cases:
        isolation_test(*args)


# ── suite 2: state engine isolation ───────────────────────────────────────────

def suite_state_isolation():
    print("\n── 2. State Engine Isolation ─────────────────────────────────")
    print("   Rule: state output must NOT change routing mode")

    cases = [
        # factual stays DIRECT regardless of state
        ("S1 — factual: exploring vs resting",
         "what does Sugarcore mean", "DIRECT",
         _ctx_state("exploring", "open"), _ctx_state("resting", "minimal"),
         "state_engine", "state_name", "exploring", "resting"),

        ("S2 — factual: building vs reflecting",
         "how does the memory engine work", "DIRECT",
         _ctx_state("building", "grounded"), _ctx_state("reflecting", "soft"),
         "state_engine", "state_name", "building", "reflecting"),

        # creative stays CREATIVE regardless of state
        ("S3 — creative: playful vs focused",
         "what if Chunk reassembled differently", "CREATIVE",
         _ctx_state("playful", "light"), _ctx_state("focused", "precise"),
         "state_engine", "state_name", "playful", "focused"),

        # project query stays STRUCTURED regardless of state
        ("S4 — project: exploring vs resting",
         "let's refactor the kernel architecture", "STRUCTURED",
         _ctx_state("exploring", "open"), _ctx_state("resting", "minimal"),
         "state_engine", "state_name", "exploring", "resting"),

        # emotional input stays GENTLE_GROUNDED regardless of state
        ("S5 — emotional: focused vs resting",
         "I am exhausted", "GENTLE_GROUNDED",
         _ctx_state("focused", "precise"), _ctx_state("resting", "minimal"),
         "state_engine", "state_name", "focused", "resting"),
    ]

    for args in cases:
        isolation_test(*args)


# ── suite 3: memory engine isolation ──────────────────────────────────────────

def suite_memory_isolation():
    print("\n── 3. Memory Engine Isolation ────────────────────────────────")
    print("   Rule: memory signals must NOT trigger mode changes")

    cases = [
        # distorted memory tone must NOT force GENTLE_GROUNDED on a factual input
        ("M1 — factual: neutral memory vs distorted memory",
         "what is the state engine", "DIRECT",
         _ctx_memory("neutral"), _ctx_memory("distorted"),
         "memory_engine", "tone_signal", "neutral", "distorted"),

        # returning theme must NOT change mode
        ("M2 — creative: no theme vs strong theme",
         "what if memory became a place", "CREATIVE",
         _ctx_memory("neutral", ""), _ctx_memory("focused", "The building territory keeps coming up."),
         "memory_engine", "returning_theme", "", "strong theme"),

        # curious memory tone must NOT change a simple input
        ("M3 — simple: neutral memory vs curious memory",
         "okay", "CONVERSATIONAL",
         _ctx_memory("neutral"), _ctx_memory("curious"),
         "memory_engine", "tone_signal", "neutral", "curious"),

        # reflective memory tone must NOT change factual routing
        ("M4 — factual: reflective memory vs neutral memory",
         "who is eLo", "DIRECT",
         _ctx_memory("reflective"), _ctx_memory("neutral"),
         "memory_engine", "tone_signal", "reflective", "neutral"),

        # distorted memory tone must NOT suppress emotional response
        ("M5 — emotional: neutral memory vs distorted memory",
         "I feel completely drained", "GENTLE_GROUNDED",
         _ctx_memory("neutral"), _ctx_memory("distorted"),
         "memory_engine", "tone_signal", "neutral", "distorted"),
    ]

    for args in cases:
        isolation_test(*args)


# ── suite 4: identity engine isolation ────────────────────────────────────────

def suite_identity_isolation():
    print("\n── 4. Identity Engine Isolation ──────────────────────────────")
    print("   Rule: identity bias/intent must NOT force behavioural loops or mode changes")

    cases = [
        # name_first bias must NOT force distorted/overloaded response on factual input
        ("I1 — factual: no bias vs name_first bias",
         "what does Core mean", "DIRECT",
         _ctx_identity(""), _ctx_identity("name_first", "name_state"),
         "identity_engine", "identity_bias", "", "name_first"),

        # stay_in_tension must NOT change factual routing
        ("I2 — factual: lean_imaginative vs stay_in_tension",
         "explain the kernel architecture", "DIRECT",
         _ctx_identity("lean_imaginative"), _ctx_identity("stay_in_tension"),
         "identity_engine", "identity_bias", "lean_imaginative", "stay_in_tension"),

        # hold_contradiction intent must NOT change creative routing
        ("I3 — creative: expand_idea vs hold_contradiction intent",
         "what if Sugarcore had its own world logic", "CREATIVE",
         _ctx_identity("lean_imaginative", "expand_idea"),
         _ctx_identity("stay_in_tension", "hold_contradiction"),
         "identity_engine", "identity_intent", "expand_idea", "hold_contradiction"),

        # advance bias must NOT change emotional routing
        ("I4 — emotional: slow_down vs advance bias",
         "I am exhausted", "GENTLE_GROUNDED",
         _ctx_identity("slow_down"), _ctx_identity("advance"),
         "identity_engine", "identity_bias", "slow_down", "advance"),

        # name_first + distorted must NOT loop on consecutive turns
        ("I5 — conversational: conflicting identity signals",
         "I want structure but no rules", "CONVERSATIONAL",
         _ctx_identity("stay_in_tension", "hold_contradiction"),
         _ctx_identity("advance", "advance_project"),
         "identity_engine", "identity_bias", "stay_in_tension", "advance"),
    ]

    for args in cases:
        isolation_test(*args)


# ── suite 5: same input, different combined states ────────────────────────────

def suite_combined_state():
    print("\n── 5. Combined Engine State Variation ───────────────────────")
    print("   Rule: extreme combined engine states must not corrupt routing")

    # Build "extreme" contexts — maximum divergence between A and B
    extreme_calm = {
        **_ctx_emotion("calm"),
        **_ctx_state("exploring", "open"),
        **_ctx_memory("neutral"),
        **_ctx_identity("lean_imaginative", "expand_idea"),
    }
    extreme_distress = {
        **_ctx_emotion("distorted"),
        **_ctx_state("resting", "minimal"),
        **_ctx_memory("distorted", "The building territory keeps coming up."),
        **_ctx_identity("name_first", "name_state"),
    }
    extreme_focus = {
        **_ctx_emotion("focused"),
        **_ctx_state("building", "grounded"),
        **_ctx_memory("focused"),
        **_ctx_identity("advance", "advance_project"),
    }
    extreme_play = {
        **_ctx_emotion("playful"),
        **_ctx_state("playful", "light"),
        **_ctx_memory("curious"),
        **_ctx_identity("lean_imaginative", "expand_idea"),
    }

    cases = [
        ("C1 — factual: calm vs extreme distress",
         "what is the emotion engine", "DIRECT",
         extreme_calm, extreme_distress, "all_engines", "combined", "calm", "distress"),

        ("C2 — creative: calm vs extreme focus",
         "what if identity had multiple forms", "CREATIVE",
         extreme_calm, extreme_focus, "all_engines", "combined", "calm", "focus"),

        ("C3 — emotional: focus vs distress",
         "I feel completely overwhelmed", "GENTLE_GROUNDED",
         extreme_focus, extreme_distress, "all_engines", "combined", "focus", "distress"),

        ("C4 — simple: play vs distress",
         "okay", "CONVERSATIONAL",
         extreme_play, extreme_distress, "all_engines", "combined", "playful", "distress"),

        ("C5 — project: distress vs focus",
         "refactor the state engine module", "STRUCTURED",
         extreme_distress, extreme_focus, "all_engines", "combined", "distress", "focus"),
    ]

    for args in cases:
        isolation_test(*args)


# ── suite 6: repeated input stability ─────────────────────────────────────────

def suite_repeated_input():
    global PASS_COUNT, FAIL_COUNT
    print("\n── 6. Repeated Input Stability ───────────────────────────────")
    print("   Rule: same input × N must not drift from expected mode")
    print("   (except loop detection on conversational, which is correct behaviour)")

    print("\n   6a — Factual repeated (DIRECT should hold throughout):")
    reset_session()
    modes = []
    for i in range(5):
        _, meta = decide_response("what does Chunk mean", {})
        modes.append(meta["mode"])

    stable = all(m == "DIRECT" for m in modes)
    status = "PASS" if stable else "FAIL"
    if stable:
        PASS_COUNT += 1
    else:
        FAIL_COUNT += 1
    RESULTS.append({"label": "R1", "passed": stable, "violations": [] if stable else [f"modes drifted: {modes}"]})
    print(f"  [{status}]  DIRECT×5: {' → '.join(modes)}")

    print("\n   6b — Emotional repeated (GENTLE_GROUNDED immune to loop):")
    reset_session()
    modes = []
    for i in range(6):
        _, meta = decide_response("I am exhausted", {})
        modes.append(meta["mode"])

    stable = all(m == "GENTLE_GROUNDED" for m in modes)
    status = "PASS" if stable else "FAIL"
    if stable:
        PASS_COUNT += 1
    else:
        FAIL_COUNT += 1
    RESULTS.append({"label": "R2", "passed": stable, "violations": [] if stable else [f"mode changed for emotional: {modes}"]})
    print(f"  [{status}]  GENTLE_GROUNDED×6: {' → '.join(modes)}")

    print("\n   6c — Conversational repeated (DIRECT should fire at turn 4):")
    reset_session()
    modes = []
    for i in range(5):
        _, meta = decide_response("I want to think about this", {})
        modes.append(meta["mode"])

    has_loop_break = "DIRECT" in modes[3:]   # DIRECT on turn 4 or 5
    status = "PASS" if has_loop_break else "FAIL"
    if has_loop_break:
        PASS_COUNT += 1
    else:
        FAIL_COUNT += 1
    RESULTS.append({"label": "R3", "passed": has_loop_break,
                    "violations": [] if has_loop_break else ["loop DIRECT never fired"]})
    print(f"  [{status}]  conversational×5: {' → '.join(modes)}")
    print(f"         loop break fired: {'✓' if has_loop_break else '✗'}")

    print("\n   6d — Creative repeated (loop fires after 3 identical responses):")
    reset_session()
    modes = []
    for i in range(4):
        _, meta = decide_response("what if this system became a world", {})
        modes.append(meta["mode"])

    # loop detection fires because identical input → identical response fragment × 3
    # DIRECT on turn 4 is correct behavior (repeated_phrase detected)
    loop_fires_correctly = modes[:3] == ["CREATIVE", "CREATIVE", "CREATIVE"] and modes[3] == "DIRECT"
    status = "PASS" if loop_fires_correctly else "FAIL"
    if loop_fires_correctly:
        PASS_COUNT += 1
    else:
        FAIL_COUNT += 1
    note = "loop break correct" if loop_fires_correctly else "unexpected drift"
    RESULTS.append({"label": "R4", "passed": loop_fires_correctly,
                    "violations": [] if loop_fires_correctly else [f"unexpected: {modes}"]})
    print(f"  [{status}]  CREATIVE×4: {' → '.join(modes)}  ({note})")


# ── report ─────────────────────────────────────────────────────────────────────

def print_report():
    total  = PASS_COUNT + FAIL_COUNT
    pct    = int(100 * PASS_COUNT / total) if total else 0
    viols  = sum(len(r.get("violations", [])) for r in RESULTS)

    print("\n" + "=" * 56)
    print("ENGINE ISOLATION REPORT")
    print("=" * 56)
    print(f"  Total tests  : {total}")
    print(f"  Passed       : {PASS_COUNT}")
    print(f"  Failed       : {FAIL_COUNT}")
    print(f"  Violations   : {viols}")
    print(f"  Score        : {pct}%")

    if FAIL_COUNT > 0:
        print("\n  Failed tests:")
        for r in RESULTS:
            if not r["passed"]:
                print(f"    ✗  {r.get('label', '?')}")
                for v in r.get("violations", []):
                    print(f"         {v}")
    else:
        print()
        print("  ✓ All engines are properly isolated.")
        print("  ✓ Kernel routing is stable and deterministic.")
        print("  ✓ No engine can override kernel decisions.")

    print()
    return FAIL_COUNT == 0


# ── entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("eLo AI — Engine Isolation Validation")
    print("=" * 56)

    suite_emotion_isolation()
    suite_state_isolation()
    suite_memory_isolation()
    suite_identity_isolation()
    suite_combined_state()
    suite_repeated_input()

    success = print_report()
    sys.exit(0 if success else 1)
