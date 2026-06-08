"""
core/state_bus.py — eLo AI state bus.

Replaces the flat mutable dict that previously flowed between engines.

Architecture:
    Each engine produces one snapshot (immutable after creation).
    core_engine assembles all four into a StateBus.
    Kernel reads ONLY from the StateBus via to_context().
    No engine may write to the bus after it is created.

Four snapshot types:
    IdentitySnapshot  — frozen dataclass (identity_engine output)
    StateSnapshot     — frozen dataclass (state_engine output)
    EmotionSnapshot   — frozen dataclass (emotion_engine output)
    MemorySnapshot    — read-only proxy  (memory_engine output)

One aggregation class:
    StateBus          — holds all four snapshots, immutable after __init__
"""

from dataclasses import dataclass
from types import MappingProxyType


# ── frozen snapshot types ──────────────────────────────────────────────────────

@dataclass(frozen=True)
class IdentitySnapshot:
    """Output of identity_engine.decide() — immutable after creation."""
    values:        tuple   # frozen from list
    perspective:   str
    intent:        str
    response_bias: str
    entities:      tuple   # frozen from list

    @classmethod
    def from_dict(cls, d: dict) -> "IdentitySnapshot":
        return cls(
            values        = tuple(d.get("values",        [])),
            perspective   = d.get("perspective",         "expansion"),
            intent        = d.get("intent",              "offer_question"),
            response_bias = d.get("response_bias",       "stay_grounded"),
            entities      = tuple(d.get("entities",      [])),
        )

    def to_dict(self) -> dict:
        return {
            "identity_values":      list(self.values),
            "identity_perspective": self.perspective,
            "identity_intent":      self.intent,
            "identity_bias":        self.response_bias,
            "entities":             list(self.entities),
        }


@dataclass(frozen=True)
class StateSnapshot:
    """Output of state_engine.get_style_influence() — immutable after creation."""
    name:         str
    tone_bias:    str
    style_weight: float
    pacing_bias:  str

    @classmethod
    def from_dict(cls, d: dict) -> "StateSnapshot":
        return cls(
            name         = d.get("state",        "exploring"),
            tone_bias    = d.get("tone_bias",    "open"),
            style_weight = float(d.get("style_weight", 0.5)),
            pacing_bias  = d.get("pacing_bias",  "moderate"),
        )

    def to_dict(self) -> dict:
        return {
            "state":           self.name,
            "state_tone_bias": self.tone_bias,
            "state_weight":    self.style_weight,
            "state_pacing":    self.pacing_bias,
        }


@dataclass(frozen=True)
class EmotionSnapshot:
    """Output of emotion_engine.get_tone_modifier() — immutable after creation."""
    emotion: str
    tone:    str
    pacing:  str
    warmth:  float

    @classmethod
    def from_dict(cls, d: dict) -> "EmotionSnapshot":
        return cls(
            emotion = d.get("emotion", "neutral"),
            tone    = d.get("tone",    "warm"),
            pacing  = d.get("pacing",  "moderate"),
            warmth  = float(d.get("warmth", 0.7)),
        )

    def to_dict(self) -> dict:
        return {
            "emotion": {"emotion": self.emotion, "tone": self.tone,
                        "pacing": self.pacing, "warmth": self.warmth},
        }


class MemorySnapshot:
    """
    Read-only proxy around the memory_engine influence dict.

    The underlying dict is wrapped in MappingProxyType — any attempt to
    mutate it raises TypeError at runtime, not silently at the wrong time.
    """

    __slots__ = ("_data",)

    def __init__(self, memory_dict: dict):
        object.__setattr__(self, "_data", MappingProxyType(dict(memory_dict)))

    def get(self, key: str, default=None):
        return self._data.get(key, default)

    def __contains__(self, key: str) -> bool:
        return key in self._data

    def __setattr__(self, name, value):
        raise AttributeError("MemorySnapshot is read-only after creation")

    def to_dict(self) -> dict:
        return dict(self._data)

    # ── typed property access ────────────────────────────────────────────────

    @property
    def tone_signal(self) -> str:
        return self._data.get("tone_signal", "neutral")

    @property
    def returning_theme(self) -> str:
        return self._data.get("returning_theme", "")

    @property
    def symbolic_echo(self) -> str:
        return self._data.get("symbolic_echo", "")

    @property
    def project(self) -> str:
        return self._data.get("project_momentum", self._data.get("project", "elo_core"))

    @property
    def concept_pairs(self) -> dict:
        return dict(self._data.get("concept_pairs", {}))

    @property
    def recurring_concepts(self) -> list:
        return list(self._data.get("recurring_concepts", []))


# ── state bus ──────────────────────────────────────────────────────────────────

class StateBus:
    """
    Immutable raw_context for one conversation turn.

    Created by core_engine.prepare_context() — the ONLY place engine calls happen.
    Passed directly to kernel.decide_response(raw_context).
    Kernel reads it. Kernel does not modify it.

    Fields:
        user_input  — the raw text from the user (included so kernel needs nothing else)
        identity    — IdentitySnapshot (frozen dataclass)
        state       — StateSnapshot (frozen dataclass)
        emotion     — EmotionSnapshot (frozen dataclass)
        memory      — MemorySnapshot (MappingProxyType — read-only)
        mode        — active conversation mode string
        project     — active project namespace string

    Mutation attempt → AttributeError immediately.
    """

    __slots__ = ("_user_input", "_identity", "_state", "_emotion",
                 "_memory", "_mode", "_project")

    def __init__(
        self,
        user_input: str,
        identity:   IdentitySnapshot,
        state:      StateSnapshot,
        emotion:    EmotionSnapshot,
        memory:     MemorySnapshot,
        mode:       str = "companion",
        project:    str = "elo_core",
    ):
        object.__setattr__(self, "_user_input", user_input)
        object.__setattr__(self, "_identity",   identity)
        object.__setattr__(self, "_state",      state)
        object.__setattr__(self, "_emotion",    emotion)
        object.__setattr__(self, "_memory",     memory)
        object.__setattr__(self, "_mode",       mode)
        object.__setattr__(self, "_project",    project)

    def __setattr__(self, name, value):
        raise AttributeError(
            f"StateBus is immutable — cannot set '{name}' after creation"
        )

    # ── read-only properties ──────────────────────────────────────────────────

    @property
    def user_input(self) -> str:             return self._user_input
    @property
    def identity(self)   -> IdentitySnapshot: return self._identity
    @property
    def state(self)      -> StateSnapshot:   return self._state
    @property
    def emotion(self)    -> EmotionSnapshot: return self._emotion
    @property
    def memory(self)     -> MemorySnapshot:  return self._memory
    @property
    def mode(self)       -> str:             return self._mode
    @property
    def project(self)    -> str:             return self._project

    # ── context export ────────────────────────────────────────────────────────

    def to_context(self) -> dict:
        """
        Flatten all snapshots into a context dict for kernel consumption.

        Called once by the kernel at the start of decide_response().
        Returns a new independent dict — mutations do not affect the bus.
        """
        ctx: dict = {}

        # memory signals (foundation layer)
        ctx.update(self._memory.to_dict())

        # state style weights
        ctx.update(self._state.to_dict())

        # emotion delivery hints (under "emotion" key — kernel reads sub-dict)
        ctx.update(self._emotion.to_dict())

        # identity signals (flat keys for kernel._assemble)
        ctx.update(self._identity.to_dict())

        # session metadata
        ctx["project"] = self._project
        ctx["mode"]    = self._mode

        return ctx

    def __repr__(self) -> str:
        return (
            f"StateBus(input={self._user_input[:30]!r}, "
            f"state={self._state.name!r}, "
            f"emotion={self._emotion.emotion!r}, "
            f"mode={self._mode!r}, "
            f"project={self._project!r})"
        )
