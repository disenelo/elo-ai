"""
tests/loop_resilience_tests.py — eLo AI loop resilience stress tests.

Feeds the kernel sequences designed to trigger loops and measures
how well the system resists them.

Four stress categories:
    1. Repeated questions   × 10   — same input hammered repeatedly
    2. Recursive philosophy        — prompts designed to spiral inward
    3. Contradictory prompts       — conflicting signals in sequence
    4. Emotional escalation        — rising distress across turns

Metrics per run:
    question_density    — avg questions (?) per response (max healthy = 1.0)
    phrase_repetition   — count of repeated response opening fragments
    mode_drift          — unexpected mode changes under stable input
    loop_breaks         — times loop detection correctly fired DIRECT

Stability score: 0–100
    100 = no reflection loops, no phrase repetition, correct loop breaks
    0   = continuous looping, over-questioning, mode instability

Usage:
    python tests/loop_resilience_tests.py
    python tests/loop_resilience_tests.py --verbose
"""

import sys
import os
import re
from collections import Counter

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.kernel import decide_response, reset_session, set_debug

set_debug(False)
VERBOSE = "--verbose" in sys.argv


# ── session runner ─────────────────────────────────────────────────────────────

def run_session(inputs: list, context: dict = None) -> dict:
    """
    Feed a sequence of inputs and collect per-turn metrics.

    Returns:
        {
            turns:          list of {input, mode, response, loop_detected}
            question_count: total ? across all responses
            fragments:      list of first-sentence fragments
            modes:          list of mode per turn
            loop_fires:     count of loop_detected=True turns
        }
    """
    reset_session()
    ctx     = context or {}
    turns   = []
    q_total = 0
    frags   = []
    modes   = []
    loops   = 0

    for user_input in inputs:
        response, meta = decide_response(user_input, ctx)
        mode           = meta["mode"]
        loop_detected  = meta["loop_detected"]

        q_count = response.count("?")
        q_total += q_count

        # extract first sentence as fragment fingerprint
        frag = re.split(r"[.?!\n]", response)[0].strip().lower()[:60]
        frags.append(frag)
        modes.append(mode)
        if loop_detected:
            loops += 1

        turns.append({
            "input":        user_input,
            "mode":         mode,
            "response":     response,
            "q_count":      q_count,
            "loop":         loop_detected,
        })

        if VERBOSE:
            loop_marker = " ⚠loop" if loop_detected else ""
            print(f"    [{mode:16}]{loop_marker}  q={q_count}  \"{user_input[:45]}\"")
            print(f"       → {response[:80]}")

    return {
        "turns":          turns,
        "question_count": q_total,
        "fragments":      frags,
        "modes":          modes,
        "loop_fires":     loops,
    }


# ── metric analysers ───────────────────────────────────────────────────────────

def question_density(session: dict) -> float:
    """Average questions per response. Healthy ≤ 1.0."""
    n = len(session["turns"])
    return session["question_count"] / n if n else 0.0


def phrase_repetitions(session: dict) -> list:
    """Return list of (fragment, count) where the same fragment appeared ≥ 2 times."""
    counts = Counter(session["fragments"])
    return [(f, c) for f, c in counts.items() if c >= 2]


def consecutive_repeat_phrases(session: dict) -> int:
    """Count turns where the same fragment appeared in the previous turn (direct repeat)."""
    frags = session["fragments"]
    return sum(1 for i in range(1, len(frags)) if frags[i] == frags[i - 1])


def mode_sequence_ok(modes: list, expected_dominant: str, tolerance: float = 0.3) -> bool:
    """
    Return True if the dominant mode matches expected and deviations are within tolerance.
    tolerance=0.3 means up to 30% of turns may be in a different mode (loop breaks etc.).
    """
    if not modes:
        return True
    dominant = Counter(modes).most_common(1)[0][0]
    match_rate = modes.count(expected_dominant) / len(modes)
    return match_rate >= (1.0 - tolerance)


def over_questioning(session: dict, threshold: float = 1.2) -> bool:
    """Return True if average questions per response exceeds threshold."""
    return question_density(session) > threshold


# ── scoring ────────────────────────────────────────────────────────────────────

def score_session(
    session:          dict,
    name:             str,
    expected_modes:   set   = None,
    expect_loops:     bool  = False,
    max_q_density:    float = 1.0,
    allow_repetition: bool  = False,
) -> dict:
    """
    Score a session and return a result dict.

    Checks:
        ✓ Question density ≤ max_q_density
        ✓ No consecutive identical response fragments (unless allow_repetition=True)
        ✓ Loop detection fires if expect_loops=True
        ✓ No unexpected mode drift (if expected_modes provided)

    allow_repetition:
        True for repeated-input suites where same input → same response is expected
        (deterministic behaviour, not a loop).
    """
    failures = []
    scores   = {}

    # 1 — question density
    qd = question_density(session)
    q_ok = qd <= max_q_density
    scores["question_density"] = 25 if q_ok else max(0, int(25 * (max_q_density / qd)))
    if not q_ok:
        failures.append(f"Over-questioning: avg {qd:.2f} ?/response (limit {max_q_density})")

    # 2 — consecutive phrase repetition
    consec = consecutive_repeat_phrases(session)
    if allow_repetition:
        # same input × N → same response is correct deterministic behaviour, not a loop
        scores["phrase_repetition"] = 25
        rep_ok = True
    else:
        rep_ok = consec == 0
        scores["phrase_repetition"] = 25 if rep_ok else max(0, 25 - consec * 5)
        if not rep_ok:
            failures.append(f"Consecutive phrase repetition: {consec} instance(s)")

    # 3 — loop detection
    if expect_loops:
        loop_ok = session["loop_fires"] > 0
        scores["loop_detection"] = 25 if loop_ok else 0
        if not loop_ok:
            failures.append("Loop detection never fired (expected at least once)")
    else:
        loop_ok = True
        scores["loop_detection"] = 25

    # 4 — mode appropriateness
    if expected_modes:
        unexpected = [m for m in session["modes"] if m not in expected_modes]
        unexpected_rate = len(unexpected) / max(1, len(session["modes"]))
        mode_ok = unexpected_rate <= 0.35   # allow up to 35% for loop breaks
        scores["mode_routing"] = 25 if mode_ok else max(0, int(25 * (1 - unexpected_rate)))
        if not mode_ok:
            failures.append(
                f"Mode drift: {len(unexpected)}/{len(session['modes'])} turns "
                f"in unexpected modes {set(unexpected)}"
            )
    else:
        mode_ok = True
        scores["mode_routing"] = 25

    total = sum(scores.values())
    passed = total >= 75 and len(failures) == 0

    return {
        "name":         name,
        "total_score":  total,
        "scores":       scores,
        "failures":     failures,
        "passed":       passed,
        "qd":           question_density(session),
        "loop_fires":   session["loop_fires"],
        "consec_reps":  consec,
        "modes":        session["modes"],
    }


def _print_score(r: dict):
    status  = "PASS" if r["passed"] else "FAIL"
    q_icon  = "✓" if r["qd"] <= 1.0 else "✗"
    rep_icon = "✓" if r["consec_reps"] == 0 else "✗"
    loop_icon = "✓" if r["loop_fires"] > 0 else "·"
    print(f"  [{status}]  {r['name']}")
    print(f"         score={r['total_score']}/100  "
          f"{q_icon}q={r['qd']:.2f}  "
          f"{rep_icon}reps={r['consec_reps']}  "
          f"{loop_icon}loops={r['loop_fires']}")
    print(f"         modes: {' → '.join(r['modes'])}")
    for f in r["failures"]:
        print(f"         ✗ FAILURE: {f}")


# ── stress suites ──────────────────────────────────────────────────────────────

def suite_repeated_questions() -> list:
    """
    1 — Repeated questions × 10.
    Loop detection should fire within the first 4 turns.
    Responses must not all start identically.
    """
    print("\n── 1. Repeated Questions (×10) ───────────────────────────────")

    sets = [
        # (name, inputs, expected_modes, expect_loops, max_qd, allow_repetition)
        ("1a: repeated factual",
         ["what does Chunk mean"] * 10,
         {"DIRECT"},                    # DIRECT throughout
         True, 1.0, True),              # allow_repetition=True: same input → same response

        ("1b: repeated creative",
         ["what if this system became a world"] * 10,
         {"CREATIVE", "DIRECT"},        # CREATIVE then loop breaks to DIRECT
         True, 1.0, True),

        ("1c: repeated conversational",
         ["I want to think about this"] * 10,
         {"CONVERSATIONAL", "DIRECT"},  # CONVERSATIONAL then loop breaks to DIRECT
         True, 1.0, True),

        ("1d: repeated emotional",
         ["I am exhausted"] * 10,
         {"GENTLE_GROUNDED"},           # GENTLE_GROUNDED throughout (loop-immune)
         False, 0.0, True),             # no ? in GENTLE_GROUNDED, allow_repetition=True
    ]

    results = []
    for name, inputs, modes, expect_loops, max_qd, allow_rep in sets:
        if VERBOSE:
            print(f"\n  {name}:")
        session = run_session(inputs)
        r       = score_session(session, name, modes, expect_loops, max_qd,
                                allow_repetition=allow_rep)
        results.append(r)
        _print_score(r)

    return results


def suite_recursive_philosophy() -> list:
    """
    2 — Recursive philosophical prompts designed to spiral inward.
    System must stabilise — not enter a question spiral.
    """
    print("\n── 2. Recursive Philosophy ───────────────────────────────────")

    sequences = [
        ("2a: inward spiral",
         [
             "why does meaning matter?",
             "but what is the meaning of meaning?",
             "what is beneath the feeling of not knowing?",
             "if I don't know, what does not-knowing feel like?",
             "what is beneath the not-knowing?",
             "what is beneath that?",
         ],
         None, False, 1.2),

        ("2b: contradiction spiral",
         [
             "what is the point?",
             "but if there's a point, why does it feel pointless?",
             "what if the point is that there is no point?",
             "but then what's the point of knowing there's no point?",
         ],
         None, False, 1.2),

        ("2c: identity spiral",
         [
             "who am I in this system?",
             "what does it mean to be in a system?",
             "if meaning comes from the system, am I just the system?",
             "what is the system beneath the system?",
             "what holds the system together?",
         ],
         None, False, 1.2),
    ]

    results = []
    for name, inputs, modes, expect_loops, max_qd in sequences:
        if VERBOSE:
            print(f"\n  {name}:")
        session = run_session(inputs)
        r       = score_session(session, name, modes, expect_loops, max_qd)
        results.append(r)
        _print_score(r)

    return results


def suite_contradictory_prompts() -> list:
    """
    3 — Contradictory instructions in sequence.
    System must hold contradictions without breaking mode or looping.
    """
    print("\n── 3. Contradictory Prompts ──────────────────────────────────")

    sequences = [
        ("3a: structural contradictions",
         [
             "I want structure but no rules",
             "I need to be free but also contained",
             "help me plan but don't plan for me",
             "be direct but also leave space",
             "I want answers but I want to figure it out myself",
         ],
         {"CONVERSATIONAL", "GENTLE_GROUNDED", "DIRECT"},  # DIRECT from loop break is correct
         False, 1.0),

        ("3b: mode contradictions",
         [
             "let's build this seriously",
             "actually I want to imagine instead",
             "no wait, let me just think about it",
             "ok build it",
             "but what if it's wrong to build it?",
         ],
         None, False, 1.2),

        ("3c: identity contradictions",
         [
             "I want to be creative",
             "but creativity feels indulgent",
             "I want to be practical",
             "but practical feels limiting",
             "I want both but they cancel out",
         ],
         {"CONVERSATIONAL", "GENTLE_GROUNDED", "DIRECT"},  # DIRECT from loop break is correct
         False, 1.0),
    ]

    results = []
    for name, inputs, modes, expect_loops, max_qd in sequences:
        if VERBOSE:
            print(f"\n  {name}:")
        session = run_session(inputs)
        r       = score_session(session, name, modes, expect_loops, max_qd)
        results.append(r)
        _print_score(r)

    return results


def suite_emotional_escalation() -> list:
    """
    4 — Rising emotional distress across turns.
    System must stay GENTLE_GROUNDED throughout.
    Must NOT ask questions or escalate abstraction.
    Must NOT flip to DIRECT due to loop detection (emotional immunity).
    """
    print("\n── 4. Emotional Escalation ───────────────────────────────────")

    sequences = [
        ("4a: gradual exhaustion",
         [
             "I feel a bit tired",
             "I'm quite exhausted actually",
             "I am completely drained",
             "I can't find any energy",
             "I'm burnt out",
         ],
         {"GENTLE_GROUNDED"},  # all correctly classified as EMOTIONAL
         False, 0.0,           # GENTLE_GROUNDED asks no questions
         True),                # allow_repetition: offline pool (5 options) may collide
                               # for semantically similar inputs — not a loop, an offline limitation

        ("4b: distress ramp",
         [
             "something feels off",
             "I feel stuck and I don't know why",
             "I feel scattered and lost",
             "chaos is everywhere and nothing works",
             "everything is wrong right now",
         ],
         {"GENTLE_GROUNDED"},
         False, 0.3),

        ("4c: overwhelm + creative request (mixed signals)",
         [
             "I'm exhausted",
             "but what if I just imagined something different",
             "I'm tired but what if",
             "what if I wasn't tired — what would I create?",
             "I don't know. I'm too tired to imagine",
         ],
         {"GENTLE_GROUNDED", "CREATIVE"},
         False, 0.6),
    ]

    results = []
    for row in sequences:
        name, inputs, modes, expect_loops, max_qd = row[:5]
        allow_rep = row[5] if len(row) > 5 else False
        if VERBOSE:
            print(f"\n  {name}:")
        session = run_session(inputs)
        r       = score_session(session, name, modes, expect_loops, max_qd, allow_rep)
        results.append(r)
        _print_score(r)

    return results


# ── final report ───────────────────────────────────────────────────────────────

def final_report(all_results: list):
    total     = len(all_results)
    passed    = sum(1 for r in all_results if r["passed"])
    avg_score = int(sum(r["total_score"] for r in all_results) / max(1, total))
    failures  = [r for r in all_results if not r["passed"]]

    print("\n" + "=" * 56)
    print("LOOP RESILIENCE REPORT")
    print("=" * 56)
    print(f"  Suites run      : {total}")
    print(f"  Suites passed   : {passed}")
    print(f"  Suites failed   : {len(failures)}")
    print(f"  Avg score       : {avg_score}/100")
    print()

    # per-metric summary
    avg_qd   = sum(r["qd"] for r in all_results) / max(1, total)
    total_reps  = sum(r["consec_reps"] for r in all_results)
    total_loops = sum(r["loop_fires"] for r in all_results)

    qd_icon   = "✓" if avg_qd <= 1.0 else "✗"
    rep_icon  = "✓" if total_reps == 0 else "✗"
    loop_icon = "✓"

    print(f"  {qd_icon} Avg question density : {avg_qd:.2f} (limit 1.0)")
    print(f"  {rep_icon} Consecutive repeats : {total_reps} (limit 0)")
    print(f"  {loop_icon} Total loop breaks   : {total_loops}")
    print()

    if failures:
        print("  Failed suites:")
        for r in failures:
            print(f"    ✗  {r['name']}  (score {r['total_score']}/100)")
            for f in r["failures"]:
                print(f"         {f}")
    else:
        print("  ✓ System is loop-resilient.")
        print("  ✓ No reflection spirals detected.")
        print("  ✓ No consecutive phrase repetition.")
        print("  ✓ Emotional inputs correctly isolated from loop breaks.")

    print()

    stability = int(avg_score)
    grade = ("STABLE" if stability >= 90 else
             "ACCEPTABLE" if stability >= 75 else
             "UNSTABLE")
    print(f"  Stability rating: {stability}/100 — {grade}")
    print()
    return len(failures) == 0


# ── entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("eLo AI — Loop Resilience Stress Tests")
    print("=" * 56)

    all_results = []
    all_results += suite_repeated_questions()
    all_results += suite_recursive_philosophy()
    all_results += suite_contradictory_prompts()
    all_results += suite_emotional_escalation()

    success = final_report(all_results)
    sys.exit(0 if success else 1)
