"""
backends/prompt_builder.py — Mode personality overlay layer.

Loads config/mode_overlays.json and injects the current mode's tone and style
into the system prompt sent to the backend.

This is a prompt-construction layer ONLY.
It does not:
    - change routing
    - change mode selection
    - change loop detection
    - change memory logic
    - modify any kernel file

It only appends a MODE STYLE RULES section to the system prompt,
after the kernel has already decided the mode.
"""

import json
import os

_CONFIG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "config", "mode_overlays.json"
)

_BASE_IDENTITY_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "config", "system_prompt.txt"
)

_overlays: dict = {}


def _load_overlays() -> dict:
    """Load mode overlays from config. Cached after first load."""
    global _overlays
    if not _overlays and os.path.exists(_CONFIG_PATH):
        with open(_CONFIG_PATH) as f:
            _overlays = json.load(f)
    return _overlays


def get_mode_overlay(mode: str) -> str:
    """
    Return the formatted MODE STYLE RULES block for the given mode.
    Returns empty string if mode is not in the config.
    """
    overlays = _load_overlays()
    entry    = overlays.get(mode, {})
    if not entry:
        return ""

    tone  = entry.get("tone",  "")
    style = entry.get("style", "")

    lines = ["MODE STYLE RULES:"]
    if tone:
        lines.append(f"Tone: {tone}")
    if style:
        lines.append(f"Style: {style}")

    return "\n".join(lines)


def build_system_prompt(
    mode:     str,
    memory:   dict = None,
    state:    dict = None,
    identity: dict = None,
) -> str:
    """
    Assemble the full system prompt for a backend call.

    Layer order (top to bottom):
        1. Base identity (config/system_prompt.txt)
        2. Mode style rules (config/mode_overlays.json)  ← this file's contribution
        3. Memory context  (tone, theme, project)
        4. Identity intent (from identity engine)

    The kernel has already decided the mode before this is called.
    This function only constructs what gets sent to the language model.

    Args:
        mode:     Routing mode from the kernel (DIRECT, CONVERSATIONAL, etc.)
        memory:   Memory influence signals dict
        state:    State snapshot dict
        identity: Identity engine snapshot dict

    Returns:
        Complete system prompt string.
    """
    parts = []

    # 1 — base identity
    if os.path.exists(_BASE_IDENTITY_PATH):
        with open(_BASE_IDENTITY_PATH) as f:
            base = f.read().strip()
        if base:
            parts.append(base)

    # 2 — mode style rules (the overlay)
    overlay = get_mode_overlay(mode)
    if overlay:
        parts.append(overlay)

    # 3 — memory context
    mem = memory or {}
    memory_lines = []
    if mem.get("tone_signal") and mem["tone_signal"] != "neutral":
        memory_lines.append(f"Tone pattern: {mem['tone_signal']}")
    if mem.get("returning_theme"):
        memory_lines.append(f"Recurring theme: {mem['returning_theme']}")
    if mem.get("project") and mem.get("project") != "elo_core":
        memory_lines.append(f"Active project: {mem['project']}")
    if memory_lines:
        parts.append("[MEMORY]\n" + "\n".join(memory_lines))

    # 4 — identity intent
    id_ = identity or {}
    if id_.get("intent"):
        parts.append(f"[INTENT] {id_['intent']}")

    return "\n\n".join(p for p in parts if p)
