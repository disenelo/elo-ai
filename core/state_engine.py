"""
core/state_engine.py — eLo AI conversational state machine.

Six states, each with a distinct behavioral profile.
Transitions happen naturally from input signals — no AI model, no explicit commands.

States:
    focused     — locked in on a specific task, high precision energy
    playful     — light, experimental, trying things without heavy commitment
    exploring   — curious and open, following unknowns
    building    — concrete execution, step by step, making things real
    reflecting  — slow and spacious, processing or looking within
    resting     — low energy, recovery, simple acknowledgment

Each state produces a behavioral profile:
    tone              — how eLo speaks
    response_length   — "short" | "medium"
    imagination_level — "low" | "medium" | "high"
    project_focus     — "tight" | "loose" | "open"

Transition logic:
    Inertia: the current state gets a 1.5× score bonus — prevents jitter.
    Hysteresis: a new state must win on 2 consecutive turns to commit — prevents
    single-word anomalies from triggering a shift.
    Forced transitions: resting overrides everything when overload signals appear.
"""

import re
from collections import Counter


# ── state signal patterns ──────────────────────────────────────────────────────
# Each pattern maps to a weight. Higher weight = stronger signal for that state.

_STATE_SIGNALS: dict = {
    "focused": {
        r"\bjust\s+this\b": 2,   r"\bspecifically\b": 2,  r"\bfocus\s+on\b": 2,
        r"\bfocus\b": 1,         r"\bonly\b": 1,           r"\bexactly\b": 1,
        r"\bprecise\b": 1,       r"\bone\s+thing\b": 1,    r"\bthis\s+one\b": 1,
    },
    "playful": {
        r"\bhaha\b": 3,    r"\bthis is wild\b": 3,  r"\bso weird\b": 3,
        r"\bfun\b": 2,     r"\bsilly\b": 2,         r"\bcrazy\b": 2,
        r"\bplay\b": 1,    r"\bexperiment\b": 1,    r"\bwhat\s+if\s+we\b": 1,
    },
    "exploring": {
        r"\bwhat if\b": 2,    r"\bimagine\b": 2,    r"\bwonder\b": 2,
        r"\bcurious\b": 2,    r"\bexplore\b": 1,    r"\bpossible\b": 1,
        r"\bmaybe\b": 1,      r"\bwhat\s+else\b": 1, r"\bnot sure yet\b": 1,
    },
    "building": {
        r"\blet'?s build\b": 2,  r"\bstep by step\b": 2,  r"\bimplement\b": 2,
        r"\bwrite\s+the\b": 2,
        r"\bbuild\b": 1,         r"\bcreate\b": 1,         r"\bmake\b": 1,
        r"\bcode\b": 1,          r"\bdesign\b": 1,         r"\bship\b": 1,
        r"\bplan\b": 1,
    },
    "reflecting": {
        r"\bi don'?t know\b": 2, r"\bnot sure\b": 2, r"\bsomething feels\b": 2,
        r"\bwhy\s+do\s+i\b": 2,  r"\bfeel\b": 1,     r"\bthink\b": 1,
        r"\bmeaning\b": 1,       r"\bpurpose\b": 1,  r"\bunderstand\b": 1,
        r"\bprocess\b": 1,
    },
    "resting": {
        r"\bexhausted\b": 4, r"\bdrained\b": 4, r"\bburnt?\s*out\b": 4,
        r"\btired\b": 3,     r"\boverwhelm\b": 3, r"\bchaos\b": 2,
        r"\bstuck\b": 2,     r"\bcan'?t\b": 1,   r"\btoo\s+much\b": 2,
        r"\bneed\s+a\s+break\b": 4,
    },
}

# ── behavioral profiles ────────────────────────────────────────────────────────

_STATE_PROFILES: dict = {
    "focused": {
        "tone":              "precise and direct — no preamble, no abstraction",
        "response_length":   "short",
        "imagination_level": "low",
        "project_focus":     "tight",
        "description":       "Locked in. Specific task. Execution energy.",
        "elo_voice_hint":    "Lead with the next concrete thing. Skip the context.",
    },
    "playful": {
        "tone":              "light and experimental — follow the energy",
        "response_length":   "short",
        "imagination_level": "medium",
        "project_focus":     "loose",
        "description":       "Trying things without heavy investment. Light touch.",
        "elo_voice_hint":    "Match the lightness. Play back. Don't be earnest when playful works.",
    },
    "exploring": {
        "tone":              "curious and open — follow threads before concluding",
        "response_length":   "medium",
        "imagination_level": "high",
        "project_focus":     "open",
        "description":       "Moving through unknowns. Curiosity outrunning certainty.",
        "elo_voice_hint":    "Expand before narrowing. Ask what this could become before naming what it is.",
    },
    "building": {
        "tone":              "grounded and action-oriented — next step is foreground",
        "response_length":   "medium",
        "imagination_level": "low",
        "project_focus":     "tight",
        "description":       "Executing. Making things real. Step-by-step.",
        "elo_voice_hint":    "Lead with the next real action. Structure is the creative act right now.",
    },
    "reflecting": {
        "tone":              "slow and spacious — hold before redirecting",
        "response_length":   "short",
        "imagination_level": "medium",
        "project_focus":     "loose",
        "description":       "Processing. Looking back or within. No urgency.",
        "elo_voice_hint":    "Slow down. Don't offer solutions before the feeling has been named.",
    },
    "resting": {
        "tone":              "minimal and acknowledging — presence without push",
        "response_length":   "short",
        "imagination_level": "low",
        "project_focus":     "open",
        "description":       "Low energy. Recovery mode. Simple acknowledgment.",
        "elo_voice_hint":    "Name the state. Don't try to move through it. Nothing needs to happen yet.",
    },
}

# ── natural transition map ─────────────────────────────────────────────────────
# Defines which states each state can naturally flow into, and the signal words
# that favour that transition. Used only for readable documentation / future extensions.
# Actual transitions are score-driven, not rule-driven.

_NATURAL_TRANSITIONS: dict = {
    "resting":    ["exploring", "reflecting"],
    "exploring":  ["building", "focused", "playful", "reflecting"],
    "building":   ["focused", "exploring", "reflecting"],
    "focused":    ["building", "exploring", "playful"],
    "reflecting": ["exploring", "building", "resting"],
    "playful":    ["exploring", "building", "resting"],
}

# Resting is a forced state — these signals override inertia completely
_FORCED_RESTING_SIGNALS = [
    r"\bexhausted\b", r"\bdrained\b", r"\bburnt?\s*out\b",
    r"\bneed\s+a\s+break\b", r"\bcan'?t\s+anymore\b",
]


# ── core state machine ─────────────────────────────────────────────────────────

class StateEngine:
    """
    Tracks the user's conversational state across turns.

    Transitions happen from accumulated signal evidence — not from a single word,
    not from explicit commands (unless the behavior engine routes /mode explicitly).
    """

    _INERTIA_BONUS   = 1.5   # current state gets this multiplier on its score
    _HYSTERESIS_NEED = 2     # turns a candidate state must lead before committing
    _HISTORY_MAX     = 12

    def __init__(self, default_state: str = "exploring"):
        self._state:         str   = default_state
        self._pending_state: str   = None
        self._pending_count: int   = 0
        self._history:       list  = []
        self.turn_count:     int   = 0

    # ── state detection ────────────────────────────────────────────────────────

    def _score_text(self, text: str) -> dict:
        """Score input text against all state signals. Returns {state: score}."""
        text_lower = text.lower()
        scores = {state: 0.0 for state in _STATE_SIGNALS}
        for state, patterns in _STATE_SIGNALS.items():
            for pattern, weight in patterns.items():
                if re.search(pattern, text_lower):
                    scores[state] += weight
        return scores

    def detect_state(self, text: str) -> str:
        """Return the state most strongly signalled by this text, ignoring inertia."""
        scores = self._score_text(text)
        best = max(scores, key=lambda s: scores[s])
        return best if scores[best] > 0 else self._state

    # ── transition logic ───────────────────────────────────────────────────────

    def update(self, text: str) -> tuple:
        """
        Process one input and potentially transition state.

        Returns:
            (current_state: str, did_transition: bool)
        """
        self.turn_count += 1
        scores = self._score_text(text)

        # forced resting — overrides everything
        if any(re.search(p, text.lower()) for p in _FORCED_RESTING_SIGNALS):
            did_transition = self._state != "resting"
            self._commit("resting")
            return self._state, did_transition

        # apply inertia to current state
        scores[self._state] = scores.get(self._state, 0) * self._INERTIA_BONUS + self._INERTIA_BONUS

        best_candidate = max(scores, key=lambda s: scores[s])

        if best_candidate == self._state:
            # inertia holds — clear any pending transition
            self._pending_state = None
            self._pending_count = 0
            self._history.append(self._state)
            self._trim_history()
            return self._state, False

        # hysteresis: new candidate must lead for _HYSTERESIS_NEED turns
        if best_candidate == self._pending_state:
            self._pending_count += 1
        else:
            self._pending_state = best_candidate
            self._pending_count = 1

        if self._pending_count >= self._HYSTERESIS_NEED:
            did_transition = True
            self._commit(best_candidate)
        else:
            self._history.append(self._state)
            self._trim_history()
            did_transition = False

        return self._state, did_transition

    def _commit(self, new_state: str):
        self._state         = new_state
        self._pending_state = None
        self._pending_count = 0
        self._history.append(new_state)
        self._trim_history()

    def _trim_history(self):
        if len(self._history) > self._HISTORY_MAX:
            self._history.pop(0)

    # ── explicit override ─────────────────────────────────────────────────────

    def force_state(self, state: str) -> bool:
        """Directly set state — used when /mode is set explicitly. Returns True if changed."""
        # map mode names to state names
        _MODE_TO_STATE = {
            "studio":    "building",
            "adventure": "exploring",
            "companion": "reflecting",
        }
        target = _MODE_TO_STATE.get(state, state)
        if target in _STATE_PROFILES and target != self._state:
            self._commit(target)
            return True
        return False

    # ── behavioral output ─────────────────────────────────────────────────────

    @property
    def state(self) -> str:
        return self._state

    def get_profile(self) -> dict:
        """Return the full behavioral profile for the current state."""
        return _STATE_PROFILES.get(self._state, _STATE_PROFILES["exploring"])

    def get_behavioral_hint(self) -> dict:
        """
        Return the four behavioral values that influence response generation.

        tone              — how eLo should speak
        response_length   — "short" or "medium"
        imagination_level — "low", "medium", or "high"
        project_focus     — "tight", "loose", or "open"
        elo_voice_hint    — specific instruction for the behavior engine
        """
        profile = self.get_profile()
        return {
            "state":             self._state,
            "tone":              profile["tone"],
            "response_length":   profile["response_length"],
            "imagination_level": profile["imagination_level"],
            "project_focus":     profile["project_focus"],
            "elo_voice_hint":    profile["elo_voice_hint"],
        }

    def history_summary(self) -> str:
        """Human-readable summary of recent state history."""
        if not self._history:
            return "no history"
        counts = Counter(self._history[-8:])
        top = counts.most_common(3)
        return " → ".join(f"{s}({n})" for s, n in top)

    def to_dict(self) -> dict:
        return {
            "state":          self._state,
            "turn_count":     self.turn_count,
            "pending":        self._pending_state,
            "pending_count":  self._pending_count,
            "history":        self.history_summary(),
        }
