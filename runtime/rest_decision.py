"""
runtime/rest_decision.py — WO-TIRED-SIT-001 Part B: eLo decides whether to sit.

The dispatch is explicit about who owns this:

    "DO NOT issue a direct motion command from the ambient tick — eLo decides
     whether to sit, not the health battery. The inner event is a signal.
     Executive decides the action."

Why this is not in runtime/executive.py: that file is treated as frozen
(FREEZE_V1_LOCK; runtime/agency_engine.py states "does NOT modify
runtime/executive.py" as a standing constraint). And sit cannot become a tenth
CAL action — FREEZE_V1_LOCK §5 freezes the nine verbatim and they are all
verbal moves (answer, build, connect, celebrate, reflect, ground, challenge,
witness, silence). None of them is motor. A body decision needs its own
surface rather than a quietly widened frozen one.

Deliberately pure: inputs in, decision out, no state read, no state written,
no clock. Every refusal is named, so "eLo did not sit" is always answerable
with a reason instead of a shrug.

THRESHOLD — [BUILDER CHOICE, pending David/Board confirmation]
    tired      → notice, do not act.
    fatigued   → sit.
    exhausted  → sit.

PHYSICAL_EXPRESSIONS already draws this line in its own words: "tired" is
"Been at this a while. Legs know it." while "fatigued" is "Legs are heavy.
Time to sit." Noticing and acting are different, and a body that sits at the
first flicker of tiredness never actually walks anywhere. Same standing as
PHYSICAL_TICK_RATES, which are marked [ESTIMATE] for David to confirm after
runtime observation.
"""
from __future__ import annotations

from typing import Any, Mapping

# Bands that justify sitting. "tired" is deliberately absent — see module doc.
ACT_BANDS: frozenset[str] = frozenset({"fatigued", "exhausted"})

# Bands eLo can feel and speak about without acting on.
NOTICE_BANDS: frozenset[str] = frozenset({"tired"})

# Already at rest — nothing to decide. Mirrors ambient_engine._RESTING_MODES.
RESTING_MODES: frozenset[str] = frozenset({
    "calm", "sit", "sitting", "sleep", "sleeping", "dream",
    "lie_down", "lying_down",
})


def decide_rest(
    physical_state: str,
    *,
    motion: Mapping[str, Any] | None = None,
    speaking: bool = False,
    commanded: bool = False,
    dreaming: bool = False,
) -> dict | None:
    """
    Return a sit intent, or None with the reason available via explain().

    The returned dict is the intent shape blender_bridge.state_writer already
    understands — {"name": "sit"} is what derives sit_command for Unity — so
    this adds a decision, not a second command contract.
    """
    verdict, _ = _evaluate(physical_state, motion, speaking, commanded, dreaming)
    return verdict


def explain(
    physical_state: str,
    *,
    motion: Mapping[str, Any] | None = None,
    speaking: bool = False,
    commanded: bool = False,
    dreaming: bool = False,
) -> str:
    """Why eLo did or did not sit. Every path names itself."""
    _, reason = _evaluate(physical_state, motion, speaking, commanded, dreaming)
    return reason


def _evaluate(
    physical_state: str,
    motion: Mapping[str, Any] | None,
    speaking: bool,
    commanded: bool,
    dreaming: bool,
) -> tuple[dict | None, str]:
    band = str(physical_state or "").strip().lower()

    if band in NOTICE_BANDS:
        return None, "noticed_not_acted"
    if band not in ACT_BANDS:
        return None, "not_tired_enough"

    # Sleep=Dream owns the body while it runs; never interrupt it to sit.
    if dreaming:
        return None, "dreaming"
    # Mid-sentence is not the moment to change posture.
    if speaking:
        return None, "speaking"
    # David asked for something. His instruction outranks eLo's legs.
    if commanded:
        return None, "commanded"

    mode = str((motion or {}).get("mode", "")
               or (motion or {}).get("animation", "")).strip().lower()
    if mode in RESTING_MODES:
        return None, "already_resting"

    return (
        {"name": "sit", "issued_by": "elo", "reason": f"physical_{band}"},
        f"sitting:{band}",
    )
