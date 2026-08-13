#!/usr/bin/env python3
"""
agent_refresh.py — the AGENT-side refresh. Same idea as the coordinator's loop, but
scoped to ONE agent and run on demand: when David says "refresh", the agent runs this,
it re-pings the bus (rebuilds its inbox from the CURRENT board), and shows its queue +
WHAT CHANGED since the last time it looked.

  python3 -m company_runtime.agent_refresh builder     # Builder pulls its latest
  python3 -m company_runtime.agent_refresh design
  python3 -m company_runtime.agent_refresh chatgpt

Repo/local agents run it directly. Web agents (Gemini) can't — they re-read their inbox
from the Google Drive mirror instead; this same diff is what the coordinator pushes there.
"""
from __future__ import annotations
import json, os, sys, time

from company_runtime import agent_bus

BUS = agent_bus.BUS


def _snap_path(aid): return os.path.join(BUS, aid, ".last_refresh.json")


def refresh(aid: str) -> dict:
    # 1) re-ping so every inbox reflects the current board (same refresh the coordinator does)
    agent_bus.ping_all()
    inbox_p = os.path.join(BUS, aid, "inbox.json")
    if not os.path.exists(inbox_p):
        print(f"no mailbox for '{aid}'. Allocated agents: "
              f"{', '.join(sorted(agent_bus._load_registry().keys()))}")
        return {}
    inbox = json.load(open(inbox_p))
    now = {p["wo"]: p for p in inbox.get("pending", [])}

    # 2) diff against the last time this agent refreshed
    snap_p = _snap_path(aid)
    prev = {}
    if os.path.exists(snap_p):
        try: prev = {p["wo"]: p for p in json.load(open(snap_p)).get("pending", [])}
        except Exception: prev = {}
    new     = [w for w in now if w not in prev]
    gone    = [w for w in prev if w not in now]                       # closed / reassigned
    changed = [w for w in now if w in prev and now[w].get("state") != prev[w].get("state")]

    # 3) show the queue grouped by state, newest first
    print(f"\n╔══ {aid} refresh · {inbox.get('role','')} · {time.strftime('%H:%M:%S')} ══╗")
    seats = ", ".join(s["seat"] for s in inbox.get("seats", []))
    print(f"  seats: {seats or '—'}   transport: {inbox.get('transport','')}")
    for state, label in (("active","▶ ACTIVE — do this now"), ("ready","· READY — pull next"),
                         ("in_review","⏳ IN_REVIEW — with David"), ("blocked","⛔ BLOCKED")):
        items = [p for p in inbox["pending"] if p.get("state") == state]
        if not items: continue
        print(f"\n  {label}")
        for p in items:
            star = " 🆕" if p["wo"] in new else (" ✏️" if p["wo"] in changed else "")
            print(f"    {p.get('badge','')} {p['wo']:20} {p.get('title','')[:46]}{star}")

    # 4) headline of what changed since last look
    print("\n  ── since your last refresh ──")
    print(f"    🆕 new:     {', '.join(new)  or '—'}")
    print(f"    ✏️  changed: {', '.join(changed) or '—'}")
    print(f"    ✅ cleared: {', '.join(gone) or '—'}")
    print(f"\n  Reply into blender/agent_bus/{aid}/outbox.json — "
          "{\"ts\":<epoch>,\"updates\":[{\"wo\":\"..\",\"status\":\"done|blocked|question|progress\",\"detail\":\"..\"}]}")

    # 5) save snapshot for next diff
    json.dump({"ts": time.time(), "pending": list(now.values())}, open(snap_p, "w"), indent=2)
    return {"new": new, "changed": changed, "cleared": gone, "pending": len(now)}


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: python3 -m company_runtime.agent_refresh <agent-id>")
        print("agents:", ", ".join(sorted(agent_bus._load_registry().keys())))
        sys.exit(1)
    refresh(sys.argv[1].lower())
