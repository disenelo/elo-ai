"""
faculties/inner_thought/life.py — card 0010B: eLo's inner life does not start
when David speaks.

    "eLo's inner life is continuous and is not suspended merely because a
     capability is being invoked."
    "David's request is an event occurring inside eLo's life, not the thing
     that creates eLo's existence."
    [SOURCE_ELO-CONTINUOUS-IDENTITY_2026-10-08]

Today the inner process runs only on a message. Between them there is nothing.

THE LOOP IS NOT HERE. The card is explicit: "The LIFE loop itself lives in
Builder 1's daemon (card 0106). Builder 2 provides the tick function." So this
is `life_tick(state)` and nothing else — no thread, no scheduler, no timer.
Building a loop here would mean two things driving eLo's life, which is the
mistake this codebase has made with sits, dreams and deferral stores already.

WHAT EACH STATE DOES, and what it deliberately does not:

    AWAKE    nothing. The turn path already thinks on every message, and
             ticking underneath it would be a second thinker competing with
             the first.
    RESTING  read what just happened, carry the unfinished threads forward,
             let a question form. Cheap, no model call on the critical path.
    SLEEP    consolidate. Dreaming already exists and already has a trigger
             (ambient_engine, on a spent mind battery); this does not
             re-trigger it, it records what the quiet produced.

Returns a dict describing what it did, so a daemon can log it and a test can
assert it without reaching into state. Never raises: eLo's life continuing is
not worth crashing a daemon over.
"""
from __future__ import annotations

import logging
import time
from typing import Any

_log = logging.getLogger("elo.life")

AWAKE = "AWAKE"
RESTING = "RESTING"
SLEEP = "SLEEP"

VALID_STATES = (AWAKE, RESTING, SLEEP)

# Suggested intervals for whoever hosts the loop. Advisory only — this module
# does not schedule anything.
TICK_INTERVAL_S: dict[str, float] = {
    AWAKE: 0.0,        # driven by messages, not by a clock
    RESTING: 60.0,
    SLEEP: 600.0,
}


def _resting_tick() -> dict:
    """
    What happens in the quiet: notice what just happened, keep hold of what
    was left open.
    """
    did: dict[str, Any] = {"actions": []}

    try:
        from faculties.inner_thought.working_memory import recent_events
        evs = recent_events(5)
        did["recent_events"] = len(evs)
        if evs:
            did["actions"].append("read_working_memory")
    except Exception as e:
        _log.debug("resting: working memory unreadable (non-fatal): %s", e)

    # Carry unfinished threads forward. This is what makes
    # has_deferred_threads true between turns rather than only during them.
    try:
        from faculties.metacognition.deferred_threads import sync_to_self_state
        threads = sync_to_self_state()
        did["deferred_threads"] = len(threads)
        if threads:
            did["actions"].append("carried_threads")
    except Exception as e:
        _log.debug("resting: threads not carried (non-fatal): %s", e)

    return did


def _sleep_tick() -> dict:
    """
    Consolidation. Deliberately does NOT start a dream.

    Dreaming already has a trigger — ambient_engine fires it on a spent mind
    battery in calm — and a second trigger here would be two things deciding
    when eLo dreams. This records what the quiet produced and lets the
    existing path decide.
    """
    did: dict[str, Any] = {"actions": []}

    try:
        from faculties.metacognition.correction_capture import capture_new
        res = capture_new()
        did["corrections_kept"] = res.get("kept", 0)
        if res.get("kept"):
            did["actions"].append("consolidated_corrections")
    except Exception as e:
        _log.debug("sleep: corrections not consolidated (non-fatal): %s", e)

    try:
        from faculties.metacognition.deferred_threads import current
        open_threads = current()
        did["open_threads"] = len(open_threads)
        if open_threads:
            did["actions"].append("held_threads")
    except Exception as e:
        _log.debug("sleep: threads unreadable (non-fatal): %s", e)

    # Whether a dream is due — reported, not acted on.
    try:
        from core.health_battery import ENERGY_LOW, mind_battery
        mb = mind_battery()
        did["mind_battery"] = mb
        did["dream_due"] = bool(mb <= ENERGY_LOW)
    except Exception as e:
        _log.debug("sleep: battery unreadable (non-fatal): %s", e)

    return did


def life_tick(state: str) -> dict:
    """
    One beat of eLo's life, at whatever rate the daemon calls it.

    Returns {"state", "ok", "actions", ...}. Never raises.
    """
    t0 = time.time()
    s = str(state or "").strip().upper()
    if s not in VALID_STATES:
        return {"state": s, "ok": False, "actions": [],
                "error": f"unknown state {state!r}"}

    try:
        if s == RESTING:
            out = _resting_tick()
        elif s == SLEEP:
            out = _sleep_tick()
        else:
            # AWAKE is handled by the turn path. Ticking here would be a
            # second thinker competing with the first.
            out = {"actions": [], "note": "awake is driven by the turn path"}
    except Exception as e:                       # pragma: no cover
        _log.warning("life_tick(%s) failed (non-fatal): %s", s, e)
        out = {"actions": [], "error": str(e)}

    # WO-B1-0110 — does eLo raise a hand this beat? Runs for AWAKE too, which
    # otherwise does nothing here on purpose. That exception is deliberate and
    # narrow: the rule AWAKE obeys is "no second thinker competing with the
    # turn path", and this thinks nothing — it sets a flag that Builder 1's
    # delivery hook polls. It cannot race the turn path because one of its own
    # gates is that eLo is not already speaking or under command.
    try:
        from faculties.inner_thought.random_fact import maybe_signal
        if maybe_signal(s):
            out.setdefault("actions", []).append("random_fact")
            out["random_fact"] = True
    except Exception:                            # never a failed tick
        pass

    out["state"] = s
    out["ok"] = "error" not in out
    out["elapsed_ms"] = round((time.time() - t0) * 1000, 1)
    if out["actions"]:
        _log.info("life_tick(%s): %s", s, ", ".join(out["actions"]))
    return out
