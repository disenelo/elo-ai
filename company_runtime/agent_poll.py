#!/usr/bin/env python3
"""
agent_poll.py — the autonomous board-reader for the repo agents (Builder / Design /
Game). Runs on a schedule so agents' queues stay read WITHOUT David asking.

TWO-SPEED (David 2026-08-02):
  • auto-READ + auto-REPORT (always, safe): refresh each repo agent's inbox from the
    LIVE board, update the heartbeat, and diff what changed since last poll.
  • auto-ACT (gated): only surfaces items David has explicitly dispatched as ▶ ACTIVE
    — it does NOT let an agent self-select work or edit code unattended (that's how a
    syntax error reached the live app once). Acting on a flagged item is a separate,
    compile-gated step.

Web agents (chatgpt/gemini) are excluded — a browser chat can't self-poll; they read
their inbox (Drive for Gemini) when invoked.

  python3 -m company_runtime.agent_poll            # one sweep (for the scheduled task)
  python3 -m company_runtime.agent_poll --loop 900 # standalone daemon, every 15 min
"""
from __future__ import annotations
import json, os, sys, time

from company_runtime import agent_bus

REPO_AGENTS = ("builder", "design", "game")
BUS = agent_bus.BUS
REPORT = os.path.join(BUS, "poll_report.json")


def _dispatched_active(pending):
    """Items David explicitly dispatched as ACTIVE (the only ones eligible to auto-act)."""
    return [p for p in pending if p.get("state") == "active"]


def sweep() -> dict:
    # auto-READ: rebuild every inbox from the live board + refresh heartbeat (auto-REPORT)
    agent_bus.ping_all()
    out = {"ts": time.time(), "generated": time.strftime("%Y-%m-%d %H:%M:%S"), "agents": {}}
    for aid in REPO_AGENTS:
        inbox_p = os.path.join(BUS, aid, "inbox.json")
        snap_p = os.path.join(BUS, aid, ".poll_snapshot.json")
        if not os.path.exists(inbox_p):
            continue
        pending = json.load(open(inbox_p)).get("pending", [])
        now = {p["wo"] for p in pending}
        prev = set()
        if os.path.exists(snap_p):
            try: prev = set(json.load(open(snap_p)).get("wos", []))
            except Exception: pass
        active = _dispatched_active(pending)
        # heartbeat freshness (did the agent report back recently?)
        ob = os.path.join(BUS, aid, "outbox.json")
        seen = os.path.getmtime(ob) if os.path.exists(ob) else None
        fresh = seen is not None and (time.time() - seen) < 86400
        out["agents"][aid] = {
            "active_dispatched": [{"wo": p["wo"], "title": p["title"], "badge": p.get("badge")} for p in active],
            "new_since_last": sorted(now - prev),
            "cleared_since_last": sorted(prev - now),
            "pending": len(pending),
            "agent_fresh": fresh,
            "act_eligible": [p["wo"] for p in active],   # gated: only these may be auto-acted
        }
        json.dump({"ts": time.time(), "wos": sorted(now)}, open(snap_p, "w"))
    json.dump(out, open(REPORT, "w"), indent=2)
    return out


def _print(rep: dict):
    print(f"\n╔══ AGENT POLL · {rep['generated']} ══╗")
    for aid, a in rep["agents"].items():
        flag = "🟢" if a["agent_fresh"] else "⚪"
        act = ", ".join(a["act_eligible"]) or "—"
        new = ", ".join(a["new_since_last"]) or "—"
        print(f"{flag} {aid:8} · dispatched-ACTIVE: {act:30} · new: {new}")
    print("\nauto-read + heartbeat refreshed. Dispatched-ACTIVE items are the only ones eligible to act on.")


def main():
    if len(sys.argv) > 2 and sys.argv[1] == "--loop":
        every = float(sys.argv[2])
        print(f"agent_poll daemon: sweeping repo agents every {every}s")
        while True:
            try: _print(sweep())
            except Exception as e: print("poll error:", e)
            time.sleep(every)
    else:
        _print(sweep())


if __name__ == "__main__":
    main()
