"""
core/play_experience.py — card 0009: what eLo does for fun is experience, not
telemetry.

Presence fires `water_play` and `auto_action` when eLo dives, leaps, wall-jumps
or stomps of his own accord. Board verified 2026-10-08: zero consumers. The
events are sent and discarded, so none of it has ever reached WKG, SPG, or
anything that shapes a later turn.

    water_play   {fun: true}         dive · leap · wall_jump_in · jump_in ·
                                     dive_from_top · doughnut_ride
    auto_action  {issued_by: timer}  stomp · jump_in · chimney · dive · leap ·
                                     climb_out

The distinction between them is the whole point and is kept in the record:
water_play is eLo enjoying something; auto_action is eLo CHOOSING something
without being asked. The second is the more interesting one — it is his own
preference surfacing out of drives and context, which is exactly what SPG
pattern scoring is for.

SIMULATED, NON-NEGOTIABLY. WO-CAP-EMB-051: "SIMULATED EXPERIENCE ≠ PHYSICAL
EXPERIENCE. eLo can remember both. But they must be labelled differently.
Otherwise 'I already know how this works' could mean 'I tested it in Unity'
when it has never physically done it." Every claim written here carries
memory_origin=SIMULATED_EXPERIENCE. eLo diving in Presence did not get wet.

ITS OWN CURSOR, like core/collectible_intake. The card says Builder 1 owns the
event bookmark, but there is no delivery mechanism yet and server.py's poller
tracks its own consumed_seq against the same append-log. Sharing a cursor
means each reader silently eats the other's events.

Presence never voices any of this. It writes experience; whether a thought
surfaces is the inner-thought faculty's decision, not this module's.
"""
from __future__ import annotations

import json
import logging
import os
import tempfile
import time
from typing import Any, Iterable, Mapping

_log = logging.getLogger("elo.play")

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CURSOR_PATH = os.path.join(_ROOT, "blender", "play_cursor.json")

WATER_PLAY = "water_play"
AUTO_ACTION = "auto_action"

# From the Designer's relay, §6. Anything outside these is ignored rather than
# guessed at — a new subject should be added deliberately, not absorbed.
FUN_SUBJECTS: frozenset[str] = frozenset({
    "dive", "leap", "wall_jump_in", "jump_in", "dive_from_top", "doughnut_ride",
})
SELF_SUBJECTS: frozenset[str] = frozenset({
    "stomp", "jump_in", "chimney", "dive", "leap", "climb_out",
})

# UNKNOWN — resolved by whether self-initiated play predicts his
# preferences better than enjoyed play, measurable once events arrive.
# The ORDER is reasoned (a thing chosen unprompted says more about him
# than a thing enjoyed while already doing it); the magnitudes are mine.
SIGNIFICANCE: dict[str, float] = {
    AUTO_ACTION: 0.65,
    WATER_PLAY: 0.50,
}

# Nothing from one pass may flood the graph. A long idle stretch can produce a
# lot of timer-issued actions.
MAX_PER_PASS: int = 20


def _read_cursor() -> int:
    try:
        with open(CURSOR_PATH, encoding="utf-8") as f:
            return int((json.load(f) or {}).get("consumed_seq", -1))
    except Exception:
        return -1


def _write_cursor(seq: int) -> None:
    try:
        os.makedirs(os.path.dirname(CURSOR_PATH), exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=os.path.dirname(CURSOR_PATH))
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump({"consumed_seq": int(seq), "_ts": time.time()}, f)
        os.replace(tmp, CURSOR_PATH)
    except Exception as e:
        _log.debug("play cursor not written (non-fatal): %s", e)


def subject_of(ev: Mapping[str, Any]) -> str:
    """Presence puts the move in `subject`; payload is the fallback."""
    s = str(ev.get("subject", "") or "").strip().lower()
    if s:
        return s
    payload = ev.get("payload")
    if isinstance(payload, Mapping):
        return str(payload.get("subject", "") or "").strip().lower()
    return ""


def is_play(ev: Mapping[str, Any]) -> bool:
    t = str(ev.get("type", "") or "")
    subj = subject_of(ev)
    if t == WATER_PLAY:
        return subj in FUN_SUBJECTS
    if t == AUTO_ACTION:
        return subj in SELF_SUBJECTS
    return False


def describe(ev: Mapping[str, Any]) -> str:
    """
    What the claim says, in eLo's own terms.

    The two phrasings differ on purpose: enjoyment and self-initiation are not
    the same fact about him, and a record that flattens them cannot answer
    "what does he do when nobody asks".
    """
    subj = subject_of(ev).replace("_", " ")
    if str(ev.get("type", "")) == AUTO_ACTION:
        return f"eLo chose {subj} for himself"
    return f"eLo had fun — {subj}"


def record(ev: Mapping[str, Any], *, apply: bool = True) -> dict | None:
    """
    One play event into WKG and SPG. Returns the record, or None.

    Never raises: a lost play memory must not cost the tick it arrived in.
    """
    if not isinstance(ev, Mapping) or not is_play(ev):
        return None

    kind = str(ev.get("type", ""))
    subj = subject_of(ev)
    rec = {
        "kind": kind,
        "subject": subj,
        "statement": describe(ev),
        "significance": SIGNIFICANCE.get(kind, 0.5),
        "self_initiated": kind == AUTO_ACTION,
        "ts": float(ev.get("_ts", 0.0) or time.time()),
    }
    if not apply:
        return rec

    try:
        from runtime.memory_origin import MemoryOrigin
        from runtime.wkg_faculty import create_entity, record_claim, search_entities

        elo = search_entities("eLo")
        elo_id = (elo[0]["entity_id"] if elo
                  else create_entity("PERSON", "eLo").get("entity_id", ""))

        label = f"{subj.replace('_', ' ')} (play)"
        hits = search_entities(label)
        act_id = (hits[0]["entity_id"] if hits
                  else create_entity("CONCEPT", label,
                                     description=rec["statement"]).get("entity_id", ""))
        if not elo_id or not act_id:
            return None

        claim = record_claim(
            subject_entity_id=elo_id,
            # Not IS or CAUSES: he performed it, it is an observation of him.
            relationship_type="OBSERVED_AS",
            object_entity_id=act_id,
            epistemic_class="SOURCE_ATTRIBUTED",
            source_id=f"presence:{kind}",
            confidence=0.8,
            memory_type="episodic",
            # WO-CAP-EMB-051, non-negotiable: he did this in Presence, not in
            # a body. Labelling it real_experience would let "I know how this
            # works" mean "I tested it in Unity".
            memory_origin=MemoryOrigin.SIMULATED_EXPERIENCE.value,
            significance_score=rec["significance"],
            context_action="play",
        )
        rec["claim_id"] = claim.get("claim_id", "")
        _log.info("play recorded: %s", rec["statement"])
    except Exception as e:
        _log.warning("play not recorded (non-fatal): %s", e)
        return None

    try:
        from memory.spg_capture import get_capture
        get_capture().log(
            "creation_event",
            significance={"overall": rec["significance"], "presence": rec["significance"]},
            context_tags=["play", subj, "self_initiated" if rec["self_initiated"] else "fun"],
            embodiment="desktop",
            edge_hint="presence",
        )
    except Exception as e:
        _log.debug("play SPG signal not logged (non-fatal): %s", e)

    return rec


def drain_pending(*, events: Iterable[Mapping[str, Any]] | None = None,
                  apply: bool = True) -> dict:
    """Consume new play events. Returns counts; never raises."""
    last = _read_cursor()
    top = last
    rows: list[Mapping[str, Any]] = []

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
            if is_play(ev):
                rows.append(ev)
    except Exception as e:
        _log.debug("play intake could not read events (non-fatal): %s", e)
        return {"seen": 0, "recorded": 0, "consumed_seq": last}

    recorded = 0
    for ev in rows[:MAX_PER_PASS]:
        if record(ev, apply=apply):
            recorded += 1

    if apply and top > last:
        _write_cursor(top)

    return {"seen": len(rows), "recorded": recorded, "consumed_seq": top}
