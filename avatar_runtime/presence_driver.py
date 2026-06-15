"""
avatar_runtime/presence_driver.py — routes commands to animation brain.

Sits between the presence pipeline and the animation brain.
Converts a PresenceState + avatar command into an AvatarRuntimeState.
"""
from __future__ import annotations

from avatar_runtime.animation_brain import AnimationBrain
from avatar_runtime.avatar_state    import AvatarRuntimeState

_brain = AnimationBrain()


def drive(command: dict) -> AvatarRuntimeState:
    """
    Take an avatar command dict and update the animation brain.
    Returns the resulting AvatarRuntimeState.
    """
    return _brain.update(command)


def current() -> AvatarRuntimeState:
    return _brain.current()


def reset() -> None:
    global _brain
    _brain = AnimationBrain()
