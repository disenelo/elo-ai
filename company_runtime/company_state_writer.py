"""
company_runtime/company_state_writer.py — writes company_state.json for Presence company panel.

Pattern mirrors blender_bridge/brain_state_writer.py.
ADDITIVE ONLY — never modifies the frozen cognitive kernel (LAW-017 / FREEZE_V1_LOCK).

Schema: company_state/v1
Output: blender/company_state.json  (Unity polls alongside brain_state.json)
Intake: blender/company_actions.json  (Presence writes; we watch and process)

Entry points:
  publish()                           — emit company_state.json from dispatch board
  process_action(action: dict) -> dict — validate + handle one action dict
  watch_actions(interval=2.0)         — background poll loop (call from a thread)
  handle_company_approve(...)         — CAL stub for EA2-2 to wire
"""
from __future__ import annotations

import datetime
import json
import logging
import os
import re
import time

from company_runtime import company_graph

_logger = logging.getLogger(__name__)

# Builder status vocab → dashboard kanban columns (READY/WORKING/REVIEW/BLOCKED/DONE)
_KANBAN = {
    # "DONE" means done — both David-approved and agent-claimed land in DONE, so approvals STICK
    # and never bounce back into review. Items genuinely awaiting David use IN_REVIEW (→ REVIEW).
    "done_david": "DONE", "done_claimed": "DONE", "ready": "READY",
    "blocked": "BLOCKED", "in_progress": "WORKING", "in_review": "REVIEW",
    "dispatched": "WORKING", "queued": "READY", "deferred": "BLOCKED",
    "superseded": "DONE",
}


def _kanban(status: str) -> str:
    return _KANBAN.get(status, "READY")

_ROOT         = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_STATE_PATH   = os.path.join(_ROOT, "blender", "company_state.json")
_ACTIONS_PATH = os.path.join(_ROOT, "blender", "company_actions.json")
_BOARD_PATH   = os.path.join(_ROOT, "engineering", "work_orders", "DISPATCH_BOARD.md")

# keywords that identify safety-gated WOs; missing human_flag → refused
_SAFETY_KEYWORDS: frozenset[str] = frozenset({
    "money", "financial", "legal", "compliance", "budget", "billing",
    "payment", "kickstarter", "fundrais", "salary", "invest", "revenue",
    "cost", "price", "licence", "license", "tax", "insurance", "contract",
    "safety", "security", "personal data", "gdpr", "privacy",
})

# L3 actors who may approve (stub — real gate is EA2-5 Approval Faculty)
_L3_ACTORS: frozenset[str] = frozenset({"david", "disenelo", "founder"})

# table-row regex: | **ID** | title | agent | pri | status | depends |
_ROW_RE = re.compile(
    r"^\|\s*\*?\*?([\w][\w\-]*)\*?\*?\s*\|"   # group 1: WO id
    r"([^|]+)\|"                                # group 2: title
    r"([^|]+)\|"                                # group 3: agent
    r"([^|]*)\|"                                # group 4: priority
    r"([^|]+)\|"                                # group 5: status
    r"([^|]*)\|"                                # group 6: depends_on
)

# prefixes that identify work-order rows (skip header/separator lines)
# NOTE: must cover EVERY lane or those WOs go invisible to the dashboard (RD-2 bug, 2026-07-31).
_WO_PREFIXES = ("WO-", "GM-", "INT", "EA", "MK-", "CR-", "FH-",
                "RD-", "BO-", "LG-", "SD-", "DIV-", "SEAT-")


# ── Board parsing ─────────────────────────────────────────────────────────────

def _norm_status(raw: str) -> str:
    r = raw.strip()
    if "DONE" in r and "David" in r:   return "done_david"
    if "DONE" in r:                    return "done_claimed"
    if "READY" in r:                   return "ready"
    if "BLOCKED" in r:                 return "blocked"
    if "IN_PROGRESS" in r:             return "in_progress"
    if "IN_REVIEW" in r:               return "in_review"
    if "DISPATCHED" in r:              return "dispatched"
    if "DEFERRED" in r:                return "deferred"
    if "QUEUED" in r:                  return "queued"
    if "superseded" in r.lower():      return "superseded"
    return r[:40].strip()


def _norm_priority(raw: str) -> str:
    m = re.search(r"P([0-9])", raw)
    return f"P{m.group(1)}" if m else "P3"


def _parse_board(board_text: str) -> list[dict]:
    rows: list[dict] = []
    for line in board_text.splitlines():
        m = _ROW_RE.match(line.strip())
        if not m:
            continue
        wo_id = m.group(1).strip()
        if not any(wo_id.startswith(pfx) for pfx in _WO_PREFIXES):
            continue
        rows.append({
            "id":         wo_id,
            "title":      m.group(2).strip()[:80],
            "agent":      m.group(3).strip()[:40],
            "priority":   _norm_priority(m.group(4)),
            "status":     _norm_status(m.group(5)),
            "status_raw": m.group(5).strip(),
            "depends_on": m.group(6).strip()[:40] or "—",
        })
    return rows


def _build_graph(rows: list[dict]) -> dict:
    """Simple dependency map: wo_id → [dep_id, ...]"""
    graph: dict[str, list[str]] = {}
    for row in rows:
        deps_raw = row.get("depends_on", "—")
        deps = []
        for token in re.findall(r"[\w\-]+", deps_raw):
            if any(token.startswith(pfx) for pfx in _WO_PREFIXES):
                deps.append(token)
        if deps:
            graph[row["id"]] = deps
    return graph


def _parse_company_focus(board_text: str) -> dict | None:
    """Extract the COMPANY_FOCUS HTML comment from the board.
    Format: <!-- COMPANY_FOCUS: <milestone> | items: <csv> | note: <note> -->
    Returns {"milestone": str, "items": [str], "note": str} or None.
    Searches full board_text — the marker may appear well past 10 000 chars.
    """
    m = re.search(r"COMPANY_FOCUS:\s*([^|]+)\|\s*items:\s*([^|]+)(?:\|\s*note:\s*(.+?))?(?:\s*-->)",
                  board_text)
    if not m:
        return None
    return {
        "milestone": m.group(1).strip(),
        "items":     [x.strip() for x in m.group(2).split(",") if x.strip()],
        "note":      (m.group(3) or "").strip(),
    }


def _voiced_briefing(today: list, waiting: list, blocked: list, in_progress: list) -> str:
    parts = []
    if today:
        parts.append(f"{len(today)} item{'s' if len(today) != 1 else ''} ready to pick up")
    if waiting:
        parts.append(f"{len(waiting)} awaiting David approval")
    if in_progress:
        ids = ", ".join(r["id"] for r in in_progress[:3])
        parts.append(f"{ids} in progress")
    if blocked:
        parts.append(f"{len(blocked)} blocked")
    return " · ".join(parts) if parts else "all clear"


# ── WO test health (from wo_test_runner report) → dashboard block ─────────────

def _load_wo_tests(report_path: str) -> dict:
    """Compact WO-test summary for the Company Brain dashboard. Empty if no report yet."""
    if not os.path.exists(report_path):
        return {"generated": None, "note": "no test report yet — run company_runtime.wo_test_runner",
                "totals": {}, "items": []}
    with open(report_path, encoding="utf-8") as f:
        rep = json.load(f)
    items = rep.get("items", [])
    def tier_roll(t):
        sub = [x for x in items if x.get("tier") == t]
        return {"green": sum(1 for x in sub if x.get("green")), "total": len(sub)}
    return {
        "generated": rep.get("generated"),
        "applied": rep.get("apply", False),
        "closed": rep.get("closed", []),
        "totals": {
            "green": sum(1 for x in items if x.get("green")),
            "total": len(items),
            "AUTO": tier_roll("AUTO"), "CONFIRM": tier_roll("CONFIRM"), "REVIEW": tier_roll("REVIEW"),
        },
        "items": [
            {"wo": x.get("wo"), "tier": x.get("tier"), "green": x.get("green"),
             "passed": x.get("passed"), "failed": x.get("failed"),
             "summary": x.get("summary"), "test": x.get("test"),
             "action": ("AUTO-CLOSE" if x.get("tier") == "AUTO" and x.get("green")
                        else "PROPOSE-CLOSE" if x.get("tier") == "CONFIRM" and x.get("green")
                        else "HOLD → David" if x.get("tier") == "REVIEW"
                        else "OPEN (not green)")}
            for x in items
        ],
    }


# ── Atomic writer (mirrors brain_state_writer pattern) ────────────────────────

def _atomic_write(path: str, payload: dict) -> bool:
    try:
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        os.replace(tmp, path)
        return True
    except Exception as exc:
        _logger.error("company_state_writer: write failed: %s", exc)
        return False


# ── publish() ─────────────────────────────────────────────────────────────────

def publish(board_path: str = _BOARD_PATH, state_path: str = _STATE_PATH) -> bool:
    """
    Read the dispatch board and emit company_state.json.

    Callable once per cycle (e.g. from server.py after brain_state write),
    or as a CLI one-shot. Returns True on success.
    """
    try:
        with open(board_path, encoding="utf-8") as f:
            board_text = f.read()
    except FileNotFoundError:
        _logger.warning("company_state_writer: board not found at %s", board_path)
        board_text = ""

    rows = _parse_board(board_text)

    # dashboard-shaped views (Presence panel + Company Brain consume these)
    from company_runtime import wo_policy
    def _pol(r): return wo_policy.classify(r["id"], r["title"], r.get("status_raw", ""))

    board_view = [
        dict({"id": r["id"], "title": r["title"], "lane": company_graph.lane_for(r["agent"]),
              "status": _kanban(r["status"]), "seat": r["agent"], "pri": r["priority"]},
             **{k: _pol(r)[k] for k in ("importance", "needs_david", "badge")})
        for r in rows
    ]
    # WO-061: read COMPANY_FOCUS marker → today_priorities reflects the active milestone, not stale backlog.
    # When the marker exists, surface IN_PROGRESS/IN_REVIEW P0/P1 items that match the focus WO IDs.
    _focus = _parse_company_focus(board_text)
    if _focus:
        # Extract focus WO IDs from the items list.
        # Handles slash-series notation: "TTS(WO-016/019)" → {"WO-016", "WO-019"}
        # and suffix variants: "WO-052A" → normalised base "WO-052" for matching.
        _focus_nums: set[str] = set()
        for _fi in _focus["items"]:
            for _m2 in re.finditer(r"WO-(\d+[A-Z]?)(/\d+[A-Z]?)*", _fi):
                # First ID: full match group "WO-NNN[A]"
                _parts = _m2.group(0).split("/")
                for _i, _part in enumerate(_parts):
                    _raw = _part if _i == 0 else f"WO-{_part}"
                    # Normalise: strip trailing letter suffix so WO-052A matches row WO-052
                    _focus_nums.add(re.sub(r"[A-Z]+$", "", _raw.strip()))

        def _wo_base(wid: str) -> str:
            return re.sub(r"[A-Z]+$", "", wid.strip())

        _active_rows = [
            r for r in rows
            if r["status"] in ("in_progress", "dispatched", "in_review")
            and r["priority"] in ("P0", "P1")
            and (not _focus_nums or _wo_base(r["id"]) in _focus_nums)
        ]
        # Fallback: any dispatched/in_progress Builder-lane P0/P1 (never surfaces MK/BO/LG)
        if not _active_rows:
            _active_rows = [
                r for r in rows
                if r["status"] in ("in_progress", "dispatched")
                and r["priority"] in ("P0", "P1")
                and "Builder" in r["agent"]
            ]
        today = [
            {"text": r["title"], "owner": r["agent"], "priority": r["priority"],
             "status": r["status"], "focus_milestone": _focus["milestone"]}
            for r in _active_rows
        ][:5] or [
            {"text": f"Focus: {_focus['milestone']}", "owner": "Builder",
             "priority": "P0", "items": _focus["items"]}
        ]
    else:
        today = [
            {"text": r["title"], "owner": r["agent"], "priority": r["priority"]}
            for r in rows if r["status"] == "ready" and r["priority"] in ("P0", "P1")
        ][:5]
    waiting = [
        dict({"wo": r["id"], "text": r["title"], "level": "L3"},
             **{k: _pol(r)[k] for k in ("importance", "needs_david", "badge", "label")})
        for r in rows if _kanban(r["status"]) == "REVIEW"
    ]
    blocked = [
        {"wo": r["id"], "text": r["title"], "on": r["depends_on"]}
        for r in rows if r["status"] == "blocked"
    ]
    in_progress = [r for r in rows if r["status"] in ("in_progress", "dispatched")]
    open_n = sum(1 for r in rows if r["status"] in ("ready", "in_progress", "dispatched"))

    payload = {
        "schema":               "company_state/v1",
        "_ts":                  round(time.time(), 3),
        "updated":              datetime.datetime.utcnow().isoformat() + "Z",
        "source":               "company_runtime.company_state_writer — parsed live from DISPATCH_BOARD.md",
        "greeting":             {"founder": "David",
                                 "phase": "Phase I → II (Digital Companion → Executive Partner)"},
        "voiced_briefing":      _voiced_briefing(today, waiting, blocked, in_progress),
        "company_focus":        _focus or {},
        "today_priorities":     today,
        "waiting_for_approval": waiting,
        "blocked":              blocked,
        "money": {
            "status": "not yet modeled",
            "detail": "Finance seat (SEAT-BIZ-002) runs WO BO-2 — no figures invented.",
        },
        "roadmap": [
            {"id": "PROJ-ELOOS",   "name": "eLo OS (Cognitive Spine)", "phase": "Foundations",        "progress": 0.72},
            {"id": "PROJ-ONEBRAIN","name": "One Brain Visualiser",     "phase": "M1–M4+C1 done; M5 building", "progress": 0.50},
            {"id": "PROJ-GAME",    "name": "eLo's Planet (game)",       "phase": "Model transition",    "progress": 0.55},
            {"id": "PROJ-ROBOT",   "name": "eLo Robot",                 "phase": "R&D opening",         "progress": 0.15},
            {"id": "PROJ-008",     "name": "Kickstarter",               "phase": "Pre-campaign",        "progress": 0.10},
        ],
        "engineering": {"open": open_n, "in_review": len(waiting), "blocked": len(blocked),
                        "notes": f"{len(rows)} work orders parsed live from the board."},
        "alerts": [{"id": "ALT-1", "level": "info",
                    "text": "company_state.json is LIVE — written by company_runtime, parsed from the board."}],
        "suggested_decisions": [
            {"id": "SUG-1", "text": "Wire EA2-2 (Presence panel) to show + approve from this live state"},
        ],
        "board":        board_view,
        "dep_graph":    _build_graph(rows),                # WO dependency map (Builder's original)
        "graph":        company_graph.build_graph(),        # division/seat/mood connectome (Company Brain)
        "seats_sample": [
            {"id": s[0], "role": s[2], "occupant": s[3], "state": s[5]}
            for s in company_graph.SEATS
        ],
    }

    # coordination digest — the "bring what's waiting to David" layer (lazy import avoids a cycle)
    try:
        from company_runtime import coordinator
        payload["coordination"] = coordinator.digest(board_path)
    except Exception as exc:
        _logger.debug("company_state_writer: coordination digest skipped: %s", exc)

    # WO test health — feeds the Company Brain dashboard (latest wo_test_runner report, if present)
    try:
        payload["wo_tests"] = _load_wo_tests(os.path.join(os.path.dirname(state_path), "wo_test_report.json"))
    except Exception as exc:
        _logger.debug("company_state_writer: wo_tests skipped: %s", exc)

    # importance legend — how each WO is flagged for approval (David's 2026-08-01 rule)
    try:
        from company_runtime import wo_policy
        payload["policy_legend"] = [
            {"importance": k, "badge": wo_policy.BADGE[k], "label": wo_policy.LABEL[k]}
            for k in ("AUTO", "CONFIRM", "DAVID", "RESERVED")
        ]
    except Exception:
        pass

    # agent heartbeat — feeds the Company Brain for transparency (latest agent_bus ping)
    try:
        hb = os.path.join(os.path.dirname(state_path), "agent_bus", "heartbeat.json")
        payload["agents"] = json.load(open(hb, encoding="utf-8")).get("agents", []) if os.path.exists(hb) else []
    except Exception as exc:
        _logger.debug("company_state_writer: agents skipped: %s", exc)

    ok = _atomic_write(state_path, payload)
    if ok:
        _logger.debug("company_state_writer: emitted %d rows", len(rows))
    return ok


# ── Safety gate ───────────────────────────────────────────────────────────────

def _is_safety_wo(wo_id: str, board_text: str) -> bool:
    """
    True only if the WO is genuinely in a safety-critical DOMAIN.

    Precise, not substring: checks WORD-BOUNDARY keyword hits in the WO's **title + agent/lane cells
    only** (not the verbose spec text, which trips false positives — e.g. a One Brain motion WO). Prevents
    the M6 false-positive where a keyword was buried inside the row's description.
    """
    kw_re = re.compile(r"\b(" + "|".join(re.escape(k) for k in _SAFETY_KEYWORDS) + r")\b")
    for line in board_text.splitlines():
        if not re.match(r"^\|\s*\*?\*?" + re.escape(wo_id) + r"\*?\*?\s*\|", line.strip()):
            continue
        cells = line.split("|")
        # cells[1]=id, [2]=title, [3]=agent/lane — scope the safety check to these, not the spec text
        scope = " ".join(cells[2:4]).lower()
        return bool(kw_re.search(scope))
    return False


# ── Approval stub (EA2-5 will replace with a real Approval Faculty) ───────────

def _flip_wo_status(wo_id: str, new_status: str, board_path: str = _BOARD_PATH) -> bool:
    """
    Replace the status cell of a WO row in the dispatch board markdown.
    Targeted line-level replacement — does not rewrite unrelated content.
    Returns True if a replacement was made.
    """
    try:
        with open(board_path, encoding="utf-8") as f:
            original = f.read()
    except FileNotFoundError:
        return False

    # Match the specific WO row and replace its 5th pipe-delimited field (status).
    # Pattern: | WO_ID | title | agent | pri | STATUS | ...
    pattern = (
        r"(\|\s*\*?\*?" + re.escape(wo_id) + r"\*?\*?\s*\|"
        r"[^|]+\|[^|]+\|[^|]+\|)"
        r"([^|]+)"
        r"(\|)"
    )
    updated, n = re.subn(pattern, rf"\g<1> {new_status} \3", original, count=1)
    if not n:
        return False

    try:
        tmp = board_path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(updated)
        os.replace(tmp, board_path)
        return True
    except Exception as exc:
        _logger.error("company_state_writer: board flip failed: %s", exc)
        return False


def handle_company_approve(
    work_order: str,
    to_status: str = "DONE",
    actor: str = "",
    human_flag: bool = False,
    board_path: str = _BOARD_PATH,
    state_path: str = _STATE_PATH,
) -> dict:
    """
    CAL stub for company.approve intent.

    EA2-2 wires this to the Presence request channel.
    EA2-5 (Approval Faculty) will replace the stub body.

    Returns: {"ok": bool, "reason": str}
    """
    # L3 gate
    if actor.lower() not in _L3_ACTORS:
        msg = f"company.approve: actor '{actor}' is not L3 — refused"
        _logger.warning(msg)
        return {"ok": False, "reason": msg}

    # Safety gate
    try:
        with open(board_path, encoding="utf-8") as f:
            board_text = f.read()
    except FileNotFoundError:
        board_text = ""

    if _is_safety_wo(work_order, board_text) and not human_flag:
        msg = f"company.approve: {work_order} is safety-gated; human_flag required — refused"
        _logger.warning(msg)
        return {"ok": False, "reason": msg}

    # Flip status and re-emit
    flipped = _flip_wo_status(work_order, to_status, board_path=board_path)
    if not flipped:
        return {"ok": False, "reason": f"company.approve: {work_order} row not found in board"}

    publish(board_path=board_path, state_path=state_path)
    _logger.info("company.approve: %s → %s (actor=%s)", work_order, to_status, actor)
    return {"ok": True, "reason": f"{work_order} → {to_status}"}


# ── Action intake ─────────────────────────────────────────────────────────────

def process_action(action: dict, board_path: str = _BOARD_PATH, state_path: str = _STATE_PATH) -> dict:
    """
    Validate and dispatch one action dict from company_actions.json.

    Supported action types:
      approval_request — flip a WO status (stub: calls handle_company_approve)
      move / reorder   — reserved for EA2-4 Scheduling Faculty

    Always returns a result dict. Never raises.
    """
    try:
        action_type = action.get("type") or action.get("action", "")
        wo_id       = action.get("work_order", "").strip()
        to_status   = action.get("to_status", "DONE").strip()
        actor       = action.get("actor", "").strip()
        human_flag  = bool(action.get("human_flag", False))

        if not action_type:
            return {"ok": False, "reason": "malformed: missing type/action field"}
        if not wo_id:
            return {"ok": False, "reason": "malformed: missing work_order field"}

        if action_type == "approval_request":
            return handle_company_approve(
                work_order=wo_id,
                to_status=to_status,
                actor=actor,
                human_flag=human_flag,
                board_path=board_path,
                state_path=state_path,
            )

        if action_type in ("move", "reorder"):
            msg = f"company_runtime: '{action_type}' reserved for EA2-4 Scheduling Faculty — not yet built"
            _logger.info(msg)
            return {"ok": False, "reason": msg}

        return {"ok": False, "reason": f"unknown action type: '{action_type}'"}

    except Exception as exc:
        _logger.error("company_state_writer.process_action: unexpected error: %s", exc)
        return {"ok": False, "reason": f"internal error: {exc}"}


def _wrap_envelope(action: dict, result: dict) -> None:
    """
    Wrap the action as a Faculty Bus Envelope and publish to the Executive path.
    Best-effort — never blocks or raises.
    """
    try:
        from core.faculty_bus import make_envelope, get_bus
        env = make_envelope(
            sender       = "CompanyRuntime",
            receiver     = "Executive",
            payload_type = action.get("type", "company_action"),
            priority     = "high" if action.get("type") == "approval_request" else "normal",
            body         = {
                "runtime":    "company",
                "type":       action.get("type"),
                "work_order": action.get("work_order"),
                "to_status":  action.get("to_status"),
                "actor":      action.get("actor"),
                "result":     result,
            },
        )
        get_bus().publish(env)
    except Exception as exc:
        _logger.debug("company_state_writer: envelope publish skipped: %s", exc)


_last_action_ts: float = 0.0


def watch_actions(
    interval: float  = 2.0,
    actions_path: str = _ACTIONS_PATH,
    board_path: str   = _BOARD_PATH,
    state_path: str   = _STATE_PATH,
) -> None:
    """
    Blocking poll loop — call from a daemon thread.

    Reads company_actions.json. On a new entry (new _ts), processes the action,
    wraps as Faculty Bus Envelope, then clears the file to prevent re-processing.
    """
    global _last_action_ts
    while True:
        try:
            if os.path.exists(actions_path):
                with open(actions_path, encoding="utf-8") as f:
                    raw = f.read().strip()
                if raw:
                    action = json.loads(raw)
                    ts = float(action.get("_ts", 0.0))
                    if ts > _last_action_ts:
                        _last_action_ts = ts
                        result = process_action(action, board_path=board_path, state_path=state_path)
                        _wrap_envelope(action, result)
                        _logger.info(
                            "company_runtime: action=%s wo=%s result=%s",
                            action.get("type"), action.get("work_order"), result.get("reason"),
                        )
                        # clear so Presence sees acknowledgement (write empty object)
                        _atomic_write(actions_path, {"_cleared": True, "_ts": round(time.time(), 3)})
        except json.JSONDecodeError:
            _logger.warning("company_state_writer: malformed JSON in company_actions.json — skipped")
        except Exception as exc:
            _logger.debug("company_state_writer: watch_actions tick error: %s", exc)
        time.sleep(interval)


# ── EA2-2: voice intent detection + handler ───────────────────────────────────

_COMPANY_INTENTS: dict[str, tuple[str, ...]] = {
    "company.briefing": (
        # identity / general state
        "how's the company", "how is the company", "company status", "company update",
        "company briefing", "company overview", "what's going on with the company",
        "what's the company situation", "company check", "company check-in",
        "how we doing as a company", "company health",
        "how are things", "how are we doing", "how we doing",
        "what's happening at the company", "what's happening with the company",
        "what's disenelo doing", "what's disenelo up to", "what is disenelo doing",
        "what's the company doing", "tell me about the company",
        # focus / priority
        "what's the focus", "what's our focus", "what are we focused on",
        "what's the plan", "what's the priority", "what are the priorities",
        "what's important right now", "what's most important",
        "what should i work on", "what do i work on", "what should we work on",
        "what's next", "what's best to work on", "what to work on",
        # progress / milestone
        "how's the build going", "what's the milestone", "what are we building toward",
        "give me an update", "give me a briefing", "give me the company update",
        "company progress", "what's the progress", "any updates",
        "how's the elo project going", "how's elo os going",
    ),
    "company.board": (
        "company board", "show the board", "show me the board", "what's on the board",
        "what are we building", "company kanban", "work orders overview",
        "what's ready to pick up", "what's in progress",
        "what are we working on", "what's in the pipeline", "board update",
        "board status", "work order status", "what are the work orders",
        "what's in the queue", "the board", "read the board",
    ),
    "company.approvals": (
        "what needs approval", "what needs approving", "pending approvals",
        "company approvals", "waiting for my approval", "what's waiting on me",
        "what do i need to approve", "approval queue", "what needs my sign-off",
    ),
}

# Patterns that require a WO ID in the input
_APPROVE_RE = re.compile(r"\bapprove\s+([\w][\w\-]+)", re.IGNORECASE)
_MOVE_RE    = re.compile(r"\bmove\s+([\w][\w\-]+)\s+to\s+(\w+)", re.IGNORECASE)


def is_company_intent(raw: str) -> str | None:
    """Return the matched company.* intent key, or None if no match."""
    low = raw.lower().strip()
    # Normalise contractions and missing apostrophes so all forms match the pattern list.
    low = (low.replace("what is ", "what's ").replace("how is ", "how's ")
              .replace("it is ", "it's ")
              .replace("hows ", "how's ").replace("whats ", "what's "))
    for intent, patterns in _COMPANY_INTENTS.items():
        if any(p in low for p in patterns):
            return intent
    if _APPROVE_RE.search(raw):
        return "company.approve"
    if _MOVE_RE.search(raw):
        return "company.move"
    return None


def _strip_md(text: str) -> str:
    """Strip markdown bold/italic markers and leading symbols from a title string."""
    return re.sub(r"\*+", "", text).strip(" ↩▲⚠✅⛔▶").strip()


def _load_fresh_state(state_path: str = _STATE_PATH) -> dict:
    """Load company_state.json, republishing from the board first if stale."""
    state: dict = {}
    try:
        with open(state_path, encoding="utf-8") as f:
            state = json.load(f)
    except Exception:
        pass
    # If company_focus is empty the board marker may have been missed — re-publish.
    if not state.get("company_focus"):
        try:
            publish(state_path=state_path)
            with open(state_path, encoding="utf-8") as f:
                state = json.load(f)
        except Exception:
            pass
    return state


def _recommend(state: dict) -> str:
    """Return the single highest-priority unblocked focus WO as a recommendation string."""
    focus = state.get("company_focus", {})
    focus_items = focus.get("items", [])

    # Build set of WO IDs mentioned in the focus items list
    focus_ids: set[str] = set()
    for fi in focus_items:
        for m in re.finditer(r"WO-\d+[A-Z]?", fi):
            focus_ids.add(m.group(0))

    board = state.get("board", [])

    def _score(row: dict) -> int:
        p = row.get("pri", "P3")
        return {"P0": 0, "P1": 1, "P2": 2, "P3": 3}.get(p, 9)

    candidates = []
    for row in board:
        if row.get("status") in ("DONE", "BLOCKED"):
            continue
        wo_id = row.get("id", "")
        # Prefer focus WOs; also accept any open P0/P1 Builder WO as fallback
        if wo_id in focus_ids or (row.get("pri") in ("P0", "P1") and "Builder" in row.get("seat", "")):
            candidates.append(row)

    if not candidates:
        return ""
    candidates.sort(key=_score)
    best = candidates[0]
    title = _strip_md(best.get("title", "").split("—")[0])[:50]
    return f"{best.get('id')} — {title} ({best.get('pri')})"


def _build_briefing(state: dict) -> str:
    """
    WO-048: rich, varied, real briefing reply. API-free — reads company_state.json only.
    Content changes whenever the state changes (varied by design).
    """
    focus = state.get("company_focus", {})
    milestone = focus.get("milestone", "")
    today = state.get("today_priorities", [])
    roadmap = state.get("roadmap", [])
    in_prog = [r for r in state.get("board", []) if r.get("status") == "WORKING"]
    waiting_david = [w for w in state.get("waiting_for_approval", []) if w.get("needs_david")]
    eng = state.get("engineering", {})

    parts: list[str] = []

    # Company identity — always present
    parts.append("DISENELO is building eLo — the character, the world, and the presence —"
                 " across desktop, game, robot, and book.")

    # Active milestone
    if milestone:
        parts.append(f"Current milestone: {milestone}.")

    # What's in flight (focus items)
    if today:
        names = [_strip_md(r.get("text", "?"))[:45] for r in today[:3]]
        parts.append(f"In flight: {'; '.join(names)}.")
    elif in_prog:
        ids = ", ".join(r.get("id", "?") for r in in_prog[:4])
        parts.append(f"In progress: {ids}.")

    # Top recommendation
    rec = _recommend(state)
    if rec:
        parts.append(f"Best to pick up next: {rec}.")

    # Waiting on David
    if waiting_david:
        items = ", ".join(
            f"{w.get('wo','?')} ({_strip_md(w.get('text','?'))[:30]})"
            for w in waiting_david[:3]
        )
        suffix = f" and {len(waiting_david) - 3} more" if len(waiting_david) > 3 else ""
        parts.append(f"Waiting on you: {items}{suffix}.")

    # Engineering headline
    if eng.get("open"):
        parts.append(f"{eng['open']} work orders open, {eng.get('in_review', 0)} in review.")

    # Board link (required by WO-048 spec)
    parts.append("Board: engineering/work_orders/DISPATCH_BOARD.md.")

    return " ".join(parts)


def _build_board_reply(state: dict) -> str:
    """WO-048: board intent → surface FOCUS items, not the ready backlog."""
    focus = state.get("company_focus", {})
    milestone = focus.get("milestone", "")
    today = state.get("today_priorities", [])
    in_prog = [r for r in state.get("board", []) if r.get("status") == "WORKING"]

    parts: list[str] = []
    if milestone:
        parts.append(f"Milestone: {milestone}.")

    if today:
        ids = "; ".join(_strip_md(r.get("text", "?"))[:40] for r in today[:4])
        parts.append(f"Focus items: {ids}.")
    if in_prog:
        ids = ", ".join(r.get("id", "?") for r in in_prog[:5])
        parts.append(f"In progress: {ids}.")

    if not parts:
        return state.get("voiced_briefing", "No board data yet.")

    parts.append("Full board: engineering/work_orders/DISPATCH_BOARD.md.")
    return " ".join(parts)


def handle_company_voice_intent(
    raw: str,
    state_path: str   = _STATE_PATH,
    actions_path: str = _ACTIONS_PATH,
) -> str:
    """
    Handle a company.* voice intent. Returns the spoken reply string.
    For approve/move: also writes to company_actions.json (Presence + watch_actions picks it up).
    WO-048: briefing + board intents now return rich, real, varied answers (no more canned string).
    """
    intent = is_company_intent(raw)

    # WO-048: reload fresh state (re-publishes if company_focus was missed)
    state = _load_fresh_state(state_path)

    voiced = state.get("voiced_briefing", "no data yet")

    if intent in ("company.briefing", None):
        return _build_briefing(state)

    if intent == "company.board":
        return _build_board_reply(state)

    if intent == "company.approvals":
        waiting = [w for w in state.get("waiting_for_approval", []) if w.get("needs_david")]
        if not waiting:
            return "Nothing waiting on you right now."
        items = ", ".join(w.get("wo", "?") for w in waiting[:5])
        suffix = f" and {len(waiting) - 5} more" if len(waiting) > 5 else ""
        return f"{len(waiting)} waiting on you: {items}{suffix}."

    if intent == "company.approve":
        m = _APPROVE_RE.search(raw)
        wo_id = m.group(1).upper() if m else ""
        if not wo_id:
            return "Which work order should I approve?"
        result = handle_company_approve(work_order=wo_id, actor="david", to_status="DONE")
        if result.get("ok"):
            _write_action({"type": "approval_request", "work_order": wo_id,
                           "to_status": "DONE", "actor": "David (L3)"}, actions_path)
            return f"{wo_id} approved and logged."
        return f"Couldn't approve {wo_id} — {result.get('reason', 'check the log')}."

    if intent == "company.move":
        m = _MOVE_RE.search(raw)
        wo_id    = m.group(1).upper() if m else ""
        to_status = m.group(2).upper() if m else ""
        if not wo_id or not to_status:
            return "Which work order and what status?"
        _write_action({"type": "move", "work_order": wo_id, "to_status": to_status,
                       "actor": "David (L3)"}, actions_path)
        return f"Move request sent — {wo_id} → {to_status}. I'll update when it lands."

    return voiced


def _write_action(action: dict, actions_path: str = _ACTIONS_PATH) -> None:
    """Write one action to company_actions.json (atomic). watch_actions picks it up."""
    try:
        action["_ts"] = round(time.time(), 3)
        _atomic_write(actions_path, action)
    except Exception as exc:
        _logger.error("company_state_writer._write_action: %s", exc)


# ── CLI one-shot ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    ok = publish()
    if ok:
        print(f"company_state.json written → {_STATE_PATH}")
        with open(_STATE_PATH, encoding="utf-8") as fh:
            data = json.load(fh)
        print(f"  today_priorities:     {len(data['today_priorities'])} items")
        print(f"  waiting_for_approval: {len(data['waiting_for_approval'])} items")
        print(f"  blocked:              {len(data['blocked'])} items")
        print(f"  board rows:           {len(data['board'])} total")
        print(f"  voiced_briefing:      {data['voiced_briefing']}")
    else:
        print("ERROR: write failed")
        sys.exit(1)
