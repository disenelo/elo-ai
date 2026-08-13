#!/usr/bin/env python3
"""
agent_bus.py — how the coordinator talks to the agents, and how it knows they're
alive. A file-based mailbox + heartbeat over the transports each agent actually
uses (there is no live push-API into another LLM session, so we use the shared
files they already read/write):

  Builder / UI-Avatar (Design)  →  transport = repo   (local files + git)
  ChatGPT (Chief Arch / Biz / Legal / Marketing via Codex)  →  transport = local (Output ⇄ Codex)
  Gemini (R&D)                  →  transport = drive  (Google Drive mirror — no local disk)

Each agent gets a mailbox under blender/agent_bus/<id>/:
  • inbox.json   — WHAT WE PUSH: their pending queue (their board rows), approvals
                   cleared for them, and any brief pointers. Written every ping.
  • outbox.json  — WHAT THEY PUSH BACK: heartbeat, completions, blocks, questions.
                   The ping reads this for updates to triage.

`ping` = read each outbox (updates + last-seen), recompute + push each inbox, and
report a CHECKLIST: agent · transport · fresh/stale · pending · updates · blocks.
That checklist is the thing the coordinator (and David) monitors for auto-complete
and onboarding.

  python3 -m company_runtime.agent_bus               # ping all + print checklist
  python3 -m company_runtime.agent_bus --onboard gemini "R&D" drive
"""
from __future__ import annotations
import json, os, re, time, sys

ROOT   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOARD  = os.path.join(ROOT, "engineering", "work_orders", "DISPATCH_BOARD.md")
BUS    = os.path.join(ROOT, "blender", "agent_bus")
REG    = os.path.join(BUS, "registry.json")

# The bus roster is NOT seeded or auto-onboarded — it MIRRORS the already-allocated
# seats (Seat Occupancy Map / company_graph.SEATS). Each bus endpoint = a real
# occupant tool that holds one or more allocated seats. Occupant → {transport, match}.
# Occupants with no external mailbox (Lead Architect = coordinator/me) are excluded.
_OCCUPANT = {
    "claude code": {"id": "builder", "role": "Builder (Python/runtime)",
                    "transport": "repo",  "match": ["builder"]},
    # NOTE: the Unity agent holds TWO allocated seats — ENG-004 (Avatar/One Brain) and
    # ENG-005 (Game). They are SPLIT into separate endpoints below so One-Brain work never
    # leaks into the game queue (and vice-versa). Keyed here for the Avatar seat; the Game
    # seat is redirected in _load_registry.
    "unity agent": {"id": "design",  "role": "UI/Avatar · One Brain (Unity)",
                    "transport": "repo",  "match": ["ui/avatar", "design", "designer"]},
    "chatgpt":     {"id": "chatgpt", "role": "Chief Architect / Creative / Biz·Legal·Marketing (Codex)",
                    "transport": "local", "match": ["chatgpt", "business ops", "finance", "legal", "marketing", "product safety", "creative"]},
    "gemini":      {"id": "gemini",  "role": "Robotics R&D",
                    "transport": "drive", "match": ["gemini", "r&d"]},
}
# occupants that are coordinators/humans, not bus workers → never a mailbox
_EXCLUDE_OCC = ("claude opus", "claude", "claude + human")


def _load_registry() -> dict:
    """Derive the roster STRICTLY from the allocated seats — no seeding, no onboarding.
    An agent only exists on the bus if it holds an allocated seat in company_graph.SEATS."""
    from company_runtime import company_graph as g
    roster: dict = {}
    for seat_id, div, role, occ, focus, state in g.SEATS:
        key = (occ or "").strip().lower()
        spec = _OCCUPANT.get(key)
        if not spec or key in _EXCLUDE_OCC:
            continue
        # split the Unity agent's Game seat into its own endpoint (separate allocated seat)
        if key == "unity agent" and "game" in role.lower():
            aid, arole, match = "game", "Game (Unity)", ["game"]
        else:
            aid, arole, match = spec["id"], spec["role"], list(spec["match"])
        r = roster.setdefault(aid, {"role": arole, "transport": spec["transport"],
                                    "match": match, "seats": []})
        r["seats"].append({"seat": seat_id, "div": div, "role": role, "state": state})
    os.makedirs(BUS, exist_ok=True)
    json.dump(roster, open(REG, "w"), indent=2)   # snapshot of the allocation (read-only mirror)
    return roster


def _rows() -> list[dict]:
    """Parse the board into {id,title,agent,status_raw,importance,needs_david}."""
    from company_runtime import wo_policy
    out = []
    if not os.path.exists(BOARD):
        return out
    for l in open(BOARD, encoding="utf-8"):
        if not l.startswith("|") or l.count("|") < 6:
            continue
        c = [x.strip() for x in l.strip().strip("|").split("|")]
        if len(c) < 6:
            continue
        wo = re.sub(r"\*\*", "", c[0]).strip()
        if wo.lower() in ("wo", "----") or not wo:
            continue
        pol = wo_policy.classify(wo, c[1], c[4])
        out.append({"id": wo, "title": re.sub(r"\*\*", "", c[1])[:70],
                    "agent": c[2].lower(), "status_raw": c[4],
                    "importance": pol["importance"], "needs_david": pol["needs_david"],
                    "badge": pol["badge"]})
    return out


def _owned(rows, match) -> list[dict]:
    return [r for r in rows if any(m in r["agent"] for m in match)]


def _mbox(aid) -> str:
    d = os.path.join(BUS, aid)
    os.makedirs(d, exist_ok=True)
    return d


def _pending(rows_owned) -> list[dict]:
    """Their live queue: not DONE — the work they should be pulling / finishing.
    Uses the shared _norm_status (leading-marker only) so a WO that merely *mentions*
    another WO's 'DONE ✅' in its prose is not mistaken for done."""
    from company_runtime.company_state_writer import _norm_status
    q = []
    for r in rows_owned:
        st = _norm_status(r["status_raw"])
        if st in ("done_david", "done_claimed", "superseded"):
            continue
        state = ("in_review" if st == "in_review"
                 else "active" if st in ("dispatched", "in_progress")
                 else "blocked" if st in ("blocked", "deferred")
                 else "ready")
        q.append({"wo": r["id"], "title": r["title"], "state": state,
                  "importance": r["importance"], "badge": r["badge"]})
    return q


def ping(aid: str, reg: dict, rows: list[dict]) -> dict:
    meta = reg[aid]
    box  = _mbox(aid)
    owned = _owned(rows, meta["match"])
    pending = _pending(owned)

    # READ their outbox — TOLERANT: agents write slightly different shapes (some add
    # from/seat/next, some send a bare list, some a malformed ts). Normalize defensively
    # so divergence never breaks the loop; only wo+status+detail are actually required.
    outbox_p = os.path.join(box, "outbox.json")
    updates, last_seen, plan = [], None, None
    if os.path.exists(outbox_p):
        mtime = os.path.getmtime(outbox_p)
        last_seen = mtime
        try:
            ob = json.load(open(outbox_p))
            if isinstance(ob, list):                 # agent sent a bare updates list
                ob = {"updates": ob}
            raw = ob.get("updates") or ob.get("update") or []
            if isinstance(raw, dict):
                raw = [raw]
            for u in (raw if isinstance(raw, list) else []):
                if not isinstance(u, dict):
                    continue
                updates.append({"wo": u.get("wo") or u.get("id") or "?",
                                "status": (u.get("status") or u.get("state") or "progress"),
                                "detail": (u.get("detail") or u.get("note") or "")})
            plan = ob.get("next")                    # capture Design's extra "next" signal if present
            ts = ob.get("ts")
            last_seen = ts if (isinstance(ts, (int, float)) and abs(mtime - float(ts)) < 86400) else mtime
        except Exception:
            pass                                     # unreadable outbox → heartbeat = file mtime, no crash

    drive = meta["transport"] == "drive"
    # WRITE their inbox (push their queue + cleared approvals)
    inbox = {
        "to": aid, "role": meta["role"], "transport": meta["transport"],
        "seats": meta.get("seats", []),          # the allocated seats this agent holds
        "ts": time.time(), "generated": time.strftime("%Y-%m-%d %H:%M:%S"),
        "pending": pending,
        "refresh": (f"python3 -m company_runtime.agent_refresh {aid}" if not drive
                    else "re-read this inbox file from the Google Drive mirror"),
        "note": (("REFRESH when David says so: RE-READ this file from the Google Drive mirror "
                  "(you can't run a shell); it's the live queue, kept current by the coordinator. "
                  "Write your reply to a 'DISENELO_agent_bus_gemini_outbox' Doc in the same Drive folder: "
                  if drive else
                  f"REFRESH when David says so: run  python3 -m company_runtime.agent_refresh {aid}  "
                  "— it re-pulls the live board + shows what changed since you last looked. "
                  "Then reply into outbox.json: ")
                 + "{\"ts\":<epoch>,\"updates\":[{\"wo\":\"WO-XXX\","
                   "\"status\":\"done|blocked|question|progress\",\"detail\":\"...\"}]}"),
    }
    json.dump(inbox, open(os.path.join(box, "inbox.json"), "w"), indent=2)
    if drive:  # stage a copy for the Drive push (coordinator mirrors this folder to Google Drive)
        stage = os.path.join(BUS, "_drive_outgoing"); os.makedirs(stage, exist_ok=True)
        json.dump(inbox, open(os.path.join(stage, f"{aid}_inbox.json"), "w"), indent=2)

    # heartbeat freshness
    fresh = last_seen is not None and (time.time() - float(last_seen)) < 86400
    return {
        "id": aid, "role": meta["role"], "transport": meta["transport"],
        "seats": [s["seat"] for s in meta.get("seats", [])],
        "last_seen": last_seen, "fresh": fresh,
        "pending": len(pending),
        "active":  sum(1 for p in pending if p["state"] == "active"),
        "in_review": sum(1 for p in pending if p["state"] == "in_review"),
        "blocked": sum(1 for p in pending if p["state"] == "blocked"),
        "updates": updates,
        "next": plan,
        "needs_david": [p["wo"] for p in pending if p["importance"] in ("DAVID", "RESERVED", "CONFIRM") and p["state"] == "in_review"],
    }


def ping_all() -> list[dict]:
    reg = _load_registry()
    rows = _rows()
    results = [ping(aid, reg, rows) for aid in reg]
    # write an aggregate the dashboard/coordinator can read
    json.dump({"ts": time.time(), "agents": results},
              open(os.path.join(BUS, "heartbeat.json"), "w"), indent=2)
    return results


# NOTE: no onboard() — the roster is the ALLOCATED SEATS (Seat Occupancy Map /
# company_graph.SEATS). To add/move an agent, allocate the seat there; the bus mirrors it.


def _checklist(results):
    def ago(ts):
        if not ts: return "never"
        d = time.time() - float(ts)
        return f"{int(d//3600)}h ago" if d >= 3600 else f"{int(d//60)}m ago"
    print("\n╔══ AGENT PING CHECKLIST · roster = allocated seats ══╗")
    print(f"{'agent':9} {'transport':9} {'heartbeat':11} {'pend':>4} {'actv':>4} {'rev':>3} {'blk':>3}  seats · updates/needs")
    for r in results:
        flag = "🟢" if r["fresh"] else "⚪"
        nd = (" · David:" + ",".join(r["needs_david"])) if r["needs_david"] else ""
        up = f" · {len(r['updates'])} update(s)" if r["updates"] else ""
        seats = ",".join(r.get("seats", []))
        print(f"{flag}{r['id']:8} {r['transport']:9} {ago(r['last_seen']):11} "
              f"{r['pending']:>4} {r['active']:>4} {r['in_review']:>3} {r['blocked']:>3}  {seats}{up}{nd}")
    print("\nRoster mirrors company_graph.SEATS (allocated) — no onboarding on the bus.")
    print("Inboxes → blender/agent_bus/<id>/inbox.json · heartbeat → heartbeat.json · Drive agents staged in _drive_outgoing/")


if __name__ == "__main__":
    _checklist(ping_all())
