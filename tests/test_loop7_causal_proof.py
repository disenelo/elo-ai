"""
tests/test_loop7_causal_proof.py — WO-LOOP7-CAUSAL-PROOF-001

Counterfactual proof that the LOOP-7 causal chain is live:

  lesson_store → consult() → executive.decide() action substitution

Four assertions per the WO:
  1. Install a lesson with verified=True, prefers_action="challenge", strength=0.7.
  2. Run executive.decide() on an input that would normally produce "answer"/"reflect".
  3. Assert the decision switches to "challenge".
  4. Remove the lesson.
  5. Assert the same input returns the non-challenge default.

Uses intent="recall" with a neutral input so the default path is "reflect" at
confidence 0.5 — well below the lesson weight 0.7, ensuring the lesson can shift
the action. Intent "conversation" defaults to "answer" at 0.85 which would also
beat the lesson; recall is the minimal viable test surface.

Depends on WO-SELF-MODEL-EXEC-WIRE-001 fix: learning_advice is now forwarded
through executive_context.as_dict() to executive.decide().
"""
from __future__ import annotations


def _make_lesson(prefers_action: str, strength: float = 0.7,
                 session_id: str = "CAUSAL_PROOF_TEST_001") -> dict:
    """
    Minimal verified lesson that passes the ADR-Exec-005 D1 gate.

    consult() reads `prefers_action` (str) and `strength` (float).
    The D1 gate requires evidence[].verified=True and a non-empty,
    non-numeric session_id.
    """
    return {
        "lesson_key":     f"causal_proof_{prefers_action}",
        "summary":        f"prefer {prefers_action} in neutral recall context",
        "statement":      f"In a neutral recall context, {prefers_action} is the right move.",
        "strength":       strength,
        "prefers_action": prefers_action,   # the key consult() reads at line 155
        "applies_when":   ["neutral", "recall", "causal", "proof"],
        "evidence": [
            {
                "session_id":  session_id,
                "action":      prefers_action,
                "verified":    True,
                "outcome":     "causal proof verified",
                "verified_by": "test_loop7_causal_proof",
            }
        ],
    }


def _build_attn(learning_advice_dict: dict | None = None) -> dict:
    """Build a minimal attention model. intent=recall → default 'reflect' at 0.5."""
    d: dict = {
        "intent": "recall",
        "emotional_context": {
            "inferred_state": "present",
            "valence":        "neutral",
            "momentum":       "stable",
        },
        "wm_winner": "",
        "world_state": {},
    }
    if learning_advice_dict is not None:
        d["learning_advice"] = learning_advice_dict
    return d


# ── 1 + 2 + 3: lesson present → action switches to "challenge" ────────────────

def test_lesson_present_switches_action_to_challenge():
    """
    Counterfactual arm: with a verified lesson preferring 'challenge', the
    executive action changes from the default ('reflect') to 'challenge'.
    """
    from faculties.learning.faculty import consult
    from runtime.executive import decide as exec_decide

    lesson  = _make_lesson("challenge", strength=0.7)
    context = {"intent": "neutral recall causal proof", "focal_thread": ""}

    # Consult the learning faculty — this is the LOOP-7 path.
    advice = consult(lessons=[lesson], context=context)
    assert advice.preferences.get("challenge", 0) > 0, (
        f"consult() returned no 'challenge' preference — cannot proceed with causal proof. "
        f"rationale={advice.rationale!r}"
    )
    assert advice.confidence >= 0.5, (
        f"advice confidence {advice.confidence} is below the executive gate (0.5)"
    )

    attn = _build_attn(learning_advice_dict=advice.as_dict())
    out  = exec_decide(attn, user_input="Some neutral statement.")

    assert out["action"] == "challenge", (
        f"Expected executive to choose 'challenge' with lesson present. "
        f"Got '{out['action']}' (reason={out.get('reason','?')!r})"
    )


# ── 4 + 5: lesson absent → action returns to default ─────────────────────────

def test_lesson_absent_returns_default_action():
    """
    Counterfactual control: without the lesson, the executive returns the default
    ('reflect' at 0.5 for intent=recall with no matching pattern).
    """
    from runtime.executive import decide as exec_decide

    attn = _build_attn(learning_advice_dict=None)
    out  = exec_decide(attn, user_input="Some neutral statement.")

    assert out["action"] != "challenge", (
        f"Expected executive NOT to choose 'challenge' without a lesson. "
        f"Got '{out['action']}' — lesson advice may be leaking."
    )


# ── Full counterfactual: same input, two outcomes ─────────────────────────────

def test_full_counterfactual_same_input_different_action():
    """
    The central claim: identical input, lesson present vs absent, produces
    different CAL actions. Proves LEARN → ALTER DECISION is a live causal chain.
    """
    from faculties.learning.faculty import consult
    from runtime.executive import decide as exec_decide

    lesson  = _make_lesson("challenge", strength=0.7)
    context = {"intent": "neutral recall causal proof", "focal_thread": ""}

    advice_with    = consult(lessons=[lesson], context=context)
    advice_without = consult(lessons=[],       context=context)

    attn_with    = _build_attn(learning_advice_dict=advice_with.as_dict())
    attn_without = _build_attn(learning_advice_dict=advice_without.as_dict()
                               if advice_without.preferences else None)

    out_with    = exec_decide(attn_with,    user_input="Some neutral statement.")
    out_without = exec_decide(attn_without, user_input="Some neutral statement.")

    assert out_with["action"] != out_without["action"], (
        f"Causal chain broken: same input produced '{out_with['action']}' with lesson "
        f"AND '{out_without['action']}' without lesson — no causal effect."
    )
    assert out_with["action"] == "challenge", (
        f"With lesson present, expected 'challenge'. Got '{out_with['action']}'."
    )


# ── Lesson strength gate: too weak to overcome default ───────────────────────

def test_weak_lesson_does_not_override():
    """
    A lesson with strength BELOW the default action's confidence does not change
    the action. Ensures the gate is real (weight >= confidence required).
    """
    from faculties.learning.faculty import consult
    from runtime.executive import decide as exec_decide

    # strength=0.4 < reflect's confidence=0.5 — should not win
    lesson  = _make_lesson("challenge", strength=0.4)
    context = {"intent": "neutral recall causal proof", "focal_thread": ""}

    advice = consult(lessons=[lesson], context=context)
    attn   = _build_attn(learning_advice_dict=advice.as_dict())
    out    = exec_decide(attn, user_input="Some neutral statement.")

    assert out["action"] != "challenge", (
        f"Weak lesson (strength=0.4 < default confidence=0.5) should not override. "
        f"Got '{out['action']}'. Gate may be miscalibrated."
    )
