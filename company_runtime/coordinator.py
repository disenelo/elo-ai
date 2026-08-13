"""
company_runtime/coordinator.py — the Architect's coordination pass over the board.

This is the "talk to the agents → they relay → I triage → I bring what's waiting to David" layer.
Reads the live dispatch board (the shared medium the agents relay through) and computes:

  outstanding   — everything not done
  priorities    — outstanding ranked P0→P3 then by activity
  easy_links    — READY work whose dependencies are all met, ranked by leverage (how much it unblocks)
  needs_david   — the cross-approval queue: anything awaiting L3 (in-review / claimed) or safety-gated

Pure read + compute. Additive; no kernel edits (LAW-017).

  from company_runtime import coordinator
  d = coordinator.digest()            # the structured digest
  print(coordinator.summary(d))       # the human-readable "bring to David" briefing
"""
from __future__ import annotations
import os

from company_runtime import company_state_writer as csw

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_BOARD = os.path.join(_ROOT, "engineering", "work_orders", "DISPATCH_BOARD.md")

_DONE = {"done_david", "done_claimed", "superseded"}
_AWAIT_L3 = {"done_claimed", "in_review"}          # agent says done / in review → needs David's stamp
_ACTIVE = {"ready", "in_progress", "dispatched", "queued"}
_PRI_ORDER = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}

_SAFETY = csw._SAFETY_KEYWORDS  # reuse the safety-keyword set


def _rows(board_path=_BOARD):
    with open(board_path, encoding="utf-8") as f:
        return csw._parse_board(f.read())


def digest(board_path=_BOARD) -> dict:
    rows = _rows(board_path)
    by_id = {r["id"]: r for r in rows}
    done_ids = {r["id"] for r in rows if r["status"] in _DONE}

    # who depends on whom (leverage)
    dep_graph = csw._build_graph(rows)                 # {id: [deps]}
    dependents: dict[str, int] = {}
    for wid, deps in dep_graph.items():
        for d in deps:
            dependents[d] = dependents.get(d, 0) + 1

    def deps_met(r):
        deps = dep_graph.get(r["id"], [])
        return all(d in done_ids for d in deps)

    outstanding = [r for r in rows if r["status"] not in _DONE]

    priorities = sorted(
        outstanding,
        key=lambda r: (_PRI_ORDER.get(r["priority"], 3),
                       0 if r["status"] in ("in_progress", "dispatched") else 1),
    )

    # easiest to link = READY-ish, all deps met, ranked by how much it unblocks
    easy = [r for r in outstanding if r["status"] in ("ready", "queued") and deps_met(r)]
    easy.sort(key=lambda r: (-dependents.get(r["id"], 0), _PRI_ORDER.get(r["priority"], 3)))

    blocked = [r for r in rows if r["status"] == "blocked"]

    def is_safety(r):
        t = (r["title"] + " " + r["agent"]).lower()
        return any(k in t for k in _SAFETY)

    needs_david = [r for r in rows if r["status"] in _AWAIT_L3]
    safety_wait = [r for r in needs_david if is_safety(r)]

    return {
        "counts": {
            "total": len(rows), "outstanding": len(outstanding),
            "needs_david": len(needs_david), "blocked": len(blocked),
            "ready_now": len(easy),
        },
        "priorities": [_slim(r) for r in priorities[:6]],
        "easy_links": [dict(_slim(r), unblocks=dependents.get(r["id"], 0)) for r in easy[:6]],
        "needs_david": [_slim(r) for r in needs_david],
        "safety_gated_waiting": [_slim(r) for r in safety_wait],
        "blocked": [dict(_slim(r), on=r["depends_on"]) for r in blocked[:8]],
    }


def _slim(r):
    return {"id": r["id"], "title": r["title"], "pri": r["priority"],
            "status": r["status"], "agent": r["agent"]}


def summary(d: dict) -> str:
    """The 'bring it to David' briefing — what I'd say when I read the board."""
    c = d["counts"]
    L = [f"Board read: {c['total']} WOs · {c['outstanding']} outstanding · "
         f"{c['needs_david']} waiting on you · {c['blocked']} blocked."]
    if d["needs_david"]:
        L.append("\nWAITING ON YOU (cross-approval):")
        for r in d["needs_david"]:
            flag = "  ⚠ safety-gate" if r in d["safety_gated_waiting"] else ""
            L.append(f"  • {r['id']} [{r['pri']}] {r['title']} — {r['agent']}{flag}")
    if d["easy_links"]:
        L.append("\nEASIEST TO LINK NEXT (ready, deps met, high-leverage):")
        for r in d["easy_links"]:
            L.append(f"  • {r['id']} [{r['pri']}] {r['title']} — unblocks {r['unblocks']} other(s)")
    if d["priorities"]:
        L.append("\nTOP PRIORITIES:")
        for r in d["priorities"]:
            L.append(f"  • {r['id']} [{r['pri']}] {r['title']} ({r['status']})")
    if d["blocked"]:
        L.append("\nBLOCKED:")
        for r in d["blocked"]:
            L.append(f"  • {r['id']} {r['title']} — on {r['on']}")
    return "\n".join(L)


if __name__ == "__main__":
    print(summary(digest()))
