"""
core/collectible_intake.py — WO-GAME-002, Builder 2's half: eating restores
energy.

The WO assigns the spawning and pickup to the Designer and names one thing as
mine:

    "Signal feeds Health Battery (Builder 2) — collecting food restores
     energy."
    Done when: ... Health Battery receives signal and responds.

Signal shape, from the WO verbatim:

    {"type": "collectible", "item": "apple", "count": N, "timestamp": ...}

BUILT TO BE WIRED, NOT TO WAIT. The Unity side does not exist yet, and the
honest failure mode for that is a module that works perfectly and is called
by nothing — which is most of what I have spent today removing. So this is
consumed by ambient_engine's existing tick from the moment it lands: when no
collectible events arrive it does nothing, and when they start arriving it
responds without anyone remembering to connect it.

ITS OWN CURSOR, deliberately. unity_events.json is an append-only log and
server.py already tracks a consumed_seq against it for body ACKs. Sharing
that cursor would mean each reader silently eating the other's events. This
keeps its own file and never writes the shared one.

PHYSICAL, NOT COGNITIVE. Food restores the body track. eLo walking across the
desktop to reach an apple is physical effort and eating it is physical
recovery; it does not make him less tired of thinking. health_battery keeps
those tracks separate and this respects that.
"""
from __future__ import annotations

import json
import logging
import os
import tempfile
import time
from typing import Any, Iterable, Mapping

_log = logging.getLogger("elo.collectible")

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CURSOR_PATH = os.path.join(_ROOT, "blender", "collectible_cursor.json")

COLLECTIBLE_TYPE = "collectible"

# [BUILDER CHOICE — pending David/Designer confirmation] What one item gives
# back, as a fraction of the physical battery. An apple is a snack, not a
# meal: ten of them is a full recovery, which keeps collecting worth doing
# across a play session without making one pickup trivialise fatigue.
ITEM_RESTORE: dict[str, float] = {
    "apple": 0.10,
}
DEFAULT_RESTORE: float = 0.06

# No more than this from a single batch, however many arrive at once. A
# pickup burst — or a replayed log — must not refill the whole battery in one
# tick.
MAX_RESTORE_PER_DRAIN: float = 0.30


def _read_cursor() -> int:
    try:
        with open(CURSOR_PATH, encoding="utf-8") as f:
            return int((json.load(f) or {}).get("consumed_seq", -1))
    except Exception:
        return -1


def _write_cursor(seq: int) -> None:
    """Atomic: a half-written cursor would replay or skip the whole log."""
    try:
        os.makedirs(os.path.dirname(CURSOR_PATH), exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=os.path.dirname(CURSOR_PATH))
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump({"consumed_seq": int(seq), "_ts": time.time()}, f)
        os.replace(tmp, CURSOR_PATH)
    except Exception as e:
        _log.debug("collectible cursor not written (non-fatal): %s", e)


def restore_for(item: str) -> float:
    return ITEM_RESTORE.get(str(item or "").strip().lower(), DEFAULT_RESTORE)


def _is_collectible(ev: Mapping[str, Any]) -> bool:
    return str(ev.get("type", "")) == COLLECTIBLE_TYPE


def amount_for_events(events: Iterable[Mapping[str, Any]]) -> float:
    """
    Total restoration for a batch, capped.

    `count` is honoured because the WO's schema carries it, but a malformed or
    hostile count cannot drain the cap — it is clamped per event before the
    batch cap applies.
    """
    total = 0.0
    for ev in events:
        if not isinstance(ev, Mapping) or not _is_collectible(ev):
            continue
        try:
            n = int(ev.get("count", 1) or 1)
        except (TypeError, ValueError):
            n = 1
        n = max(0, min(n, 10))
        total += restore_for(ev.get("item", "")) * n
    return round(min(total, MAX_RESTORE_PER_DRAIN), 4)


def drain_pending(*, events=None, apply: bool = True) -> dict:
    """
    Consume any new collectible events and restore the physical battery.

    Returns what happened, so a caller can log or test it without reaching
    into the battery. Never raises: a missing log, a corrupt row or an absent
    battery all yield a no-op.
    """
    last = _read_cursor()
    rows: list[Mapping[str, Any]] = []
    top = last

    try:
        if events is None:
            from runtime.unity_events_cursor import iter_events_from
            source = iter_events_from(last)
        else:
            source = events
        for ev in source:
            if not isinstance(ev, Mapping):
                continue
            try:
                seq = int(ev.get("seq", -1))
            except (TypeError, ValueError):
                seq = -1
            if seq > top:
                top = seq
            if _is_collectible(ev):
                rows.append(ev)
    except Exception as e:
        _log.debug("collectible intake could not read events (non-fatal): %s", e)
        return {"items": 0, "restored": 0.0, "consumed_seq": last}

    amount = amount_for_events(rows)

    if apply and amount > 0.0:
        try:
            from core.health_battery import restore_physical
            restore_physical(amount)
            _log.info("collectible: %d item(s) restored %.3f physical energy",
                      len(rows), amount)
        except Exception as e:
            _log.warning("collectible restore failed: %s", e)
            return {"items": len(rows), "restored": 0.0, "consumed_seq": last}

    if top > last:
        _write_cursor(top)

    return {"items": len(rows), "restored": amount, "consumed_seq": top}
