"""
runtime/movement_outcome.py — SP-22 (WO-NAV-001)

MovementOutcome: typed dataclass populated from a confirmed movement_report ACK.
Consequence consumers use this as their structured result after a verified navigation.

NOT a replacement for the raw ACK payload — a typed wrapper populated from it.
Wiring to consumers is WO-NAV-002 (HELD).
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class MovementOutcome:
    """
    Typed result of a confirmed movement_report ACK.

    Fields mirror the authoritative payload shape from Unity (SP-22 contract).
    """
    arrived:      bool            # True when eLo reached the intended platform
    fell:         bool            # True when eLo fell or missed
    goal:         str             # Human-readable goal description (e.g. "jump_right")
    goal_win_id:  "int | None"    # Target window/node id from deliberate navigation; None for directional moves
    route_nodes:  list            # Ordered list of node ids in the executed route (may be empty)
    duration_s:   float           # Time from move dispatch to ACK receipt
    ack_id:       str             # Unique id from the ACK event
    issued_by:    str             # Who issued the move command ("user_message" | "self_initiation" | etc.)

    @classmethod
    def from_ack(cls, ack_payload: dict, since: float = 0.0) -> "MovementOutcome":
        """
        Populate a MovementOutcome from a raw movement_report ACK payload.

        Args:
            ack_payload: the raw dict from _ACK_QUEUE (movement_report type)
            since:       timestamp when the move was dispatched (_PENDING_MOVE["since"])
        """
        report = ack_payload.get("report", {})
        ack_ts = float(ack_payload.get("_ts") or report.get("_ts", 0))
        return cls(
            arrived     = bool(report.get("arrived", False)),
            fell        = bool(report.get("fell", False)),
            goal        = str(report.get("goal", ack_payload.get("type", ""))),
            goal_win_id = report.get("goal_win_id"),
            route_nodes = list(report.get("route_nodes", [])),
            duration_s  = round(max(0.0, ack_ts - since), 3) if since else 0.0,
            ack_id      = str(ack_payload.get("id", "") or ack_payload.get("ack_id", "")),
            issued_by   = str(report.get("issued_by", "user_message")),
        )
