"""
runtime/spine/executive_extension.py — Executive-Delegated Capability Selection

Capability selection is an Executive decision: what eLo is permitted to use this turn.
runtime/executive.py is frozen (FREEZE_V1_LOCK). This module is the designated extension
point for Executive-layer decisions that cannot be placed in the frozen file.

All logic here is authorised by the Executive's output (exec_out / CognitivePlan fields).
Spine.py calls this after _executive_faculty() — not during assembly.

Architecture authority:
    engineering/work_packages/WP_G_IMPLEMENTATION_PLAN.md
    engineering/proofs/06_executive_proof.md
"""
from __future__ import annotations


def select_capabilities(
    plan_meaning: str,
    plan_is_system_turn: bool,
    capabilities: list[dict],
    intent_chain: list[str],
    conversation_action: str,
    tone: str,
) -> list[tuple[str, str]]:
    """
    Determine which capabilities eLo is authorised to use this turn.

    Delegated from Executive context: conversation_action and tone from the
    CognitivePlan inform which tools are appropriate. Capability candidates
    (from capability_faculty) are inputs, not the authority.

    Returns: list of (agent_name, query) tuples — empty if no capability needed.
    """
    # Silence-aware and ground turns: no external capabilities
    if tone == "SILENCE-AWARE" or conversation_action in ("silence", "ground"):
        return []

    if plan_is_system_turn:
        return []

    # Single-capability turns: first healthy candidate
    if capabilities:
        for cap in capabilities:
            if cap.get("health") not in ("OFFLINE", "AUTH_REQUIRED", "DISABLED"):
                return [(cap["id"], plan_meaning)]

    # Chain turns: honour 2-agent chain from intent_engine
    if len(intent_chain) == 2:
        return [(intent_chain[0], plan_meaning), (intent_chain[1], plan_meaning)]

    return []
