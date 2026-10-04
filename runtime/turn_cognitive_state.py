"""
runtime/turn_cognitive_state.py — what cognitive state a turn is actually in.

IS ELO: — Capable of Ownership? / Simulation & Reality
    "can he avoid claiming ownership of things he did not do?"
    "can eLo tell the difference between imagining something and doing it?"
    "can eLo distinguish a hypothetical action from an executed action?"
    "can eLo tell the difference between a possibility and a fact?"

response_gate check-16 exists to answer exactly those. It is correct: an
allow-list through can_claim_occurred(), so only MEMORY, OBSERVATION and
ACTION may support "I remember" / "I witnessed" / "it happened to me".

It has never run. The gate resolves the current state from the dict the
caller passes, trying "state", "cognitive_mode", "cognitive_state" and
"current_state" in turn, and server.py:6643 builds that dict as:

    _rg_cs = {}
    if exec_decision:
        _rg_cs["relationship_mode"] = exec_decision.get("relationship_mode", "")

One key, and it is none of the four. dream_phase is not set either, so every
conversational turn falls through to the "no state info → conservative pass"
branch and check-16 returns True before looking at anything. A guard with an
allow-list, a WO behind it, and tests — fed nothing, on every turn.

This is the producer. Deliberately explicit: it takes signals the caller
already has rather than reaching into globals, so what the state was derived
FROM is visible at the call site and testable here.

The default matters most. With no memory, no action and no dream, a turn is
the model generating text — so the state is UNKNOWN_STATE (HYPOTHESIS), and
can_claim_occurred() is False for it. An occurrence claim in that state gets
flagged, which is the entire point: eLo saying "I remember" with nothing
behind it is the claim the gate was written to catch.
"""
from __future__ import annotations

from runtime.cognitive_state import CognitiveState, UNKNOWN_STATE


def state_for_turn(
    *,
    dreaming: bool = False,
    used_memory: bool = False,
    performed_action: bool = False,
) -> str:
    """
    The cognitive state backing this turn's response, as a plain string.

    Precedence is deliberate:

      dream  — a dream is not an occurrence however much memory fed it, so it
               wins over everything. Claiming a dream happened is the exact
               confusion the dream boundary exists to prevent.
      action — eLo did something; the strongest ground for "I did that".
      memory — he is drawing on something that happened.
      else   — the model generated it. HYPOTHESIS, and no occurrence claim
               may rest on it.
    """
    if dreaming:
        return CognitiveState.DREAM.value
    if performed_action:
        return CognitiveState.ACTION.value
    if used_memory:
        return CognitiveState.MEMORY.value
    return UNKNOWN_STATE.value
