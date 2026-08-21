"""
runtime/motor_contract.py — Vol XI Motor Contract (WO-CANON-XI §B/§E/§F)

Three concerns housed here:
  §B  UP envelope — validate events from Unity (at mandatory on motion ACKs)
  §E  §1.7 audit rule — every observable body behaviour must be commanded or a reported reflex
  §F  Embodiment parity — closed verb set, bone assertion, no driver port

§A/§D (generalised DOWN envelope + PEEK enforcement) require David L3 (OQ-1.2):
they extend the DOWN contract David signed and are NOT implemented here.
"""
from __future__ import annotations

# ── §C/§F: Movement Grammar — exactly 12 verbs, closed set ───────────────────
# Adding one requires a canon change (Vol XI Ch.2 §2.2).
# Verbs are parameterised, not multiplied: APPROACH at speed 0.3 and speed 1.0
# are the SAME verb — there is no separate WALK/RUN.
MOVEMENT_VERBS: frozenset = frozenset({
    "APPROACH",   # close in (parameterised by speed)
    "CLIMB",      # ascend a surface
    "BALANCE",    # hold precarious stance
    "LEAP",       # airborne jump (PEEK precondition — §D, blocked David L3)
    "HANG",       # cling to an edge
    "SLIDE",      # traverse a sloped surface
    "PEEK",       # look before leaping; realises as OBSERVE orientation
    "PERCH",      # land on a narrow surface and hold
    "REST",       # idle/calm body state
    "OBSERVE",    # deliberate attention without motion
    "RETREAT",    # move away
    "RETURN",     # come back to a prior position
})

# ── §B: Bounded reflexes — local safety decisions LEGAL without a DOWN command ─
# Every bounded reflex MUST emit an UP event. A behaviour not in this set and
# not commanded is a §1.7 VIOLATION.
BOUNDED_REFLEXES: frozenset = frozenset({
    "landed",       # gravity/physics landing after a leap
    "resurfaced",   # survival re-attach after drag/offscreen (DesktopBuddy WO-094)
    "collided",     # collision avoidance reflex
})

# UP event types that carry the mandatory 'at' field (real position read-back)
_MOTION_ACK_TYPES: frozenset = frozenset({
    "sit_complete",
    "move_complete",
    "exit_complete",
    "arrived",        # terminal per-leg ACK (Vol XI §1.5 OQ-1.4)
})


# ── §B: UP envelope validation ─────────────────────────────────────────────────

def validate_up_event(event: dict) -> tuple:
    """
    Validate a Unity→Brain UP event against the Vol XI §1.5 envelope.

    Returns (ok: bool, reason: str).

    Motion ACK types MUST carry 'at': {surface_id, pos} — the brain reads back
    the *real* position, never assumes the commanded one. _ts is mandatory on
    every event.
    """
    ev_type = event.get("type", "")
    if "_ts" not in event:
        return False, f"event '{ev_type}' missing mandatory '_ts'"
    if ev_type in _MOTION_ACK_TYPES and "at" not in event:
        return False, f"motion ACK '{ev_type}' missing mandatory 'at' field"
    return True, "ok"


# ── §B: ACK freshness check ────────────────────────────────────────────────────

def ack_is_fresh(event_ts: float, pending_since: float) -> bool:
    """
    Return True iff the ACK _ts strictly follows the pending command _ts.

    A stale ACK (event_ts <= pending_since) must not clear pending state or
    permit speech. Prevents a prior command's ACK satisfying a newer one.
    This is the Vol XI §1.5 / WO-041 guard, expressed as a testable function.
    """
    return event_ts > pending_since


# ── §E: §1.7 audit rule ────────────────────────────────────────────────────────

def audit_motor_behaviour(
    commanded: list,
    relay_events: list,
    observed_behaviours: list,
) -> dict:
    """
    Vol XI §1.7 audit: for every observable behaviour B the body performs —
      1. Is there a DOWN command (issued_by set, _ts before B)?  → LEGAL (commanded)
      2. Else, is B a bounded reflex AND was it relayed UP?       → LEGAL (reflex)
      3. Else                                                     → VIOLATION

    Note: EloDesktopNav's _route local selection WILL appear as a VIOLATION here
    until WO-CANON-XIII §E lands (Ruling D-XIII-1 demotes it — that WO owns the
    retirement, not this one).

    Args:
        commanded:             list[dict] — DOWN commands: 'action', '_ts', optional 'issued_by'
        relay_events:          list[dict] — UP relay log entries: 'event_kind' field
        observed_behaviours:   list[dict] — {'kind': str, '_ts': float}

    Returns:
        {ok, violations, legal_commanded, legal_reflex}
    """
    violations: list = []
    legal_commanded = 0
    legal_reflex = 0

    relayed_kinds = {r.get("event_kind", "") for r in relay_events}

    for b in observed_behaviours:
        kind = b.get("kind", "")
        b_ts = float(b.get("_ts", 0.0))

        # 1. Commanded with issued_by, before this behaviour's timestamp?
        if any(
            c.get("action") == kind
            and c.get("issued_by")
            and float(c.get("_ts", 0.0)) < b_ts
            for c in commanded
        ):
            legal_commanded += 1
            continue

        # 2. Bounded reflex that was relayed UP?
        if kind in BOUNDED_REFLEXES and kind in relayed_kinds:
            legal_reflex += 1
            continue

        # 3. VIOLATION
        violations.append(
            f"VIOLATION: '{kind}' (_ts={b_ts}) — not commanded and not a reported reflex"
        )

    return {
        "ok": len(violations) == 0,
        "violations": violations,
        "legal_commanded": legal_commanded,
        "legal_reflex": legal_reflex,
    }


# ── §F: Verb validation ────────────────────────────────────────────────────────

def is_valid_verb(verb: str) -> bool:
    """Return True iff verb is in the closed 12-verb movement grammar."""
    return verb in MOVEMENT_VERBS


def validate_route_verbs(route: list) -> tuple:
    """
    Validate verb fields across all legs of a route.

    Returns (ok: bool, unknown_verbs: list[str]).
    A route with any unknown verb must be rejected at the channel.
    """
    unknown = [
        leg.get("verb", "")
        for leg in route
        if leg.get("verb", "") not in MOVEMENT_VERBS
    ]
    return len(unknown) == 0, unknown


# ── §F: Bone assertion ────────────────────────────────────────────────────────

def assert_bone_present(rig_bones: list, required_bone: str) -> None:
    """
    Assert a required bone exists in the rig.

    Per WO-CANON-XI §F: per-gesture code ports MUST FAIL LOUDLY if a bone is
    absent — never a silent no-op. This is how the feel is shared without
    sharing baked clips or rig binding.

    Raises KeyError on a missing bone.
    """
    if required_bone not in rig_bones:
        raise KeyError(
            f"Required bone '{required_bone}' absent from rig — "
            "WO-CANON-XI §F: fail loudly, never a silent no-op"
        )
