"""
runtime/the_moment.py — WO-079: The Situated Self Invariant / The Moment.

Compiles a verified snapshot of eLo's current state each turn from existing
sources (self-model, perch_state, capability registry). Writes self/state/
the_moment.json for cross-process reading (robot NeoPixels, iOS, DesktopBuddy).

This is ASSEMBLY, not a new daemon. One call per turn, synchronous, <1ms.

ADR-Exec-004 (Situated Self) · ADR-Exec-006 (Executive Assembly) · WO-079.
"""
from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import dataclass, field

_log = logging.getLogger(__name__)
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_MOMENT_PATH = os.path.join(_ROOT, "self", "state", "the_moment.json")

# Epistemic tier vocabulary (CA-proposed, WO-079; extended WO-110 beyond body)
# OBSERVED   — directly sensed this turn (hardware/OS/tool result)
# INFERRED   — probabilistic, derived from recent observation
# REMEMBERED — from persistent memory/vault (may be stale, source declared)
# LAST-KNOWN — from state file, age unknown
# LIVE       — checked against live registry this turn
# UNKNOWN    — no data available; absence itself is a statable fact
_TIER = {
    "observed":   "[observed]",
    "verified":   "[verified]",    # alias for observed (body legacy)
    "inferred":   "[inferred]",
    "remembered": "[remembered]",
    "last-known": "[last-known]",
    "live":       "[live]",
    "unknown":    "[unknown]",
    "absent":     "[absent]",
}

# Recency threshold for demoting "observed" to "last-known" (90 seconds)
_FRESH_THRESHOLD_S = 90.0


def tier_fact(
    value,
    *,
    source: str = "unknown",
    age_s: float | None = None,
    confirmed: bool = False,
) -> str:
    """
    WO-110: Compute an epistemic tier for ANY fact, not just body state.

    Args:
        value     — the fact value (None / empty = UNKNOWN)
        source    — where it came from: "sensor", "vault", "lesson", "inferred",
                    "tool", "user_statement", "unknown"
        age_s     — seconds since the fact was acquired (None = unknown age)
        confirmed — True if the fact was directly confirmed this turn

    Returns one of the _TIER keys.
    """
    if value is None or value == "" or value == [] or value == {}:
        return "unknown"
    if source in ("sensor", "tool") or confirmed:
        if age_s is not None and age_s > _FRESH_THRESHOLD_S:
            return "last-known"
        return "observed"
    if source in ("vault", "lesson", "memory"):
        return "remembered"
    if source == "inferred":
        return "inferred"
    # Default: if we have a value but uncertain provenance, treat as last-known
    return "last-known"


# ── Speech Licence (WO-CANON-VII §B) ─────────────────────────────────────────

# Tier priority order: best → worst (highest index = most uncertain)
_TIER_RANK = ["observed", "verified", "live", "inferred", "remembered", "last-known", "unknown", "absent"]


@dataclass
class SpeechLicence:
    """
    Epistemic gate computed from the_moment tier snapshot.

    The Executive emits this alongside the plan; it governs what eLo may assert
    vs. what he must hedge or withhold.

    allow          — always True (eLo can always speak)
    hedge_required — True if any field is last-known/unknown; eLo must use hedging language
    violations     — fields where tier is "unknown" or "absent"; eLo must NOT assert facts here
    min_tier       — the worst tier across all snapshot fields
    notes          — human-readable summary for prompt injection
    """
    tier_snapshot: dict
    allow: bool
    hedge_required: bool
    violations: tuple   # field names where eLo must not assert
    min_tier: str
    notes: str


def verify_response_tiers(tier_snapshot: dict) -> SpeechLicence:
    """
    WO-CANON-VII §B: Wire tier markers to a runtime gate.

    Args:
        tier_snapshot: {field_name: tier_key} — e.g. {"pose": "last-known", ...}

    Returns a SpeechLicence the Executive uses to annotate and constrain output.
    """
    violations = tuple(
        k for k, v in tier_snapshot.items()
        if v in ("unknown", "absent")
    )
    hedge_required = any(
        v in ("unknown", "last-known", "absent")
        for v in tier_snapshot.values()
    )

    def _rank(t: str) -> int:
        try:
            return _TIER_RANK.index(t)
        except ValueError:
            return len(_TIER_RANK)

    all_tiers = list(tier_snapshot.values())
    min_tier = max(all_tiers, key=_rank) if all_tiers else "unknown"

    if violations:
        notes = f"GATE: eLo must not assert facts for unknown fields: {', '.join(violations)}"
    elif hedge_required:
        notes = "GATE: some fields are last-known — hedge uncertain claims"
    else:
        notes = "GATE: all fields at observed/live — no hedge required"

    return SpeechLicence(
        tier_snapshot=tier_snapshot,
        allow=True,
        hedge_required=hedge_required,
        violations=violations,
        min_tier=min_tier,
        notes=notes,
    )


def compile(  # noqa: A001 — shadows builtin intentionally for domain clarity
    state,
    *,
    perch_fresh: bool = False,
    pose_acked: bool = False,
) -> dict:
    """
    Build the current-moment snapshot from verified state.

    Args:
        state        : EloSelfState (self/elo_self_model.py)
        perch_fresh  : True if perch_state.json was successfully read THIS turn
        pose_acked   : True if a pose ACK was received this turn

    Returns a plain dict — serialisable to JSON for cross-process reading.
    """
    now = time.time()

    # Capability registry — live check (never guess)
    caps_live: list[str] = []
    try:
        from runtime.capabilities.registry import all_enabled as _cap_all
        caps_live = [getattr(c, "id", str(c)) for c in _cap_all()]
    except Exception:
        pass

    # Nearby surfaces — inferred if data present, unknown if absent
    _nearby = list(state.nearby_surfaces or [])
    _nearby_tier = tier_fact(_nearby, source="inferred") if _nearby else "unknown"

    # Recent behaviour — observed this session (from record_behaviour calls)
    _recent_bhv = dict(getattr(state, "recent_behavior", {}) or {})
    _bhv_tier = tier_fact(_recent_bhv, source="sensor", confirmed=True) if _recent_bhv else "unknown"

    # Lessons — from lesson store (remembered, not live)
    _lessons: list[dict] = []
    try:
        from self.lesson_store import recall as _ls_recall
        _lessons = _ls_recall()[:3]
    except Exception:
        pass
    _lessons_tier = tier_fact(_lessons, source="lesson") if _lessons else "unknown"

    # WO-115: Autobiography — chronological record of ACK-verified events
    _autobiography: list[dict] = []
    try:
        from self.emergent_cognition import recent_autobiography as _ra
        _autobiography = _ra(5)
    except Exception:
        pass

    # WO-118 Row 14 ROUTE: recent route history — readable by Executive
    _route_history: list[dict] = []
    try:
        from self.route_memory import recent_routes as _rr
        _route_history = _rr(5)
    except Exception:
        pass

    # WO-CAP-001: last 3 capability results — readable by Executive
    _cap_results: tuple = ()
    try:
        from self.capability_memory import recent_capability_results as _rcr
        _cap_results = tuple(_rcr(3))
    except Exception:
        pass

    # WO-126 Row 26 MEANING: last turn's significance profile.
    # evaluate() runs AFTER the response is sent, so this is the PREVIOUS turn's score.
    # eLo must never attribute this score to the sentence he is currently producing.
    # No file → empty dict (no score → no claim).
    # Staleness: a score written hours ago is not "the last thing that mattered" — drop it.
    _SIGNIFICANCE_MAX_AGE_S = 1800.0  # 30 minutes — beyond this the session has moved on
    _last_significance: dict = {}
    try:
        _sig_path = os.path.join(_ROOT, "self", "state", "last_significance.json")
        with open(_sig_path, encoding="utf-8") as _sigf:
            _sig_record = json.load(_sigf)
        _sig_age = now - _sig_record.get("ts", 0.0)
        if _sig_age <= _SIGNIFICANCE_MAX_AGE_S:
            _last_significance = _sig_record
        else:
            # Card 0013 fix 4: stale score dropped — WARN so a dead journal_router
            # can't hide. If this fires every turn the writer has stopped.
            _log.warning(
                "last_significance stale: age=%.0fs > max=%.0fs — dropped to {}. "
                "If persistent, journal_router.route() is not being called.",
                _sig_age, _SIGNIFICANCE_MAX_AGE_S,
            )
    except Exception:
        pass

    # WO-108: Last directed-look observation record
    _last_obs: dict = {}
    try:
        from runtime.directed_look import last_observation as _lo
        _obs_list = _lo(1)
        _last_obs = _obs_list[0].to_dict() if _obs_list else {}
    except Exception:
        pass

    # WO-113: Gap assessment — 7-state vocabulary with real numbers
    _gap_results: list[dict] = []
    try:
        import json as _json
        import os as _os
        _sp_path = _os.path.join(_ROOT, "blender", "elo_spatial.json")
        _spatial: dict = {}
        with open(_sp_path, encoding="utf-8") as _spf:
            _spatial = _json.load(_spf)
    except Exception:
        _spatial = {}
    try:
        from runtime.gap_assessment import assess as _gap_assess
        _gap_results = [
            r.to_dict() for r in _gap_assess(
                list(state.available_actions or []),
                spatial=_spatial,
                locomotion_health=str(getattr(state, "locomotion_faculty_health", "OK")),
            )
        ]
    except Exception:
        pass

    moment = {
        "ts":               now,
        "embodiment":       state.embodiment,
        "embodiment_tier":  tier_fact(state.embodiment, source="sensor", confirmed=True),
        "pose":             state.pose,
        "pose_tier":        "observed" if pose_acked else "last-known",
        "surface":          state.surface or state.location or "",
        "surface_tier":     "observed" if perch_fresh else "last-known",
        "balance":          state.balance,
        "size_cm": {
            "height": state.size.get("height_cm"),
            "reach":  state.size.get("reach_cm"),
            "jump":   state.size.get("jump_cm"),
        },
        "available_actions":    list(state.available_actions or []),
        "current_action":       state.current_action or "idle",
        "locomotion_health":    state.locomotion_faculty_health,
        "locomotion_tier":      "live",
        "capabilities":         caps_live,
        "capabilities_tier":    "live" if caps_live else "unknown",
        "nearby_surfaces":      _nearby,
        "nearby_tier":          _nearby_tier,
        "mood":                 round(getattr(state, "mood", 0.5), 3),
        "curiosity":            round(getattr(state, "curiosity", 0.5), 3),
        "goal":                 getattr(state, "goal", ""),
        "last_self_update":     getattr(state, "last_updated", 0.0),
        # WO-110: non-body epistemic facts
        "recent_behaviour":     _recent_bhv,
        "recent_behaviour_tier": _bhv_tier,
        "lessons":              _lessons,
        "lessons_tier":         _lessons_tier,
        # WO-115: autobiography — chronological verified event log (last 5)
        "autobiography":        _autobiography,
        "autobiography_tier":   "observed" if _autobiography else "unknown",
        # WO-118 Row 14 ROUTE: last 5 route records — Executive can consult history
        "route_history":        _route_history,
        # WO-CAP-001: last 3 capability results
        "capability_results":   list(_cap_results),
        # WO-113: gap assessment — one GapResult per jump-class action
        "gap_assessment":       _gap_results,
        # WO-108: last directed-look observation record (for Executive verified-speech gate)
        "last_observation":     _last_obs,
        # WO-126 Row 26 MEANING: previous turn's significance profile.
        # Empty dict when no prior turn exists — eLo must not claim significance without it.
        "last_significance":    _last_significance,
    }
    return moment


def write(state, *, perch_fresh: bool = False, pose_acked: bool = False) -> None:
    """Compile and write the_moment.json. Silent on failure — never blocks a turn."""
    try:
        moment = compile(state, perch_fresh=perch_fresh, pose_acked=pose_acked)
        os.makedirs(os.path.dirname(_MOMENT_PATH), exist_ok=True)
        with open(_MOMENT_PATH, "w", encoding="utf-8") as f:
            json.dump(moment, f, indent=2, ensure_ascii=False)
    except Exception as e:
        _log.debug("the_moment write failed (non-critical): %s", e)


def situated_with_epistemic(state, *, perch_fresh: bool = False, pose_acked: bool = False) -> str:
    """
    Returns a [SITUATED SELF] block with epistemic tier markers.
    Drop-in replacement for self.elo_self_model.situated_block() — extends it
    with WO-079 tier labels so eLo's language can match verification level.
    """
    m = compile(state, perch_fresh=perch_fresh, pose_acked=pose_acked)

    where     = m["surface"] or "unknown"
    pose      = m["pose"]
    e_pose    = _TIER[m["pose_tier"]]
    e_surface = _TIER[m["surface_tier"]]
    e_body    = _TIER["verified"]  # size/embodiment
    e_caps    = _TIER[m["capabilities_tier"]]
    e_near    = _TIER[m["nearby_tier"]]

    acts = ", ".join(m["available_actions"]) if m["available_actions"] else "unknown"
    caps = ", ".join(m["capabilities"][:8]) if m["capabilities"] else "none listed"

    lines = [
        "[SITUATED SELF — verified. Answer where you are / what you can do / pose ONLY from "
        "this. Never invent; if a field is unknown say so — never claim unverified state.]",
        f"embodiment: {m['embodiment']} {e_body}",
        f"where: {where} {e_surface}   pose: {pose} {e_pose}   balance: {m['balance']}",
        f"size: ~{m['size_cm']['height']}cm tall · reach ~{m['size_cm']['reach']}cm · "
        f"jump ~{m['size_cm']['jump']}cm {e_body}",
        f"actions now: {acts}",
        f"capabilities: {caps} {e_caps}",
        f"locomotion: {m['locomotion_health']} {_TIER['live']}",
    ]
    # WO-110 Row 11: UNKNOWN must be statable — always show nearby, even when absent
    if m["nearby_surfaces"]:
        lines.append(f"nearby: {', '.join(map(str, m['nearby_surfaces']))} {e_near}")
    else:
        lines.append(f"nearby: [unknown] — no surfaces perceived")
    if m["current_action"] and m["current_action"] != "idle":
        lines.append(f"currently: {m['current_action']}")

    # Ruling 1 (card 0012) — Verified Speech for last_significance:
    # only surface the score when it is present, and only as the PREVIOUS turn's.
    # eLo must never attribute the score to the sentence he is currently producing.
    _ls = m.get("last_significance") or {}
    _prof = _ls.get("profile") if isinstance(_ls, dict) else None
    if _prof and _prof.get("overall") is not None:
        _overall = _prof.get("overall")
        _prev_action = _ls.get("action", "?")
        _outcome = _ls.get("outcome")
        _tag = f", outcome={_outcome}" if _outcome else ""
        lines.append(
            f"last turn ({_prev_action}{_tag}): significance={float(_overall):.2f} "
            f"[previous turn only — NOT this sentence]"
        )
    return "\n".join(lines)
