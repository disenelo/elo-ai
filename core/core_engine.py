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

from core.kernel         import decide_response, reset_session
from core.behavior_engine import generate_offline_response
from core.memory_engine import (
    load_registry,
    resolve_project,
    build_memory_influence,
    store_interaction,
    load_long_term_memory,
)
from core.state_engine    import StateEngine
from core.identity_engine import decide as identity_decide, explain as identity_explain
from plugins.hardware.orb_engine import OrbEngine


# ── paths ──────────────────────────────────────────────────────────────────────

_DIR         = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # project root
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
        self.state_engine = StateEngine()
        reset_session()   # clear kernel loop state at session start

    def reload(self):
        """Re-read config from disk — call after editing files or exporting memory."""
        self._registry    = load_registry()
        self._personality = _load_personality()

    def set_mode(self, mode: str):
        if mode in _OVERLAYS:
            self._active_mode = mode
            self.state_engine.force_state(mode)
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

        # update conversational state (natural transition from input signals)
        current_state, transitioned = self.state_engine.update(user_input)
        state_hint = self.state_engine.get_behavioral_hint()

        # build active memory influence — derived signals, not just raw records
        self.orb.think()
        memory = build_memory_influence(user_input, project_hint=project)

        # ── identity decision (highest level — runs before emotion) ──
        identity = identity_decide(
            user_input=user_input,
            state=current_state,
            memory=memory,
            project=project,
        )

        # inject all signals into memory dict for behavior_engine to read
        memory["state"]            = current_state
        memory["state_tone"]       = state_hint["tone"]
        memory["response_length"]  = state_hint["response_length"]
        memory["imagination_level"]= state_hint["imagination_level"]
        memory["project_focus"]    = state_hint["project_focus"]
        memory["elo_voice_hint"]   = state_hint["elo_voice_hint"]
        # identity signals — response_bias is the most actionable
        memory["identity_values"]    = identity["values"]
        memory["identity_perspective"]= identity["perspective"]
        memory["identity_intent"]    = identity["intent"]
        memory["identity_bias"]      = identity["response_bias"]

        # ── kernel: single decision pipeline ──
        # decide_response() runs: classify → assemble → route → generate → filter
        response, kernel_meta = decide_response(user_input, memory)

        if debug:
            _print_reasoning(kernel_meta, current_state, transitioned, state_hint, identity)

        # store + wrap up
        self.orb.insight()
        store_interaction(user_input, response, mode, project_tag=project)
        self.orb.idle()

        return response


def _print_reasoning(kernel_meta: dict, state: str, transitioned: bool, state_hint: dict, identity: dict = None):
    """Print kernel decision summary for debug mode."""
    ic   = kernel_meta.get("input_class", {})
    mode = kernel_meta.get("mode", "?")
    loop = kernel_meta.get("loop_detected", False)
    transition_marker = " ← TRANSITION" if transitioned else ""

    print(f"\n  [kernel]   mode={mode}{' ← LOOP BREAK' if loop else ''}")
    print(f"  [classify] factual={ic.get('is_factual')} emotional={ic.get('is_emotional')} "
          f"creative={ic.get('is_creative')} distorted={ic.get('is_distorted')} "
          f"contradiction={ic.get('is_contradiction')} entities={ic.get('entities')}")
    print(f"  [state]    {state}{transition_marker} | "
          f"length={state_hint['response_length']} "
          f"imagination={state_hint['imagination_level']}")
    if identity:
        print(f"  [identity] intent={identity['intent']} bias={identity['response_bias']}")
