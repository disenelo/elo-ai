"""
runtime/capabilities/health_producer.py — Card 0032: Capability health producer.

Derives Capability.health_state from real signals so eLo's self-knowledge is
accurate. Before this module, health_state defaulted to ONLINE on every capability
and nothing ever changed it.

Signal sources:
  1. Executor gate: capability with agent_module="tools.tool_router" but no
     matching _AGENTS key → OFFLINE (C3 close — Executive cannot select a
     non-existent executor).
  2. Faculty gate: runtime/faculty_health.py DEGRADED/OFFLINE propagates to
     backend-dependent capabilities (requires_api=True) as OFFLINE.

Vocabulary bridge (one mapping, one home):
  faculty_health  →  Capability.health_state
  CONNECTED       →  ONLINE
  DEGRADED        →  ONLINE     (faculty still responds; capability not blocked)
  OFFLINE         →  OFFLINE

API:
    refresh()                     — update all capabilities from current signals
    _startup_assert()             — WARNING log for every executor gap at boot
    _faculty_to_cap_health(s)     — mapping function

Not called on the hot path — call once at startup, then on backend change.
"""
from __future__ import annotations

import logging

from runtime.capabilities.capability import ONLINE, OFFLINE

_log = logging.getLogger(__name__)


# ── Vocabulary bridge ──────────────────────────────────────────────────────────

def _faculty_to_cap_health(faculty_status: str) -> str:
    """Map faculty_health vocabulary → Capability.health_state vocabulary."""
    if faculty_status == "CONNECTED":
        return ONLINE
    if faculty_status == "DEGRADED":
        return ONLINE   # degraded faculty still responds; capability not blocked
    if faculty_status == "OFFLINE":
        return OFFLINE
    return ONLINE   # unknown status → optimistically online


# ── Executor presence check ────────────────────────────────────────────────────

def _get_tool_router_agents() -> frozenset[str]:
    """Return the set of capability IDs that have tool_router executors."""
    try:
        from tools.tool_router import _AGENTS
        return frozenset(_AGENTS.keys())
    except Exception as _e:
        _log.warning("health_producer: could not import _AGENTS: %s", _e)
        return frozenset()


def _has_executor(cap, agents: frozenset[str]) -> bool:
    """True when this capability has a reachable executor."""
    if not cap.agent_module:
        return False
    if cap.agent_module == "tools.tool_router":
        return cap.id in agents
    # Any other agent_module (system_agent, spotify_agent, etc.) is its own
    # execution path — assume executor exists unless it's future-flagged.
    return True


# ── Health derivation ──────────────────────────────────────────────────────────

def _derive_one(cap, agents: frozenset[str]) -> str:
    """Derive the real health state for a single capability."""
    if cap.future:
        return cap.health_state   # future caps are unchanged — is_available() filters them

    # Executor gate
    if not _has_executor(cap, agents):
        return OFFLINE

    # Faculty gate: backend-dependent capabilities fail when reasoning faculty is down
    if cap.requires_api:
        try:
            from runtime.faculty_health import get_status as _fh_get
            faculty_st = _fh_get("reasoning")
            derived = _faculty_to_cap_health(faculty_st)
            if derived == OFFLINE:
                return OFFLINE
        except Exception:
            pass   # faculty health unreadable → stay ONLINE

    # WO-CANON-XXII genome gate: per-capability faculty binding (if declared)
    # takes precedence over the coarse reasoning bucket. Read the genome status
    # by the capability's declared faculty_binding attribute if present.
    _faculty_bind = getattr(cap, "faculty_binding", "") or ""
    if _faculty_bind:
        try:
            from runtime.faculty_health import genome_health_status as _gh_status
            _genome_st = _gh_status(_faculty_bind)
            if _genome_st == "OFFLINE":
                return OFFLINE
        except Exception:
            pass

    return ONLINE


def refresh() -> dict[str, str]:
    """
    Derive and update health_state for every capability in the registry.
    Returns {capability_id: new_health_state} for diagnostics.
    """
    try:
        from runtime.capabilities.registry import ALL_CAPABILITIES
    except Exception as _e:
        _log.warning("health_producer.refresh: cannot load registry: %s", _e)
        return {}

    agents = _get_tool_router_agents()
    report: dict[str, str] = {}
    for cap in ALL_CAPABILITIES:
        new_state = _derive_one(cap, agents)
        if new_state != cap.health_state:
            _log.info(
                "CT0032 health: %s %s → %s",
                cap.id, cap.health_state, new_state,
            )
            cap.health_state = new_state
        report[cap.id] = cap.health_state
    return report


def _startup_assert() -> None:
    """
    Log WARNING for every enabled, non-future capability with no executor.
    Does NOT raise — server must boot even with gaps (C3 close: they are OFFLINE).
    """
    try:
        from runtime.capabilities.registry import ALL_CAPABILITIES
    except Exception as _e:
        _log.warning("health_producer._startup_assert: cannot load registry: %s", _e)
        return

    agents = _get_tool_router_agents()
    offline_ids = [
        cap.id
        for cap in ALL_CAPABILITIES
        if cap.enabled and not cap.future and not _has_executor(cap, agents)
    ]
    if offline_ids:
        _log.warning(
            "CT0032 startup: %d capability/ies have no executor → OFFLINE: %s",
            len(offline_ids), offline_ids,
        )
    else:
        _log.info("CT0032 startup: all enabled non-future capabilities have executors")
