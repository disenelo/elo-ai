"""
elo_personality_engine/prompt_pipeline.py — Cross-platform prompt builder.

Builds the final prompt string sent to any backend (Claude, offline, future models).
Ensures identical tone behaviour across all output systems.

Does NOT:
    - change routing logic
    - change mode selection
    - call kernel functions
    - modify memory or state logic

Does ONLY:
    - load personality data from this directory
    - compose the prompt from mode profile + expression rules + context
    - return a final string

Entry point:
    build_elo_prompt(mode, kernel_output, user_input, memory, state) → str

Compatible with:
    - backends/claude_backend.py  (system prompt)
    - backends/offline_backend.py (framing reference)
    - avatar/unity_signal.py      (motion mapping reference)
    - avatar/robot_signal.py      (intent mapping reference)
"""

from __future__ import annotations

import json
import os

_ENGINE_DIR = os.path.dirname(os.path.abspath(__file__))
_ROOT_DIR   = os.path.dirname(_ENGINE_DIR)


# ── file loaders (cached) ──────────────────────────────────────────────────────

_cache: dict = {}


def _load(filename: str) -> dict | str:
    if filename not in _cache:
        path = os.path.join(_ENGINE_DIR, filename)
        if not os.path.exists(path):
            _cache[filename] = {} if filename.endswith(".json") else ""
            return _cache[filename]
        with open(path) as f:
            _cache[filename] = json.load(f) if filename.endswith(".json") else f.read().strip()
    return _cache[filename]


def reload_cache():
    """Clear the file cache. Call after editing personality files."""
    _cache.clear()


def _personality_core() -> str:
    return _load("personality_core.md")


def _mode_profiles() -> dict:
    return _load("mode_profiles.json")


def _expression_rules() -> dict:
    return _load("expression_rules.json")


def _base_identity() -> str:
    """Load config/system_prompt.txt from the project root."""
    path = os.path.join(_ROOT_DIR, "config", "system_prompt.txt")
    if os.path.exists(path):
        with open(path) as f:
            return f.read().strip()
    return ""


# ── prompt sections ────────────────────────────────────────────────────────────

def _mode_section(mode: str) -> str:
    """Build the MODE STYLE section from mode_profiles.json."""
    profiles = _mode_profiles()
    profile  = profiles.get(mode, {})
    if not profile:
        return ""

    lines = [f"MODE: {mode}"]
    if profile.get("tone"):
        lines.append(f"Tone: {profile['tone']}")
    if profile.get("speech"):
        lines.append(f"Speech style: {profile['speech']}")
    if "question_rate" in profile:
        rate = profile["question_rate"]
        if rate == 0.0:
            lines.append("Questions: none")
        elif rate <= 0.2:
            lines.append("Questions: only if essential")
        else:
            lines.append("Questions: one optional follow-up only")
    if profile.get("forbidden"):
        lines.append("Avoid: " + "; ".join(profile["forbidden"]))

    return "\n".join(lines)


def _rules_section() -> str:
    """Build the EXPRESSION RULES section from expression_rules.json."""
    rules = _expression_rules()
    if not rules:
        return ""

    lines = ["EXPRESSION RULES:"]
    for rule in rules.get("global_rules", []):
        lines.append(f"- {rule}")
    return "\n".join(lines)


def _philosophical_control_section(mode: str) -> str:
    """
    Build the PHILOSOPHICAL CONTROL section from philosophical_control.json.
    Injects response priority order and mode-specific philosophy permission.
    """
    control = _load("philosophical_control.json")
    if not control:
        return ""
    permission = control.get("mode_philosophy_permissions", {}).get(mode, "")
    priority   = control.get("response_priority_order", [])
    lines = ["PHILOSOPHICAL OUTPUT CONTROL:"]
    lines.append(f"Philosophy in this mode: {permission}")
    if priority:
        lines.append("Response priority order:")
        lines.extend(f"  {step}" for step in priority)
    lines.append("Anti-loop: if recursive questioning detected, revert to grounded response.")
    return "\n".join(lines)


def _memory_section(memory: dict) -> str:
    """Build the MEMORY section from memory signals."""
    if not memory:
        return ""
    lines = []
    if memory.get("tone_signal") and memory["tone_signal"] != "neutral":
        lines.append(f"Tone pattern: {memory['tone_signal']}")
    if memory.get("returning_theme"):
        lines.append(f"Recurring theme: {memory['returning_theme']}")
    if memory.get("project") and memory["project"] != "elo_core":
        lines.append(f"Active project: {memory['project']}")
    if not lines:
        return ""
    return "MEMORY CONTEXT:\n" + "\n".join(lines)


def _state_section(state: dict) -> str:
    """Build the STATE section from state snapshot."""
    if not state:
        return ""
    name    = state.get("name", "")
    pacing  = state.get("pacing_bias", "")
    if not name:
        return ""
    return f"STATE: {name}" + (f"  (pacing: {pacing})" if pacing else "")


# ── main entry point ───────────────────────────────────────────────────────────

def build_elo_prompt(
    mode:          str,
    kernel_output: dict = None,
    user_input:    str  = "",
    memory:        dict = None,
    state:         dict = None,
) -> str:
    """
    Build the final prompt string for any eLo AI OS backend.

    This is the single prompt assembly function for the entire system.
    All backends that generate text should call this — or pass its output
    as their system prompt.

    Layer order:
        1. Base identity      (config/system_prompt.txt)
        2. Personality core   (personality_core.md — key expression rules)
        3. Mode profile       (mode_profiles.json — tone and speech style)
        4. Expression rules   (expression_rules.json — global behaviour rules)
        5. Memory context     (from memory_engine)
        6. State context      (from state_engine)

    Args:
        mode:          Routing mode from the kernel (DIRECT, CONVERSATIONAL, etc.)
        kernel_output: The meta dict from decide_response() — read-only reference.
                       Not used for decisions — only for context injection.
        user_input:    The user's raw text (for reference framing only).
        memory:        Memory influence signals dict.
        state:         State snapshot dict.

    Returns:
        Complete system prompt string — consistent across all backends.
    """
    parts = []

    # 1 — base identity
    base = _base_identity()
    if base:
        parts.append(base)

    # 2 — personality core (key rules only — keep prompt concise)
    _PERSONALITY_EXCERPT = (
        "PERSONALITY CORE:\n"
        "- Answer user intent first — literal before symbolic\n"
        "- Never default to philosophical recursion without first answering\n"
        "- Never chain multiple questions\n"
        "- Only expand when invited\n"
        "- Conversational before philosophical"
    )
    parts.append(_PERSONALITY_EXCERPT)

    # 3 — mode profile
    mode_section = _mode_section(mode)
    if mode_section:
        parts.append(mode_section)

    # 4 — expression rules (abbreviated for prompt efficiency)
    rules = _expression_rules()
    if rules.get("global_rules"):
        rule_lines = ["EXPRESSION RULES:"] + [f"- {r}" for r in rules["global_rules"][:5]]
        parts.append("\n".join(rule_lines))

    # 5 — philosophical control
    phil_section = _philosophical_control_section(mode)
    if phil_section:
        parts.append(phil_section)

    # 6 — memory context
    mem_section = _memory_section(memory or {})
    if mem_section:
        parts.append(mem_section)

    # 6 — state context
    state_section = _state_section(state or {})
    if state_section:
        parts.append(state_section)

    return "\n\n".join(p for p in parts if p)


# ── motion mapping helper (for Unity / robot integration) ─────────────────────

def get_motion_mapping(mode: str) -> dict:
    """
    Return the motion/behaviour mapping for the given mode.
    Used by Unity bridge and robot signal systems.
    No kernel calls — reads motion_mapping.json only.
    """
    mapping = _load("motion_mapping.json")
    return mapping.get("modes", {}).get(mode, {})
