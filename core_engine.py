"""
core_engine.py — eLo AI runtime orchestration.

Offline-only. No LLM API calls. No external dependencies.

Flow per turn:
    user input
        → detect mode (studio / adventure / companion)
        → resolve project namespace from registry
        → retrieve structured memory (identity / project / emotional / symbolic)
        → generate offline response (5-phase reasoning simulation)
        → store interaction tagged to project
        → update orb state
        → return response
"""

import json
import os
import re

from offline_engine import generate_offline_response
from memory_engine import (
    load_registry,
    resolve_project,
    build_memory_influence,
    store_interaction,
    load_long_term_memory,
)
from orb_engine import OrbEngine


# ── paths ──────────────────────────────────────────────────────────────────────

_DIR         = os.path.dirname(os.path.abspath(__file__))
_PROMPT_FILE = os.path.join(_DIR, "config", "system_prompt.txt")
_PERSONALITY = os.path.join(_DIR, "config", "personality.json")


# ── config loaders ─────────────────────────────────────────────────────────────

def _load_system_prompt() -> str:
    if os.path.exists(_PROMPT_FILE):
        with open(_PROMPT_FILE) as f:
            return f.read().strip()
    return "You are eLo AI — a creative companion intelligence."


def _load_personality() -> dict:
    if os.path.exists(_PERSONALITY):
        with open(_PERSONALITY) as f:
            return json.load(f)
    return {}


# ── mode detection ─────────────────────────────────────────────────────────────

_MODE_SIGNALS = {
    "studio": {
        r"\bstep by step\b": 2, r"\blet'?s build\b": 2, r"\bbreak it down\b": 2,
        r"\bhow do i\b": 2,     r"\bwhat'?s the plan\b": 2,
        r"\bbuild\b": 1, r"\bplan\b": 1, r"\bstructure\b": 1,
        r"\bsystem\b": 1,       r"\bdesign\b": 1, r"\bchunk\b": 1,
    },
    "adventure": {
        r"\bwhat if\b": 2, r"\bimagine if\b": 2, r"\btell me the story\b": 2,
        r"\bwhat does it mean\b": 2,
        r"\bstory\b": 1, r"\bworld\b": 1, r"\bmyth\b": 1,
        r"\bnarrative\b": 1,    r"\bjourney\b": 1, r"\bexplore\b": 1,
    },
    "companion": {
        r"\bi don'?t know\b": 2, r"\bi'?m not sure\b": 2, r"\bsomething feels\b": 2,
        r"\bhelp me understand\b": 2,
        r"\bfeel\b": 1, r"\bstuck\b": 1, r"\bwrong\b": 1,
        r"\bconfused\b": 1,     r"\bk-7\b": 1, r"\bsugarcore\b": 1,
    },
}


def detect_mode(text: str) -> str:
    text_lower = text.lower()
    scores = {mode: 0 for mode in _MODE_SIGNALS}
    for mode, signals in _MODE_SIGNALS.items():
        for pattern, weight in signals.items():
            if re.search(pattern, text_lower):
                scores[mode] += weight
    best = max(scores, key=lambda m: scores[m])
    return best if scores[best] > 0 else "companion"


# ── mode overlays (injected into offline engine context) ───────────────────────

_OVERLAYS = {
    "studio": (
        "MODE: STUDIO — building. Lead with the next real step. "
        "Structure is the creative act. Chunk logic: reassemble fragments into a new shape. "
        "Be direct. Do not philosophise. Build."
    ),
    "companion": (
        "MODE: COMPANION — thinking together. "
        "Listen before responding. Ask one good question. "
        "Stay in contradiction if needed. K-7 logic: respond through behaviour, not declaration."
    ),
    "adventure": (
        "MODE: ADVENTURE — world logic. Expand before naming. Think in systems that become stories. "
        "Follow symbols. eLo Universe rules apply. Ask 'what does this become?' not 'what is this?'"
    ),
}


# ── main runtime ───────────────────────────────────────────────────────────────

class CoreEngine:

    def __init__(self, orb: OrbEngine = None):
        self.orb          = orb or OrbEngine()
        self._registry    = load_registry()
        self._personality = _load_personality()
        self._active_mode = "companion"

    def reload(self):
        """Re-read config from disk — call after editing files or exporting memory."""
        self._registry    = load_registry()
        self._personality = _load_personality()

    def set_mode(self, mode: str):
        if mode in _OVERLAYS:
            self._active_mode = mode
            print(f"  [mode: {mode}]")

    def turn(self, user_input: str, debug: bool = False) -> str:
        """
        Process one user turn end-to-end.

        Args:
            user_input: Raw text from the user.
            debug:      If True, prints the internal reasoning summary.

        Returns:
            eLo's response as a plain string.
        """
        # sense
        self.orb.listen()

        # mode: respect explicit set_mode; otherwise detect from input
        mode    = self._active_mode
        project = resolve_project(user_input, self._registry)

        # build active memory influence — derived signals, not just raw records
        self.orb.think()
        memory = build_memory_influence(user_input, project_hint=project)

        # generate offline response
        if debug:
            response, reasoning = generate_offline_response(
                user_input, memory, mode, debug=True
            )
            _print_reasoning(reasoning)
        else:
            response = generate_offline_response(user_input, memory, mode)

        # store + wrap up
        self.orb.insight()
        store_interaction(user_input, response, mode, project_tag=project)
        self.orb.idle()

        return response


def _print_reasoning(reasoning: dict):
    """Print internal phase summary for debug mode."""
    p1 = reasoning.get("phase_1_interpretation", {})
    p2 = reasoning.get("phase_2_memory", {})
    p3 = reasoning.get("phase_3_identity", {})
    print(f"\n  [debug p1] type={p1.get('input_type')} emotion={p1.get('emotion')} "
          f"concepts={p1.get('concepts')} entities={p1.get('entities')}")
    print(f"  [debug p2] tone={p2.get('memory_tone')} blended={p2.get('blended_emotion')} "
          f"recurring={p2.get('recurring_concepts')} "
          f"theme={p2.get('returning_theme')!r}")
    print(f"  [debug p3] mode={p3.get('mode')} contradiction={p3.get('is_contradiction')}")
