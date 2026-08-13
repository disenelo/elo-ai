"""
company_runtime/orchestration_faculty.py — EA2-6 Orchestration Faculty.

Orchestrate multi-seat Work-Order chains: dependency-driven sequencing +
cross-seat hand-offs, so "what should fire next" and "who's waiting on whom"
become computable from the live dispatch board.

ADDITIVE ONLY — a net-new, READ-ONLY faculty. It NEVER writes the board or any
state file. It does NOT touch server.py, runtime/*, core/*, or the frozen
cognitive kernel (LAW-017 / FREEZE_V1_LOCK). It only parses + computes.

Board parsing is reused verbatim from company_state_writer (`_parse_board`,
`_build_graph`, `_BOARD_PATH`, `_DONE`-equivalent status vocab) — nothing is
reinvented.

Public API (all pure — take a board_path, return plain dicts/lists):
  build_chains(board_path=…)      -> dict   dependency chains per WO (topo order),
                                            grouped by seat, + cross-seat hand-offs,
                                            + detected cycles.
  next_actionable(seat=None, …)   -> list   WOs whose deps are ALL met AND are
                                            READY (can start now), ranked by
                                            leverage (downstream WOs unblocked).
  blocked_by(wo_id, …)            -> dict   the unmet dependencies blocking a WO.
  handoffs(board_path=…)          -> list   cross-seat dependencies (seat A waiting
                                            on seat B) — chains across agents.
  detect_cycles(board_path=…)     -> list   dependency cycles (list of id-lists);
                                            terminates — never infinite-loops.

Dependency-"met" rule:
  A dependency is MET if it is a WO on the board whose status is done
  (done_david / done_claimed / superseded), OR if it is a WO id no longer on the
  board at all (an archived / completed WO is not blocking anything visible).
  Anything else — a present, not-done WO — is UNMET.
"""
from __future__ import annotations

import logging
import os

# Reuse canonical board parsing from the state writer — do not reinvent.
from company_runtime.company_state_writer import (
    _parse_board,     # (board_text) -> list[dict rows]
    _build_graph,     # (rows) -> {id: [dep_id, ...]} for ids that HAVE deps
    _BOARD_PATH,
)

_logger = logging.getLogger(__name__)

# Statuses that count as "done" for dependency satisfaction (matches coordinator).
_DONE_STATUSES: frozenset[str] = frozenset({"done_david", "done_claimed", "superseded"})

# Statuses a WO can be in to "start now" once its deps are met.
_ACTIONABLE_STATUSES: frozenset[str] = frozenset({"ready", "queued"})

_PRI_ORDER = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}


def _clean_seat(agent: str) -> str:
    """Normalise a board 'agent' cell for display + comparison: strip markdown
    bold (`**`) and collapse whitespace, so `**UI/Avatar (Design)**` and
    `UI/Avatar (Design)` are recognised as the SAME seat (avoids false hand-offs).
    """
    return " ".join((agent or "").replace("*", " ").split())


# ── Board load (graceful — never raises) ──────────────────────────────────────

def _load_rows(board_path: str = _BOARD_PATH) -> list[dict]:
    """Parse the board into rows. Missing / unreadable / malformed → []."""
    try:
        with open(board_path, encoding="utf-8") as f:
            text = f.read()
    except (FileNotFoundError, OSError):
        return []
    try:
        return _parse_board(text) or []
    except Exception as exc:  # defensive — parsing must never crash a caller
        _logger.debug("orchestration_faculty: parse failed: %s", exc)
        return []


# ── Core index (rows → maps we compute everything from) ───────────────────────

class _Index:
    """Precomputed views over the board. Pure; built once per public call."""

    def __init__(self, rows: list[dict]):
        self.rows = rows
        self.by_id: dict[str, dict] = {r["id"]: r for r in rows}
        self.seat_of: dict[str, str] = {r["id"]: _clean_seat(r.get("agent", "")) for r in rows}
        self.done_ids: set[str] = {
            r["id"] for r in rows if r.get("status") in _DONE_STATUSES
        }
        # Full forward dep map: EVERY row id present, deps = [] when none.
        partial = _build_graph(rows)                       # {id:[deps]} (deps-only ids)
        self.deps: dict[str, list[str]] = {
            r["id"]: list(partial.get(r["id"], [])) for r in rows
        }
        # Reverse map: dep_id -> [ids that directly depend on it] (only on-board ids).
        self.dependents: dict[str, list[str]] = {}
        for wid, ds in self.deps.items():
            for d in ds:
                self.dependents.setdefault(d, []).append(wid)

    # A dependency is met if it's a done WO on the board, or not on the board at all.
    def dep_met(self, dep: str) -> bool:
        if dep in self.done_ids:
            return True
        if dep not in self.by_id:      # off-board (archived / completed) → not blocking
            return True
        return False

    def unmet(self, wo_id: str) -> list[str]:
        return [d for d in self.deps.get(wo_id, []) if not self.dep_met(d)]

    def deps_all_met(self, wo_id: str) -> bool:
        return not self.unmet(wo_id)


# ── Cycle detection (DFS 3-colour; terminates, never infinite-loops) ──────────

def _find_cycles(deps: dict[str, list[str]]) -> list[list[str]]:
    """
    Return dependency cycles as ordered id-lists (e.g. ['A','B','A']).
    Only edges between nodes present in `deps` are followed, so off-board deps
    can never create a phantom cycle. Guaranteed to terminate.
    """
    WHITE, GRAY, BLACK = 0, 1, 2
    color: dict[str, int] = {n: WHITE for n in deps}
    cycles: list[list[str]] = []
    seen_signatures: set[frozenset[str]] = set()

    def visit(node: str, path: list[str]) -> None:
        color[node] = GRAY
        path.append(node)
        for nxt in deps.get(node, []):
            if nxt not in color:        # off-board dep — not a graph node, skip
                continue
            if color[nxt] == GRAY:      # back-edge → cycle
                idx = path.index(nxt)
                cyc = path[idx:] + [nxt]
                sig = frozenset(cyc)
                if sig not in seen_signatures:
                    seen_signatures.add(sig)
                    cycles.append(cyc)
            elif color[nxt] == WHITE:
                visit(nxt, path)
        path.pop()
        color[node] = BLACK

    for n in deps:
        if color[n] == WHITE:
            visit(n, [])
    return cycles


def detect_cycles(board_path: str = _BOARD_PATH) -> list[list[str]]:
    """Public: dependency cycles on the board. [] when acyclic or board empty."""
    idx = _Index(_load_rows(board_path))
    return _find_cycles(idx.deps)


# ── Topological prerequisite chain for one WO (cycle-safe) ────────────────────

def _prereq_chain(idx: _Index, wo_id: str) -> list[str]:
    """
    Ordered list of the WO's transitive prerequisites (deps-first / topological),
    restricted to prerequisites that are present on the board. Cycle-safe: a node
    already on the current path is not re-entered, so this always terminates.
    """
    order: list[str] = []
    placed: set[str] = set()

    def walk(node: str, path: set[str]) -> None:
        for dep in idx.deps.get(node, []):
            if dep not in idx.by_id:        # off-board prereq — not orderable
                continue
            if dep in path:                 # cycle guard — do not recurse
                continue
            if dep not in placed:
                walk(dep, path | {dep})
                if dep not in placed:
                    order.append(dep)
                    placed.add(dep)

    walk(wo_id, {wo_id})
    return order


# ── Leverage: how many downstream WOs a WO unblocks (transitive) ──────────────

def _downstream_count(idx: _Index) -> dict[str, int]:
    """id -> number of distinct WOs transitively downstream (that it unblocks)."""
    memo: dict[str, set[str]] = {}

    def descendants(node: str, path: set[str]) -> set[str]:
        if node in memo:
            return memo[node]
        acc: set[str] = set()
        for child in idx.dependents.get(node, []):
            if child in path:               # cycle guard
                continue
            acc.add(child)
            acc |= descendants(child, path | {child})
        memo[node] = acc
        return acc

    return {r["id"]: len(descendants(r["id"], {r["id"]})) for r in idx.rows}


# ── next_actionable ───────────────────────────────────────────────────────────

def next_actionable(seat: str | None = None, board_path: str = _BOARD_PATH) -> list[dict]:
    """
    WOs that can START NOW: status is READY-ish AND every dependency is met.
    Optionally filter to one seat (case-insensitive substring on the agent cell).
    Ranked by leverage (transitive downstream WOs unblocked), then priority, then id.

    Each item: {id, title, seat, priority, status, leverage, unblocks(direct)}.
    """
    idx = _Index(_load_rows(board_path))
    lev = _downstream_count(idx)

    want = (seat or "").strip().lower() or None
    out: list[dict] = []
    for r in idx.rows:
        if r.get("status") not in _ACTIONABLE_STATUSES:
            continue
        if not idx.deps_all_met(r["id"]):
            continue
        seat_str = idx.seat_of.get(r["id"], "")
        if want and want not in seat_str.lower():
            continue
        out.append({
            "id":       r["id"],
            "title":    r["title"],
            "seat":     seat_str,
            "priority": r.get("priority", "P3"),
            "status":   r.get("status", ""),
            "leverage": lev.get(r["id"], 0),
            "unblocks": list(idx.dependents.get(r["id"], [])),
        })

    out.sort(key=lambda x: (-x["leverage"], _PRI_ORDER.get(x["priority"], 3), x["id"]))
    return out


# ── blocked_by ─────────────────────────────────────────────────────────────────

def blocked_by(wo_id: str, board_path: str = _BOARD_PATH) -> dict:
    """
    The unmet dependencies blocking `wo_id`.

    Returns:
      {"wo": id, "found": bool, "ready": bool,
       "blocked_by": [{id, status, seat, on_board}],   # unmet deps
       "met":        [id, ...]}                          # already-satisfied deps
    Unknown wo_id → found=False, empty lists (graceful; never raises).
    """
    idx = _Index(_load_rows(board_path))
    wo_id = (wo_id or "").strip()
    if wo_id not in idx.by_id:
        return {"wo": wo_id, "found": False, "ready": False, "blocked_by": [], "met": []}

    deps = idx.deps.get(wo_id, [])
    unmet, met = [], []
    for d in deps:
        if idx.dep_met(d):
            met.append(d)
        else:
            unmet.append({
                "id":       d,
                "status":   idx.by_id.get(d, {}).get("status", "unknown"),
                "seat":     idx.seat_of.get(d, ""),
                "on_board": d in idx.by_id,
            })
    return {
        "wo":        wo_id,
        "found":     True,
        "ready":     not unmet,
        "blocked_by": unmet,
        "met":       met,
    }


# ── handoffs ───────────────────────────────────────────────────────────────────

def handoffs(board_path: str = _BOARD_PATH) -> list[dict]:
    """
    Cross-seat dependencies: a WO owned by seat A depends on a WO owned by seat B
    (A != B). These are the chain hand-off points across agents.

    Each item: {wo, wo_seat, depends_on, dep_seat, dep_status, met}.
    Sorted so unmet hand-offs (still waiting) come first.
    """
    idx = _Index(_load_rows(board_path))
    out: list[dict] = []
    for r in idx.rows:
        wo_seat = idx.seat_of.get(r["id"], "")
        for dep in idx.deps.get(r["id"], []):
            if dep not in idx.by_id:            # off-board dep has no known seat
                continue
            dep_seat = idx.seat_of.get(dep, "")
            if dep_seat and wo_seat and dep_seat != wo_seat:
                out.append({
                    "wo":         r["id"],
                    "wo_seat":    wo_seat,
                    "depends_on": dep,
                    "dep_seat":   dep_seat,
                    "dep_status": idx.by_id[dep].get("status", ""),
                    "met":        idx.dep_met(dep),
                })
    out.sort(key=lambda x: (x["met"], x["wo"]))   # unmet (False) first
    return out


# ── build_chains ────────────────────────────────────────────────────────────────

def build_chains(board_path: str = _BOARD_PATH) -> dict:
    """
    Full orchestration view. For every WO that has prerequisites, compute:
      - prerequisites:  transitive prereqs in topological (deps-first) order
      - by_seat:        those prereqs grouped by owning seat
      - handoffs:       cross-seat prereqs within this WO's chain
      - ready:          whether all direct deps are currently met

    Returns:
      {"chains": { wo_id: {...} },
       "cycles": [[...], ...],
       "counts": {"work_orders", "with_deps", "cross_seat_handoffs", "cycles"}}
    Empty / malformed board → empty chains, empty cycles (no crash).
    """
    idx = _Index(_load_rows(board_path))
    cycles = _find_cycles(idx.deps)

    chains: dict[str, dict] = {}
    handoff_total = 0
    for r in idx.rows:
        deps = idx.deps.get(r["id"], [])
        if not deps:
            continue
        wo_seat = idx.seat_of.get(r["id"], "")
        prereqs = _prereq_chain(idx, r["id"])

        by_seat: dict[str, list[str]] = {}
        for p in prereqs:
            by_seat.setdefault(idx.seat_of.get(p, ""), []).append(p)

        ho = []
        for dep in deps:
            if dep not in idx.by_id:
                continue
            dep_seat = idx.seat_of.get(dep, "")
            if dep_seat and wo_seat and dep_seat != wo_seat:
                ho.append({"depends_on": dep, "dep_seat": dep_seat,
                           "met": idx.dep_met(dep)})
        handoff_total += len(ho)

        chains[r["id"]] = {
            "seat":          wo_seat,
            "status":        r.get("status", ""),
            "direct_deps":   list(deps),
            "prerequisites": prereqs,       # topological, deps-first
            "by_seat":       by_seat,
            "handoffs":      ho,
            "ready":         idx.deps_all_met(r["id"]),
        }

    return {
        "chains": chains,
        "cycles": cycles,
        "counts": {
            "work_orders":         len(idx.rows),
            "with_deps":           len(chains),
            "cross_seat_handoffs": handoff_total,
            "cycles":              len(cycles),
        },
    }


# ── CLI one-shot (read-only briefing) ─────────────────────────────────────────

if __name__ == "__main__":
    import json
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    bc = build_chains()
    print("Orchestration Faculty — live board")
    print(f"  work orders:          {bc['counts']['work_orders']}")
    print(f"  with dependencies:    {bc['counts']['with_deps']}")
    print(f"  cross-seat hand-offs: {bc['counts']['cross_seat_handoffs']}")
    print(f"  dependency cycles:    {bc['counts']['cycles']}")

    na = next_actionable()
    print(f"\nNext actionable (deps met + ready), top {min(8, len(na))} by leverage:")
    for item in na[:8]:
        print(f"  • {item['id']} [{item['priority']}] leverage={item['leverage']} "
              f"({item['seat']}) — {item['title'][:50]}")

    ho = handoffs()
    print(f"\nCross-seat hand-offs: {len(ho)} (unmet first)")
    for h in ho[:8]:
        flag = "waiting" if not h["met"] else "met"
        print(f"  • {h['wo']} ({h['wo_seat']}) → {h['depends_on']} ({h['dep_seat']}) [{flag}]")

    if bc["cycles"]:
        print(f"\n⚠ dependency cycles detected: {json.dumps(bc['cycles'])}")
