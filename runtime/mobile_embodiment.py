"""
runtime/mobile_embodiment.py — WO-MOBILE-001: Mobile Embodiment Wiring (Spine Side)

Handles mobile foreground/background events:
  D-SPINE-1: foreground → apply_embodiment("mobile"), update world_dict, record history
  D-SPINE-2: background → keep embodiment="mobile", update mobile_lifecycle="background"
  D-SPINE-3: clear nearby_surfaces on mobile switch

Authority: David L3 + CA ruling 2026-08-27
Guardrails: G2 (only transition on verified event), G5 (no desktop win_id semantics on mobile)

_MOBILE_EMBODIMENT_SCOPE: capabilities available on phone.
Desktop movement/window capabilities (traverse_desktop, win_id nav) are excluded.
"""
from __future__ import annotations

import logging
import time

_log = logging.getLogger("mobile_embodiment")

# G9: smallest authorised change — preserve existing desktop scope, define mobile subset
_MOBILE_EMBODIMENT_SCOPE: frozenset[str] = frozenset({
    "time", "weather", "sun_events",   # awareness capabilities
    "respond", "memory",               # core cognitive
})


def apply_mobile_foreground(state: "EloSelfState", ts: float = 0.0) -> "EloSelfState":
    """
    D-SPINE-1: On verified mobile foreground event, transition embodiment to 'mobile'.
    D-SPINE-3: Clear nearby_surfaces (desktop surface state must not leak to mobile).
    Records transition with timestamp in embodiment_transitions.
    G2: Only call this from a verified authenticated event source.
    """
    try:
        from_embodiment = state.embodiment
        ts = ts or time.time()

        state.embodiment = "mobile"
        state.mobile_lifecycle = "foreground"

        # D-SPINE-3: clear desktop surface state
        state.nearby_surfaces = []
        _log.warning(
            "MOBILE: nearby_surfaces cleared on embodiment transition desktop→phone"
        )

        # Record transition
        transition = {
            "ts": ts,
            "from_": from_embodiment,
            "to": "mobile",
            "event": "mobile_foreground",
        }
        transitions = list(getattr(state, "embodiment_transitions", []))
        transitions.append(transition)
        state.embodiment_transitions = transitions[-20:]  # keep last 20

        _log.warning(
            "MOBILE D-SPINE-1: embodiment=%s → mobile (foreground). nearby_surfaces cleared.",
            from_embodiment,
        )
    except Exception as _e:
        _log.warning("apply_mobile_foreground error (non-fatal): %s", _e)

    return state


def apply_mobile_background(state: "EloSelfState", ts: float = 0.0) -> "EloSelfState":
    """
    D-SPINE-2: On mobile background notification, keep embodiment='mobile',
    update mobile_lifecycle='background'.
    D-2 governed: embodiment identity and lifecycle are separate dimensions.
    """
    try:
        ts = ts or time.time()

        # D-SPINE-2: embodiment stays "mobile" — do NOT revert to "desktop"
        # Only lifecycle changes
        state.mobile_lifecycle = "background"

        transition = {
            "ts": ts,
            "from_": "mobile",
            "to": "mobile",
            "event": "mobile_background",
            "lifecycle": "background",
        }
        transitions = list(getattr(state, "embodiment_transitions", []))
        transitions.append(transition)
        state.embodiment_transitions = transitions[-20:]

        _log.warning(
            "MOBILE D-SPINE-2: embodiment stays 'mobile', lifecycle=background"
        )
    except Exception as _e:
        _log.warning("apply_mobile_background error (non-fatal): %s", _e)

    return state
