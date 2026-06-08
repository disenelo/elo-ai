"""
core/core_engine.py — eLo AI session orchestrator.

Manages session state and I/O. Passes all inputs to the kernel.

Responsibilities:
    - StateEngine (session-scoped machine — tracks conversation state)
    - memory_engine calls (file I/O — retrieves and stores interactions)
    - OrbEngine (hardware/simulation output)
    - Active mode for the session (/mode commands)

What it does NOT do:
    - Call emotion_engine  (kernel owns this)
    - Call identity_engine (kernel owns this)
    - Make routing decisions (kernel owns this)

Flow per turn:
    update state → build memory → pass to kernel → store result
"""

import json
import os
import re

from core.kernel      import decide_response, reset_session, set_debug
from core.memory_engine import (
    load_registry,
    resolve_project,
    build_memory_influence,
    store_interaction,
)
from core.state_engine import StateEngine
from plugins.hardware.orb_engine import OrbEngine


# ── paths ──────────────────────────────────────────────────────────────────────

_DIR         = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
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


# ── mode vocabulary ────────────────────────────────────────────────────────────

_VALID_MODES = ("studio", "companion", "adventure")

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


# ── session runtime ────────────────────────────────────────────────────────────

class CoreEngine:
    """
    Session runtime. Manages state, memory I/O, and orb.
    Delegates all response decisions to the kernel.
    """

    def __init__(self, orb: OrbEngine = None):
        self.orb          = orb or OrbEngine()
        self._registry    = load_registry()
        self._personality = _load_personality()
        self._active_mode = "companion"
        self.state_engine = StateEngine()
        reset_session()

    def reload(self):
        """Re-read config and registry from disk."""
        self._registry    = load_registry()
        self._personality = _load_personality()

    def set_mode(self, mode: str):
        if mode in _VALID_MODES:
            self._active_mode = mode
            self.state_engine.force_state(mode)
            print(f"  [mode: {mode}]")

    def turn(self, user_input: str, debug: bool = False) -> str:
        """
        Process one user turn.

        core_engine's job here:
            1. Update state machine (session-scoped)
            2. Build memory influence (file I/O)
            3. Assemble a clean context dict
            4. Call kernel.decide_response() — all decisions happen there
            5. Store the interaction

        Returns:
            eLo's response string.
        """
        self.orb.listen()

        # resolve project from input
        project = resolve_project(user_input, self._registry)

        # 1 — state update (session machine — must run before memory)
        current_state, transitioned = self.state_engine.update(user_input)
        state_influence = self.state_engine.get_style_influence()

        # 2 — memory (file I/O — builds influence signals from stored interactions)
        self.orb.think()
        memory = build_memory_influence(user_input, project_hint=project)

        # 3 — clean context for kernel
        # kernel receives: memory signals + state style weights + project + mode
        # kernel handles: emotion engine + identity engine internally
        context = {
            **memory,
            "state":           current_state,
            "state_tone_bias": state_influence["tone_bias"],
            "state_weight":    state_influence["style_weight"],
            "state_pacing":    state_influence["pacing_bias"],
            "project":         project,
            "mode":            self._active_mode,
        }

        # 4 — kernel: single decision pipeline
        if debug:
            set_debug(True)
        response, meta = decide_response(user_input, context)
        if debug:
            set_debug(False)
            _print_kernel_meta(meta, current_state, transitioned)

        # 5 — store
        self.orb.insight()
        store_interaction(user_input, response, meta["mode"], project_tag=project)
        self.orb.idle()

        return response


def _print_kernel_meta(meta: dict, state: str, transitioned: bool):
    """Print kernel decision summary (used when debug=True)."""
    ic     = meta.get("input_class", {})
    mode   = meta.get("mode", "?")
    loop   = meta.get("loop_detected", False)
    reason = meta.get("loop_reason", "")
    marker = " ← TRANSITION" if transitioned else ""

    print(f"\n  [kernel]   mode={mode}{' ← LOOP BREAK: ' + reason if loop else ''}")
    print(f"  [classify] type={ic.get('_resolved_type', '?')} "
          f"factual={ic.get('is_factual')} creative={ic.get('is_creative')} "
          f"distorted={ic.get('is_distorted')} entities={ic.get('entities')}")
    print(f"  [state]    {state}{marker}")
