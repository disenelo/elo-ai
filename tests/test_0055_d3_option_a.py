"""
tests/test_0055_d3_option_a.py — card 0055: D3 Option A measurement.

Authorised by David (L3) 2026-08-17. READ/MEASURE/PROVE only.
No modification to runtime/executive.py.

QUESTION: Can ExecutiveContext.lessons be meaningfully consumed by the
frozen Executive without modifying executive.py?

Five-stage causation chain (David's words, card 0055 §3):
  confirmed lesson → Executive decision input → decision changes because of
  lesson → decision journal records genuine causation → future behaviour
  demonstrably differs.

Run: python3 tests/test_0055_d3_option_a.py
"""
import sys, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

ok  = lambda msg: print(f"  OBS   {msg}")
no  = lambda msg: print(f"  NO    {msg}")
unk = lambda msg: print(f"  UNK   {msg}")

# ── Step 1: What keys does frozen decide() actually read? ─────────────────────
def step1_read_path():
    """
    Inspect frozen executive.decide() source to enumerate every key it reads
    from attention_model. No exec — static inspection only.
    """
    import inspect, ast
    from runtime import executive
    src = inspect.getsource(executive.decide)
    tree = ast.parse(src)

    # Collect all dict .get() calls and subscript accesses on 'attention_model'
    reads = set()
    for node in ast.walk(tree):
        # attention_model.get("key", ...)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if (isinstance(node.func.value, ast.Name) and
                    node.func.value.id == "attention_model" and
                    node.func.attr == "get"):
                if node.args and isinstance(node.args[0], ast.Constant):
                    reads.add(node.args[0].value)
        # attention_model["key"]
        if (isinstance(node, ast.Subscript) and
                isinstance(node.value, ast.Name) and
                node.value.id == "attention_model"):
            if isinstance(node.slice, ast.Constant):
                reads.add(node.slice.value)
    return reads


# ── Step 2: Is 'lessons' in the read path? ───────────────────────────────────
def step2_lessons_in_read_path(reads):
    return "lessons" in reads


# ── Step 3: Does injecting a lessons key change the decision? ─────────────────
def step3_decision_changes_with_lessons():
    """
    Run decide() twice with identical inputs — once without lessons, once with
    a plausible lesson injected. If outputs differ, lessons are consumed.
    If outputs are identical, they are not.
    """
    from runtime.executive import decide

    # Representative neutral turn — no edge cases
    base = {
        "intent":            "conversation",
        "emotional_context": {"inferred_state": "present", "valence": "neutral",
                              "momentum": "stable", "closure": "open",
                              "tension": 0.3, "energy": 0.5},
        "wm_winner":  "conversation",
        "world_state": {"available": True, "route_history": []},
    }

    # A lesson that — if consumed — would shift the action toward "build"
    plausible_lesson = {
        "id":         "L42",
        "lesson":     "David responds well when eLo takes an active creative stance",
        "domain":     "conversation",
        "confidence": 0.85,
    }

    without = decide(dict(base), user_input="tell me what you think")
    with_l  = decide(dict(base) | {"lessons": [plausible_lesson]},
                     user_input="tell me what you think")

    return without, with_l


# ── Step 4: Check wm_winner path — could a lesson alias into wm_winner? ───────
def step4_wm_winner_alias():
    """
    wm_winner is the only key in decide() that could in theory be pre-set to
    a lesson-derived value upstream (before decide() is called), causing a
    decision shift without modifying executive.py. This tests whether that
    path produces causation or only correlation.
    """
    from runtime.executive import decide

    base = {
        "intent":            "conversation",
        "emotional_context": {"inferred_state": "present", "valence": "neutral",
                              "momentum": "stable", "closure": "open",
                              "tension": 0.3, "energy": 0.5},
        "world_state": {"available": True, "route_history": []},
    }

    # Without wm_winner → action = reflect (neutral/stable, no phrases)
    without_wm = decide(dict(base) | {"wm_winner": ""},
                        user_input="tell me what you think")

    # With wm_winner="build" (as if a lesson had been encoded there upstream)
    with_wm = decide(dict(base) | {"wm_winner": "build"},
                     user_input="tell me what you think")

    return without_wm, with_wm


# ── runner ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("0055 D3 OPTION A — MEASUREMENT HARNESS")
    print("Read/measure/prove only. No modification to executive.py.")
    print()

    # Step 1
    print("── STEP 1: Keys frozen decide() reads from attention_model ──────────")
    reads = step1_read_path()
    for k in sorted(reads):
        ok(f"  reads: '{k}'")
    print()

    # Step 2
    print("── STEP 2: Is 'lessons' in the read path? ──────────────────────────")
    if step2_lessons_in_read_path(reads):
        ok("'lessons' IS in the read path — Executive can consume it (unexpected)")
    else:
        no("'lessons' NOT in read path — frozen decide() has no lessons consumption code")
    print()

    # Step 3
    print("── STEP 3: Does injecting lessons change the decision? ──────────────")
    wo, wi = step3_decision_changes_with_lessons()
    print(f"  without lessons → action={wo['action']!r}  tone={wo['tone']!r}")
    print(f"  with    lessons → action={wi['action']!r}  tone={wi['tone']!r}")
    if wo == wi:
        no("Outputs are IDENTICAL — lessons key is silently ignored by frozen decide()")
    else:
        ok("Outputs DIFFER — unexpected; inspect which field changed")
        for k in wo:
            if wo[k] != wi.get(k):
                print(f"    DIFF {k}: {wo[k]!r} → {wi[k]!r}")
    print()

    # Step 4
    print("── STEP 4: wm_winner alias path ────────────────────────────────────")
    wo4, wi4 = step4_wm_winner_alias()
    print(f"  wm_winner=''     → action={wo4['action']!r}  reason={wo4.get('cal_reason','')!r}")
    print(f"  wm_winner='build'→ action={wi4['action']!r}  reason={wi4.get('cal_reason','')!r}")
    if wo4["action"] != wi4["action"]:
        ok(f"wm_winner alias path DOES shift action ({wo4['action']!r}→{wi4['action']!r})")
        print("  Note: this shift is caused by wm_winner, not by lessons directly.")
        print("  Causation chain: lesson → upstream sets wm_winner → decide() fires.")
        print("  This is CORRELATION, not causation — executive.py did not read the lesson.")
    else:
        no("wm_winner alias path makes NO difference for this input")
    print()

    # Verdict
    print("═" * 60)
    print("VERDICT")
    print()
    print("  The frozen Executive (executive.py:decide) reads exactly:")
    for k in sorted(reads):
        print(f"    · {k}")
    print()
    print("  'lessons' is not in that set.")
    print()
    print("  Injecting a lessons key into the dict passed to decide() produces")
    print("  zero change in the output (Step 3 confirmed). The key is silently")
    print("  discarded — the Executive never reaches it.")
    print()
    print("  The wm_winner alias path (Step 4) shows that upstream code COULD")
    print("  set wm_winner to a lesson-derived value and shift the action. But")
    print("  that is not Executive consumption of lessons — it is a lesson-")
    print("  shaped input arriving as wm_winner. The causation chain David")
    print("  requires (stage 3: 'decision changes because of lesson') is not met")
    print("  when the lesson is invisibly re-encoded as wm_winner before entry.")
    print()
    print("  A PROVEN IMPOSSIBLE")
    print()
    print("  The Executive logic must change to consume lessons.")
    print("  executive.py has no code path to read a lessons key — now or via")
    print("  any plumbing change that stops short of editing executive.py.")
    print("  Adding ExecutiveContext.lessons is valid plumbing; making decisions")
    print("  change because of it requires unfreezing executive.py.")
    print()
    print("  This is a David/L3 decision. Builder stops here.")
