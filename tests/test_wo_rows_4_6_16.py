"""
tests/test_wo_rows_4_6_16.py — Rows 4 SEE · 6 ATTEND · 16 AFFORD.

Proof (card 0008 / card 0012):
  Blank plan.world ⇒ the chosen action or tone DIFFERS from state present.
  If it can't differ, the inputs aren't reaching the decision.

The Executive uses new inputs to choose differently among the existing nine
CAL actions. No new actions, no tone changes, no priority reordering.

AT-4616-1: world_state.available=False → build/connect/celebrate → witness (quieter)
AT-4616-2: world_state absent → same input → build stays build (no false override)
AT-4616-3: blank plan.world vs world_state.available=False → decision differs (main proof)
AT-4616-4: wm_winner=build → reflect promoted to build (Row 6 ATTEND foregrounding)
AT-4616-5: wm_winner absent → reflect stays reflect (no fabricated foregrounding)
AT-4616-6: loop protection still wins over all world-state overrides (no regression)
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from runtime.executive import decide


def _attn(intent="conversation", valence="neutral", momentum="stable",
          world_state=None, wm_winner="", surface_affordances=None):
    """Build a minimal attention_model dict for testing."""
    a = {
        "intent": intent,
        "emotional_context": {
            "inferred_state": "present",
            "valence":        valence,
            "momentum":       momentum,
            "tension":        0.3,
            "energy":         0.5,
        },
        "wm_winner": wm_winner,
    }
    if world_state is not None:
        a["world_state"] = world_state
    if surface_affordances is not None:
        a["surface_affordances"] = surface_affordances
    return a


# ── AT-4616-1: user unavailable → build becomes witness ───────────────────────

def test_world_unavailable_shifts_build_to_witness():
    """Row 4 SEE / 16 AFFORD: user unavailable → quieter presence."""
    attn = _attn(
        intent="creation",     # would normally → build
        valence="positive_low",
        world_state={"available": False, "active_app": "Final Cut", "surface": "desktop"},
    )
    result = decide(attn, user_input="let's build something new")
    assert result["action"] == "witness", (
        f"world_state.available=False + 'build' input must yield 'witness', got {result['action']!r}"
    )


# ── AT-4616-2: world absent → build stays build (no false override) ───────────

def test_world_absent_build_stays_build():
    """When world_state is absent, normal action selection is unaffected."""
    attn = _attn(intent="creation", valence="positive_low")
    result = decide(attn, user_input="let's build something new")
    assert result["action"] == "build", (
        f"Without world_state, 'build' input must remain 'build', got {result['action']!r}"
    )


# ── AT-4616-3: blank plan.world ⇒ decision DIFFERS (main proof) ──────────────

def test_blank_world_vs_unavailable_world_differs():
    """
    Row 4 SEE · 16 AFFORD core proof.
    Same user input. Same intent/valence/momentum.
    World absent → one action. World unavailable → a different action.
    If these are equal, the inputs are not reaching the decision.
    """
    base_input = "let's build something new"
    base_attn  = _attn(intent="creation", valence="positive_low")

    result_no_world  = decide(base_attn, user_input=base_input)
    result_with_world = decide(
        _attn(
            intent="creation",
            valence="positive_low",
            world_state={"available": False, "active_app": "Xcode", "surface": "desktop"},
        ),
        user_input=base_input,
    )

    assert result_no_world["action"] != result_with_world["action"], (
        f"Blank plan.world must produce a DIFFERENT action than world_state.available=False.\n"
        f"No world: {result_no_world['action']!r} | With unavailable world: "
        f"{result_with_world['action']!r}\n"
        "If these are equal, the seam is not open and rows 4/16 cannot be VERIFIED."
    )


# ── AT-4616-4: wm_winner=build → reflect promoted to build (Row 6 ATTEND) ────

def test_wm_winner_build_promotes_reflect_to_build():
    """Row 6 ATTEND: WM competition foregrounded a build thread — lean into it."""
    attn = _attn(
        intent="emotional",   # would normally → reflect (emotional + neutral)
        valence="neutral",
        wm_winner="build",
    )
    result = decide(attn, user_input="I was thinking about this")
    assert result["action"] == "build", (
        f"wm_winner=build should promote reflect → build. Got {result['action']!r}"
    )


# ── AT-4616-5: wm_winner absent → reflect stays reflect ──────────────────────

def test_wm_winner_absent_reflect_stays():
    """Without wm_winner, reflect stays reflect — no fabricated foregrounding."""
    attn = _attn(intent="emotional", valence="neutral", wm_winner="")
    result = decide(attn, user_input="I was thinking about this")
    assert result["action"] == "reflect", (
        f"Without wm_winner, emotional+neutral must remain reflect, got {result['action']!r}"
    )


# ── AT-4616-6: loop protection still wins (regression guard) ─────────────────

def test_loop_protection_overrides_world_state():
    """loop_detected=True must still win over all world-state logic."""
    attn = _attn(
        intent="creation",
        world_state={"available": False},
        wm_winner="build",
    )
    result = decide(attn, loop_detected=True, user_input="let's build!")
    assert result["action"] == "ground", (
        f"Loop protection must override world-state — always. Got {result['action']!r}"
    )
    assert result.get("stability") is True, "Loop protection must set stability=True"
