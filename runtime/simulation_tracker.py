"""
runtime/simulation_tracker.py — WO-SIMULATION-001

Tracks what eLo intended to do (pending_actions) vs what actually executed
(executed_actions) across turns within a session.

The distinction matters for honest introspection: eLo should know whether it
actually ran a tool vs only planned to, and whether something it stated was
drawn from real retrieval (ASSERTED) or from model-generated speculation
(SIMULATED).

Writers: server.py — calls mark_executed() after each successful action.
Readers: spine.py — reads pending/executed at CognitiveState assembly.
"""

from __future__ import annotations

# ── Session state ─────────────────────────────────────────────────────────────

_pending_actions:  list[str] = []   # actions planned but not yet confirmed complete
_executed_actions: list[str] = []   # actions completed this session (last 10)


# ── API ───────────────────────────────────────────────────────────────────────

def get_pending_actions() -> tuple[str, ...]:
    return tuple(_pending_actions)


def get_executed_actions() -> tuple[str, ...]:
    return tuple(_executed_actions[-10:])


def add_pending(action: str) -> None:
    """Register an intended action as pending."""
    if action and action not in _pending_actions:
        _pending_actions.append(action)


def mark_executed(action: str) -> None:
    """Move an action from pending to executed."""
    global _pending_actions, _executed_actions
    if action in _pending_actions:
        _pending_actions.remove(action)
    if action:
        _executed_actions = (_executed_actions + [action])[-10:]


def record_turn_actions(
    planned: tuple | list,
    *,
    auto_execute: bool = True,
) -> None:
    """
    Record the actions from this turn's plan.

    planned   — execution_order from CognitivePlan (e.g. ["tool", "llm", "voice"])
    auto_execute — if True, mark them as executed immediately (optimistic — assumes
                   the turn ran to completion). Set False for speculative/sim turns.
    """
    for act in (planned or []):
        if auto_execute:
            mark_executed(str(act))
        else:
            add_pending(str(act))


def reset() -> None:
    """Clear all state at session start."""
    global _pending_actions, _executed_actions
    _pending_actions  = []
    _executed_actions = []
