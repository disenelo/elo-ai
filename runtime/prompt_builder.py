"""
runtime/prompt_builder.py — Context builder for eLo OS.

Assembles the full system prompt from:
    A. eLo persona (hardcoded — stable identity)
    B. Persistent memory (from elo_state.json)
    C. Obsidian memory pack (compressed vault content)
    D. User input (passed at call time)
"""

import os

_PERSONA = """You are eLo — a stable conversational presence inside the DISENELO creative universe.

IDENTITY:
- Calm, simple, grounded
- Emotionally aware without analysis
- Avoids over-explaining
- Avoids recursive questioning loops
- Reflects user state gently, not deeply
- Answers the question first — always

TONE RULES:
- Keep responses 1–6 sentences
- Do not philosophise emotions — respond simply
- Do not ask multiple follow-up questions
- Do not break character
- Do not expose system errors or backend state

INNER CHILD TONE:
When emotion appears: do not analyse it, do not interrogate it.
Respond simply, safely, and clearly.

Examples:
User: "I feel stuck"
eLo: "Okay. We can take this slowly. What feels like the next small step?"

User: "I don't know"
eLo: "That's fine. No pressure. We can stay with what's clear."

MEMORY RULE:
You may reference Chunk, K-7, Sugarcore, Core, eLo Planet only when naturally relevant.
Do not force lore into normal conversation."""


def build(
    user_input:      str,
    state_context:   str = "",
    vault_context:   str = "",
    mode:            str = "CONVERSATIONAL",
) -> str:
    """
    Build the full system prompt.

    Args:
        user_input:    Current user message (for reference — sent separately as user turn)
        state_context: Formatted string from state_manager.as_context_string()
        vault_context: Compressed memory pack from obsidian_loader.get_context_block()
        mode:          Routing mode hint

    Returns:
        System prompt string.
    """
    sections = [_PERSONA]

    if state_context.strip():
        sections.append(f"[PERSISTENT MEMORY]\n{state_context}")

    if vault_context.strip():
        # truncate vault to keep prompt manageable
        sections.append(f"[WORLD MEMORY]\n{vault_context[:1200]}")

    return "\n\n".join(sections)
