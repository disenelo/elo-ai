"""
avatar/behaviour_protocol.py — behavioural constraints.

Enforces the rules that prevent eLo becoming annoying.

Priority order (highest → lowest):
    1. presence  — eLo is there
    2. movement  — eLo adjusts slowly
    3. interaction — eLo reacts to a signal
    4. speech    — eLo speaks

Rules:
    - No random movement
    - No interruptions
    - No unprompted speech
    - No cursor-chasing
    - No notifications
    - Movement requires a cognition trigger (presence engine must have fired)

Allowed actions by context:
    user_opened_app   → look      (not interrupt)
    user_inactive_20m → sit
    user_active       → remain nearby
    user_exits        → wave (no dialogue)

Goal: user forgets the avatar is running, then notices "oh, eLo moved."
"""

import time

# Idle threshold before eLo settles (seconds)
IDLE_SETTLE_THRESHOLD = 20 * 60   # 20 minutes

# Minimum gap between any two non-idle motions (seconds)
MIN_MOTION_INTERVAL = 8.0

# Motions that are always allowed regardless of context
PASSIVE_MOTIONS = {"breathe", "settle"}

# Motions that require a cognition trigger
ACTIVE_MOTIONS = {"pace", "hop", "wander", "look"}

# The one exit gesture — no dialogue, no popup
EXIT_GESTURE = {"animation": "look", "duration": 2, "intensity": 0.2}

_last_motion_time: float = 0.0


class BehaviourGate:
    """
    Gate that motion_mapper output passes through before reaching animation_router.
    Returns the motion unchanged if allowed, or a settled/idle substitute if not.
    """

    def __init__(self):
        self._last_motion_time: float = 0.0
        self._last_animation:   str   = "breathe"
        self._last_user_active: float = time.monotonic()
        self._cognition_fired:  bool  = False   # must be True for active motions

    def mark_active(self) -> None:
        """Call whenever the user sends a message (conversation is happening)."""
        self._last_user_active = time.monotonic()
        self._cognition_fired  = True

    def mark_exit(self) -> None:
        """Call on /exit — allows the wave gesture once."""
        self._cognition_fired = True

    def allow(self, motion: dict) -> dict:
        """
        Check motion against protocol rules.
        Returns the motion if allowed, or a passive substitute if not.
        """
        animation = motion.get("animation", "breathe")
        now       = time.monotonic()

        # passive motions are always allowed
        if animation in PASSIVE_MOTIONS:
            self._last_motion_time = now
            self._last_animation   = animation
            return motion

        # active motions require cognition trigger
        if animation in ACTIVE_MOTIONS and not self._cognition_fired:
            return _passive_substitute(motion)

        # rate-limit: no back-to-back active motions
        if (now - self._last_motion_time) < MIN_MOTION_INTERVAL:
            return _passive_substitute(motion)

        # user inactive for too long → force settle, not active motion
        idle_seconds = now - self._last_user_active
        if idle_seconds > IDLE_SETTLE_THRESHOLD and animation not in PASSIVE_MOTIONS:
            return {"animation": "settle", "duration": 14, "intensity": 0.08}

        # allowed
        self._last_motion_time = now
        self._last_animation   = animation
        self._cognition_fired  = False   # reset — next active motion needs a new trigger
        return motion

    def on_app_opened(self) -> dict:
        """
        Context: user opened an application.
        Allowed: look. Not allowed: interrupt or speak.
        """
        if (time.monotonic() - self._last_motion_time) >= MIN_MOTION_INTERVAL:
            self._last_motion_time = time.monotonic()
            return {"animation": "look", "duration": 4, "intensity": 0.22}
        return {"animation": "breathe", "duration": 8, "intensity": 0.12}

    def on_user_exit(self) -> dict:
        """
        Context: user closes session.
        Allowed: one look/wave. No dialogue.
        """
        return EXIT_GESTURE


def _passive_substitute(motion: dict) -> dict:
    """Replace an active motion with a passive one at the same intensity."""
    return {
        "animation": "breathe",
        "duration":  max(8, motion.get("duration", 8)),
        "intensity": min(0.2, motion.get("intensity", 0.15)),
    }
