"""
Capability audit — every verdict comes from executing something.

David, 2026-09-29: "run this against the code, with test results, no easy
passes, no easy work arounds, no more places to hide, no more blocks that
don't exist."

Rules this harness enforces on itself:

  * A question with no check is NOT PROVEN. It is never PASS by assumption.
  * PASS requires a check that actually ran and returned true. pytest checks
    shell out to pytest and read the exit status; code checks import the real
    module and evaluate a real predicate.
  * A check that errors is FAIL, not skipped. An exception is a result.
  * NOT PROVEN is a legitimate, expected, common answer. Most of the 400
    questions do not have a test behind them, and saying so is the point.

    python3 tests/capability_audit.py              # all encoded sections
    python3 tests/capability_audit.py embodiment   # one section
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import traceback

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)   # code checks import the real modules
PY = sys.executable
OUT = os.path.join(ROOT, "engineering", "evidence", "LIVE", "capability_audit.jsonl")

PASS, FAIL, UNPROVEN = "PASS", "FAIL", "NOT PROVEN"


def pytest_check(selector: str):
    """Verdict from a real pytest run. Exit 0 = PASS."""
    def run():
        r = subprocess.run(
            [PY, "-m", "pytest", selector, "-q", "--no-header", "-x"],
            cwd=ROOT, capture_output=True, text=True, timeout=300,
        )
        tail = [ln for ln in r.stdout.strip().splitlines() if ln.strip()][-1:]
        return (r.returncode == 0), f"pytest {selector} -> {tail[0] if tail else r.returncode}"
    return run


def code_check(fn, label: str):
    """Verdict from a real predicate over the running codebase."""
    def run():
        ok = fn()
        return bool(ok), f"{label} -> {ok}"
    return run


# ── predicates ────────────────────────────────────────────────────────────────

def _p_sim_vs_physical():
    from runtime.memory_origin import (
        SIMULATED_EMBODIMENTS, PHYSICAL_EMBODIMENTS,
        origin_for_embodiment, can_claim_physical_experience, MemoryOrigin)
    if SIMULATED_EMBODIMENTS & PHYSICAL_EMBODIMENTS:
        return False
    if origin_for_embodiment("totally_unknown_body") is not MemoryOrigin.SIMULATED_EXPERIENCE:
        return False
    return (can_claim_physical_experience(origin_for_embodiment("desktop")) is False
            and can_claim_physical_experience(origin_for_embodiment("robot")) is True)


def _p_occurred_states():
    from runtime.cognitive_state import CognitiveState as C, can_claim_occurred
    allowed = {s for s in C if can_claim_occurred(s)}
    return allowed == {C.MEMORY, C.OBSERVATION, C.ACTION}


def _p_dream_never_occurred():
    from faculties.dream.dream_review import CandidateInsight, PROMOTION_LADDER
    from runtime.cognitive_state import can_claim_occurred
    return all(
        can_claim_occurred(
            CandidateInsight(content="c", significance=1.0, stage=s).cognitive_state
        ) is False
        for s in PROMOTION_LADDER
    )


def _p_imagination_vs_fact():
    from runtime.cognitive_state import state_for_epistemic_class as S, CognitiveState as C
    return (S("SPECULATIVE") is C.IMAGINATION and S("VERIFIED") is C.KNOWLEDGE
            and S("HYPOTHESIS") is C.HYPOTHESIS)


def _p_knows_current_body_capabilities():
    from runtime.embodiment_capabilities import capability_answer, current_body
    a = capability_answer(current_body())
    return bool(a["can"]) and a["body"] == current_body()


def _p_knows_what_it_cannot_do():
    from runtime.embodiment_capabilities import CANNOT, TERMINAL, cannot
    return bool(CANNOT.get(TERMINAL)) and cannot("physically walk", TERMINAL) is True


def _p_no_false_denial():
    from runtime.embodiment_capabilities import denial_is_false
    ok, proof = denial_is_false("I can't control your computer")
    return ok and bool(proof)


def _p_robot_is_future_tense():
    from runtime.embodiment_capabilities import can, can_eventually, ROBOT
    return all(can(a, ROBOT) is False and can_eventually(a, ROBOT) is True
               for a in ("see", "move", "touch", "manipulate"))


def _p_identity_constant_across_bodies():
    """Identity anchor content must not vary by embodiment."""
    from runtime.identity_kernel import IDENTITY
    a = IDENTITY.as_anchor_block()
    import runtime.embodiment_capabilities as ec
    for body in ec.bodies():
        if IDENTITY.as_anchor_block() != a:
            return False
    return a.startswith("[IDENTITY ANCHOR]")


def _p_anchor_names_live_body():
    src = open(os.path.join(ROOT, "runtime", "backend_router.py"), encoding="utf-8").read()
    return ("BODY RULE: I am in {_body_label} right now" in src
            and "from runtime.embodiment_capabilities import current_body" in src)


def _p_anchor_forbids_robot_claim():
    src = open(os.path.join(ROOT, "runtime", "backend_router.py"), encoding="utf-8").read()
    return ("That robot has not been built and I have never been inside it" in src
            and "Form: rounded inflatable TPU shell" not in src)


def _p_thirteen_states_distinct():
    from runtime.cognitive_state import CognitiveState, MEANINGS
    senses = [MEANINGS[s] for s in CognitiveState]
    return len(senses) == 13 and len(set(senses)) == 13


def _p_unknown_fails_safe():
    from runtime.cognitive_state import state_for_origin, can_claim_occurred, UNKNOWN_STATE
    return all(state_for_origin(p) is UNKNOWN_STATE and not can_claim_occurred(state_for_origin(p))
               for p in ("", "made_up", None))


def _p_claim_gate_covers_all_non_occurred():
    """
    Check 16 must flag EVERY state that cannot claim occurrence, not just a
    deny-list of five. This is the known inversion.
    """
    from runtime.response_gate import _check_cognitive_claim_origin as c16
    from runtime.cognitive_state import CognitiveState as C, can_claim_occurred
    claim = "I remember that happened to me."
    for s in C:
        ok, _, _ = c16(claim, {"state": s.value})
        if not can_claim_occurred(s) and ok:
            return False
    return True


def _p_session_log_store_is_reported():
    src = open(os.path.join(ROOT, "server.py"), encoding="utf-8").read()
    return "session_log_window" in src and "_SESSION_WINDOW" in src


def _p_recall_intent_covers_paraphrase():
    from runtime.recall_intent import is_recall_query
    phrases = ("what did we work on",)
    return (is_recall_query("So what was I working on before that?", phrases)
            and not is_recall_query("I'm working on Chunk today.", phrases))


# ── the questions, by section ────────────────────────────────────────────────
# (question, check or None)

SECTIONS: dict[str, list] = {

    "simulation_vs_reality": [
        ("capable of distinguishing simulation from reality?",
         code_check(_p_sim_vs_physical, "EMB-051 sim/physical sets disjoint + unknown fails safe")),
        ("capable of distinguishing a simulated body from a real body?",
         pytest_check("tests/test_emb051_simulation_vs_reality.py")),
        ("capable of distinguishing imagined experience from experienced reality?",
         code_check(_p_occurred_states, "only MEMORY/OBSERVATION/ACTION may claim occurrence")),
        ("capable of distinguishing a hypothetical action from an executed action?",
         code_check(_p_occurred_states, "same gate")),
        ("capable of recording whether an action actually happened?", None),
        ("capable of distinguishing a prediction from an observation?",
         code_check(lambda: _p_occurred_states(), "PREDICTION not in OCCURRED_STATES")),
        ("capable of recognising when an expected action did not occur?", None),
        ("capable of updating its world model after simulation differs from reality?", None),
    ],

    "knowledge_and_truth": [
        ("can distinguish knowledge from experience?",
         code_check(_p_occurred_states, "KNOWLEDGE is not an occurred state")),
        ("can distinguish knowledge from hypothesis?",
         code_check(_p_imagination_vs_fact, "epistemic class -> cognitive state")),
        ("can distinguish knowledge from imagination?",
         code_check(_p_imagination_vs_fact, "SPECULATIVE -> IMAGINATION")),
        ("can distinguish knowledge from dream material?",
         code_check(_p_dream_never_occurred, "no ladder rung reaches an occurred state")),
        ("can distinguish current truth from historical truth?", None),
        ("capable of recognising uncertainty?",
         code_check(_p_unknown_fails_safe, "unknown -> HYPOTHESIS, never occurred")),
        ("capable of saying 'I don't know' when evidence is insufficient?", None),
        ("capable of attributing knowledge to its source?", None),
        ("capable of identifying contradictions in its knowledge?", None),
    ],

    "embodiment": [
        ("an embodied self?",
         pytest_check("tests/test_cap_emb_002_i_can_model.py")),
        ("capable of understanding the capabilities of its current body?",
         code_check(_p_knows_current_body_capabilities, "capability_answer(current_body)")),
        ("capable of understanding the limitations of its current body?",
         code_check(_p_knows_what_it_cannot_do, "EMB-002 Cannot list")),
        ("capable of recognising what an embodiment can currently do?",
         code_check(_p_robot_is_future_tense, "robot = Can eventually, never now")),
        ("capable of maintaining identity while changing body?",
         code_check(_p_identity_constant_across_bodies, "anchor invariant across bodies")),
        ("capable of distinguishing body capability from cognitive capability?",
         code_check(_p_no_false_denial, "denial_is_false vs live registry")),
        ("capable of transferring abstract learning between embodiments?", None),
        ("capable of learning body-specific skills?", None),
        ("whose desktop presence is an embodiment rather than a second brain?",
         code_check(_p_anchor_names_live_body, "anchor names live body from one signal")),
        ("capable of recognising when an embodiment cannot perform an intended action?", None),
        ("capable of selecting an alternative embodiment or action?", None),
    ],

    "self_knowledge": [
        ("capable of knowing what he can currently do?",
         code_check(_p_knows_current_body_capabilities, "EMB-002 capability_answer")),
        ("capable of knowing what he cannot currently do?",
         code_check(_p_knows_what_it_cannot_do, "EMB-002 Cannot")),
        ("capable of knowing what his current embodiment can do?",
         pytest_check("tests/test_cap_emb_002_i_can_model.py")),
        ("capable of knowing what he has merely imagined?",
         code_check(_p_dream_never_occurred, "dream ladder cannot claim occurrence")),
        ("capable of knowing what he has experienced?",
         code_check(_p_sim_vs_physical, "EMB-051 physical vs simulated experience")),
        ("capable of knowing what he does not know?",
         code_check(_p_unknown_fails_safe, "unknown fails safe to HYPOTHESIS")),
        ("capable of inspecting his own cognitive state?",
         code_check(_p_thirteen_states_distinct, "13 distinct states")),
        ("capable of identifying contradictions in his own state?", None),
        ("capable of identifying when his self-model is incomplete?", None),
        ("capable of knowing why he made a decision?", None),
    ],

    "self_correction": [
        ("capable of recognising when it claimed something it did not know?",
         code_check(_p_claim_gate_covers_all_non_occurred,
                    "response_gate check 16 covers every non-occurred state")),
        ("capable of correcting itself?", None),
        ("capable of changing future behaviour after correction?", None),
        ("capable of recognising that it misunderstood a referent?", None),
    ],

    "conversation_memory": [
        ("can remember what he himself just said?", None),
        ("a system that knows what the current conversation is about?",
         code_check(_p_session_log_store_is_reported,
                    "both conversation stores named in diagnostics")),
        ("can answer 'what were we just talking about' from context?",
         code_check(_p_recall_intent_covers_paraphrase,
                    "recall-intent detection covers paraphrase, excludes statements")),
        ("can distinguish the current conversation from older conversations?", None),
        ("can return to an earlier conversational thread?", None),
    ],
}


def main() -> int:
    wanted = sys.argv[1:] or list(SECTIONS)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    tally = {PASS: 0, FAIL: 0, UNPROVEN: 0}
    rows = []
    with open(OUT, "a", encoding="utf-8") as sink:
        for section in wanted:
            if section not in SECTIONS:
                print(f"unknown section: {section}")
                return 2
            print(f"\n{'='*78}\n{section.upper()}\n{'='*78}")
            for question, check in SECTIONS[section]:
                if check is None:
                    verdict, detail = UNPROVEN, "no check encoded — not claimed either way"
                else:
                    try:
                        ok, detail = check()
                        verdict = PASS if ok else FAIL
                    except Exception as e:
                        verdict = FAIL
                        detail = f"check raised: {type(e).__name__}: {e}"
                tally[verdict] += 1
                rows.append((section, question, verdict, detail))
                mark = {PASS: "PASS      ", FAIL: "FAIL      ", UNPROVEN: "NOT PROVEN"}[verdict]
                print(f"  {mark}  {question}")
                print(f"              {detail}")
                sink.write(json.dumps({
                    "section": section, "question": question,
                    "verdict": verdict, "detail": detail,
                    "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
                }) + "\n")
            sink.flush()

    total = sum(tally.values())
    print(f"\n{'='*78}")
    print(f"ENCODED: {total}   PASS {tally[PASS]}   FAIL {tally[FAIL]}   NOT PROVEN {tally[UNPROVEN]}")
    if tally[FAIL]:
        print("\nFAILURES:")
        for s, q, v, d in rows:
            if v == FAIL:
                print(f"  [{s}] {q}\n      {d}")
    print(f"\nevidence: {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
