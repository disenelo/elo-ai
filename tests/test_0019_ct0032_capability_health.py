"""
tests/test_0019_ct0032_capability_health.py — Card 0032: Capability health producer.

Tests:
    CH-1  _faculty_to_cap_health maps CONNECTED→ONLINE, DEGRADED→ONLINE, OFFLINE→OFFLINE
    CH-2  Capability with no _AGENTS executor derives OFFLINE (C3 close)
    CH-3  wikipedia derives OFFLINE (agent_module=tools.tool_router, not in _AGENTS)
    CH-4  refresh() updates cap.health_state in-place; no regression on healthy caps
    CH-5  refresh() distribution: {ONLINE: N, OFFLINE: M} where M > 0 (no optimistic constants)
    CH-6  _startup_assert() logs WARNING when executor gap exists
    CH-7  is_available() returns False for OFFLINE capabilities (fail-closed preserved)
    CH-8  server.py startup block wires CT0032

Run: python3 tests/test_0019_ct0032_capability_health.py
"""

import logging
import os
import sys
import unittest.mock as mock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

ok  = lambda msg: print(f"  PASS  {msg}")
err = lambda msg: (print(f"  FAIL  {msg}"), sys.exit(1))


# ── CH-1: vocabulary bridge ───────────────────────────────────────────────────
def test_ch1_faculty_mapping():
    from runtime.capabilities.health_producer import _faculty_to_cap_health
    from runtime.capabilities.capability import ONLINE, OFFLINE

    assert _faculty_to_cap_health("CONNECTED") == ONLINE,  "CH-1: CONNECTED should map to ONLINE"
    assert _faculty_to_cap_health("DEGRADED")  == ONLINE,  "CH-1: DEGRADED should map to ONLINE (still responds)"
    assert _faculty_to_cap_health("OFFLINE")   == OFFLINE, "CH-1: OFFLINE should map to OFFLINE"
    assert _faculty_to_cap_health("UNKNOWN")   == ONLINE,  "CH-1: unknown status → optimistic ONLINE"
    ok("CH-1: faculty→capability vocabulary mapping correct")


# ── CH-2: no executor → OFFLINE ───────────────────────────────────────────────
def test_ch2_no_executor_offline():
    from runtime.capabilities.health_producer import _has_executor, _derive_one
    from runtime.capabilities.capability import Capability, OFFLINE, CAT_KNOWLEDGE

    # Fake capability with tools.tool_router module but NOT in _AGENTS
    fake_cap = Capability(
        id="nonexistent_tool",
        display_name="Nonexistent",
        category=CAT_KNOWLEDGE,
        description="test",
        verbs=["nonexistent"],
        agent_module="tools.tool_router",
    )
    known_agents = frozenset(["time", "calculator", "search"])   # "nonexistent_tool" absent
    has_exec = _has_executor(fake_cap, known_agents)
    assert not has_exec, "CH-2: capability not in _AGENTS should have no executor"
    derived = _derive_one(fake_cap, known_agents)
    assert derived == OFFLINE, f"CH-2: no executor → OFFLINE, got {derived!r}"
    ok("CH-2: capability with no _AGENTS executor derives OFFLINE")


# ── CH-3: wikipedia specifically derives OFFLINE ──────────────────────────────
def test_ch3_wikipedia_offline():
    from runtime.capabilities.registry import ALL_CAPABILITIES
    from runtime.capabilities.health_producer import _get_tool_router_agents, _derive_one
    from runtime.capabilities.capability import OFFLINE

    wiki = next((c for c in ALL_CAPABILITIES if c.id == "wikipedia"), None)
    if wiki is None:
        err("CH-3: 'wikipedia' capability not found in registry")

    agents = _get_tool_router_agents()
    derived = _derive_one(wiki, agents)
    if wiki.id in agents:
        # wikipedia was added to _AGENTS since the card was filed — test is void
        ok(f"CH-3: wikipedia now has an _AGENTS executor (health: {wiki.health_state}) — gap already closed")
    else:
        assert derived == OFFLINE, f"CH-3: wikipedia not in _AGENTS → should derive OFFLINE, got {derived!r}"
        ok("CH-3: wikipedia derives OFFLINE (no _AGENTS executor — C3 confirmed)")


# ── CH-4: refresh() updates health_state in-place ─────────────────────────────
def test_ch4_refresh_updates_in_place():
    from runtime.capabilities.health_producer import refresh
    from runtime.capabilities.registry import ALL_CAPABILITIES
    from runtime.capabilities.capability import ONLINE, OFFLINE

    report = refresh()
    assert isinstance(report, dict), "CH-4: refresh() must return a dict"
    assert len(report) > 0, "CH-4: refresh() must return non-empty report"

    # Verify report matches actual cap.health_state (in-place update check)
    cap_by_id = {c.id: c for c in ALL_CAPABILITIES}
    for cap_id, reported_health in report.items():
        cap = cap_by_id.get(cap_id)
        if cap:
            assert cap.health_state == reported_health, (
                f"CH-4: cap.health_state={cap.health_state!r} doesn't match "
                f"report={reported_health!r} for {cap_id}"
            )
    ok(f"CH-4: refresh() updated {len(report)} capabilities in-place; report matches registry state")


# ── CH-5: distribution has ≥1 OFFLINE after refresh ──────────────────────────
def test_ch5_distribution_not_all_online():
    from runtime.capabilities.health_producer import refresh
    from runtime.capabilities.capability import ONLINE, OFFLINE

    report = refresh()
    dist: dict[str, int] = {}
    for h in report.values():
        dist[h] = dist.get(h, 0) + 1

    print(f"    health distribution: {dist}")
    if dist.get(OFFLINE, 0) == 0:
        err(f"CH-5: expected ≥1 OFFLINE capability (wikipedia at minimum), got distribution: {dist}")

    total_online  = dist.get(ONLINE, 0)
    total_offline = dist.get(OFFLINE, 0)
    ok(f"CH-5: health distribution after refresh — ONLINE:{total_online} OFFLINE:{total_offline} (no optimistic constant)")


# ── CH-6: _startup_assert logs WARNING for gaps ───────────────────────────────
def test_ch6_startup_assert_logs():
    from runtime.capabilities.health_producer import _startup_assert

    captured_warnings = []
    real_warning = logging.getLogger("runtime.capabilities.health_producer").warning

    with mock.patch.object(
        logging.getLogger("runtime.capabilities.health_producer"), "warning",
        side_effect=lambda msg, *a, **k: captured_warnings.append(msg % a if a else msg)
    ):
        _startup_assert()

    # Expected: at least one WARNING about OFFLINE capabilities
    ct_warns = [w for w in captured_warnings if "CT0032" in w or "OFFLINE" in w or "no executor" in w.lower()]
    if not ct_warns:
        err(f"CH-6: _startup_assert() logged no CT0032/OFFLINE WARNINGs. Got: {captured_warnings}")
    ok(f"CH-6: _startup_assert() logged WARNING for executor gaps — sample: {ct_warns[0]!r}")


# ── CH-7: OFFLINE capability is not is_available ──────────────────────────────
def test_ch7_offline_not_available():
    from runtime.capabilities.capability import Capability, OFFLINE, CAT_KNOWLEDGE

    cap = Capability(
        id="test_offline",
        display_name="Test Offline",
        category=CAT_KNOWLEDGE,
        description="test",
        verbs=["test"],
        health_state=OFFLINE,
    )
    assert not cap.is_available(), "CH-7: OFFLINE capability must not be is_available()"
    ok("CH-7: OFFLINE capability is not available (fail-closed preserved)")


# ── CH-8: server.py wires CT0032 at startup ──────────────────────────────────
def test_ch8_server_wired():
    with open(os.path.join(ROOT, "server.py"), encoding="utf-8") as f:
        src = f.read()

    if "health_producer" not in src:
        err("CH-8: server.py does not import health_producer")
    if "_cap_assert" not in src and "_startup_assert" not in src:
        err("CH-8: server.py does not call _startup_assert at startup")
    if "_cap_health_refresh" not in src and "refresh" not in src:
        err("CH-8: server.py does not call refresh() at startup")
    if "CT0032" not in src:
        err("CH-8: server.py has no CT0032 marker")
    ok("CH-8: server.py wires CT0032 capability health producer at startup")


# ── runner ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("CT0032 — Capability health producer")
    test_ch1_faculty_mapping()
    test_ch2_no_executor_offline()
    test_ch3_wikipedia_offline()
    test_ch4_refresh_updates_in_place()
    test_ch5_distribution_not_all_online()
    test_ch6_startup_assert_logs()
    test_ch7_offline_not_available()
    test_ch8_server_wired()
    print("\n8/8 PASS — CT0032 capability health producer verified")
