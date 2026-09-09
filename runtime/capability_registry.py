"""
runtime/capability_registry.py — eLo OS Capability Registry

Registers authorised capabilities and routes dispatch to tool agents.
WO-CREATE-CAPABILITY: CREATE capability (CREATE_FILE, CREATE_DRAFT, CREATE_MODEL, READ_FILE_CONTEXT).

Authority: David L3 global ruling 2026-08-30; SPEC_CE_001_file_output_capability_2026-08-27.md
Lane: Builder only.
"""
from __future__ import annotations

import os
import logging

_log = logging.getLogger(__name__)

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DRAFTS_DIR = os.path.join(_ROOT, "data", "create_drafts")

# ── Capability manifest ───────────────────────────────────────────────────────

CAPABILITY_REGISTRY: dict[str, dict] = {
    "CREATE": {
        "description": "File and draft creation — governed output capability (CE-001)",
        "required_tier": "REASONING",
        "sub_capabilities": {
            "CREATE_FILE":          "tools.llm_file_agent",
            "CREATE_DRAFT":         "tools.draft_agent",
            "CREATE_MODEL":         "tools.model_gen_agent",
            "READ_FILE_CONTEXT":    "tools.file_reader_agent",
            "CREATE_DROP_INGEST":   "runtime.background_drop_watcher",  # WO-DROP-INGESTION
        },
        "output_dir": _DRAFTS_DIR,
        "confirmation_required": True,   # L3 gate — David approves before delivery
    },
    "WORLD_VISUAL_READ": {
        "description": "Visual Brainiser (PE-033) — ingest and reason about visual input",
        "required_tier": "REASONING",
        "sub_capabilities": {
            "DESCRIBE_IMAGE": "tools.vision_agent",
            "SCREENSHOT":     "tools.vision_loop",
        },
        "confirmation_required": False,  # read-only; no write gate needed
        "taste_signal_threshold": 0.72,  # significance ≥ 0.72 → taste_signal: true
    },
    # WO-WORLD-INTERFACE: Phase 1 — Calendar / Reminders / Web / Filesystem (read-only)
    "WORLD_CALENDAR_READ": {
        "description": "Read macOS Calendar events — today/week, read-only",
        "required_tier": "CONVERSATIONAL",
        "sub_capabilities": {"READ_EVENTS": "tools.calendar_agent"},
        "confirmation_required": False,
        "write_allowed": False,   # no calendar writes without per-turn David L3 gate
    },
    "WORLD_REMINDERS_READ": {
        "description": "Read macOS Reminders — due items, read-only",
        "required_tier": "CONVERSATIONAL",
        "sub_capabilities": {"READ_REMINDERS": "tools.reminders_agent"},
        "confirmation_required": False,
        "write_allowed": False,
    },
    "WORLD_WEB_RESEARCH": {
        "description": "Web research — search and summarise, read-only",
        "required_tier": "REASONING",
        "sub_capabilities": {"SEARCH": "tools.web_search"},
        "confirmation_required": False,
        "write_allowed": False,
    },
    "WORLD_FILESYSTEM_READ": {
        "description": "Read files from David's connected folders — Output/, Documents/, Desktop/",
        "required_tier": "CONVERSATIONAL",
        "sub_capabilities": {"READ_FILE": "builtin.open"},
        "confirmation_required": False,
        "write_allowed": False,   # no filesystem writes without per-turn David L3 gate
        "allowed_roots": ["Output", "Documents", "Desktop"],
    },
    # [DAVID 2026-09-05] WORLD_CREATE — authorised 2026-09-05
    # Source: SOURCE_2026-09-05_DAVID_L3_BA02_BA03_BA06_VOICE_ratification.md §BA-06
    # CREATE does not decide when to create. The Executive decides. (One Brain invariant preserved.)
    # Supported output types: written documents, specifications, research outputs, structured files,
    #   drafts, code, project artefacts, research notes.
    # DEFERRED: Blender/3D-related outputs — no appropriate tool confirmed available yet.
    "WORLD_CREATE": {
        "description": "Create files, documents, specifications, drafts, code, research outputs, project artefacts",
        "tools": ["llm_file_agent", "draft_agent", "model_gen_agent"],
        "requires_executive_approval": True,
        "execution_report": True,
        "health_check": "create_health_check",
    },
    # WO-VOICE-IO: Voice I/O capabilities — registered 2026-08-31
    "WORLD_VOICE_OUTPUT": {
        "description": "Speak eLo's response aloud — TTS (OpenAI shimmer primary; ElevenLabs configurable)",
        "required_tier": "CONVERSATIONAL",
        "sub_capabilities": {
            "TTS_OPENAI":    "voice.voice_engine.speak",
            "TTS_ELEVENLABS": "voice.voice_engine.speak_elevenlabs",
            "TTS_SYSTEM":    "voice.voice_engine.speak_system",
        },
        "confirmation_required": False,
        "write_allowed": False,
        "law": "LAW-017",   # Executive must set speech_text; voice output reads it
    },
    "WORLD_VOICE_INPUT": {
        "description": "Listen for David's voice — STT (Whisper API primary; local whisper fallback)",
        "required_tier": "CONVERSATIONAL",
        "sub_capabilities": {
            "STT_WHISPER_API":   "voice.stt.transcribe_whisper_api",
            "STT_WHISPER_LOCAL": "voice.stt.transcribe_local",
            "STT_STDIN":         "voice.stt.transcribe_stdin",
        },
        "confirmation_required": False,
        "write_allowed": False,
        "silence_threshold_s": 1.5,   # default from voice/stt.py
    },
}


# ── Dispatch ─────────────────────────────────────────────────────────────────

def is_registered(capability: str) -> bool:
    """Return True if the capability name is registered."""
    return capability.upper() in CAPABILITY_REGISTRY


def get_capability(capability: str) -> dict | None:
    """Return the capability spec dict, or None if not registered."""
    return CAPABILITY_REGISTRY.get(capability.upper())


def create_health_check() -> dict:
    """
    WO-CREATE-001 D-4: Health status for all CREATE tools.

    Returns which tools are importable and functionally present.
    Does not execute any tool — importability check only.
    """
    _tools = {
        "llm_file_agent":  "tools.llm_file_agent",
        "draft_agent":     "tools.draft_agent",
        "model_gen_agent": "tools.model_gen_agent",
    }
    import importlib
    status: dict[str, dict] = {}
    for name, module_path in _tools.items():
        try:
            mod = importlib.import_module(module_path)
            status[name] = {
                "importable": True,
                "has_agent":  hasattr(mod, "agent"),
                "status":     "OK" if hasattr(mod, "agent") else "MISSING_AGENT_FN",
            }
        except Exception as _e:
            status[name] = {"importable": False, "has_agent": False, "status": str(_e)}

    all_ok = all(v["importable"] and v["has_agent"] for v in status.values())
    return {
        "healthy":     all_ok,
        "tools":       status,
        "capability":  "WORLD_CREATE",
        "deferred":    ["blender_3d_outputs"],   # no tool confirmed available
    }


def dispatch_create(query: str, sub_capability: str = "CREATE_DRAFT", **kwargs) -> dict:
    """
    WO-CREATE-IMPL-001: Dispatch a CREATE capability request.

    sub_capability options:
        CREATE_FILE — create a file at kwargs["path"] with kwargs["content"]
        READ_FILE   — read kwargs["path"]
        EDIT_FILE   — append/edit kwargs["path"] with kwargs["instructions"]
        MOVE_FILE   — move kwargs["src"] to kwargs["dest"]
        SAVE_NOTE   — save note with kwargs["content"] and optional kwargs["tag"]
        RUN_PYTHON  — execute kwargs["code"] in sandboxed subprocess
        GENERATE_RESEARCH — research kwargs["query"]
        CREATE_DRAFT — generate creative content from query (draft_agent)

    Returns:
        {dispatched, sub_capability, draft_path, notification, error}
    """
    import importlib
    os.makedirs(_DRAFTS_DIR, exist_ok=True)

    result: dict = {
        "dispatched":     False,
        "sub_capability": sub_capability,
        "draft_path":     None,
        "notification":   "",
        "error":          None,
    }

    try:
        _ec = importlib.import_module("tools.elo_create")

        if sub_capability == "CREATE_FILE":
            _path    = kwargs.get("path", os.path.join(_DRAFTS_DIR, f"elo_file_{int(__import__('time').time())}.md"))
            _content = kwargs.get("content", query)
            _purpose = kwargs.get("purpose", "")
            _r = _ec.create_file(_path, _content, _purpose)
            result["dispatched"]   = _r["success"]
            result["draft_path"]   = _r.get("path")
            result["notification"] = _r["notification"]
            result["error"]        = _r.get("error")

        elif sub_capability == "READ_FILE":
            _path = kwargs.get("path", "")
            _r = _ec.read_file(_path)
            result["dispatched"]   = _r["success"]
            result["notification"] = _r.get("content", "")[:500] or _r.get("error", "nothing there")
            result["error"]        = _r.get("error")

        elif sub_capability == "EDIT_FILE":
            _path  = kwargs.get("path", "")
            _instr = kwargs.get("instructions", query)
            _r = _ec.edit_file(_path, _instr)
            result["dispatched"]   = _r["success"]
            result["notification"] = _r["notification"]
            result["error"]        = _r.get("error")

        elif sub_capability == "MOVE_FILE":
            _src  = kwargs.get("src", "")
            _dest = kwargs.get("dest", "")
            _r = _ec.move_file(_src, _dest)
            result["dispatched"]   = _r["success"]
            result["notification"] = _r["notification"]
            result["error"]        = _r.get("error")

        elif sub_capability == "SAVE_NOTE":
            _content = kwargs.get("content", query)
            _tag     = kwargs.get("tag", "")
            _r = _ec.save_note(_content, _tag)
            result["dispatched"]   = _r["success"]
            result["draft_path"]   = _r.get("path")
            result["notification"] = _r["notification"]
            result["error"]        = _r.get("error")

        elif sub_capability == "RUN_PYTHON":
            _code = kwargs.get("code", query)
            _r = _ec.run_python(_code)
            result["dispatched"]   = _r["success"]
            result["notification"] = _r["notification"]
            result["error"]        = _r.get("error")

        elif sub_capability == "GENERATE_RESEARCH":
            _q = kwargs.get("query", query)
            _r = _ec.generate_research(_q)
            result["dispatched"]   = _r["success"]
            result["notification"] = _r["notification"]
            result["error"]        = _r.get("error")

        elif sub_capability in ("CREATE_DRAFT", "CREATE_FILE_DRAFT"):
            from tools.draft_agent import agent as _draft_agent
            _draft_output = _draft_agent(query)

            import time as _time, re as _re
            _slug = _re.sub(r"[^\w]+", "_", query[:40]).strip("_").lower()
            _draft_fname = f"draft_{_slug}_{int(_time.time())}.md"
            _draft_path  = os.path.join(_DRAFTS_DIR, _draft_fname)
            with open(_draft_path, "w", encoding="utf-8") as _df:
                _df.write(_draft_output)
            result["dispatched"]   = True
            result["draft_path"]   = _draft_path
            result["notification"] = f"Draft ready — {_draft_fname}"

        elif sub_capability == "READ_FILE_CONTEXT":
            from tools.file_reader_agent import agent as _file_reader
            _file_reader(query)
            result["dispatched"]   = True
            result["notification"] = "File context read."

        else:
            result["error"]        = f"Unknown sub_capability: {sub_capability!r}"
            result["notification"] = "I don't know that CREATE type."

    except Exception as _e:
        _log.warning("dispatch_create FAILED: %s", _e)
        result["error"]        = str(_e)
        result["notification"] = "Hit a snag on that one."

    return result


def dispatch_visual(image_path: str | None, query: str = "", significance: float = 0.0) -> dict:
    """
    WO-VISUAL-BRAINISER (PE-033): Visual Brainiser dispatch.

    Ingests an image path or screenshot and returns a structured visual description.
    Output enters cognitive state as a perception input (alongside text).
    Sets taste_signal=True when significance >= 0.72.

    Returns:
        {
            "dispatched": bool,
            "description": str,          # visual description from vision_agent
            "taste_signal": bool,
            "epistemic_class": str,      # "VERIFIED" if dispatched successfully
            "error": str | None,
        }
    """
    cap = CAPABILITY_REGISTRY.get("WORLD_VISUAL_READ")
    if not cap:
        return {"dispatched": False, "error": "WORLD_VISUAL_READ not registered", "description": ""}

    result: dict = {
        "dispatched":      False,
        "description":     "",
        "taste_signal":    False,
        "epistemic_class": "UNKNOWN",
        "error":           None,
    }

    try:
        from tools.vision_agent import agent as _vision_agent
        _prompt = query if query else (f"Describe this image: {image_path}" if image_path else "Describe what you see.")
        _description = _vision_agent(_prompt)
        result["dispatched"]      = True
        result["description"]     = _description or ""
        result["epistemic_class"] = "VERIFIED" if _description else "UNKNOWN"
        result["taste_signal"]    = significance >= cap.get("taste_signal_threshold", 0.72)
    except Exception as _ve:
        _log.warning("dispatch_visual FAILED: %s", _ve)
        result["error"] = str(_ve)

    return result


# ── WO-WORLD-INTERFACE dispatch helpers ───────────────────────────────────────

def dispatch_calendar(query: str = "today") -> dict:
    """Read macOS Calendar events. Read-only — no write without David L3 per-turn gate."""
    result: dict = {"dispatched": False, "events": [], "error": None, "write_blocked": True}
    try:
        from tools.calendar_agent import agent as _cal
        _raw = _cal(query)
        result["dispatched"] = True
        result["events"]     = [_raw] if isinstance(_raw, str) else list(_raw)
    except Exception as _e:
        _log.warning("dispatch_calendar FAILED: %s", _e)
        result["error"] = str(_e)
    return result


def dispatch_reminders(query: str = "due") -> dict:
    """Read macOS Reminders. Read-only — no write without David L3 per-turn gate."""
    result: dict = {"dispatched": False, "reminders": [], "error": None, "write_blocked": True}
    try:
        from tools.reminders_agent import agent as _rem
        _raw = _rem(query)
        result["dispatched"]  = True
        result["reminders"]   = [_raw] if isinstance(_raw, str) else list(_raw)
    except Exception as _e:
        _log.warning("dispatch_reminders FAILED: %s", _e)
        result["error"] = str(_e)
    return result


def dispatch_web_research(query: str) -> dict:
    """Web research — search and summarise. Read-only output."""
    result: dict = {"dispatched": False, "results": [], "error": None, "write_blocked": True}
    try:
        from tools.web_search import search as _search, SearchResult
        _raw = _search(query, max_results=5)
        result["dispatched"] = True
        result["results"]    = [
            {"title": r.title, "url": r.url, "snippet": r.snippet}
            if hasattr(r, "title") else {"text": str(r)}
            for r in (_raw or [])
        ]
    except Exception as _e:
        _log.warning("dispatch_web_research FAILED: %s", _e)
        result["error"] = str(_e)
    return result


def read_company_state() -> dict:
    """
    WO-COMPANY-INTERFACE-001: read DISPATCH_BOARD.md and return structured company state.
    Returns {active, blocked, waiting_for_david, next_governed_item, raw_summary}.
    """
    result: dict = {
        "dispatched": False,
        "active": [],
        "blocked": [],
        "waiting_for_david": [],
        "next_governed_item": "",
        "raw_summary": "",
        "error": None,
    }
    _board_path = os.path.join(_ROOT, "engineering", "work_orders", "DISPATCH_BOARD.md")
    try:
        with open(_board_path, encoding="utf-8", errors="replace") as _f:
            _board = _f.read()
    except Exception as _e:
        result["error"] = f"DISPATCH_BOARD unreadable: {_e}"
        return result

    # Parse blocking indicators and WO states from the board
    _lines = _board.splitlines()
    _active: list[str] = []
    _blocked: list[str] = []
    _waiting: list[str] = []
    _next_item: str = ""

    for _line in _lines:
        _ll = _line.lower()
        if "🔴" in _line and ("in progress" in _ll or "active" in _ll):
            _active.append(_line.strip())
        elif "🔴" in _line and ("blocked" in _ll):
            _blocked.append(_line.strip())
        elif "david l3" in _ll and ("pending" in _ll or "awaiting" in _ll or "ba-" in _ll):
            _waiting.append(_line.strip())
        elif "🟡" in _line and not _next_item and "wo-" in _ll:
            _next_item = _line.strip()

    # Summary of the board's most recent §62-style section (first 800 chars)
    _summary_start = _board.find("§")
    _raw = _board[_summary_start:_summary_start + 800] if _summary_start >= 0 else _board[:800]

    result.update({
        "dispatched": True,
        "active": _active[:5],
        "blocked": _blocked[:5],
        "waiting_for_david": _waiting[:5],
        "next_governed_item": _next_item,
        "raw_summary": _raw.strip(),
    })
    return result


def dispatch_filesystem_read(path: str) -> dict:
    """Read a file from David's connected folders. Read-only."""
    result: dict = {"dispatched": False, "content": "", "error": None, "write_blocked": True}
    cap = CAPABILITY_REGISTRY.get("WORLD_FILESYSTEM_READ", {})
    _roots = cap.get("allowed_roots", [])
    # Gate: only allowed roots
    _norm = os.path.normpath(os.path.expanduser(path))
    _allowed = any(root in _norm for root in _roots) or any(root.lower() in path.lower() for root in _roots)
    if not _allowed:
        result["error"] = f"Path not in allowed roots {_roots}: {path!r}"
        return result
    try:
        with open(_norm, encoding="utf-8", errors="replace") as _f:
            result["content"]    = _f.read()
        result["dispatched"] = True
    except Exception as _e:
        _log.warning("dispatch_filesystem_read FAILED: %s", _e)
        result["error"] = str(_e)
    return result
