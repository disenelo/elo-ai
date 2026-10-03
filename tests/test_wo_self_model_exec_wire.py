"""
tests/test_wo_self_model_exec_wire.py — WO-SELF-MODEL-EXEC-WIRE-001

Acceptance: EloSelfState.curiosity=0.9 produces a different action distribution
than curiosity=0.1 for the same input. Test verifies action changes, not just
prompt text changes.

Also verifies:
- learning_advice forwarding bug fix: learning_advice in attention dict is
  preserved through as_dict()
- mood=low downweights create/connect
- ec_self_state appears in as_dict() output for transparency
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class _FakeAttn:
    wm_winner: str = ""
    learning_advice: dict | None = None

    def get(self, key, default=None):
        if key == "wm_winner":
            return self.wm_winner
        if key == "learning_advice":
            return self.learning_advice
        return {}.get(key, default)


def _make_ec(curiosity: float, mood: float = 0.55,
             wm_winner: str = "",
             existing_la: dict | None = None) -> "ExecutiveContext":
    from runtime.executive_context import ExecutiveContext
    return ExecutiveContext(
        intent="conversation",
        self_state={"curiosity": curiosity, "mood": mood, "lifecycle_state": "awake"},
        attention={"wm_winner": wm_winner, "learning_advice": existing_la},
    )


# ── ec_self_state is visible in output ────────────────────────────────────────

def test_ec_self_state_in_as_dict():
    ec = _make_ec(curiosity=0.5)
    d = ec.as_dict()
    assert "ec_self_state" in d
    assert d["ec_self_state"]["curiosity"] == 0.5


# ── curiosity >= 0.7 injects a bias ───────────────────────────────────────────

def test_high_curiosity_injects_challenge_connect_bias():
    ec = _make_ec(curiosity=0.9)
    d = ec.as_dict()
    la = d.get("learning_advice") or {}
    prefs = la.get("preferences") or {}
    assert prefs.get("challenge", 0) > 0, "challenge bias expected when curiosity=0.9"
    assert prefs.get("connect", 0)  > 0, "connect bias expected when curiosity=0.9"


def test_low_curiosity_no_bias():
    ec = _make_ec(curiosity=0.1)
    d = ec.as_dict()
    la = d.get("learning_advice") or {}
    prefs = la.get("preferences") or {}
    assert prefs.get("challenge", 0) == 0, "no challenge bias when curiosity=0.1"
    assert prefs.get("connect",   0) == 0, "no connect bias when curiosity=0.1"


def test_different_action_preference_for_high_vs_low_curiosity():
    """
    The acceptance test: different learning_advice yields different exec preference.

    Uses intent="recall" with a neutral input. The default path returns "reflect" at
    confidence 0.5 — deliberately below the curiosity bias weight (0.72 at curiosity=0.9)
    so the bias can shift the action, while curiosity=0.1 produces no bias and stays
    at the default. This is the minimal scenario that proves causal influence.
    """
    from runtime.executive import decide as exec_decide
    # intent="recall" → default path → "reflect" at 0.5.  No phrase in the input
    # triggers a higher-confidence override, so the bias (or its absence) decides.
    _BASE_ATTN = {
        "intent": "recall",
        "emotional_context": {"inferred_state": "present", "valence": "neutral",
                               "momentum": "stable"},
        "wm_winner": "",
        "world_state": {},
    }
    import copy
    attn_high = copy.deepcopy(_BASE_ATTN)
    attn_low  = copy.deepcopy(_BASE_ATTN)

    ec_high = _make_ec(curiosity=0.9)
    ec_low  = _make_ec(curiosity=0.1)

    # Only inject learning_advice from the ExecutiveContext — do NOT let as_dict()
    # overwrite intent/emotional_context (those are the controlled variables here).
    _d_high = ec_high.as_dict()
    _d_low  = ec_low.as_dict()
    if _d_high.get("learning_advice"):
        attn_high["learning_advice"] = _d_high["learning_advice"]
    if _d_low.get("learning_advice"):
        attn_low["learning_advice"] = _d_low["learning_advice"]

    out_high = exec_decide(attn_high, user_input="Some neutral statement.")
    out_low  = exec_decide(attn_low,  user_input="Some neutral statement.")

    # Both decisions are valid CAL actions; they must differ.
    assert out_high["action"] != out_low["action"], (
        f"Expected high-curiosity action ({out_high['action']}) to differ from "
        f"low-curiosity action ({out_low['action']})"
    )


# ── learning_advice forwarding bug fix ────────────────────────────────────────

def test_existing_learning_advice_is_preserved():
    existing_la = {"preferences": {"build": 0.8}, "confidence": 0.7, "rationale": "test"}
    ec = _make_ec(curiosity=0.1, existing_la=existing_la)
    d = ec.as_dict()
    la = d.get("learning_advice") or {}
    assert la.get("preferences", {}).get("build", 0) == 0.8, (
        "existing learning_advice.preferences.build must survive as_dict()"
    )


def test_curiosity_bias_does_not_override_stronger_lesson_pref():
    """Lesson evidence with weight >= BIAS_W must not be lowered."""
    existing_la = {
        "preferences": {"challenge": 0.90},  # strong lesson preference for challenge
        "confidence": 0.8,
        "rationale": "lesson",
    }
    ec = _make_ec(curiosity=0.9, existing_la=existing_la)
    d = ec.as_dict()
    la = d.get("learning_advice") or {}
    assert la["preferences"]["challenge"] == 0.90, (
        "strong lesson pref (0.90) must not be downgraded by curiosity bias"
    )


# ── mood=low downweights create/connect ───────────────────────────────────────

def test_low_mood_downweights_create_connect():
    existing_la = {
        "preferences": {"create": 0.75, "connect": 0.70},
        "confidence": 0.6,
        "rationale": "lesson",
    }
    ec = _make_ec(curiosity=0.1, mood=0.25, existing_la=existing_la)
    d = ec.as_dict()
    la = d.get("learning_advice") or {}
    prefs = la.get("preferences") or {}
    assert prefs.get("create",  1.0) < 0.75, "create should be downweighted when mood < 0.35"
    assert prefs.get("connect", 1.0) < 0.70, "connect should be downweighted when mood < 0.35"


# ── curiosity bias is suppressed when wm_winner=creation/build ────────────────

def test_bias_suppressed_when_wm_winner_is_creation():
    ec = _make_ec(curiosity=0.95, wm_winner="creation")
    d = ec.as_dict()
    la = d.get("learning_advice") or {}
    prefs = la.get("preferences") or {}
    assert prefs.get("challenge", 0) == 0, (
        "curiosity bias must not fire when wm_winner=creation"
    )
