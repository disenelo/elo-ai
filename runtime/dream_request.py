"""
runtime/dream_request.py — S3: an external request to dream.

Board dispatch 2026-10-04 (David L3, "wire end to end"): Builder 1's ambient
tick writes intent="dream" into blender_state.json when elo_battery <=
ENERGY_LOW and eLo is calm; server.py detects it and the dream runs.

THE DISPATCH SAYS "call executive.run_dream_window()". Read against the
source, that wire cannot fire, and there is a second reason not to add it:

  1. run_dream_window() returns {"action": "awake", "ran": False} unless
     blender_state["asleep"] is true (executive.py:629, _read_asleep).
     Builder 1's _should_sleep() explicitly only fires when
     `not already_sleeping`. So the trigger sets intent and never sets
     asleep, and the call it is wired to would decline every single time.
     Dead on arrival, and silently — it returns a dict, it does not raise.

  2. There are already TWO dream executors. server.py's ambient tick calls
     run_dream()/wake_from_dream() directly and is the complete one — it
     publishes dream phases, restores the battery via on_wake_from_dream,
     routes insight through dream_review and clears intent on wake.
     spine.py:894 calls run_dream_window() behind the same asleep gate.
     Adding a third call site would be the third executor for one
     behaviour, which is the mistake WO-TIRED-SIT-001 already made once
     today with two sit emitters.

So the request becomes an additional ENTRY CONDITION on the executor that
already works, rather than a new path. eLo dreams when should_dream() says
so OR when something asked him to.

runtime/executive.py is not touched: it is treated as frozen.

CONSUMPTION. The request is cleared the moment it is accepted. The dream
path immediately rewrites intent="dream" for Unity's lay-down pose
(server.py:1050 — Unity triggers on intent, not state.mode) and the wake
block sets it back to "idle" ("PHASE 9: clear the dream intent, or Unity
never stands up"). That lifecycle already self-consumes on the happy path;
clearing on accept means a dream that CRASHES mid-flight cannot leave a
stuck intent re-triggering on every tick.
"""
from __future__ import annotations

import json
import logging
import os

_log = logging.getLogger("elo.dream_request")

_STATE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "blender", "blender_state.json",
)

DREAM_INTENT = "dream"


def _read_state() -> dict:
    try:
        with open(_STATE_PATH, encoding="utf-8") as f:
            return json.load(f) or {}
    except Exception:
        return {}


def already_dreaming(state: dict) -> bool:
    """
    True if a dream is in flight.

    Three independent signals, because the one that is set depends on how
    far into the cycle it is: dream_phase is written by the sleep schedule,
    asleep is what the Executive's own gate reads, and lifecycle_state is
    what the lifecycle manager sets on enter_dream().
    """
    return bool(
        state.get("dream_phase")
        or state.get("asleep")
        or str(state.get("lifecycle_state", "")) == "dreaming"
    )


def dream_requested(state: dict | None = None, *, consume: bool = True) -> bool:
    """
    Has something asked eLo to dream?

    False while a dream is already running — otherwise the intent the dream
    path writes for Unity would be read back as a fresh request and the
    dream would re-enter itself on every tick.
    """
    st = _read_state() if state is None else state
    if already_dreaming(st):
        return False
    if str(st.get("intent", "")) != DREAM_INTENT:
        return False

    if consume:
        try:
            from blender_bridge.state_writer import patch as _patch
            _patch({"intent": "idle"})
        except Exception:
            pass
    _log.info("dream request accepted (battery/calm trigger) — entering dream window")
    return True
