"""
runtime/ack_contract.py — WO-111: Generic action → ACK contract.

Every action that ack_required=True must report a real outcome — not "I wrote a file"
(anim_trigger's old lie), not silence (early-return paths), not assumed success.

The three physical actions (sit / move / exit) have real Unity ACKs.
Everything else is "unconfirmed" until proven otherwise.

ActionResult carries the outcome. check_ack() converts it to a string eLo can say.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import time


# ── Result type ───────────────────────────────────────────────────────────────

@dataclass
class ActionResult:
    """Outcome record for one action execution."""
    action_id:   str
    ok:          bool | None      # True = confirmed; False = failed; None = unconfirmed
    detail:      str   = ""
    ts:          float = field(default_factory=time.time)
    source:      str   = "internal"  # "unity_ack" | "tool_return" | "internal" | "timeout"

    @property
    def is_confirmed(self) -> bool:
        return self.ok is True

    @property
    def is_failed(self) -> bool:
        return self.ok is False

    @property
    def is_unconfirmed(self) -> bool:
        return self.ok is None


# ── Sentinel values ───────────────────────────────────────────────────────────

# Returned by callers (e.g. anim_trigger) that wrote a file but got no ACK.
UNCONFIRMED = "unconfirmed"

# Timeout threshold — no ACK within this many seconds = reported failure.
ACK_TIMEOUT_S = 15.0


# ── Contract check ────────────────────────────────────────────────────────────

def make_result(action_id: str, raw_return, *, source: str = "internal") -> ActionResult:
    """
    Convert the raw return value from an executor into a typed ActionResult.

    raw_return:
        True         → confirmed success (real ACK, e.g. from Unity or a live check)
        False / None → explicit failure
        "unconfirmed"→ fire-and-hope (e.g. anim_trigger file write)
        anything else→ treated as unconfirmed
    """
    if raw_return is True:
        return ActionResult(action_id=action_id, ok=True, source=source)
    if raw_return is False or raw_return is None:
        return ActionResult(action_id=action_id, ok=False, source=source,
                            detail="executor reported failure")
    if raw_return == UNCONFIRMED:
        return ActionResult(action_id=action_id, ok=None, source=source,
                            detail="fire-and-hope — no confirmation signal")
    return ActionResult(action_id=action_id, ok=None, source=source,
                        detail=f"unknown return: {raw_return!r}")


def honest_outcome(result: ActionResult, *, action_label: str = "") -> str:
    """
    Return the honest sentence eLo should say about this action's outcome.

    ADR-Exec-001 Verified Speech: never claim success without evidence.
    """
    label = action_label or result.action_id
    if result.is_confirmed:
        return f"Done — {label} confirmed."
    if result.is_failed:
        return f"That didn't work — {label} reported a failure."
    # Unconfirmed: honest uncertainty, not silence
    return f"I triggered {label} but can't confirm it happened."
