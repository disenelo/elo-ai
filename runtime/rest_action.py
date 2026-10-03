"""
runtime/rest_action.py — WO-TIRED-SIT-001 Part B: the impure half.

runtime/rest_decision.py is the policy and is pure — no state, no clock, no
writes. Something still has to gather the body's current situation, ask it,
and relay the answer. That is this module, and it is deliberately separate:
the threshold stays testable without a filesystem, and the relay stays
testable without a server.

It exists as a module rather than a block inside server.py because a block
inside a 7000-line request handler cannot be severed in a wire-cut and
observed. The first attempt was exactly that block, and disabling the relay
left every test green — the tests were reading the source for an import that
was still written, not calling the code. A fix nothing can prove broken is
not a fix that has been proven to work.
"""
from __future__ import annotations

import json
import logging
import os

_log = logging.getLogger("elo.body")

_STATE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "blender", "blender_state.json",
)


def _published_band() -> str:
    """
    The band as PUBLISHED, not the raw one.

    health_battery.get_physical_state() returns a band even when the physical
    track is disengaged — it reads a battery value nothing has been driving.
    snapshot() reports "untracked" in that case, which is the honest answer
    and the one that keeps eLo from sitting down over a body he has no signal
    from.
    """
    try:
        from core.health_battery import snapshot
        return str(snapshot().get("physical_state", ""))
    except Exception:
        return ""


def _current_motion() -> dict:
    try:
        with open(_STATE_PATH, encoding="utf-8") as f:
            return json.load(f).get("motion") or {}
    except Exception:
        return {}


def _is_speaking() -> bool:
    try:
        from voice.voice_engine import is_speaking
        return bool(is_speaking())
    except Exception:
        return False


def _is_commanded() -> bool:
    try:
        from ambient.ambient_engine import _is_commanded as commanded
        return bool(commanded())
    except Exception:
        return False


def _is_dreaming() -> bool:
    try:
        from faculties.dream.dream_faculty import is_dreaming
        return bool(is_dreaming())
    except Exception:
        return False


def maybe_sit() -> dict | None:
    """
    Ask whether eLo wants to sit; if so, publish it. Returns the intent issued,
    or None.

    Sets no threshold of its own — every band name lives in rest_decision.py,
    so the policy has one home and cannot drift between here and there.
    """
    from runtime.rest_decision import decide_rest

    intent = decide_rest(
        _published_band(),
        motion=_current_motion(),
        speaking=_is_speaking(),
        commanded=_is_commanded(),
        dreaming=_is_dreaming(),
    )
    if not intent:
        return None

    from blender_bridge.state_writer import issue_intent
    issue_intent(intent)
    _log.info("eLo sat down on his own: %s", intent.get("reason", ""))
    return intent
