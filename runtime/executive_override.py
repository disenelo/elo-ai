"""
runtime/executive_override.py — D7 ruling (Card 0035).

Post-Executive action rewrites are SAFETY OVERRIDES, not decisions. Runtime
Invariant #2 says the Executive is the sole decider. Any code that changes
`exec_decision["action"]` after the Executive has decided must:

  1. Declare a REGISTERED ground (a documented safety reason).
  2. Journal the original action, the override, and the rule that fired.
  3. Never add a new ground without an Architect ruling — attempting to
     override with an unregistered ground raises AssertionError so the
     violation is loud and caught in tests.

Two grounds are registered:

  * `safety-stabilisation` — loop-detection forces stabilise/DIRECT so eLo
    doesn't runaway a bad turn (server.py stabilisation forcer).
  * `seam-a-routing` — plain imperatives / greeting-gap family that the
    frozen Executive can't distinguish natively (WO-020 Seam A, WO-029).

These are the ONLY sanctioned post-Executive action rewrites. Anything else
is a One-Brain breach.
"""
from __future__ import annotations

import logging

_log = logging.getLogger(__name__)

# ── Registered grounds — the whitelist ──────────────────────────────────────

REGISTERED_GROUNDS: frozenset[str] = frozenset({
    "safety-stabilisation",
    "seam-a-routing",
})


class UnregisteredOverrideGround(AssertionError):
    """A post-Executive override tried to use a ground not on the whitelist."""


def apply_executive_override(
    exec_decision: dict,
    *,
    ground: str,
    rule: str,
    updates: dict,
) -> dict:
    """
    Apply a post-Executive safety override to `exec_decision`.

    Returns a NEW dict with:
      - fields from `updates` merged in
      - `original_action` preserved (from prior override if already set, else
        the pre-override action) so a chain of overrides still names the
        Executive's original choice
      - `executive_override` = {ground, rule} — the documented reason
      - `overridden_by_safety` / `overridden_by_routing` set for back-compat
        with existing journal readers (decision_journal.record)

    Raises UnregisteredOverrideGround if `ground` is not in
    REGISTERED_GROUNDS — new grounds require an Architect ruling first.
    """
    if ground not in REGISTERED_GROUNDS:
        raise UnregisteredOverrideGround(
            f"executive override ground {ground!r} is not registered. "
            f"Registered grounds: {sorted(REGISTERED_GROUNDS)}. "
            "New grounds require an Architect ruling (Card 0035 D7)."
        )

    out = dict(exec_decision)
    # Preserve the earliest original_action across chained overrides.
    if "original_action" not in out or not out.get("original_action"):
        out["original_action"] = exec_decision.get("action")
    out.update(updates)

    out["executive_override"] = {"ground": ground, "rule": rule}
    if ground == "safety-stabilisation":
        out["overridden_by_safety"] = True
    else:
        out["overridden_by_routing"] = True

    _log.info(
        "executive_override applied: ground=%s rule=%s original_action=%s → %s",
        ground, rule, out.get("original_action"), out.get("action"),
    )
    return out
