"""
faculties/inner_thought/random_fact.py — WO-B1-0110, Builder 2's half.

Builder 1 asked (FROM_BUILDER1_2026-10-10_RANDOM-FACTS-LIFE-TICK-SPEC.md) for
a `random_fact` signal on the life_tick path: eLo surfaces a WKG fact
unprompted while David is around. Builder 1 owns the selector
(`wkg_faculty.pick_random_fact`) and the delivery (`_voice_speak` in
server.py). This is only the decision of WHEN.

WHY IT WRITES A FILE AS WELL AS RETURNING A FLAG. Builder 1 offered two
patterns and said either works. Both are implemented, because they are not
interchangeable here: `life_tick` is called by the daemon
(`runtime/elo_daemon.py`), and delivery lives in `server.py`. Those are
different processes, so a return value alone never reaches the thing that
speaks. The file is the cross-process half; the returned key is for the
daemon's own log and for tests.

It is a file of mine (`self/state/random_fact.json`), NOT a field on
`elo_self_state.json`. That state is mutated by `_self_mutate` in server.py
on the turn path, and adding a second writer from the daemon is the
disk-level clobber this codebase has already had once (0037/WO-ONEBRAIN-015).

PRESENCE IS ONE NOTION, NOT TWO. "David is present" reuses the same boundary
health_battery already uses for hard idle (1800s) rather than inventing a
second number that can drift away from it.

Nothing here speaks. It raises a hand.
"""
from __future__ import annotations

import json
import logging
import os
import random
import time
from pathlib import Path

_log = logging.getLogger("elo.random_fact")

_ROOT = Path(__file__).resolve().parent.parent.parent
SIGNAL_PATH = _ROOT / "self" / "state" / "random_fact.json"

# Builder 1's gates, named rather than inline so they are tunable in one place.
MIN_INTERVAL_S: float = 15 * 60      # >15 minutes since the last one
CHANCE: float = 0.12                 # 12% per eligible tick
PRESENT_WITHIN_S: float = 1800       # matches health_battery.HARD_IDLE_AFTER_S

# Gate 2: RESTING or AWAKE. Never while dreaming.
ELIGIBLE_STATES = ("RESTING", "AWAKE")


def _load() -> dict:
    try:
        with open(SIGNAL_PATH, encoding="utf-8") as f:
            d = json.load(f)
        return d if isinstance(d, dict) else {}
    except Exception:
        return {}


def _save(d: dict) -> None:
    """Atomic — a half-written flag reads as a pending fact that never clears."""
    try:
        os.makedirs(os.path.dirname(SIGNAL_PATH), exist_ok=True)
        tmp = f"{SIGNAL_PATH}.tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(d, f, indent=2)
        os.replace(tmp, SIGNAL_PATH)
    except Exception as e:
        _log.debug("random fact signal not saved (non-fatal): %s", e)


# ── what Builder 1 calls ─────────────────────────────────────────────────────

def is_pending() -> bool:
    """True when eLo has something to say and has not said it yet."""
    return bool(_load().get("pending"))


def clear_pending(now: float | None = None) -> None:
    """
    Called after delivery. Starts the 15-minute clock from now.

    `now` is injectable for the same reason the roll is: otherwise the
    interval gate can only be tested against real wall-clock, which means it
    cannot be tested at all.
    """
    d = _load()
    d["pending"] = False
    d["last_random_fact_ts"] = time.time() if now is None else float(now)
    _save(d)


# ── the decision ─────────────────────────────────────────────────────────────

def _david_is_present(now: float) -> bool:
    """
    Reuses the turn path's own `last_user_ts`. Absent means nobody has spoken
    this boot, which is not the same as David being away — but it is also not
    evidence he is here, and an unprompted remark to an empty room is worse
    than silence. So absent reads as away.
    """
    try:
        from ambient.ambient_engine import _read_state
        last = (_read_state() or {}).get("last_user_ts")
        if last is None:
            return False
        return (now - float(last)) < PRESENT_WITHIN_S
    except Exception:
        return False


def _eLo_is_free() -> bool:
    """Not dreaming, not already talking, not under a direct command."""
    try:
        from faculties.dream.dream_faculty import is_dreaming
        if is_dreaming():
            return False
    except Exception:
        pass
    try:
        from ambient.ambient_engine import _is_speaking, _is_commanded
        if _is_speaking() or _is_commanded():
            return False
    except Exception:
        pass
    return True


def maybe_signal(state: str, *, now: float | None = None,
                 rng: random.Random | None = None) -> bool:
    """
    Decide whether eLo raises a hand this tick. Returns True if he did.

    All four of Builder 1's gates must pass. `now` and `rng` are injectable so
    a test can pin the roll instead of hoping — a 12% branch is exactly the
    kind that gets "verified" by a run that happened not to fire.

    Never raises.
    """
    try:
        s = str(state or "").strip().upper()
        if s not in ELIGIBLE_STATES:
            return False

        now = time.time() if now is None else float(now)
        d = _load()

        # Already waiting to be said — do not stack them up.
        if d.get("pending"):
            return False

        last = float(d.get("last_random_fact_ts") or 0.0)
        if last and (now - last) < MIN_INTERVAL_S:
            return False

        if not _david_is_present(now):
            return False
        if not _eLo_is_free():
            return False

        rng = rng or random
        if rng.random() >= CHANCE:
            return False

        d["pending"] = True
        d["signalled_ts"] = now
        _save(d)
        _log.info("random fact signalled (state=%s)", s)
        return True
    except Exception as e:                       # never a failed tick
        _log.debug("random fact check failed (non-fatal): %s", e)
        return False
