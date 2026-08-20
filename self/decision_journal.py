"""
self/decision_journal.py — WO-082: Executive Decision Journal.

Append-only trace of eLo's per-turn decisions.
Source of truth for "why did you do that?" readback.
Failure entries update per-action reliability (Horizon #6).

ADR-Exec-001 (never invent) · ADR-Exec-005 (learn from consequences) · WO-082.
"""
from __future__ import annotations

import json
import logging
import os
import time

_log = logging.getLogger(__name__)
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_JOURNAL = os.path.join(_ROOT, "self", "journals", "decision_journal.jsonl")
_RELIABILITY = os.path.join(_ROOT, "self", "journals", "action_reliability.json")

# W2 (card 0040): stable per-process id, monotonic across restarts, persisted.
# Import once at module load — every record() call in this process shares it.
from runtime.session_id import SESSION_ID
_SESSION_ID: str = SESSION_ID


# ── Reliability persistence ───────────────────────────────────────────────────

def _load_reliability() -> dict:
    try:
        with open(_RELIABILITY, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_reliability(rel: dict) -> None:
    os.makedirs(os.path.dirname(_RELIABILITY), exist_ok=True)
    tmp = _RELIABILITY + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(rel, f, indent=2, ensure_ascii=False)
    os.replace(tmp, _RELIABILITY)


def get_reliability(action: str) -> float:
    """Return reliability score 0..1 for an action. Default 1.0 (never failed)."""
    return _load_reliability().get(action, 1.0)


def known_failures(action: str) -> list:
    """Return known_failure_condition strings for a given action."""
    results = []
    try:
        with open(_JOURNAL, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    e = json.loads(line)
                    if e.get("action") == action and e.get("known_failure_condition"):
                        results.append(e["known_failure_condition"])
                except Exception:
                    pass
    except FileNotFoundError:
        pass
    return results


# ── Core write API ────────────────────────────────────────────────────────────

def record(
    *,
    turn: str,
    action: str,
    exec_decision: dict,
    backend: str,
    outcome: str = "success",
    learning: str = "",
) -> None:
    """Append one decision trace entry. Silent on failure — never blocks a turn."""
    try:
        # Reconstruct alternatives considered from override fields.
        alternatives: list = []
        original = exec_decision.get("original_action")
        if original and original != action:
            reason = (exec_decision.get("reason")
                      or exec_decision.get("cal_reason")
                      or "routing override")
            alternatives.append({"rejected": original, "reason": reason})

        # D7 ruling (Card 0035): overrides are uniform — every executive_override
        # journals its ground + rule + original action. Back-compat: also emit
        # the legacy ground-name in `overrides` for existing readers.
        overrides: list = []
        eo = exec_decision.get("executive_override")
        if isinstance(eo, dict) and eo.get("ground"):
            overrides.append({
                "ground":          eo.get("ground"),
                "rule":            eo.get("rule"),
                "original_action": exec_decision.get("original_action"),
                "new_action":      action,
            })
        # Legacy flags — still honoured so old journal entries stay readable.
        if exec_decision.get("overridden_by_safety") and not any(
            isinstance(o, dict) and o.get("ground") == "safety-stabilisation" for o in overrides
        ):
            overrides.append("safety-stabilisation")
        if exec_decision.get("overridden_by_routing") and not any(
            isinstance(o, dict) and o.get("ground") == "seam-a-routing" for o in overrides
        ):
            overrides.append("seam-a-routing")

        entry = {
            "ts":                    time.time(),
            "session_id":            _SESSION_ID,
            "turn":                  turn[:120],
            "action":                action,
            "trigger":               exec_decision.get("cal_reason") or "unknown",
            # D1 ruling (Card 0035): `intent` = COGNITIVE intent (what the Executive
            # decided on); `capability_hint` = intent_engine's router hint. Journal
            # records BOTH so the "why did you do that?" answer names the intent that
            # was actually decided on, not the router's disjoint vocabulary.
            "intent":                exec_decision.get("intent", ""),
            "capability_hint":       exec_decision.get("capability_hint", ""),
            "tone":                  exec_decision.get("tone", ""),
            "confidence":            exec_decision.get("confidence"),
            "alternatives_rejected": alternatives,
            "overrides":             overrides,
            "cognitive_load":        exec_decision.get("cognitive_load", ""),
            "outcome":               outcome,
            "backend":               backend,
            "learning":              learning,
        }
        os.makedirs(os.path.dirname(_JOURNAL), exist_ok=True)
        with open(_JOURNAL, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception as e:
        _log.debug("decision_journal.record failed (non-critical): %s", e)


def record_failure(action: str, condition_desc: str) -> None:
    """
    Record a known failure condition and drop per-action reliability by 0.15.
    Feeds capability confidence (WO-055) so eLo can say "I don't think I can do that."
    """
    try:
        entry = {
            "ts":                      time.time(),
            "session_id":              _SESSION_ID,
            "action":                  action,
            "outcome":                 "failure",
            "known_failure_condition": condition_desc,
            "learning":                f"avoid: {condition_desc}",
        }
        os.makedirs(os.path.dirname(_JOURNAL), exist_ok=True)
        with open(_JOURNAL, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

        rel = _load_reliability()
        rel[action] = round(max(0.0, rel.get(action, 1.0) - 0.15), 3)
        _save_reliability(rel)
    except Exception as e:
        _log.debug("decision_journal.record_failure failed: %s", e)


# ── Read API ──────────────────────────────────────────────────────────────────

def last_n(n: int = 3) -> list:
    """Return last N journal entries as dicts (oldest first)."""
    try:
        with open(_JOURNAL, encoding="utf-8") as f:
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
    return results


def explain_last() -> str:
    """
    Natural-language explanation of the last decision.
    Reads the real trace — never fabricates a motive.
    """
    entries = last_n(1)
    if not entries:
        return "I don't have a decision trace yet — ask again after I've done something."
    e = entries[-1]

    action    = e.get("action", "?")
    trigger   = e.get("trigger") or "no trigger recorded"
    intent    = e.get("intent", "")
    alts      = e.get("alternatives_rejected") or []
    overrides = e.get("overrides") or []
    outcome   = e.get("outcome", "unknown")
    kfc       = e.get("known_failure_condition", "")
    rel       = get_reliability(action)

    parts = [f"Last action was `{action}`."]
    parts.append(f"Trigger: {trigger}.")
    if intent:
        parts.append(f"Intent: {intent}.")
    if alts:
        rejected = alts[0].get("rejected", "?")
        why = alts[0].get("reason", "routing logic")
        parts.append(f"Originally considered `{rejected}`, overridden by {why}.")
    if overrides:
        parts.append(f"Override applied: {', '.join(overrides)}.")
    if kfc:
        parts.append(f"That one failed — known condition: {kfc}.")
    elif outcome == "success":
        parts.append("Outcome: success.")
    if rel < 1.0:
        parts.append(f"Reliability for `{action}`: {rel:.0%}.")

    return " ".join(parts)
