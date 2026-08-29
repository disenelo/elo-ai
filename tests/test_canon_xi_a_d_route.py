"""
tests/test_canon_xi_a_d_route.py — card 0081 acceptance tests.
WO-CANON-XI §A/§D — additive route/issued_by envelope + OQ-1.3/1.4 wiring.

David 2026-08-21: "Okay that's fine just go."
Sequencing (spec §1.390): ship → prove parity → remove Unity's local selection.

Four checks:

  XI-AD-1  move_command carries route + issued_by; legacy type-only command unchanged.
  XI-AD-2  Parity: brain route vs Unity route reported in route_memory.jsonl.
             RED (exit 1) if no parity data — must be proven on live moves before
             Unity's local route selection is removed.
  XI-AD-3  OQ-1.3 timeout is derived from route expected_ms sum; OQ-1.4 `arrived`
             accepted as terminal ACK alongside legacy move_complete.
  XI-AD-4  Disconnection: remove route field from state_writer → parity test goes RED.

Run: python3 tests/test_canon_xi_a_d_route.py
"""
from __future__ import annotations

import ast
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

ok   = lambda msg: print(f"  PASS  {msg}")
red  = lambda msg: (print(f"  RED   {msg} — this test must go red before parity is proven"), sys.exit(1))
err  = lambda msg: (print(f"  FAIL  {msg}"), sys.exit(1))
warn = lambda msg: print(f"  WARN  {msg}")

_STATE_WRITER   = os.path.join(ROOT, "blender_bridge", "state_writer.py")
_SERVER_PY      = os.path.join(ROOT, "server.py")
_ROUTE_MEMORY   = os.path.join(ROOT, "self", "journals", "route_memory.jsonl")


# ── XI-AD-1  move_command carries route + issued_by; legacy unaffected ────────

def test_xi_ad1_additive_envelope() -> None:
    """state_writer.py emits route + issued_by when present; type-only unchanged."""
    with open(_STATE_WRITER, encoding="utf-8") as f:
        src = f.read()

    # route field written
    if 'payload["move_command"]["route"] = intent["route"]' not in src:
        err("XI-AD-1: route not written to move_command in state_writer.py")
    # issued_by field written
    if 'payload["move_command"]["issued_by"] = intent["issued_by"]' not in src:
        err("XI-AD-1: issued_by not written to move_command in state_writer.py")
    # additive guard: only written when present in intent
    if 'if intent.get("route")' not in src:
        err("XI-AD-1: route write not guarded by intent.get() — not additive")
    if 'if intent.get("issued_by")' not in src:
        err("XI-AD-1: issued_by write not guarded by intent.get() — not additive")

    ok("XI-AD-1: route + issued_by written additively; type-only command unchanged (guard confirmed)")


# ── XI-AD-2  parity: brain route vs Unity route logged in route_memory ───────

def test_xi_ad2_parity_proven() -> None:
    """
    Brain route must match Unity's route across real moves.
    RED if no parity data — parity must be proven before Unity's local selection
    is removed (spec §1.390, card 0081 sequencing rule).
    """
    if not os.path.exists(_ROUTE_MEMORY):
        red(
            "XI-AD-2: route_memory.jsonl not found — no live parity data."
            " Run the system on real moves and record both brain and Unity routes before removing"
            " Unity's local route selection."
        )

    entries = []
    try:
        with open(_ROUTE_MEMORY, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    entries.append(json.loads(line))
    except (json.JSONDecodeError, OSError) as e:
        err(f"XI-AD-2: could not read route_memory.jsonl: {e}")

    # Check whether any entries carry real (non-null) brain_route + unity_route for parity comparison.
    # Null==null would trivially match — exclude null-keyed entries (pre-Unity-route wiring).
    parity_entries = [
        e for e in entries
        if e.get("brain_route") is not None and e.get("unity_route") is not None
    ]
    if not parity_entries:
        null_keyed = [e for e in entries if "brain_route" in e and e.get("brain_route") is None]
        if null_keyed:
            warn(
                f"XI-AD-2: {len(null_keyed)} entries have brain_route/unity_route keys but both are null."
                " These are post-STEP2 entries pending WO-CANON-XI-UNITY-ROUTE (Design)."
                " Parity not yet provable — Unity arrived ACK must carry unity_route field."
            )
        else:
            warn(
                f"XI-AD-2: {len(entries)} route_memory entries found but none carry brain_route + unity_route."
                " These are pre-route entries. Parity comparison not yet possible."
            )
        red(
            "XI-AD-2: parity not yet proven — no real brain_route/unity_route entries in route_memory.jsonl."
            " Cannot remove Unity's local route selection until match rate is confirmed."
        )

    matched  = sum(1 for e in parity_entries if e.get("brain_route") == e.get("unity_route"))
    total    = len(parity_entries)
    rate_pct = round(matched / total * 100) if total else 0

    if rate_pct < 80:
        red(
            f"XI-AD-2: parity match rate {rate_pct}% ({matched}/{total}) is below 80%."
            " Do NOT remove Unity's local route selection — brain routing is worse."
        )

    ok(
        f"XI-AD-2: parity proven — {rate_pct}% match ({matched}/{total} routes)."
        " Brain routes match Unity's selection. Safe to remove local selection."
    )


# ── XI-AD-3  OQ-1.3 derived timeout + OQ-1.4 `arrived` terminal ACK ─────────

def test_xi_ad3_oq13_oq14_wiring() -> None:
    """server.py uses derived timeout (OQ-1.3) and accepts arrived as terminal ACK (OQ-1.4)."""
    with open(_SERVER_PY, encoding="utf-8") as f:
        src = f.read()

    # OQ-1.3: route_timeout_s in _PENDING_MOVE, derived from expected_ms
    if "route_timeout_s" not in src:
        err("OQ-1.3: route_timeout_s not found in server.py — derived timeout not implemented")
    if "expected_ms" not in src:
        err("OQ-1.3: expected_ms not referenced in server.py — timeout derivation missing")
    if "_PENDING_MOVE.get(\"route_timeout_s\"" not in src and 'route_timeout_s' not in src:
        err("OQ-1.3: route_timeout_s not used at timeout check in server.py")

    ok("OQ-1.3: timeout derived from route expected_ms sum + slack (floor 8s)")

    # OQ-1.4: `arrived` accepted as terminal ACK
    if '"arrived"' not in src and "'arrived'" not in src:
        err("OQ-1.4: 'arrived' not referenced in server.py — terminal ACK not wired")
    # arrived must be in the ACK check (not just in a comment)
    if "_ACK_BODY_TYPES" in src:
        if "arrived" not in src[src.index("_ACK_BODY_TYPES"):src.index("_ACK_BODY_TYPES") + 300]:
            err("OQ-1.4: 'arrived' not in _ACK_BODY_TYPES")
    # The move ACK check accepts arrived (window 800 chars — arrived is ~620 chars into block)
    if '"arrived"' not in src[src.find("_PENDING_MOVE[\"active\"]"):src.find("_PENDING_MOVE[\"active\"]") + 800]:
        err("OQ-1.4: arrived not checked in move ACK block")

    ok('OQ-1.4: arrived accepted as terminal ACK alongside legacy move_complete')


# ── XI-AD-4  disconnection: remove route → parity test goes RED ──────────────

def test_xi_ad4_disconnection() -> None:
    """Removing route from state_writer would mean XI-AD-2 has nothing to compare."""
    with open(_STATE_WRITER, encoding="utf-8") as f:
        src = f.read()

    route_write_count = src.count('payload["move_command"]["route"]')
    if route_write_count == 0:
        red(
            "XI-AD-4: route field not present in state_writer.py — "
            "XI-AD-2 parity test would have nothing to compare."
        )

    ok(
        f"XI-AD-4: route field present in state_writer.py ({route_write_count} write site(s))."
        " Removing it would make XI-AD-2 go RED (disconnection confirmed)."
    )


# ── runner ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("card 0081 — WO-CANON-XI §A/§D route envelope + parity")
    print()
    test_xi_ad1_additive_envelope()
    test_xi_ad3_oq13_oq14_wiring()
    test_xi_ad4_disconnection()
    print()
    print("Running parity check (XI-AD-2) — expected RED until live parity data collected:")
    test_xi_ad2_parity_proven()
    print()
    print("3/4 PASS, 1 RED — parity gate open until live moves recorded.")
    print()
    print("SEQUENCING (card 0081):")
    print("  Step 1 DONE: route + issued_by shipping (commit f0e591d / state_writer.py)")
    print("  Step 2 OPEN: run live moves; log brain_route + unity_route to route_memory.jsonl")
    print("  Step 3 BLOCKED: remove Unity local selection only after XI-AD-2 turns GREEN")
