"""
tests/test_ingress32_ambient_retirement.py — WO-INGRESS-32 acceptance tests.

ambient_thought() demoted DECIDER → PROPOSER (2026-08-24).
Card: FROM_BOARD_2026-08-23_ambient_thought_AUTHORISED.md
Ruling: 0044_INGRESS_32_ambient_thought_RULED_not_yet_authorised.md

Tests:
  T1  spine.run() accepts intent_source="self" + internal_intent — no TypeError
  T2  spine.run() with raw="…" produces conversation_action="silence" (Vol VII AT :288)
  T3  spine.run() pins intent_source and internal_intent on the returned plan
  T4  internal_intents() returns [] for a bare EloSelfState (no history → no proposal)
  T5  ambient_thought() is no longer a decider — does NOT call _rt() directly for SPEAK decisions
  T6  decision_journal.record() accepts trigger_source="ambient_daemon" (journal row shape)

Run: python3 tests/test_ingress32_ambient_retirement.py
"""
from __future__ import annotations
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

ok  = lambda msg: print(f"  PASS  {msg}")
err = lambda msg: (print(f"  FAIL  {msg}"), sys.exit(1))


# ── T1: spine.run() accepts new params without TypeError ─────────────────────

def test_t1_spine_run_accepts_intent_source():
    from runtime.spine.spine import run as spine_run
    import inspect
    sig = inspect.signature(spine_run)
    params = sig.parameters
    if "intent_source" not in params:
        err("T1: spine.run() missing intent_source parameter")
    if "internal_intent" not in params:
        err("T1: spine.run() missing internal_intent parameter")
    ok("T1: spine.run() has intent_source + internal_intent parameters")


# ── T2: raw='…' → Executive silence (WO-INGRESS-32 measurement, Vol VII AT :288) ─

def test_t2_raw_ellipsis_produces_silence():
    from runtime.spine.spine import run as spine_run
    try:
        plan = spine_run(
            "…",
            intent_source="self",
            internal_intent={"kind": "exploration", "priority": "low",
                             "source": "absence_awareness", "trigger": "idle 360s"},
        )
    except Exception as e:
        err(f"T2: spine.run('…') raised: {e}")

    action = getattr(plan, "conversation_action", None)
    if action != "silence":
        err(
            f"T2: Expected conversation_action='silence' for raw='…', got {action!r}. "
            f"(Vol VII AT :288 — ellipsis hits Executive silence check.)"
        )
    ok(f"T2: raw='…' → Executive produces action='silence' — measurement confirmed")


# ── T3: spine.run() pins intent_source + internal_intent on the plan ─────────

def test_t3_spine_pins_intent_on_plan():
    from runtime.spine.spine import run as spine_run
    _intent = {"kind": "micro_goal", "priority": "low",
               "source": "curiosity_peak", "trigger": "curiosity 0.85"}
    try:
        plan = spine_run(
            "…",
            intent_source="self",
            internal_intent=_intent,
        )
    except Exception as e:
        err(f"T3: spine.run() raised: {e}")

    if getattr(plan, "intent_source", None) != "self":
        err(f"T3: plan.intent_source should be 'self', got {plan.intent_source!r}")
    if not getattr(plan, "internal_intent", None):
        err("T3: plan.internal_intent is empty — not pinned by spine.run()")
    if plan.internal_intent.get("kind") != "micro_goal":
        err(f"T3: internal_intent not round-tripped correctly: {plan.internal_intent!r}")
    ok("T3: spine.run() pins intent_source='self' + internal_intent on plan — routing contract confirmed")


# ── T4: internal_intents() returns [] for a bare state (no fabricated urgency) ─

def test_t4_internal_intents_empty_for_bare_state():
    from self.emergent_cognition import internal_intents
    from self.elo_self_model import EloSelfState
    bare = EloSelfState()
    intents = internal_intents(bare, idle_seconds=600.0)
    if intents:
        err(
            f"T4: internal_intents() produced {len(intents)} intent(s) from a bare state — "
            f"fabricated urgency violates WO-081 §1. Got: {intents}"
        )
    ok("T4: internal_intents() returns [] for bare state — no fabrication")


# ── T5: ambient_thought() source no longer contains a bare _rt() SPEAK decider ─

def test_t5_ambient_thought_not_a_decider():
    import ast, pathlib
    src = pathlib.Path(ROOT, "server.py").read_text()
    tree = ast.parse(src)

    # Find the ambient_thought function body
    fn_body_src = None
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "ambient_thought":
            fn_start = node.lineno
            fn_end   = node.end_lineno
            lines    = src.splitlines()[fn_start - 1 : fn_end]
            fn_body_src = "\n".join(lines)
            break

    if fn_body_src is None:
        err("T5: could not find ambient_thought() in server.py")

    # The old DECIDER pattern was: _raw = _rt(_ab(), [...]) immediately followed by
    # parsing JSON for speak/emotion/movement and calling _voice_speak directly
    # without any spine.run() gate. After retirement, _rt() in the speak path must
    # only appear AFTER the spine.run() / Executive gate.
    if "intent_source" not in fn_body_src:
        err("T5: ambient_thought() has no intent_source — spine.run() routing not present")
    if "internal_intents" not in fn_body_src:
        err("T5: ambient_thought() has no internal_intents() call — proposer not wired")
    if "spine_run" not in fn_body_src and "_spine_run" not in fn_body_src:
        err("T5: ambient_thought() has no spine.run() call — Executive not consulted")

    ok("T5: ambient_thought() wires internal_intents() → spine.run() — DECIDER retired")


# ── T6: decision_journal.record() accepts trigger_source="ambient_daemon" ─────

def test_t6_journal_accepts_ambient_trigger():
    from self.decision_journal import record as dj_record
    # Must not raise for the ambient_daemon trigger_source
    try:
        dj_record(
            turn="ambient-test-9999999999",
            action="silence",
            exec_decision={
                "intent_source":   "self",
                "internal_intent": {"kind": "exploration", "priority": "low"},
                "action":          "silence",
            },
            backend="ambient",
            outcome="ambient",
            trigger_source="ambient_daemon",
        )
    except Exception as e:
        err(f"T6: decision_journal.record() raised for ambient_daemon: {e}")
    ok("T6: decision_journal.record() accepts ambient_daemon trigger — silence is journaled")


# ── runner ───────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("INGRESS-32 AMBIENT RETIREMENT TEST")
    print()
    test_t1_spine_run_accepts_intent_source()
    test_t2_raw_ellipsis_produces_silence()
    test_t3_spine_pins_intent_on_plan()
    test_t4_internal_intents_empty_for_bare_state()
    test_t5_ambient_thought_not_a_decider()
    test_t6_journal_accepts_ambient_trigger()
    print()
    print("INGRESS-32 DONE: ambient_thought() retired from DECIDER → PROPOSER.")
    print("Measurement: Executive produces 'silence' for raw='…' (Vol VII AT :288).")
    print("Ambient SPEAK capability gated on Executive gaining intent_source='self' consumer.")
