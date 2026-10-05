"""
runtime/body_relay.py — WO-CANON-VII §D: Body perception UP-relay audit.

Vol VII Ch.5 §5.7 L1: every body perception must relay UP on the canonical event
channel. Previously this existed only in the spec — no code checked it.

This module provides:
  relay_body_event()       — emitter; called whenever body state changes
  audit_body_relay()       — audit checker; flags VIOLATION if body state appeared
                             without a preceding DOWN command or bounded reflex

Rule:
  Every observed body state is either:
    (a) A DOWN command — something with issued_by in the decision journal preceded it, OR
    (b) A bounded reflex — self-reported, declared as reflex at emission time.
  Anything else is a VIOLATION: body state that eLo is reporting without knowing why.

Self-model updates from ACK, not command:
  commanded-but-unACKed = pending/last-known, NOT verified.
"""
from __future__ import annotations

import json
import logging
import os
import time

_log = logging.getLogger(__name__)
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_RELAY_LOG = os.path.join(_ROOT, "self", "journals", "body_relay.jsonl")


def relay_body_event(event_kind: str, payload: dict, *, is_reflex: bool = False) -> None:
    """
    Emit a body perception event UP to the canonical event channel.

    Args:
        event_kind  — e.g. "sit_commanded", "sit_acked", "movement_detected"
        payload     — arbitrary dict describing the event
        is_reflex   — True if this is a bounded reflex (not a commanded action)

    Silent on failure — never blocks a turn.
    """
    entry = {
        "ts":         time.time(),
        "event_kind": event_kind,
        "is_reflex":  is_reflex,
        "payload":    payload,
    }
    try:
        os.makedirs(os.path.dirname(_RELAY_LOG), exist_ok=True)
        with open(_RELAY_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception as e:
        _log.debug("body_relay.relay_body_event failed (non-critical): %s", e)


# How recently a relay event must have been emitted to count as evidence
# about the body RIGHT NOW. A sit is commanded and ACKed within seconds;
# two minutes is generous for that and still far short of treating last
# week as live.
RELAY_FRESH_S: float = 120.0


def recent_relay_events(n: int = 10, *, max_age_s: float | None = None) -> list:
    """
    Return the last n body relay events (oldest first).

    max_age_s drops events older than that many seconds. Default None keeps
    the unbounded behaviour for callers that want the raw tail; the audit
    passes a bound, because an old event is not evidence about now.
    """
    try:
        with open(_RELAY_LOG, encoding="utf-8") as f:
            lines = f.readlines()
    except FileNotFoundError:
        return []
    results = []
    for line in lines[-n:]:
        line = line.strip()
        if not line:
            continue
        try:
            results.append(json.loads(line))
        except Exception:
            pass
    if max_age_s is not None:
        _cutoff = time.time() - float(max_age_s)
        results = [e for e in results
                   if isinstance(e, dict) and float(e.get("ts") or 0.0) >= _cutoff]
    return results


def audit_body_relay(body, recent_journal: list) -> dict:
    """
    WO-CANON-VII §D: Audit whether current body state has a valid upstream cause.

    Args:
        body           — BodySchema instance (from CognitiveSnapshot)
        recent_journal — list of recent decision_journal entries (dicts)

    Returns:
        {
          "ok": bool,
          "violations": list[str],    # body states with no known cause
          "pending_unacked": list[str],  # commanded but no ACK yet
          "notes": str,
        }
    """
    violations: list = []
    pending_unacked: list = []

    # Check sit state: if pending_sit=True, there must be a "sit" action in the
    # recent decision journal (DOWN command) OR a relay event preceding it.
    if getattr(body, "pending_sit", False):
        # Look for a sit command in the journal
        sit_commanded = any(
            e.get("action") in ("sit", "sit_pose", "avatar_sit")
            for e in recent_journal
        )
        # Look for a relay event
        # Unbounded, this read could never fail. Measured 2026-10-05: the
        # last 20 events in the live journal were all "sit_commanded",
        # aged 0.0 to 37.5 DAYS, every one written by the test suite. So
        # sit_relayed was permanently True, and both branches below — the
        # VIOLATION and the pending_unacked — were unreachable. The audit
        # returned ok=True for the exact case it exists to catch: a body
        # sitting with nothing having commanded it.
        relay_events = recent_relay_events(20, max_age_s=RELAY_FRESH_S)
        sit_relayed = any(
            e.get("event_kind") in ("sit_commanded", "sit_acked")
            for e in relay_events
        )
        if not sit_commanded and not sit_relayed:
            violations.append("pending_sit: body shows sit-pending with no preceding DOWN command or relay event")
        elif sit_commanded and not sit_relayed:
            # Commanded but not ACK'd — this is the correct unverified state
            pending_unacked.append("sit: commanded, awaiting ACK — status is last-known, not verified")

    # queued_intent: any queued movement while sit is pending must have been commanded
    queued = getattr(body, "queued_intent", "")
    if queued and not getattr(body, "pending_sit", False):
        # queued_intent without a pending_sit is unexpected — flag it
        violations.append(f"queued_intent='{queued}' present without pending_sit context")

    ok = len(violations) == 0
    if violations:
        notes = "VIOLATION: " + "; ".join(violations)
        _log.warning("body_relay audit VIOLATION: %s", violations)
    elif pending_unacked:
        notes = "pending_unacked: " + "; ".join(pending_unacked)
    else:
        notes = "ok"

    return {
        "ok":               ok,
        "violations":       violations,
        "pending_unacked":  pending_unacked,
        "notes":            notes,
    }
