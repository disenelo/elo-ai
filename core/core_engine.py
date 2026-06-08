"""
core/core_engine.py — eLo AI context builder + session orchestrator.

3-layer architecture:

    Layer 1 — Context Builder  (this file: prepare_context)
    Layer 2 — Kernel           (kernel.py: decide_response)
    Layer 3 — Engines          (passive providers: emotion, identity, state, memory)

Rules:
    - prepare_context() is the ONLY place engine calls happen
    - turn() calls prepare_context(), then passes the bus to the kernel
    - kernel.decide_response() receives raw_context only — calls nothing
    - no engine output is mutable after prepare_context() returns
"""

import json
import os
import re

from core.kernel             import decide_response, reset_session, set_debug
from core.session_persistence import save_session, restore_session, session_info
from core.state_bus   import (StateBus, IdentitySnapshot, StateSnapshot,
                               EmotionSnapshot, MemorySnapshot)
from core.memory_engine import (
    load_registry,
    resolve_project,
    build_memory_influence,
    store_interaction,
)
from core.state_engine    import StateEngine
from core.emotion_engine  import get_tone_modifier
from core.identity_engine import decide as identity_decide
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
    Layer 1 — Context Builder + session manager.

    Responsibilities:
        - StateEngine (session-scoped — persists across turns)
        - OrbEngine (hardware output)
        - prepare_context() — calls all engines, builds StateBus
        - turn() — orchestrates context → kernel → store

    Does NOT:
        - Make routing decisions (kernel does)
        - Call emotion or identity engines outside prepare_context()
        - Mutate engine outputs after they are produced
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

    # ── session persistence ────────────────────────────────────────────────────

    def save_session(self, path: str = None) -> str:
        """
        Save current session state to disk (state engine + active mode).
        Memory interactions are persisted automatically by memory_engine.
        Returns the path written to.
        """
        return save_session(self, path)

    def restore_session(self, path: str = None) -> bool:
        """
        Restore session state from disk into this engine instance.
        Call after __init__ to continue a previous session.
        Returns True if a save file was found and applied.
        """
        return restore_session(self, path)

    @staticmethod
    def session_info(path: str = None) -> dict:
        """Return metadata about the saved session without loading it."""
        return session_info(path)

    def set_mode(self, mode: str):
        if mode in _VALID_MODES:
            self._active_mode = mode
            self.state_engine.force_state(mode)
            print(f"  [mode: {mode}]")

    def prepare_context(self, user_input: str) -> StateBus:
        """
        Layer 1 — Context Builder.

        Calls all four engines and assembles one immutable StateBus.
        This is the ONLY place engine calls happen in the system.
        After this method returns, no engine output may be modified.

        Engine call order (session-scoped before stateless):
            1. state_engine.update()      — must run first; depends on history
            2. memory_engine.build()      — file I/O; tags project from state
            3. emotion_engine.get()       — stateless; pure function of input
            4. identity_engine.decide()   — stateless; reads state + memory

        Returns:
            StateBus — immutable raw_context. user_input is included.
        """
        project = resolve_project(user_input, self._registry)

        # session-scoped engines first (order matters)
        current_state, _ = self.state_engine.update(user_input)
        state_snap        = StateSnapshot.from_dict(self.state_engine.get_style_influence())

        memory_dict = build_memory_influence(user_input, project_hint=project)
        memory_snap = MemorySnapshot(memory_dict)

        # stateless engines — pure functions with no shared mutable state
        emotion_snap  = EmotionSnapshot.from_dict(get_tone_modifier(user_input))
        identity_snap = IdentitySnapshot.from_dict(
            identity_decide(
                user_input = user_input,
                state      = current_state,
                memory     = memory_dict,
                project    = project,
            )
        )

        # assemble — all mutation ends here
        return StateBus(
            user_input = user_input,
            identity   = identity_snap,
            state      = state_snap,
            emotion    = emotion_snap,
            memory     = memory_snap,
            mode       = self._active_mode,
            project    = project,
        )

    def turn(self, user_input: str, debug: bool = False) -> str:
        """
        Full turn: Layer 1 → Layer 2 → store.

            prepare_context()  — builds immutable raw_context (all engine calls here)
            decide_response()  — kernel receives raw_context, makes all decisions
            store_interaction  — persists the exchange
        """
        self.orb.listen()

        # Layer 1: build raw_context — no decisions, only observations
        raw_context = self.prepare_context(user_input)

        # Layer 2: kernel — receives raw_context only, calls no engines
        self.orb.think()
        if debug:
            set_debug(True)
        response, meta = decide_response(raw_context)
        if debug:
            set_debug(False)
            _print_kernel_meta(meta, raw_context.state.name)

        # store
        self.orb.insight()
        store_interaction(user_input, response, meta["mode"],
                          project_tag=raw_context.project)
        self.orb.idle()

        return response


def _print_kernel_meta(meta: dict, state: str):
    """Print kernel decision summary (used when debug=True)."""
    ic     = meta.get("input_class", {})
    mode   = meta.get("mode", "?")
    loop   = meta.get("loop_detected", False)
    reason = meta.get("loop_reason", "")

    print(f"\n  [kernel]   mode={mode}{' ← LOOP BREAK: ' + reason if loop else ''}")
    print(f"  [classify] factual={ic.get('is_factual')} creative={ic.get('is_creative')} "
          f"distorted={ic.get('is_distorted')} entities={ic.get('entities')}")
    print(f"  [state]    {state}")
