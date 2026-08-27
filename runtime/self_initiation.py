"""
runtime/self_initiation.py — SP-31 + SP-32 (WO-SP31-SP32).

Self-initiation gate: ATTENDING detection + HARD-QUIET + significance threshold.
Autonomous spine call path: world-event triggered, not user-triggered.

ACTIVATION: Default OFF. ELO_SELF_INITIATION=1 (David L3) required to activate.
Fail-quiet everywhere: any signal read failure → most conservative state (blocked).
Do not flip the default without L3 unfreeze.

Design ruling: blender/agent_bus/design/FROM_DESIGN_2026-08-24_Q-ATT-1_ruling_david_attending.md
Board acceptance: docs/architecture/findings/BOARD_ACCEPTANCE_DESIGN_RULINGS_Q-ATT-1_SP38_2026-08-24.md
"""
from __future__ import annotations

import json
import logging
import os
import time

_log = logging.getLogger(__name__)

# ── Design constants (Q-ATT-1 ruling 2026-08-24) — tunable, do not change without Design/David
ATTEND_CONVERSE_SECS  = 45     # A1: max age of last conversing pulse to count as ATTENDING
ATTEND_INTERACT_SECS  = 20     # A3: max age of last direct eLo interaction
SELF_INIT_THRESHOLD   = 0.72   # §2: significance floor for verbal self-initiation (ATTENDING)
EXCEPTIONAL_THRESHOLD = 0.90   # §3: significance floor for verbal when NOT attending but present
DEEP_FOCUS_SECS       = 25     # Q3: eLo-not-front + deep-focus context threshold (seconds)
SELF_INIT_COOLDOWN    = 180    # Q4a: minimum seconds between eLo self-initiations
DISMISS_QUIET_SECS    = 300    # Q4b: quiet window after David dismisses an initiation

# ── Module-level timestamp state ─────────────────────────────────────────────
_last_conversing_ts: float = 0.0   # A1: last recorded conversation pulse
_last_interact_ts:   float = 0.0   # A3: last direct eLo interaction
_last_self_init_ts:  float = 0.0   # Q4a: last self-initiation
_last_dismiss_ts:    float = 0.0   # Q4b: last dismiss by David

_ROOT                = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_PRESENCE_PATH       = os.path.join(_ROOT, "blender", "presence.json")
_PRESENCE_STATE_PATH = os.path.join(_ROOT, "blender", "presence_state.json")


# ── Public mutators (called by server.py on events) ──────────────────────────

def record_conversation_pulse() -> None:
    """Call on every user turn. Updates A1 signal."""
    global _last_conversing_ts
    _last_conversing_ts = time.time()


def record_direct_interaction() -> None:
    """Call when David directly interacts with eLo (drag, click, summon, context-menu). A3."""
    global _last_interact_ts
    _last_interact_ts = time.time()


def record_self_init() -> None:
    """Call immediately after eLo fires a self-initiated spine turn. Starts Q4a cooldown."""
    global _last_self_init_ts
    _last_self_init_ts = time.time()


def record_dismiss() -> None:
    """Call when David dismisses or closes an eLo self-initiated turn. Starts Q4b quiet window."""
    global _last_dismiss_ts
    _last_dismiss_ts = time.time()


# ── Signal helpers ───────────────────────────────────────────────────────────

def _read_json(path: str) -> dict:
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _compute_attending(now: float) -> bool:
    """
    ATTENDING = True when ANY of A1, A2, A3 holds.
    Fail-quiet: any signal unavailable → that condition = False.

    A1: conversing pulse within ATTEND_CONVERSE_SECS.
    A2: eLo is the front window (eloOnFront=True in presence_state.json — proxy for appFocused).
    A3: direct interaction within ATTEND_INTERACT_SECS.
    """
    # A1 — recent conversing pulse
    if _last_conversing_ts > 0.0 and (now - _last_conversing_ts) < ATTEND_CONVERSE_SECS:
        return True

    # A2 — eLo on front (proxy for appFocused)
    ps = _read_json(_PRESENCE_STATE_PATH)
    if ps.get("eloOnFront", False):
        return True

    # A3 — recent direct interaction
    if _last_interact_ts > 0.0 and (now - _last_interact_ts) < ATTEND_INTERACT_SECS:
        return True

    return False


def _compute_hard_quiet(now: float) -> bool:
    """
    HARD-QUIET = True when ANY of Q1-Q4 holds.
    HARD-QUIET overrides all — eLo stays fully quiet.
    Fail-quiet: any read failure → assume the safest (non-quiet) state for that condition only.
    """
    # Q1 — user away
    p = _read_json(_PRESENCE_PATH)
    if p.get("state") == "away":
        return True

    # Q2 — take-five / privacy hold active
    ps = _read_json(_PRESENCE_STATE_PATH)
    mode = ps.get("mode", "")
    if mode in ("DORMANT", "PRIVACY", "TAKE_FIVE", "HIDDEN"):
        return True

    # Q3 — deep focus elsewhere (eLo not front + deep-focus engagement)
    if not ps.get("eloOnFront", True) and ps.get("engagement", "") in ("DEEP_IDLE", "DEEP_FOCUS"):
        return True

    # Q4a — self-initiation cooldown
    if _last_self_init_ts > 0.0 and (now - _last_self_init_ts) < SELF_INIT_COOLDOWN:
        return True

    # Q4b — dismiss quiet window
    if _last_dismiss_ts > 0.0 and (now - _last_dismiss_ts) < DISMISS_QUIET_SECS:
        return True

    return False


# ── Primary gate ─────────────────────────────────────────────────────────────

def is_enabled() -> bool:
    """True only if David L3 has activated self-initiation (ELO_SELF_INITIATION=1)."""
    return os.environ.get("ELO_SELF_INITIATION", "0") == "1"


class SelfInitResult:
    """Gate result from may_self_initiate()."""
    __slots__ = ("allowed", "tier", "reason")

    def __init__(self, allowed: bool, tier: str, reason: str) -> None:
        self.allowed = allowed
        self.tier    = tier     # "verbal" | "ambient_only" | "blocked"
        self.reason  = reason

    def __repr__(self) -> str:
        return f"SelfInitResult(allowed={self.allowed}, tier={self.tier!r}, reason={self.reason!r})"


def may_self_initiate(significance_score: float) -> SelfInitResult:
    """
    SP-31 + SP-32 gate: may eLo self-initiate a spine turn?

    Returns SelfInitResult.
    allowed=True + tier="verbal" → caller may fire spine.run() with trigger_source="world_event".
    allowed=False → do not fire; tier indicates why (ambient_only = below threshold, blocked = gate).

    Fail-quiet: any exception → blocked.
    """
    try:
        if not is_enabled():
            return SelfInitResult(False, "blocked", "self_initiation_disabled")

        now = time.time()

        if _compute_hard_quiet(now):
            return SelfInitResult(False, "blocked", "hard_quiet")

        attending = _compute_attending(now)

        # Tier 1: ATTENDING + meets threshold
        if attending and significance_score >= SELF_INIT_THRESHOLD:
            return SelfInitResult(True, "verbal", "attending+significant")

        # Tier 2: NOT attending but significance is exceptional
        if not attending and significance_score >= EXCEPTIONAL_THRESHOLD:
            return SelfInitResult(True, "verbal", "exceptional_significance")

        # Below SELF_INIT_THRESHOLD — ambient expression only, no spine call
        if significance_score < SELF_INIT_THRESHOLD:
            return SelfInitResult(False, "ambient_only", "below_threshold")

        # ATTENDING condition not met + score in [0.72, 0.90)
        return SelfInitResult(False, "ambient_only", "not_attending")

    except Exception as exc:
        _log.warning("self_initiation gate error (fail-quiet): %s", exc)
        return SelfInitResult(False, "blocked", f"error:{exc}")
