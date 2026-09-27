#!/usr/bin/env python3
"""
verify_battery_live.py — live verification for WO-HEALTH-BATTERY-001 (S4)
and WO-DREAM-ENGINE-001 PHASE 9 (S3).

Closes tier 5 (OBSERVED RESULT) of the 7-tier standard, which cannot be
closed from unit tests: it needs the fields to be driven by the running
server, not by a test harness.

    ~/miniconda3/bin/python engineering/evidence/verify_battery_live.py

READ-ONLY. It never writes blender_state.json — that was the bug in
tests/test_s4_wake_restore.py (see tests/test_no_live_state_writes.py).
Run it AFTER restarting the server; the current process predates the wiring.

Exit 0 = battery fields are being driven live. Exit 1 = they are not.
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
STATE = ROOT / "blender" / "blender_state.json"

BATTERY_FIELDS = ("elo_battery", "elo_battery_state")
PHYSICAL_FIELDS = ("physical_battery", "physical_state",
                   "activity_recent", "activity_duration_minutes")
DREAM_FIELDS = ("dream_cycle", "dream_phase", "dream_intensity")

SAMPLES = 12
INTERVAL = 1.0


def read_state() -> dict:
    try:
        return json.loads(STATE.read_text(encoding="utf-8"))
    except Exception as exc:                      # noqa: BLE001
        print(f"  ! could not read {STATE}: {exc}")
        return {}


def server_pid() -> str:
    try:
        out = subprocess.run(
            ["pgrep", "-f", "server.py"], capture_output=True, text=True, timeout=5
        )
        return out.stdout.strip().splitlines()[0] if out.stdout.strip() else ""
    except Exception:                             # noqa: BLE001
        return ""


def main() -> int:
    print("=" * 72)
    print("LIVE BATTERY / DREAM FIELD VERIFICATION")
    print(f"state file : {STATE}")
    print(f"timestamp  : {time.strftime('%Y-%m-%d %H:%M:%S')}")

    pid = server_pid()
    print(f"server pid : {pid or 'NOT RUNNING — start it before running this'}")
    if not pid:
        return 1

    first = read_state()
    ts_first = first.get("_ts", 0)
    print(f"_ts age    : {round(time.time() - ts_first, 1)}s")
    print("=" * 72)

    print("\nPRESENCE")
    present = {}
    for group, fields in (("battery", BATTERY_FIELDS),
                          ("physical", PHYSICAL_FIELDS),
                          ("dream", DREAM_FIELDS)):
        for f in fields:
            here = f in first
            present[f] = here
            print(f"  {group:9} {f:26} {'PRESENT ' + repr(first[f]) if here else 'ABSENT'}")

    print(f"\nSAMPLING {SAMPLES} x {INTERVAL}s — is the server actually driving them?")
    seen_battery: set = set()
    seen_ts: set = set()
    for i in range(SAMPLES):
        state = read_state()
        seen_ts.add(state.get("_ts"))
        if "elo_battery" in state:
            seen_battery.add(state["elo_battery"])
        print(f"  [{i + 1:2}/{SAMPLES}] _ts={state.get('_ts')} "
              f"elo_battery={state.get('elo_battery', 'ABSENT')} "
              f"state={state.get('elo_battery_state', '-')} "
              f"intent={state.get('intent', '-')}")
        time.sleep(INTERVAL)

    print("\nRESULT")
    server_writing = len(seen_ts) > 1
    battery_live = bool(seen_battery)
    print(f"  server advancing _ts        : {server_writing}")
    print(f"  elo_battery present         : {battery_live}")
    print(f"  distinct elo_battery values : {sorted(seen_battery) if seen_battery else 'none'}")

    if not server_writing:
        print("\n  VERDICT: server is not writing state. Nothing to verify.")
        return 1
    if not battery_live:
        print("\n  VERDICT: battery fields ABSENT while the server is writing.")
        print("  Expected if the running process predates the wiring commits")
        print("  (9c69801 / 967793f). Restart the server and re-run.")
        return 1

    print("\n  VERDICT: battery fields are being driven by the live server.")
    print("  Tier 5 evidence for S4. Dream fields only appear once a dream")
    print("  actually fires — they are cleared on wake by design.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
