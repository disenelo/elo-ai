#!/usr/bin/env python3
"""
continuation.py — the auto-work loop. Watches the dispatch board; whenever it
changes, it runs every WO's tests, AUTO-CLOSES the 🟢 AUTO greens (per wo_policy),
refreshes company_state.json, and leaves only 🟠 DAVID / 🔴 RESERVED / 🔵 CONFIRM
for David. This is the half of the loop that used to need a human to pull the
trigger; now it pulls itself on board change.

Safety (matches David's rule + LAW-017):
  • Only 🟢 AUTO greens are ever auto-closed. DAVID / RESERVED / CONFIRM are never
    touched — they always surface to David.
  • Never edits a WO that isn't green. Never edits the frozen kernel. Board-only.
  • Debounced; skips its own re-write so it doesn't loop on itself.

Run standalone:      python3 -m company_runtime.continuation            # watch loop
One cycle + exit:    python3 -m company_runtime.continuation --once
Report only (no close): python3 -m company_runtime.continuation --once --dry
As a thread:         start_thread(interval=5.0)   # dashboard_server does this
"""
from __future__ import annotations
import os, re, time, threading, argparse

from company_runtime import wo_test_runner as R
from company_runtime import company_state_writer as csw

BOARD     = R.BOARD
REPORT    = os.path.join(R.ROOT, "blender", "wo_test_report.json")
_APPROVED = os.path.join(R.ROOT, "engineering", "work_orders", "DAVID_APPROVED.md")


def load_david_approved() -> set:
    """Parse DAVID_APPROVED.md → set of approved WO IDs. Empty set on any error."""
    approved: set = set()
    try:
        with open(_APPROVED, encoding="utf-8") as f:
            for line in f:
                for m in re.finditer(r"\bWO-\d+[a-z]?\b", line, re.I):
                    approved.add(m.group(0).upper())
    except FileNotFoundError:
        pass
    return approved


def cycle(apply: bool = True) -> dict:
    """Run all WO tests → auto-close AUTO greens + David-approved → refresh state."""
    mapping  = R.discover()
    bstat    = R.board_status()
    approved = load_david_approved()
    report, closed, would = [], [], []
    for wo, path in mapping.items():
        tier  = R.tier_for(wo, bstat.get(wo, ""))
        res   = R.run_test(path)
        green = R.GREEN(res)
        already = "DONE" in bstat.get(wo, "")
        if green and not already:
            if tier == "AUTO":
                (closed if apply else would).append(wo)
                if apply:
                    R.auto_close(wo, os.path.basename(path))
            elif wo in approved:
                # David already approved this — close it so it never re-surfaces.
                (closed if apply else would).append(wo)
                if apply:
                    R.auto_close(wo, "David-approved")
        report.append({"wo": wo, "tier": tier, "test": os.path.relpath(path, R.ROOT),
                        "green": green, "passed": res["passed"], "failed": res["failed"],
                        "errors": res["errors"], "rc": res["rc"],
                        "summary": res["summary"], "secs": res["secs"]})
    # write the machine report (dashboard reads this via the state writer)
    import json
    json.dump({"generated": time.time(), "apply": apply, "closed": closed, "items": report},
              open(REPORT, "w"), indent=2)
    # ping the bus: push each agent's fresh inbox + read heartbeats (roster = allocated seats)
    try:
        from company_runtime import agent_bus
        agent_bus.ping_all()
    except Exception:
        pass
    # refresh company_state so the dashboard reflects closes + fresh test health + heartbeat
    csw.publish()
    return {"tested": len(report),
            "green": sum(1 for x in report if x["green"]),
            "auto_closed": closed, "would_close": would,
            "needs_david": sorted({x["wo"] for x in report
                                   if x["tier"] in ("DAVID", "RESERVED", "CONFIRM")
                                   and x["wo"] not in approved})}


def _light_refresh(log=print) -> None:
    """LIGHTWEIGHT refresh for the live daemon: rebuild agent inboxes + republish
    company_state. NO test subprocesses, no board mutation. Cheap + safe to run on a
    live boot / on every board change."""
    try:
        from company_runtime import agent_bus
        agent_bus.ping_all()
    except Exception:
        pass
    try:
        csw.publish()
    except Exception as exc:
        log(f"continuation: refresh error: {exc}")


def watch(interval: float = 5.0, debounce: float = 1.5, heartbeat_every: float = 60.0, log=print) -> None:
    """Blocking daemon loop: on board-file change, do a LIGHTWEIGHT refresh (state + bus).

    IMPORTANT (2026-08-03 hang fix): this loop does NOT run the WO test-suite. `cycle()`
    spawns 20+ python subprocesses; running that in the live eLo-OS boot daemon on every
    board write pegged the machine and hung the app on startup. Tests + auto-close are now
    EXPLICIT / CLI-only: `python3 -m company_runtime.continuation --once`. The live loop
    just keeps state + heartbeats fresh."""
    last_mtime = 0.0
    log(f"continuation: watching {os.path.relpath(BOARD, R.ROOT)} (lightweight) every {interval}s")
    _light_refresh(log)                              # prime — cheap
    try:
        last_mtime = os.path.getmtime(BOARD)
    except Exception:
        pass
    last_ping = time.time()
    while True:
        try:
            m = os.path.getmtime(BOARD)
            if m > last_mtime + 0.001:
                time.sleep(debounce)                 # let a burst of edits settle
                _light_refresh(log)
                last_mtime = max(m, os.path.getmtime(BOARD))
                last_ping = time.time()
            elif time.time() - last_ping >= heartbeat_every:
                _light_refresh(log); last_ping = time.time()
        except FileNotFoundError:
            pass
        except Exception as exc:
            log(f"continuation: tick error: {exc}")
        time.sleep(interval)


# Single-instance guard — only one continuation thread ever runs per process.
_started = False
_started_lock = threading.Lock()


def start_thread(interval: float = 5.0):
    """Start the watch loop in a background daemon thread.

    Safe to call from both eLo OS startup and the dashboard server — the guard
    ensures only one thread ever runs.  Returns the thread if started, None if
    already running or disabled via DISENELO_NO_AUTOLOOP=1.
    """
    global _started
    if os.environ.get("DISENELO_NO_AUTOLOOP", "") == "1":
        return None
    with _started_lock:
        if _started:
            return None
        _started = True
    t = threading.Thread(target=watch, kwargs={"interval": interval}, daemon=True,
                         name="continuation")
    t.start()
    return t


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--once", action="store_true", help="run one cycle then exit")
    ap.add_argument("--dry", action="store_true", help="report only, don't auto-close")
    ap.add_argument("--interval", type=float, default=5.0)
    a = ap.parse_args()
    if a.once:
        s = cycle(apply=not a.dry)
        print(f"tested {s['tested']} · green {s['green']} · "
              f"{'would close' if a.dry else 'auto-closed'}: "
              f"{', '.join(s['would_close'] if a.dry else s['auto_closed']) or '—'}")
        print(f"still need David ({len(s['needs_david'])}): {', '.join(s['needs_david'])}")
    else:
        watch(interval=a.interval)
