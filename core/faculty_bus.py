"""
core/faculty_bus.py — eLo OS Faculty Bus (WO-001)

Typed message envelope + routing layer for inter-faculty communication.
Every faculty passes through here so traffic is observable and traceable.

Canonical envelope: Volume_V/CONTRACTS.md §2 (ADR-0001 / D-A · LAW)
Architecture gap:   ARCHITECTURE_AUDIT.md #1 (HIGHEST)

Rules:
  - Synchronous, non-blocking — holds no cross-thread lock.
  - id, sender, receiver, priority, payload.type are REQUIRED.
    Missing = rejected at boundary, never silently processed.
  - confidence may only be LOWERED downstream (raised → rejected).
  - trace is append-only per hop.
  - Envelopes past expires are dropped with a trace note.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable, Any

# WO-CANON-XVI: priority-ordered delivery (critical pre-empts FIFO)
_PRIORITY_ORDER: dict[str, int] = {"critical": 0, "high": 1, "normal": 2, "low": 3}


# ── Envelope ─────────────────────────────────────────────────────────────────

@dataclass
class Envelope:
    """
    Canonical nine-field wire format (ADR-0001 / D-A · LAW).
    Never mutate after construction — pass downstream read-only.
    """
    id:         str                 # uuid
    sender:     str                 # PascalCase faculty name
    receiver:   str                 # PascalCase faculty name or "*" for broadcast
    priority:   str                 # "low" | "normal" | "high" | "critical"
    context:    dict                # conversation_id, relationship_state, significance, memory_instruction
    payload:    dict                # {"type": str, "body": dict}
    confidence: float               # 0.0–1.0; only decreases downstream
    expires:    str | None          # ISO-8601 or None (never expires)
    trace:      list[str] = field(default_factory=list)  # ["Faculty@ts", ...]

    REQUIRED_FIELDS = ("id", "sender", "receiver", "priority")
    VALID_PRIORITIES = ("low", "normal", "high", "critical")

    def is_valid(self) -> tuple[bool, str]:
        """Validate envelope at bus boundary. Returns (ok, reason)."""
        for f in self.REQUIRED_FIELDS:
            if not getattr(self, f, None):
                return False, f"missing required field: {f}"
        if self.priority not in self.VALID_PRIORITIES:
            return False, f"invalid priority: {self.priority!r}"
        if not isinstance(self.payload, dict):
            return False, "payload must be a dict"
        if not self.payload.get("type"):
            return False, "payload.type is required"
        if not isinstance(self.confidence, (int, float)):
            return False, "confidence must be numeric"
        if not 0.0 <= self.confidence <= 1.0:
            return False, f"confidence out of range: {self.confidence}"
        return True, ""

    def is_expired(self) -> bool:
        if not self.expires:
            return False
        try:
            exp = datetime.fromisoformat(self.expires)
            now = datetime.now(timezone.utc)
            if exp.tzinfo is None:
                exp = exp.replace(tzinfo=timezone.utc)
            return now > exp
        except ValueError:
            return False

    def lower_confidence(self, new_confidence: float) -> "Envelope":
        """Return a new envelope with lowered confidence. Raises if you try to raise it."""
        if new_confidence > self.confidence:
            raise ValueError(
                f"confidence may only be lowered downstream "
                f"(current={self.confidence}, attempted={new_confidence})"
            )
        return Envelope(
            id=self.id,
            sender=self.sender,
            receiver=self.receiver,
            priority=self.priority,
            context=dict(self.context),
            payload=dict(self.payload),
            confidence=new_confidence,
            expires=self.expires,
            trace=list(self.trace),
        )


# ── Bus ──────────────────────────────────────────────────────────────────────

class FacultyBus:
    """
    Synchronous routing layer. Non-blocking — must not stall the turn lock.

    Usage:
        bus = FacultyBus()
        bus.subscribe("Executive", filter_fn=lambda e: e.sender == "Attention")
        env = make_envelope(sender="Attention", receiver="Executive", ...)
        bus.publish(env)
        messages = bus.get_messages("Executive")
    """

    def __init__(self) -> None:
        self._subscribers: dict[str, list[Callable[[Envelope], bool] | None]] = {}
        self._queues: dict[str, list[Envelope]] = {}
        self._dropped: list[dict] = []    # audit trail for expired/rejected envelopes

    # ── Subscribe / Unsubscribe ───────────────────────────────────────────────

    def subscribe(
        self,
        faculty: str,
        filter_fn: Callable[[Envelope], bool] | None = None,
    ) -> None:
        """
        Register a faculty as a subscriber.

        filter_fn — optional predicate; only envelopes where filter_fn(env)=True are queued.
                    If None, the faculty receives everything addressed to it (or broadcast).
        """
        if faculty not in self._subscribers:
            self._subscribers[faculty] = []
            self._queues[faculty] = []
        self._subscribers[faculty].append(filter_fn)

    def unsubscribe(self, faculty: str) -> None:
        self._subscribers.pop(faculty, None)
        self._queues.pop(faculty, None)

    # ── Publish ──────────────────────────────────────────────────────────────

    def publish(self, envelope: Envelope) -> bool:
        """
        Validate, trace, and route an envelope.

        Returns True if the envelope was delivered to ≥1 subscriber.
        Returns False if rejected or expired (logs reason to _dropped).
        """
        ok, reason = envelope.is_valid()
        if not ok:
            self._dropped.append({
                "id": getattr(envelope, "id", "?"),
                "reason": f"REJECTED: {reason}",
                "ts": _now_ts(),
            })
            return False

        if envelope.is_expired():
            env_traced = _append_trace(envelope, "Bus[expired]")
            self._dropped.append({
                "id": envelope.id,
                "reason": "DROPPED: past expires",
                "expires": envelope.expires,
                "ts": _now_ts(),
            })
            return False

        env_traced = _append_trace(envelope, f"Bus@{_now_ts()}")

        delivered = False
        for faculty, filters in self._subscribers.items():
            if not self._addresses(env_traced, faculty):
                continue
            for filter_fn in filters:
                if filter_fn is None or filter_fn(env_traced):
                    self._queues[faculty].append(env_traced)
                    delivered = True
                    break

        return delivered

    # ── Consume ──────────────────────────────────────────────────────────────

    def get_messages(self, faculty: str) -> list[Envelope]:
        """
        Pull and clear all queued envelopes for `faculty`.
        Each call drains the queue (pull-and-clear semantics).
        """
        msgs = list(self._queues.get(faculty, []))
        if faculty in self._queues:
            self._queues[faculty] = []
        msgs.sort(key=lambda e: _PRIORITY_ORDER.get(e.priority, 2))
        return msgs

    # ── Observability ────────────────────────────────────────────────────────

    def dropped_log(self) -> list[dict]:
        """Return the audit trail of rejected/expired envelopes."""
        return list(self._dropped)

    def heartbeat(self) -> dict:
        """Snapshot of subscriber state for the Debug Agent."""
        return {
            "subscribers": list(self._subscribers.keys()),
            "queue_depths": {k: len(v) for k, v in self._queues.items()},
            "total_dropped": len(self._dropped),
        }

    # ── Internal ─────────────────────────────────────────────────────────────

    @staticmethod
    def _addresses(envelope: Envelope, faculty: str) -> bool:
        return envelope.receiver == "*" or envelope.receiver == faculty


# ── Helpers ──────────────────────────────────────────────────────────────────

def _now_ts() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def _append_trace(envelope: Envelope, hop: str) -> Envelope:
    return Envelope(
        id=envelope.id,
        sender=envelope.sender,
        receiver=envelope.receiver,
        priority=envelope.priority,
        context=dict(envelope.context),
        payload=dict(envelope.payload),
        confidence=envelope.confidence,
        expires=envelope.expires,
        trace=list(envelope.trace) + [hop],
    )


def make_envelope(
    sender: str,
    receiver: str,
    payload_type: str,
    body: dict,
    *,
    priority: str = "normal",
    confidence: float = 1.0,
    expires: str | None = None,
    context: dict | None = None,
    sender_ts: str | None = None,
) -> Envelope:
    """
    Convenience constructor — stamps id and first trace entry.

    payload_type examples:
        "cognitive_state_delta" — upstream faculty → CognitiveState
        "affect_state"          — Emotional Processing → downstream
        "execution_report"      — Embodiment → Reflection Faculty
        "attention_signal"      — Attention → Executive observability
    """
    ts = sender_ts or _now_ts()
    return Envelope(
        id=str(uuid.uuid4()),
        sender=sender,
        receiver=receiver,
        priority=priority,
        context=context or {
            "significance": 0.0,
            "memory_instruction": {"store": False, "priority": "peripheral"},
        },
        payload={"type": payload_type, "body": body},
        confidence=confidence,
        expires=expires,
        trace=[f"{sender}@{ts}"],
    )


# ── Module-level singleton ────────────────────────────────────────────────────

_bus: FacultyBus | None = None


def get_bus() -> FacultyBus:
    """Return the module-level bus singleton (created on first call)."""
    global _bus
    if _bus is None:
        _bus = FacultyBus()
        _wire_proof_pair(_bus)
    return _bus


def _wire_proof_pair(bus: FacultyBus) -> None:
    """
    Proof pair: Attention → Executive (WO-001 acceptance criterion).

    Attention publishes attention_signal envelopes; Executive subscribes with a
    filter so it only sees high/critical Attention signals. This mirrors the
    existing Attention → Executive channel without changing their decision logic.
    """
    bus.subscribe(
        "Executive",
        filter_fn=lambda e: (
            e.sender == "Attention"
            and e.payload.get("type") == "attention_signal"
            and e.priority in ("high", "critical")
        ),
    )


# ── Attention helper — proof pair publisher ──────────────────────────────────

def publish_attention_signal(
    intent: str,
    valence: float,
    momentum: float,
    confidence: float = 0.8,
    priority: str = "normal",
) -> bool:
    """
    Convenience for Attention faculty to publish its signal.
    Proof-pair complement to the Executive subscription above.

    Returns True if delivered to at least one subscriber.
    """
    bus = get_bus()
    env = make_envelope(
        sender="Attention",
        receiver="Executive",
        payload_type="attention_signal",
        body={
            "intent":   intent,
            "valence":  valence,
            "momentum": momentum,
        },
        priority=priority,
        confidence=confidence,
    )
    delivered = bus.publish(env)
    return delivered
