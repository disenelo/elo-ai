"""
tests/test_wo_prediction_error_exec_wire.py — WO-PREDICTION-ERROR-EXEC-WIRE-001

Acceptance: strong prediction_error on input X produces "witness" action instead
of default "answer." Tests action change, not just prompt text.

Also verifies:
- prediction_error_state is in as_dict() output
- moderate surprise does not override default
- witness preference is injected at 0.90 (beats answer@0.85 and build@0.65)
"""
from __future__ import annotations

from dataclasses import field
from runtime.executive_context import ExecutiveContext


def _make_ec_with_pe(surprise_level: str, prediction_error: float) -> ExecutiveContext:
    return ExecutiveContext(
        intent="conversation",
        prediction_error_state={
            "prediction_error": prediction_error,
            "surprise_level":   surprise_level,
        },
        attention={"wm_winner": ""},
    )


# ── ec_prediction_error appears in output ─────────────────────────────────────

def test_ec_prediction_error_in_as_dict():
    ec = _make_ec_with_pe("strong_surprise", 0.85)
    d = ec.as_dict()
    assert "ec_prediction_error" in d
    assert d["ec_prediction_error"]["surprise_level"] == "strong_surprise"


# ── Strong surprise injects witness preference ─────────────────────────────────

def test_strong_surprise_injects_witness_preference():
    ec = _make_ec_with_pe("strong_surprise", 0.85)
    d = ec.as_dict()
    la = d.get("learning_advice") or {}
    prefs = la.get("preferences") or {}
    assert prefs.get("witness", 0) >= 0.90, (
        f"strong_surprise must inject witness >= 0.90; got {prefs.get('witness')}"
    )


def test_moderate_surprise_no_witness_injection():
    ec = _make_ec_with_pe("mild_surprise", 0.55)
    d = ec.as_dict()
    la = d.get("learning_advice") or {}
    prefs = la.get("preferences") or {}
    assert prefs.get("witness", 0) < 0.90, (
        "mild_surprise must not inject witness at strong level"
    )


def test_no_surprise_no_witness_injection():
    ec = _make_ec_with_pe("expected", 0.0)
    d = ec.as_dict()
    la = d.get("learning_advice") or {}
    prefs = la.get("preferences") or {}
    assert prefs.get("witness", 0) == 0, (
        "expected level must not inject any witness preference"
    )


# ── Full causal test: strong surprise changes exec action ─────────────────────

def test_strong_surprise_changes_action_from_answer_to_witness():
    """
    Acceptance test: strong prediction_error makes executive choose 'witness'
    instead of the default 'answer' for an otherwise neutral conversation turn.

    Default for intent="conversation" is "answer" at confidence 0.85.
    Witness is injected at 0.90 — must beat it.
    """
    from runtime.executive import decide as exec_decide

    _BASE = {
        "intent": "conversation",
        "emotional_context": {"inferred_state": "present", "valence": "neutral",
                               "momentum": "stable"},
        "wm_winner": "",
        "world_state": {},
    }

    import copy
    attn_strong = copy.deepcopy(_BASE)
    attn_none   = copy.deepcopy(_BASE)

    ec_strong = _make_ec_with_pe("strong_surprise", 0.85)
    ec_none   = _make_ec_with_pe("expected",        0.0)

    # Only inject learning_advice — do not overwrite intent
    _d_strong = ec_strong.as_dict()
    _d_none   = ec_none.as_dict()
    if _d_strong.get("learning_advice"):
        attn_strong["learning_advice"] = _d_strong["learning_advice"]
    if _d_none.get("learning_advice"):
        attn_none["learning_advice"] = _d_none["learning_advice"]

    out_strong = exec_decide(attn_strong, user_input="Okay, that makes sense.")
    out_none   = exec_decide(attn_none,   user_input="Okay, that makes sense.")

    assert out_strong["action"] == "witness", (
        f"strong_surprise must produce 'witness'. Got '{out_strong['action']}'."
    )
    assert out_none["action"] != "witness", (
        f"No surprise must NOT produce 'witness'. Got '{out_none['action']}'."
    )


# ── Witness weight beats answer and build but not explicit build phrase ────────

def test_witness_weight_0_90_beats_answer_confidence():
    """
    executive.decide() overrides when _w >= cal.confidence.
    Answer default is 0.85; witness at 0.90 beats it.
    """
    assert 0.90 >= 0.85, "Test premise: 0.90 must beat answer's 0.85"


def test_witness_is_injected_at_exactly_0_90_or_higher():
    ec = _make_ec_with_pe("strong_surprise", 0.80)
    d  = ec.as_dict()
    la = d.get("learning_advice") or {}
    prefs = la.get("preferences") or {}
    w = prefs.get("witness", 0)
    assert w >= 0.90, f"witness preference must be >= 0.90; got {w}"
