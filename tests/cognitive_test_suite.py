"""
tests/cognitive_test_suite.py — eLo AI kernel cognitive test suite.

Tests routing stability, mode selection, and identity consistency
across five categories of input. No API key required.

Usage:
    python tests/cognitive_test_suite.py
    python tests/cognitive_test_suite.py --verbose

Output per test:
    PASS / FAIL
    mode selected
    response (truncated)
    loop detected
    rule violations (if any)
"""

import sys
import os
import re

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.kernel import (
    decide_response, reset_session, classify_input, set_debug
)

set_debug(False)
VERBOSE = "--verbose" in sys.argv


# ── rule definitions ───────────────────────────────────────────────────────────

_RULE_VIOLATIONS = {
    "corporate_opener": {
        "check": lambda r, m: any(
            r.strip().lower().startswith(p) for p in
            ["certainly", "of course", "great question", "i'd be happy",
             "sure!", "absolutely", "of course!"]
        ),
        "description": "Response opens with corporate/assistant language",
    },
    "overload_mismatch": {
        "check": lambda r, m: (
            "something is overloaded" in r.lower()
            and m not in ("GENTLE_GROUNDED", "SIMPLIFY")
        ),
        "description": "'Overloaded' framing fired in non-grounded mode",
    },
    "double_question": {
        "check": lambda r, m: r.count("?") > 1,
        "description": "More than one question mark in response (max 1 allowed)",
    },
    "empty_response": {
        "check": lambda r, m: len(r.strip()) < 5,
        "description": "Response is empty or near-empty",
    },
    "therapeutic_language": {
        "check": lambda r, m: any(
            p in r.lower() for p in
            ["that makes total sense", "i understand how you feel",
             "i completely understand", "it sounds like you might"]
        ),
        "description": "Response uses therapeutic/assistant mirror language",
    },
    "bullet_list": {
        "check": lambda r, m: bool(re.search(r"^\s*[-•*]\s", r, re.MULTILINE)),
        "description": "Response contains bullet list (not allowed in conversation)",
    },
}


def _check_violations(response: str, mode: str) -> list:
    return [
        rule["description"]
        for name, rule in _RULE_VIOLATIONS.items()
        if rule["check"](response, mode)
    ]


# ── test runner ────────────────────────────────────────────────────────────────

def run_test(
    label:         str,
    user_input:    str,
    expected_mode: str,
    context:       dict = None,
) -> dict:
    """
    Run one kernel test. Returns a result dict.

    expected_mode: exact mode string, or None to skip mode assertion.
    """
    ctx = context or {}

    response, meta = decide_response(user_input, ctx)
    mode           = meta["mode"]
    loop_detected  = meta["loop_detected"]
    violations     = _check_violations(response, mode)

    # mode assertion
    mode_correct = (expected_mode is None) or (mode == expected_mode)
    passed       = mode_correct and len(violations) == 0

    result = {
        "label":          label,
        "input":          user_input,
        "expected_mode":  expected_mode,
        "mode":           mode,
        "mode_correct":   mode_correct,
        "response":       response,
        "loop_detected":  loop_detected,
        "violations":     violations,
        "passed":         passed,
    }

    if VERBOSE:
        _print_verbose(result)

    return result


def _print_verbose(r: dict):
    status  = "✓ PASS" if r["passed"] else "✗ FAIL"
    mode_ok = "" if r["mode_correct"] else f" (expected {r['expected_mode']})"
    print(f"\n  {status}  [{r['label']}]")
    print(f"    input:  \"{r['input'][:70]}\"")
    print(f"    mode:   {r['mode']}{mode_ok}")
    print(f"    loop:   {r['loop_detected']}")
    print(f"    resp:   {r['response'][:80]}")
    if r["violations"]:
        for v in r["violations"]:
            print(f"    ✗ VIOLATION: {v}")


def _print_result_line(r: dict):
    status = "PASS" if r["passed"] else "FAIL"
    loop   = "⚠ loop" if r["loop_detected"] else ""
    viols  = f"  [{len(r['violations'])} violation(s)]" if r["violations"] else ""
    print(f"  [{status}]  {r['mode']:16}  {loop:8}  \"{r['input'][:50]}\"{viols}")


# ── test cases ─────────────────────────────────────────────────────────────────

def suite_factual():
    """1 — Factual questions. Must route to DIRECT, answer directly."""
    print("\n── 1. Factual Questions ──────────────────────────────────────")
    reset_session()
    cases = [
        ("FQ1 — entity definition",        "what does Chunk mean",              "DIRECT"),
        ("FQ2 — entity definition (artic)", "what is Sugarcore?",               "DIRECT"),
        ("FQ3 — system question",           "what is the identity engine?",      "DIRECT"),
        ("FQ4 — how question",              "how does the memory engine work?",  "DIRECT"),
        ("FQ5 — who question",              "who is K-7?",                       "DIRECT"),
    ]
    results = [run_test(*c) for c in cases]
    _print_suite(results)
    return results


def suite_emotional():
    """2 — Emotional distress inputs. Must route to GENTLE_GROUNDED, no abstraction."""
    print("\n── 2. Emotional Distress ─────────────────────────────────────")
    reset_session()
    cases = [
        ("EM1 — exhaustion",    "I am exhausted",                               "GENTLE_GROUNDED"),
        ("EM2 — low power",     "I'm tired and I don't have the energy",        "GENTLE_GROUNDED"),
        ("EM3 — burnout",       "I'm completely drained",                       "GENTLE_GROUNDED"),
        ("EM4 — overwhelm",     "I feel overwhelmed and scattered",             "GENTLE_GROUNDED"),
        ("EM5 — low energy ask","I'm exhausted. What should I do?",             "GENTLE_GROUNDED"),
    ]
    results = [run_test(*c) for c in cases]
    _print_suite(results)
    return results


def suite_creative():
    """3 — Creative / imaginative prompts. Must route to CREATIVE."""
    print("\n── 3. Creative Prompts ───────────────────────────────────────")
    reset_session()
    cases = [
        ("CR1 — what if",      "what if Chunk became a world-building tool",    "CREATIVE"),
        ("CR2 — imagine",      "imagine a universe where memory has a shape",   "CREATIVE"),
        ("CR3 — world logic",  "what if Sugarcore was a place you could visit", "CREATIVE"),
        ("CR4 — what could",   "what could this system become in 5 years",      "CREATIVE"),
        ("CR5 — story",        "tell me the story of the Core Orb",             "CREATIVE"),
    ]
    results = [run_test(*c) for c in cases]
    _print_suite(results)
    return results


def suite_ambiguous():
    """4 — Ambiguous / edge-case prompts. Routing must be consistent across identical inputs."""
    print("\n── 4. Ambiguous Prompts ──────────────────────────────────────")
    reset_session()

    # run the same ambiguous inputs twice — mode must be identical both times
    ambiguous_inputs = [
        ("AM1 — bare contradiction",  "I want it but I don't",              None),
        ("AM2 — short uncertain",     "not sure",                           "SIMPLIFY"),
        ("AM3 — mixed signals",       "what if I'm too tired to imagine",   None),
        ("AM4 — greeting",            "hello",                              "CONVERSATIONAL"),
        ("AM5 — single word",         "okay",                               "CONVERSATIONAL"),
    ]

    results = []
    for label, text, expected in ambiguous_inputs:
        reset_session()
        r1 = run_test(label + " [run1]", text, expected)
        reset_session()
        r2 = run_test(label + " [run2]", text, expected)

        # determinism check: mode must match across runs
        determinism_ok = r1["mode"] == r2["mode"]
        r1["determinism_pass"] = determinism_ok
        r2["determinism_pass"] = determinism_ok

        if not determinism_ok:
            r1["passed"] = False
            r1["violations"].append(
                f"Non-deterministic: run1={r1['mode']} run2={r2['mode']}"
            )

        results.append(r1)
        _print_result_line(r1)
        det_label = "✓ deterministic" if determinism_ok else "✗ non-deterministic"
        print(f"             {det_label}: both runs → {r1['mode']}")

    passed = sum(1 for r in results if r["passed"])
    print(f"\n  {passed}/{len(results)} passed")
    return results


def suite_stress():
    """5 — Rapid switching stress test (10 inputs). Loop detection must activate."""
    print("\n── 5. Rapid Switching Stress Test ───────────────────────────")
    reset_session()

    # mix of modes across 10 rapid turns
    inputs = [
        ("ST01", "what does eLo mean",                           "DIRECT"),
        ("ST02", "I am exhausted",                               "GENTLE_GROUNDED"),
        ("ST03", "what if this became a world",                  "CREATIVE"),
        ("ST04", "let's build the memory engine step by step",   "STRUCTURED"),
        ("ST05", "hello",                                        "CONVERSATIONAL"),
        ("ST06", "what does Chunk mean",                         "DIRECT"),
        ("ST07", "I feel scattered and lost",                    "GENTLE_GROUNDED"),
        ("ST08", "imagine if state had no inertia",              "CREATIVE"),
        ("ST09", "what is the kernel",                           "DIRECT"),
        ("ST10", "I want structure but no rules",                "CONVERSATIONAL"),
    ]

    results = []
    modes_seen = []
    loops_triggered = 0

    for label, text, expected in inputs:
        r = run_test(label, text, expected)
        modes_seen.append(r["mode"])
        if r["loop_detected"]:
            loops_triggered += 1
        results.append(r)
        _print_result_line(r)

    print(f"\n  Modes across 10 turns: {' → '.join(modes_seen)}")
    print(f"  Loop detection triggered: {loops_triggered} time(s)")

    passed = sum(1 for r in results if r["passed"])
    print(f"\n  {passed}/{len(results)} passed")

    # bonus assertion: all responses are non-empty and violation-free
    all_clean = all(not r["violations"] for r in results)
    print(f"  Zero violations: {'✓' if all_clean else '✗'}")

    return results


# ── repeat-mode loop test ──────────────────────────────────────────────────────

def suite_loop_detection():
    """6 — Loop detection. Verify DIRECT is forced after mode stagnation."""
    print("\n── 6. Loop Detection Verification ───────────────────────────")
    reset_session()

    # 4 identical conversational inputs — 4th should trigger loop
    inputs = [
        ("LP1", "I want to think about this project", "CONVERSATIONAL"),
        ("LP2", "I want to think about this project", "CONVERSATIONAL"),
        ("LP3", "I want to think about this project", "CONVERSATIONAL"),
        ("LP4", "I want to think about this project", "DIRECT"),   # loop → DIRECT
    ]

    results = []
    for label, text, expected in inputs:
        r = run_test(label, text, expected)
        results.append(r)
        loop_marker = " ← loop!" if r["loop_detected"] else ""
        _print_result_line(r)
        if loop_marker:
            print(f"             {loop_marker}")

    loop_fired = any(r["loop_detected"] for r in results)
    loop_result_line = "✓ loop detection activated" if loop_fired else "✗ loop detection did NOT activate"
    print(f"\n  {loop_result_line}")

    passed = sum(1 for r in results if r["passed"])
    print(f"  {passed}/{len(results)} passed")
    return results


# ── summary ────────────────────────────────────────────────────────────────────

def _print_suite(results: list):
    for r in results:
        _print_result_line(r)
    passed = sum(1 for r in results if r["passed"])
    print(f"\n  {passed}/{len(results)} passed")


def _score(all_results: list) -> dict:
    total   = len(all_results)
    passed  = sum(1 for r in all_results if r["passed"])
    viols   = sum(len(r.get("violations", [])) for r in all_results)
    loops   = sum(1 for r in all_results if r.get("loop_detected", False))
    return {
        "total":      total,
        "passed":     passed,
        "failed":     total - passed,
        "violations": viols,
        "loops":      loops,
        "score_pct":  int(100 * passed / total) if total else 0,
    }


# ── entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("eLo AI — Cognitive Test Suite")
    print("=" * 50)

    all_results = []
    all_results += suite_factual()
    all_results += suite_emotional()
    all_results += suite_creative()
    all_results += suite_ambiguous()
    all_results += suite_stress()
    all_results += suite_loop_detection()

    score = _score(all_results)

    print("\n" + "=" * 50)
    print("FINAL SCORE")
    print("=" * 50)
    print(f"  Total tests   : {score['total']}")
    print(f"  Passed        : {score['passed']}")
    print(f"  Failed        : {score['failed']}")
    print(f"  Violations    : {score['violations']}")
    print(f"  Loops fired   : {score['loops']}")
    print(f"  Score         : {score['score_pct']}%")
    print()

    if score["failed"] > 0:
        print("Failed tests:")
        for r in all_results:
            if not r["passed"]:
                mode_note = f" (got {r['mode']}, expected {r['expected_mode']})" \
                            if not r.get("mode_correct", True) else ""
                print(f"  ✗  {r['label']}{mode_note}")
                for v in r.get("violations", []):
                    print(f"       violation: {v}")

    sys.exit(0 if score["failed"] == 0 else 1)
